"""
MAKU - Accounts, server-side brute-force protection, privacy consent and
account deletion
===========================================================================
Everything here is stored in the application database (analytics.py's
pooled connection - SQLite in development, PostgreSQL in production), so it
survives restarts, is shared by every app instance behind the load
balancer, and cannot be reset by refreshing the browser.

  * users            - database-managed accounts (bcrypt hashes only).
  * login_attempts   - every login attempt; lockout is computed from this
                       table per username AND per client IP.
  * user_consents    - GDPR (EU 2016/679) / UAE PDPL (Federal Decree-Law
                       45/2021) purpose-specific consent, versioned against
                       the privacy-policy version the user saw.
  * account_deletions- proof that a deletion happened (SHA-256 of the
                       username + timestamp only - no personal data).

Deployment-managed "bootstrap" accounts (from st.secrets / environment, see
auth.py) still exist for the first administrator; they are not stored here
and cannot be self-deleted in-app (remove them from the deployment
configuration instead).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import bcrypt
from argon2 import PasswordHasher
from argon2 import exceptions as argon2_errors

import analytics as _analytics

logger = logging.getLogger("maku.accounts")

# Password storage (review finding F3). New hashes are Argon2id with the
# RFC 9106 second recommended parameter set (t=3, m=64 MiB, p=4). bcrypt
# hashes from earlier versions are still verified and are upgraded to
# Argon2id automatically at the user's next successful sign-in. Plain text and
# unsalted SHA-256 are rejected.
ARGON2_PREFIX = "argon2:"
BCRYPT_PREFIX = "bcrypt:"
BCRYPT_ROUNDS = 12
ACCEPTED_FORMATS = ("argon2", "bcrypt")
_ARGON2 = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=4, hash_len=32, salt_len=16)
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256   # Argon2 has no 72-byte limit; this only guards against abuse

ROLES = ("viewer", "supervisor", "admin")
DEFAULT_ROLE = "supervisor"

# Brute-force policy (server-side, shared across all sessions/instances).
MAX_FAILED_PER_USER = int(os.environ.get("MAKU_MAX_FAILED_PER_USER", "5"))
MAX_FAILED_PER_IP = int(os.environ.get("MAKU_MAX_FAILED_PER_IP", "20"))
FAILURE_WINDOW_SECONDS = int(os.environ.get("MAKU_FAILURE_WINDOW_SECONDS", "900"))    # 15 min
LOCKOUT_SECONDS = int(os.environ.get("MAKU_LOCKOUT_SECONDS", "900"))                  # 15 min
ATTEMPT_RETENTION_SECONDS = 7 * 24 * 3600

# Consent purposes. Keep keys stable - they are stored in the database.
PRIVACY_POLICY_VERSION = os.environ.get("MAKU_PRIVACY_POLICY_VERSION", "2026-10")
PRIVACY_POLICY_URL = os.environ.get("MAKU_PRIVACY_POLICY_URL", "https://maku.ae/privacy")
CONSENT_AI = "ai_processing"
CONSENT_LOCATION = "location"
CONSENT_PURPOSES = (CONSENT_AI, CONSENT_LOCATION)

_USERNAME_RE = re.compile(r"^[A-Za-z0-9._@-]{3,64}$")


class AccountError(Exception):
    """User-facing validation error (safe to display)."""


class AccountStoreUnavailable(Exception):
    """The database could not be reached. Callers fail closed."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _conn():
    if _analytics.is_db_fatal():
        raise AccountStoreUnavailable("database unavailable")
    try:
        return _analytics._get_connection()
    except Exception as exc:  # noqa: BLE001
        logger.error("Account store connection failed: %s", exc)
        raise AccountStoreUnavailable("database unavailable") from exc


# ---------------------------------------------------------------------------
# Password hashing (Argon2id; bcrypt verified and upgraded)
# ---------------------------------------------------------------------------

def password_policy_problems(password: str) -> list[str]:
    """Human-readable reasons the password fails the policy ([] = OK)."""
    password = password or ""
    problems = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        problems.append(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")
    classes = sum(bool(re.search(p, password)) for p in (r"[a-z]", r"[A-Z]", r"[0-9]", r"[^A-Za-z0-9]"))
    if classes < 3:
        problems.append("Password must mix at least three of: lowercase, uppercase, digits, symbols.")
    return problems


def validate_password_strength(password: str) -> None:
    problems = password_policy_problems(password)
    if problems:
        raise AccountError(problems[0])


def credential_format(stored: str | None) -> str:
    """'argon2' | 'bcrypt' | 'sha256' | 'plaintext' | 'empty'."""
    stored = (stored or "").strip()
    if not stored:
        return "empty"
    if stored.startswith(ARGON2_PREFIX):
        return "argon2"
    if stored.startswith(BCRYPT_PREFIX):
        return "bcrypt"
    if stored.startswith("sha256:"):
        return "sha256"
    return "plaintext"


def hash_password(plaintext: str) -> str:
    """'argon2:$argon2id$...' - the format for every new password."""
    if len(plaintext or "") > MAX_PASSWORD_LENGTH:
        raise AccountError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")
    return ARGON2_PREFIX + _ARGON2.hash(plaintext or "")


def verify_password(stored: str, supplied: str) -> bool:
    """Constant-time verification of an Argon2id or bcrypt credential. Any
    other stored format is rejected (fails closed). Never raises."""
    fmt = credential_format(stored)
    supplied = supplied or ""
    if len(supplied) > MAX_PASSWORD_LENGTH:
        return False
    try:
        if fmt == "argon2":
            return _ARGON2.verify(stored[len(ARGON2_PREFIX):].strip(), supplied)
        if fmt == "bcrypt":
            raw = supplied.encode("utf-8")
            if len(raw) > 72:        # bcrypt cannot have stored such a password
                return False
            return bcrypt.checkpw(raw, stored[len(BCRYPT_PREFIX):].strip().encode("utf-8"))
    except (argon2_errors.VerificationError, argon2_errors.InvalidHashError, ValueError):
        return False
    return False


def needs_rehash(stored: str) -> bool:
    """True for bcrypt hashes and for Argon2id hashes with outdated parameters."""
    fmt = credential_format(stored)
    if fmt == "bcrypt":
        return True
    if fmt == "argon2":
        try:
            return _ARGON2.check_needs_rehash(stored[len(ARGON2_PREFIX):].strip())
        except argon2_errors.InvalidHashError:
            return True
    return False


def upgrade_stored_hash(username: str, plaintext: str) -> bool:
    """After a successful sign-in with an old-format hash, store a fresh
    Argon2id hash. Database accounts only (deployment accounts live in
    secrets the app cannot rewrite). Best-effort; never blocks sign-in."""
    try:
        with _conn() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                         (hash_password(plaintext), username))
        _analytics.log_audit_event(AUDIT_EVENT_PASSWORD_REHASHED, actor=username,
                                   detail="upgraded to argon2id")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not upgrade password hash for %s: %s", username, exc.__class__.__name__)
        return False


AUDIT_EVENT_PASSWORD_REHASHED = "PASSWORD_REHASHED"


# A real Argon2id hash used to equalize timing for unknown usernames.
_DECOY_HASH = hash_password("decoy-password-never-matches-anything")


def burn_equal_time(supplied: str) -> None:
    verify_password(_DECOY_HASH, supplied)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _validate_username(username: str) -> str:
    username = (username or "").strip()
    if not _USERNAME_RE.match(username):
        raise AccountError("Username must be 3-64 characters: letters, digits, '.', '_', '-', '@'.")
    return username


def get_user(username: str) -> dict | None:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT username, password_hash, role, email, created_at, last_login_at, is_active "
            "FROM users WHERE username = ?", (username,),
        )
        row = cur.fetchone()
    if not row or not row[6]:
        return None
    return {"username": row[0], "password_hash": row[1], "role": row[2], "email": row[3],
            "created_at": row[4], "last_login_at": row[5]}


def list_users() -> list[dict]:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT username, role, email, created_at, last_login_at FROM users "
            "WHERE is_active = 1 ORDER BY username"
        )
        rows = cur.fetchall()
    return [{"username": r[0], "role": r[1], "email": r[2], "created_at": r[3], "last_login_at": r[4]}
            for r in rows]


def create_user(username: str, password: str, role: str = DEFAULT_ROLE,
                created_by: str = "system", email: str | None = None) -> None:
    username = _validate_username(username)
    if role not in ROLES:
        raise AccountError(f"Role must be one of {', '.join(ROLES)}.")
    validate_password_strength(password)
    with _conn() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            raise AccountError("That username already exists.")
        conn.execute(
            "INSERT INTO users (username, password_hash, role, email, created_at, created_by, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            (username, hash_password(password), role, email, _now_iso(), created_by),
        )
    _analytics.log_audit_event(_analytics.AUDIT_EVENT_USER_CREATED, actor=created_by,
                               detail=f"user={username} role={role}")


def change_password(username: str, current_password: str, new_password: str) -> None:
    user = get_user(username)
    if not user or not verify_password(user["password_hash"], current_password):
        raise AccountError("Current password is incorrect.")
    validate_password_strength(new_password)
    with _conn() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                     (hash_password(new_password), username))
    _analytics.log_audit_event(_analytics.AUDIT_EVENT_PASSWORD_CHANGED, actor=username)


def mark_login(username: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE users SET last_login_at = ? WHERE username = ?", (_now_iso(), username))


# ---------------------------------------------------------------------------
# Server-side brute-force lockout
# ---------------------------------------------------------------------------

def record_login_attempt(username: str, client_ip: str | None, succeeded: bool,
                         now: float | None = None) -> None:
    now = time.time() if now is None else now
    with _conn() as conn:
        conn.execute(
            "INSERT INTO login_attempts (username, client_ip, attempted_at, succeeded) VALUES (?, ?, ?, ?)",
            ((username or "")[:128], client_ip, now, 1 if succeeded else 0),
        )
        if succeeded:
            # A successful login clears that account's failure streak.
            conn.execute("DELETE FROM login_attempts WHERE username = ? AND succeeded = 0", (username,))
        # Opportunistic pruning keeps the table small.
        conn.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (now - ATTEMPT_RETENTION_SECONDS,))


def _lock_remaining(failure_times: list[float], threshold: int, now: float) -> int:
    if len(failure_times) < threshold:
        return 0
    lock_until = max(failure_times) + LOCKOUT_SECONDS
    return max(0, int(lock_until - now))


def lockout_status(username: str, client_ip: str | None, now: float | None = None) -> tuple[bool, int]:
    """(locked, retry_after_seconds). Locked when the username has
    >= MAX_FAILED_PER_USER failures, or the client IP has >= MAX_FAILED_PER_IP
    failures, inside the rolling FAILURE_WINDOW_SECONDS; the lock lasts
    LOCKOUT_SECONDS from the most recent failure."""
    now = time.time() if now is None else now
    since = now - max(FAILURE_WINDOW_SECONDS, LOCKOUT_SECONDS)
    with _conn() as conn:
        cur = conn.execute(
            "SELECT attempted_at FROM login_attempts WHERE username = ? AND succeeded = 0 AND attempted_at >= ?",
            ((username or "")[:128], since),
        )
        user_failures = [float(r[0]) for r in cur.fetchall()]
        ip_failures: list[float] = []
        if client_ip:
            cur = conn.execute(
                "SELECT attempted_at FROM login_attempts WHERE client_ip = ? AND succeeded = 0 AND attempted_at >= ?",
                (client_ip, since),
            )
            ip_failures = [float(r[0]) for r in cur.fetchall()]
    window_user = [t for t in user_failures if t >= now - FAILURE_WINDOW_SECONDS] or user_failures
    remaining = max(_lock_remaining(window_user, MAX_FAILED_PER_USER, now),
                    _lock_remaining(ip_failures, MAX_FAILED_PER_IP, now))
    return remaining > 0, remaining


# ---------------------------------------------------------------------------
# Consent (GDPR / UAE PDPL)
# ---------------------------------------------------------------------------

def get_consents(username: str) -> dict[str, bool | None]:
    """{purpose: True/False, or None if never asked / policy version changed}."""
    result: dict[str, bool | None] = {p: None for p in CONSENT_PURPOSES}
    with _conn() as conn:
        cur = conn.execute(
            "SELECT purpose, granted, policy_version FROM user_consents WHERE username = ?", (username,),
        )
        for purpose, granted, version in cur.fetchall():
            if purpose in result and version == PRIVACY_POLICY_VERSION:
                result[purpose] = bool(granted)
    return result


def set_consent(username: str, purpose: str, granted: bool) -> None:
    if purpose not in CONSENT_PURPOSES:
        raise AccountError(f"Unknown consent purpose '{purpose}'.")
    with _conn() as conn:
        conn.execute("DELETE FROM user_consents WHERE username = ? AND purpose = ?", (username, purpose))
        conn.execute(
            "INSERT INTO user_consents (username, purpose, granted, policy_version, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, purpose, 1 if granted else 0, PRIVACY_POLICY_VERSION, _now_iso()),
        )
    _analytics.log_audit_event(_analytics.AUDIT_EVENT_CONSENT_CHANGED, actor=username,
                               detail=f"{purpose}={'granted' if granted else 'withdrawn'} "
                                      f"policy={PRIVACY_POLICY_VERSION}")


def has_consent(username: str, purpose: str) -> bool:
    try:
        return bool(get_consents(username).get(purpose))
    except AccountStoreUnavailable:
        return False  # fail closed: no consent record -> no processing


# ---------------------------------------------------------------------------
# Data subject rights: export and deletion
# ---------------------------------------------------------------------------

def export_user_data(username: str) -> bytes:
    """GDPR Art. 15/20 and PDPL access/portability: a JSON export of the
    personal data MAKU holds about this account."""
    payload: dict = {"generated_at": _now_iso(), "username": username,
                     "privacy_policy_version": PRIVACY_POLICY_VERSION}
    with _conn() as conn:
        cur = conn.execute("SELECT role, email, created_at, last_login_at FROM users WHERE username = ?",
                           (username,))
        row = cur.fetchone()
        payload["account"] = (dict(zip(("role", "email", "created_at", "last_login_at"), row))
                              if row else "deployment-managed account (no database profile)")
        cur = conn.execute("SELECT purpose, granted, policy_version, recorded_at FROM user_consents "
                           "WHERE username = ?", (username,))
        payload["consents"] = [dict(zip(("purpose", "granted", "policy_version", "recorded_at"), r))
                               for r in cur.fetchall()]
        cur = conn.execute("SELECT timestamp, module, risk_band, safety_override, key_metric, site, "
                           "data_provenance FROM assessment_log WHERE username = ? ORDER BY timestamp",
                           (username,))
        payload["assessments"] = [dict(zip(("timestamp", "module", "risk_band", "safety_override",
                                            "key_metric", "site", "data_provenance"), r))
                                  for r in cur.fetchall()]
        cur = conn.execute("SELECT platform, created_at FROM device_tokens WHERE username = ?", (username,))
        payload["registered_devices"] = [dict(zip(("platform", "registered_at"), r)) for r in cur.fetchall()]
        cur = conn.execute("SELECT timestamp, event_type, detail FROM audit_log WHERE actor = ? ORDER BY id",
                           (username,))
        payload["security_events"] = [dict(zip(("timestamp", "event_type", "detail"), r))
                                      for r in cur.fetchall()]
    _analytics.log_audit_event(_analytics.AUDIT_EVENT_DATA_EXPORTED, actor=username)
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def is_deployment_managed(username: str, deployment_users: dict) -> bool:
    return username in deployment_users


def delete_account(username: str, password: str, requested_via: str = "in_app") -> dict:
    """Permanently deletes a database-managed account and its personal data:
      - the users row (credentials, email, role),
      - all consent records,
      - all login-attempt records for that username,
      - every assessment the user ran (assessment_log rows tagged with the
        username).
    Retained, as disclosed in the privacy policy: security audit-log entries
    (hash-chained, needed to investigate incidents; deleting them would also
    break tamper evidence) and site-level safety alerts, which are not
    linked to the account. A non-identifying deletion receipt (SHA-256 of
    the username + timestamp) is written to account_deletions.

    The current password is re-verified first so a hijacked, unlocked
    session cannot delete the account silently."""
    user = get_user(username)
    if user is None:
        raise AccountError("This account is managed by your organisation's deployment settings "
                           "and cannot be deleted in-app. Contact your MAKU administrator.")
    if not verify_password(user["password_hash"], password):
        raise AccountError("Password is incorrect - account not deleted.")

    return erase_account_data(username, requested_via=requested_via)


def erase_account_data(username: str, requested_via: str) -> dict:
    """The erasure itself (no password check). Used by delete_account()
    after re-authentication, and by manage_users.py for erasure requests
    received through the public web form or by email."""
    counts = {}
    with _conn() as conn:
        for table in ("assessment_log", "user_consents", "login_attempts", "device_tokens",
                      "organization_members", "users"):
            cur = conn.execute(f"DELETE FROM {table} WHERE username = ?", (username,))
            counts[table] = max(cur.rowcount, 0)
        conn.execute(
            "INSERT INTO account_deletions (username_sha256, deleted_at, requested_via, rows_deleted) "
            "VALUES (?, ?, ?, ?)",
            (_sha256(username), _now_iso(), requested_via, sum(counts.values())),
        )
    _analytics.log_audit_event(_analytics.AUDIT_EVENT_ACCOUNT_DELETED,
                               actor=f"deleted-user:{_sha256(username)[:12]}",
                               detail=f"via={requested_via} rows={sum(counts.values())}")
    logger.info("Account deleted (sha256 prefix %s, via %s)", _sha256(username)[:12], requested_via)
    return counts
