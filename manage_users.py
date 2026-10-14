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

  # generate a bcrypt value for st.secrets / MAKU_AUTH_USERS
  python manage_users.py hash

  # delete an account (GDPR/PDPL erasure request received by email)
  docker compose exec app python manage_users.py delete some.user
"""

from __future__ import annotations

import argparse
import getpass
import sys

import accounts


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
    sub.add_parser("hash", help="print a bcrypt credential for secrets/env configuration")

    p_delete = sub.add_parser("delete", help="permanently delete an account and its personal data")
    p_delete.add_argument("username")

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
            print(accounts.hash_password(_prompt_password()))
        elif args.command == "delete":
            user = accounts.get_user(args.username)
            if user is None:
                sys.exit("No such database account.")
            if input(f"Type '{args.username}' to permanently delete: ").strip() != args.username:
                sys.exit("Aborted.")
            counts = accounts.erase_account_data(args.username, requested_via="operator")
            print(f"Deleted {args.username}: {counts}")
    except accounts.AccountError as exc:
        sys.exit(f"Error: {exc}")
    except accounts.AccountStoreUnavailable:
        sys.exit("Error: database unavailable (check DATABASE_URL).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
