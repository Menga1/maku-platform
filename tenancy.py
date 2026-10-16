"""
MAKU - tenant isolation (review finding F2, P0)
================================================
Every read and write of organization data goes through this module. The
browser can only *choose* among organizations; whether the signed-in user may
act there is decided here, on the server, from the database, on every request.

Who may do what
---------------
  * Platform administrator - users.role = 'admin', or an account configured by
    the deployment (secrets / MAKU_AUTH_USERS). Sees and manages every
    organization. Creates organizations and memberships.
  * Organization members (organization_members table), one role per
    organization:
        viewer       read
        supervisor   read, write               (run and log assessments)
        org_admin    read, write, manage       (manage that organization)
  * Anyone else - including an unauthenticated session - has no access at all
    (fail closed).

A user can belong to several organizations (consultants, contractors) with a
different role in each.

Usage
-----
    principal = tenancy.principal_from_session(st)
    tenancy.require_access(principal, organization_id, "write")   # raises TenantAccessDenied
    orgs = tenancy.accessible_organizations(principal)

Denied attempts are written to the audit log (ACCESS_DENIED).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("maku.tenancy")

ORG_ROLES = ("viewer", "supervisor", "org_admin")
DEFAULT_ORG_ROLE = "supervisor"
ACTIONS = ("read", "write", "manage")
PERMISSIONS = {
    "viewer": frozenset({"read"}),
    "supervisor": frozenset({"read", "write"}),
    "org_admin": frozenset({"read", "write", "manage"}),
}
PLATFORM_ADMIN_ROLE = "platform_admin"
AUDIT_EVENT_ACCESS_DENIED = "ACCESS_DENIED"
AUDIT_EVENT_MEMBERSHIP_CHANGED = "MEMBERSHIP_CHANGED"
AUDIT_EVENT_ORGANIZATION_CREATED = "ORGANIZATION_CREATED"


class TenantAccessDenied(PermissionError):
    """The principal may not perform this action in this organization."""


class TenancyError(ValueError):
    """Invalid membership or organization request."""


@dataclass(frozen=True)
class Principal:
    username: str | None
    platform_admin: bool = False

    @property
    def authenticated(self) -> bool:
        return bool(self.username)


ANONYMOUS = Principal(None, False)


def principal_from_session(st_module) -> Principal:
    """The signed-in user, as established by auth.require_login(). Values in
    session_state are written only by the server after credential checks;
    the browser cannot set them."""
    state = st_module.session_state
    if not state.get("authenticated"):
        return ANONYMOUS
    username = state.get("_auth_username") or None
    if not username:
        return ANONYMOUS
    return Principal(username, state.get("_auth_role") == "admin")


def _analytics():
    import analytics
    return analytics


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ lookups
def membership_role(username: str, organization_id: int) -> str | None:
    a = _analytics()
    with a._get_connection() as conn:
        row = conn.execute(
            "SELECT role FROM organization_members WHERE username = ? AND organization_id = ?",
            (username, int(organization_id))).fetchone()
    return row[0] if row else None


def accessible_organizations(principal: Principal) -> list[dict]:
    """[{id, name, role}] the principal may at least read, sorted by name."""
    if not principal.authenticated:
        return []
    a = _analytics()
    with a._get_connection() as conn:
        if principal.platform_admin:
            rows = conn.execute("SELECT id, name FROM organizations ORDER BY name").fetchall()
            return [{"id": r[0], "name": r[1], "role": PLATFORM_ADMIN_ROLE} for r in rows]
        rows = conn.execute(
            "SELECT o.id, o.name, m.role FROM organization_members m "
            "JOIN organizations o ON o.id = m.organization_id WHERE m.username = ? ORDER BY o.name",
            (principal.username,)).fetchall()
    return [{"id": r[0], "name": r[1], "role": r[2]} for r in rows]


def role_in(principal: Principal, organization_id: int | None) -> str | None:
    if not principal.authenticated or organization_id is None:
        return None
    if principal.platform_admin:
        return PLATFORM_ADMIN_ROLE
    return membership_role(principal.username, organization_id)


def can(principal: Principal, organization_id: int | None, action: str) -> bool:
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    role = role_in(principal, organization_id)
    if role is None:
        return False
    if role == PLATFORM_ADMIN_ROLE:
        return True
    return action in PERMISSIONS.get(role, frozenset())


def require_access(principal: Principal, organization_id: int | None, action: str) -> None:
    """Raises TenantAccessDenied (and audits it) unless allowed."""
    if can(principal, organization_id, action):
        return
    who = principal.username or "anonymous"
    logger.warning("Access denied: %s may not %s organization %s", who, action, organization_id)
    try:
        _analytics().log_audit_event(AUDIT_EVENT_ACCESS_DENIED, actor=who,
                                     detail=f"action={action} organization_id={organization_id}",
                                     organization_id=organization_id)
    except Exception:  # noqa: BLE001 - auditing must not mask the denial
        pass
    raise TenantAccessDenied(f"{who} may not {action} in organization {organization_id}")


# --------------------------------------------------------- administration
def _require_platform_admin(actor: Principal) -> None:
    if not actor.platform_admin:
        raise TenantAccessDenied("Only a platform administrator can do this.")


def create_organization(actor: Principal, name: str) -> int:
    _require_platform_admin(actor)
    with _analytics().acting_as(actor):   # the database sees the same identity (RLS)
        return _create_organization(actor, name)


def _create_organization(actor: Principal, name: str) -> int:
    name = (name or "").strip()
    if not name or len(name) > 120:
        raise TenancyError("Organization name must be 1-120 characters.")
    a = _analytics()
    with a._get_connection() as conn:
        org_id = a._get_or_create_id(conn, "organizations", {}, "name", name)
    a.log_audit_event(AUDIT_EVENT_ORGANIZATION_CREATED, actor=actor.username or "system",
                      detail=f"organization={name}", organization=name, organization_id=org_id)
    return org_id


SYSTEM_PRINCIPAL = Principal("system", True)


def create_personal_workspace(username: str) -> int:
    """A private organization for a self-registered user, who becomes its
    org_admin - so a new account can use every module straight away and
    still only ever sees its own data. The name carries no personal data
    (a random suffix), so nothing identifying remains after the account
    is deleted."""
    import secrets
    with _analytics().acting_as(SYSTEM_PRINCIPAL):
        for _ in range(5):
            name = f"Personal workspace {secrets.token_hex(4)}"
            if organization_id_by_name(name) is None:
                break
        org_id = _create_organization(SYSTEM_PRINCIPAL, name)
        _set_membership(SYSTEM_PRINCIPAL, username, org_id, "org_admin")
    return org_id


def organization_id_by_name(name: str) -> int | None:
    a = _analytics()
    with a._get_connection() as conn:
        row = conn.execute("SELECT id FROM organizations WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def set_membership(actor: Principal, username: str, organization_id: int, role: str = DEFAULT_ORG_ROLE) -> None:
    with _analytics().acting_as(actor):   # the database sees the same identity (RLS)
        _set_membership(actor, username, organization_id, role)


def _set_membership(actor: Principal, username: str, organization_id: int, role: str) -> None:
    """Adds or changes a membership. Platform admins can manage any
    organization; an org_admin can manage their own organization but cannot
    create another org_admin."""
    if role not in ORG_ROLES:
        raise TenancyError(f"Role must be one of {', '.join(ORG_ROLES)}.")
    if not actor.platform_admin:
        require_access(actor, organization_id, "manage")
        if role == "org_admin":
            raise TenantAccessDenied("Only a platform administrator can appoint an organization admin.")
    username = (username or "").strip()
    if not username:
        raise TenancyError("Username required.")
    a = _analytics()
    with a._get_connection() as conn:
        if conn.execute("SELECT 1 FROM organizations WHERE id = ?", (int(organization_id),)).fetchone() is None:
            raise TenancyError("Unknown organization.")
        updated = conn.execute(
            "UPDATE organization_members SET role = ? WHERE username = ? AND organization_id = ?",
            (role, username, int(organization_id))).rowcount
        if not updated:
            conn.execute(
                "INSERT INTO organization_members (username, organization_id, role, created_at, created_by) "
                "VALUES (?, ?, ?, ?, ?)", (username, int(organization_id), role, _now(), actor.username))
    a.log_audit_event(AUDIT_EVENT_MEMBERSHIP_CHANGED, actor=actor.username or "system",
                      detail=f"user={username} role={role}", organization_id=int(organization_id))


def remove_membership(actor: Principal, username: str, organization_id: int) -> bool:
    with _analytics().acting_as(actor):   # the database sees the same identity (RLS)
        return _remove_membership(actor, username, organization_id)


def _remove_membership(actor: Principal, username: str, organization_id: int) -> bool:
    if not actor.platform_admin:
        require_access(actor, organization_id, "manage")
    a = _analytics()
    with a._get_connection() as conn:
        removed = conn.execute("DELETE FROM organization_members WHERE username = ? AND organization_id = ?",
                               (username, int(organization_id))).rowcount
    if removed:
        a.log_audit_event(AUDIT_EVENT_MEMBERSHIP_CHANGED, actor=actor.username or "system",
                          detail=f"user={username} removed", organization_id=int(organization_id))
    return bool(removed)


def list_memberships(username: str | None = None) -> list[dict]:
    a = _analytics()
    sql = ("SELECT m.username, o.id, o.name, m.role, m.created_at FROM organization_members m "
           "JOIN organizations o ON o.id = m.organization_id")
    params: tuple = ()
    if username:
        sql += " WHERE m.username = ?"
        params = (username,)
    with a._get_connection() as conn:
        rows = conn.execute(sql + " ORDER BY o.name, m.username", params).fetchall()
    return [{"username": r[0], "organization_id": r[1], "organization": r[2], "role": r[3],
             "created_at": r[4]} for r in rows]
