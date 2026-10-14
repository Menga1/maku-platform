"""
Credential audit (review finding F3). Lists every account MAKU would accept
and how its password is stored - WITHOUT printing any hash or secret.

    python scripts/audit_credentials.py                       # env + database
    python scripts/audit_credentials.py --secrets .streamlit/secrets.toml
    docker compose exec app python scripts/audit_credentials.py

Status per account
  OK        Argon2id with current parameters
  UPGRADE   bcrypt, or Argon2id with old parameters. Database accounts are
            upgraded automatically at their next sign-in; deployment accounts
            (secrets / MAKU_AUTH_USERS) must be replaced by the operator with
            `python manage_users.py hash`.
  REJECTED  plain text, unsalted SHA-256 or unreadable - MAKU refuses these at
            sign-in. Replace them now.

Exit code 1 if any account is REJECTED (usable in CI or a deployment check).
Deployment-account passwords can't be checked for length from the hash alone;
MAKU checks them at sign-in (refused in production if they fail the policy).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import accounts  # noqa: E402


def deployment_accounts(secrets_path: str | None) -> list[tuple[str, str, str]]:
    """[(username, source, stored_value)] from a secrets file and the environment."""
    found: list[tuple[str, str, str]] = []
    if secrets_path and os.path.exists(secrets_path):
        with open(secrets_path, "rb") as fh:
            auth = tomllib.load(fh).get("auth", {})
        for name, value in (auth.get("users") or {}).items():
            found.append((str(name), f"{secrets_path} [auth.users]", str(value)))
        if auth.get("username") and auth.get("password"):
            found.append((str(auth["username"]), f"{secrets_path} [auth]", str(auth["password"])))
    raw = os.environ.get("MAKU_AUTH_USERS", "").strip()
    if raw:
        try:
            for name, value in json.loads(raw).items():
                found.append((str(name), "MAKU_AUTH_USERS", str(value)))
        except (ValueError, AttributeError):
            found.append(("(MAKU_AUTH_USERS)", "MAKU_AUTH_USERS", "<unreadable JSON>"))
    if os.environ.get("MAKU_AUTH_USERNAME") and os.environ.get("MAKU_AUTH_PASSWORD"):
        found.append((os.environ["MAKU_AUTH_USERNAME"], "MAKU_AUTH_USERNAME/PASSWORD",
                      os.environ["MAKU_AUTH_PASSWORD"]))
    return found


def classify(stored: str, source: str) -> tuple[str, str]:
    fmt = accounts.credential_format(stored)
    if fmt not in accounts.ACCEPTED_FORMATS:
        return "REJECTED", f"{fmt} credential - replace with `python manage_users.py hash`"
    if accounts.needs_rehash(stored):
        if source == "database":
            return "UPGRADE", f"{fmt} - upgraded to Argon2id automatically at next sign-in"
        return "UPGRADE", f"{fmt} - replace with an Argon2id value (`python manage_users.py hash`)"
    return "OK", "argon2id"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit MAKU credentials (prints no secrets)")
    parser.add_argument("--secrets", default=".streamlit/secrets.toml",
                        help="Streamlit secrets file to inspect (default: .streamlit/secrets.toml)")
    parser.add_argument("--no-database", action="store_true", help="skip database accounts")
    args = parser.parse_args(argv)

    rows = [(u, src, *classify(v, src)) for u, src, v in deployment_accounts(args.secrets)]
    if not args.no_database:
        try:
            with accounts._conn() as conn:
                for username, stored in conn.execute("SELECT username, password_hash FROM users").fetchall():
                    rows.append((username, "database", *classify(stored, "database")))
        except accounts.AccountStoreUnavailable:
            print("! database unavailable - database accounts not checked", file=sys.stderr)

    if not rows:
        print("No accounts found.")
        return 0
    width = max(len(r[0]) for r in rows)
    for username, source, status, note in rows:
        print(f"{status:<9} {username:<{width}}  {source:<32} {note}")
    rejected = sum(1 for r in rows if r[2] == "REJECTED")
    upgrade = sum(1 for r in rows if r[2] == "UPGRADE")
    print(f"\n{len(rows)} account(s): {len(rows) - rejected - upgrade} OK, {upgrade} to upgrade, {rejected} rejected")
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
