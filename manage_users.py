#!/usr/bin/env python3
"""
MAKU user administration CLI
============================
Run inside the app container (or any machine with DATABASE_URL set):

  # create the first administrator (prompts for the password)
  docker compose exec app python manage_users.py create admin.name --role admin

  # create the App Store / Google Play reviewer account
  docker compose exec app python manage_users.py create appreview --role supervisor

  # list accounts
  docker compose exec app python manage_users.py list

  # generate an Argon2id value for st.secrets / MAKU_AUTH_USERS
  python manage_users.py hash

  # delete an account (GDPR/PDPL erasure request received by email)
  docker compose exec app python manage_users.py delete some.user

  # organizations and memberships (tenant isolation)
  docker compose exec app python manage_users.py org-create "ACME Construction"
  docker compose exec app python manage_users.py member-add some.user "ACME Construction" --role supervisor
  docker compose exec app python manage_users.py member-remove some.user "ACME Construction"
  docker compose exec app python manage_users.py member-list [--user some.user]
  roles: viewer (read only) · supervisor (runs assessments) · org_admin (manages the organization)
"""

from __future__ import annotations

import argparse
import getpass
import sys

import accounts
import tenancy

# The CLI runs on the server with direct database access: it acts as the
# platform administrator.
OPERATOR = tenancy.Principal("manage_users.py", platform_admin=True)


def _prompt_password(confirm: bool = True) -> str:
    pw = getpass.getpass("Password: ")
    if confirm and getpass.getpass("Confirm password: ") != pw:
        sys.exit("Passwords do not match.")
    return pw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MAKU user administration")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="create a database account")
    p_create.add_argument("username")
    p_create.add_argument("--role", choices=accounts.ROLES, default=accounts.DEFAULT_ROLE)
    p_create.add_argument("--email", default=None)

    sub.add_parser("list", help="list active database accounts")
    sub.add_parser("hash", help="print an Argon2id credential for secrets/env configuration")

    p_delete = sub.add_parser("delete", help="permanently delete an account and its personal data")
    p_delete.add_argument("username")

    p_org = sub.add_parser("org-create", help="create an organization")
    p_org.add_argument("name")
    p_madd = sub.add_parser("member-add", help="add a user to an organization (or change their role)")
    p_madd.add_argument("username")
    p_madd.add_argument("organization")
    p_madd.add_argument("--role", choices=tenancy.ORG_ROLES, default=tenancy.DEFAULT_ORG_ROLE)
    p_mrem = sub.add_parser("member-remove", help="remove a user from an organization")
    p_mrem.add_argument("username")
    p_mrem.add_argument("organization")
    p_mlist = sub.add_parser("member-list", help="list memberships")
    p_mlist.add_argument("--user", default=None)

    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            accounts.create_user(args.username, _prompt_password(), args.role,
                                 created_by="manage_users.py", email=args.email)
            print(f"Created {args.username} ({args.role}).")
        elif args.command == "list":
            for u in accounts.list_users():
                print(f"{u['username']:<32} {u['role']:<11} created {u['created_at']}  last login {u['last_login_at']}")
        elif args.command == "hash":
            password = _prompt_password()
            accounts.validate_password_strength(password)   # same policy as in-app accounts
            print(accounts.hash_password(password))
        elif args.command == "delete":
            user = accounts.get_user(args.username)
            if user is None:
                sys.exit("No such database account.")
            if input(f"Type '{args.username}' to permanently delete: ").strip() != args.username:
                sys.exit("Aborted.")
            counts = accounts.erase_account_data(args.username, requested_via="operator")
            print(f"Deleted {args.username}: {counts}")
        elif args.command == "org-create":
            org_id = tenancy.create_organization(OPERATOR, args.name)
            print(f"Organization '{args.name}' has id {org_id}.")
        elif args.command in ("member-add", "member-remove"):
            org_id = tenancy.organization_id_by_name(args.organization)
            if org_id is None:
                sys.exit(f"No organization named '{args.organization}' (create it with org-create).")
            if args.command == "member-add":
                tenancy.set_membership(OPERATOR, args.username, org_id, args.role)
                print(f"{args.username} is now {args.role} in '{args.organization}'.")
            elif tenancy.remove_membership(OPERATOR, args.username, org_id):
                print(f"Removed {args.username} from '{args.organization}'.")
            else:
                print("No such membership.")
        elif args.command == "member-list":
            for m in tenancy.list_memberships(args.user):
                print(f"{m['username']:<32} {m['role']:<11} {m['organization']}")
    except (accounts.AccountError, tenancy.TenancyError) as exc:
        sys.exit(f"Error: {exc}")
    except accounts.AccountStoreUnavailable:
        sys.exit("Error: database unavailable (check DATABASE_URL).")
    return 0


if __name__ == "__main__":
    import analytics as _analytics_ctx

    # Operator tool run on the server: platform-administrator identity for
    # PostgreSQL row-level security (analytics.system_context).
    with _analytics_ctx.system_context():
        _code = main()
    raise SystemExit(_code)
