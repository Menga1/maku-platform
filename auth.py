"""
MAKU - Authentication utility
==============================
A minimal login gate for app.py. Renders a centered French-language login
form ("Identifiant" / "Mot de passe" / "Se connecter") and blocks all
further script execution (st.stop()) until the credentials match.

SECURITY MODEL - FAIL CLOSED, NO HARDCODED CREDENTIALS:
There is no hardcoded username/password anywhere in this file, and none
is generated. Credentials are resolved ONLY from configuration external to
this source file, in this order:

  1. st.secrets["auth"]["users"] - a TOML table of {username: password}
     (or {username: "sha256:<hex digest>"} for a hashed password) for
     multiple accounts. See .streamlit/secrets.toml.example.
  2. st.secrets["auth"]["username"] / ["password"] - single-account form,
     kept for backward compatibility with the original secrets layout.
  3. MAKU_AUTH_USERS environment variable - a JSON object, same shape as
     (1), for deployments that inject config via environment rather than
     Streamlit secrets (e.g. a container platform).
  4. MAKU_AUTH_USERNAME / MAKU_AUTH_PASSWORD environment variables -
     single-account form of (3).

If NONE of the above resolves to at least one configured account, this
module refuses to render a login form at all - it fails CLOSED (shows a
configuration-error screen and st.stop()s) rather than falling open to
any default credential. An unconfigured MAKU deployment is inaccessible,
never insecurely accessible.

PASSWORD COMPARISON - BCRYPT PRIMARY, SHA-256/PLAINTEXT DEPRECATED (P0
"AUTHENTICATION & CRYPTOGRAPHIC HARDENING"):
The recommended, secure-at-rest format is "bcrypt:<bcrypt hash>" - a
proper adaptive, salted hash verified via bcrypt.checkpw(), immune to
rainbow-table/GPU-cracking attacks that a bare SHA-256 digest is not (a
single unsalted SHA-256 hash can be brute-forced at billions of guesses/
second on commodity hardware; bcrypt is deliberately slow and per-hash
salted, which is what "secure credentials at rest" actually requires).
Use hash_password("a real password") to generate one for st.secrets/the
environment.

Two legacy formats are still ACCEPTED for backward compatibility (an
operator's existing secrets.toml must not suddenly lock everyone out) but
are now explicitly DEPRECATED, not a supported steady state:
  - "sha256:<64-hex-char digest>" - a bare, unsalted SHA-256 hash.
  - A plain value with no prefix at all (raw plaintext in secrets/env).
Both still authenticate correctly (compared via hmac.compare_digest(), as
before), but every successful login using either one now (a) logs a
DEPRECATED_CREDENTIAL_FORMAT audit event and (b) renders a persistent,
un-dismissable warning/error in the app urging migration to bcrypt - see
_credential_format()/_warn_if_deprecated_format() and
render_deprecated_credential_banner(). This is a deliberate "deprecate,
don't silently strand operators" migration path rather than a hard
delete: removing support outright would brick any already-deployed
secrets.toml the moment this file is updated, which is a worse outage
than a loud warning.

BRUTE-FORCE MITIGATION: a simple per-session failed-attempt counter locks
the login form for a short cooldown after repeated failures. This is a
best-effort, single-process/session mitigation, NOT a substitute for a
real rate limiter or WAF in front of a production deployment - documented
honestly rather than oversold.

AUDIT TRAIL: every login attempt (success, failure, or lockout) is written
to analytics.py's hash-chained audit_log via analytics.log_audit_event() -
see that module for what "tamper-evident" does and doesn't guarantee here.
Audit logging failures never block or affect the login flow itself (the
call is wrapped so a database problem can't become an authentication
bypass OR a denial of service).

This file only handles auth state - no risk math, no UI beyond the login
form itself.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

import bcrypt
import streamlit as st

try:
    import analytics as _analytics
except Exception:  # noqa: BLE001 - auth must never fail to import because analytics did
    _analytics = None

_SHA256_PREFIX = "sha256:"
_BCRYPT_PREFIX = "bcrypt:"
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
SESSION_TIMEOUT_MINUTES = int(os.environ.get("MAKU_SESSION_TIMEOUT_MINUTES", "480"))  # 8 hours default


def hash_password(plaintext: str) -> str:
    """Generates a 'bcrypt:<hash>' value ready to paste into
    st.secrets["auth"]["users"] (or MAKU_AUTH_USERS/MAKU_AUTH_PASSWORD) as
    a configured credential - the recommended way to provision a password
    under the P0 'AUTHENTICATION & CRYPTOGRAPHIC HARDENING' directive.
    Example (run once, offline, to generate a secrets.toml value):

        python3 -c "import auth; print(auth.hash_password('a real password'))"

    Never called by require_login() itself - this is a provisioning
    utility for whoever manages secrets/environment for a deployment, not
    part of the login request path."""
    return _BCRYPT_PREFIX + bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def _credential_format(configured: str) -> str:
    """Classifies a configured credential value as "bcrypt" (recommended),
    "sha256" or "plaintext" (both deprecated - see module docstring)."""
    if configured.startswith(_BCRYPT_PREFIX):
        return "bcrypt"
    if configured.startswith(_SHA256_PREFIX):
        return "sha256"
    return "plaintext"


def _audit(event_type: str, actor: str, detail: str = "") -> None:
    """Best-effort audit log write - never raises, never blocks login."""
    if _analytics is None:
        return
    try:
        _analytics.log_audit_event(event_type, actor=actor, detail=detail)
    except Exception:  # noqa: BLE001
        pass


def _parse_users_json(raw: str) -> dict[str, str]:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except (ValueError, TypeError):
        pass
    return {}


def _configured_users() -> dict[str, str]:
    """Returns {username: password_or_hash} from whichever source is
    configured, checked in the priority order documented in the module
    docstring. Returns an empty dict (never raises) if nothing is
    configured anywhere - the caller (require_login) treats that as a
    hard configuration error, not as "no login required"."""
    try:
        users = st.secrets["auth"]["users"]
        if users:
            return {str(k): str(v) for k, v in dict(users).items()}
    except Exception:  # noqa: BLE001 - secrets.toml absent, key absent, wrong shape, etc.
        pass

    try:
        username = st.secrets["auth"]["username"]
        password = st.secrets["auth"]["password"]
        if username and password:
            return {str(username): str(password)}
    except Exception:  # noqa: BLE001
        pass

    env_users_json = os.environ.get("MAKU_AUTH_USERS", "").strip()
    if env_users_json:
        parsed = _parse_users_json(env_users_json)
        if parsed:
            return parsed

    env_username = os.environ.get("MAKU_AUTH_USERNAME", "").strip()
    env_password = os.environ.get("MAKU_AUTH_PASSWORD", "").strip()
    if env_username and env_password:
        return {env_username: env_password}

    return {}


def _password_matches(configured: str, supplied: str) -> bool:
    """Verifies `supplied` against `configured`, dispatching on format:
      - "bcrypt:<hash>" (recommended) - bcrypt.checkpw(), which is itself
        constant-time and salted/adaptive by construction.
      - "sha256:<hex>" (deprecated) - constant-time comparison against
        sha256(supplied), unchanged from the original implementation.
      - plain value (deprecated) - constant-time comparison against the
        raw configured value, unchanged from the original implementation.
    See the module docstring's PASSWORD COMPARISON section for why the
    latter two are deprecated but still accepted."""
    if configured.startswith(_BCRYPT_PREFIX):
        stored_hash = configured[len(_BCRYPT_PREFIX):].strip().encode("utf-8")
        try:
            return bcrypt.checkpw(supplied.encode("utf-8"), stored_hash)
        except ValueError:
            # Malformed stored hash (e.g. hand-edited secrets.toml) - fail
            # closed, never treat a bad hash as "no password required".
            return False
    if configured.startswith(_SHA256_PREFIX):
        expected_hex = configured[len(_SHA256_PREFIX):].strip().lower()
        supplied_hex = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected_hex, supplied_hex)
    return hmac.compare_digest(configured, supplied)


def _warn_if_deprecated_format(username: str, configured_password: str) -> None:
    """Called only on a SUCCESSFUL login. Audits (once per successful
    login, not spammed per keystroke) and flags in session_state - for
    render_deprecated_credential_banner() to surface post-login - when the
    account that just authenticated is still using a deprecated sha256/
    plaintext credential format instead of bcrypt. Never blocks or slows
    the login itself; see module docstring."""
    fmt = _credential_format(configured_password)
    if fmt == "bcrypt":
        st.session_state["_auth_credential_format_warning"] = None
        return
    message = (
        f"Account '{username}' is authenticating with a deprecated "
        f"{'SHA-256' if fmt == 'sha256' else 'plaintext'} credential format. "
        "Regenerate this credential with auth.hash_password(...) and store it "
        "as 'bcrypt:<hash>' in st.secrets/the environment."
    )
    st.session_state["_auth_credential_format_warning"] = message
    _audit(_analytics.AUDIT_EVENT_DEPRECATED_CREDENTIAL_FORMAT if _analytics
           else "DEPRECATED_CREDENTIAL_FORMAT", actor=username, detail=message)


def _verify_credentials(username: str, password: str) -> bool:
    users = _configured_users()
    configured_password = users.get(username)
    if configured_password is None:
        # Still run a dummy constant-time comparison against a fixed
        # decoy value so a nonexistent username takes the same code path
        # (and roughly the same time) as a wrong password for a real
        # username - avoids trivially timing-based username enumeration.
        hmac.compare_digest("decoy", password)
        return False
    matched = _password_matches(configured_password, password)
    if matched:
        _warn_if_deprecated_format(username, configured_password)
    return matched


def _lockout_state() -> tuple[int, float]:
    attempts = st.session_state.get("_auth_failed_attempts", 0)
    locked_until = st.session_state.get("_auth_locked_until", 0.0)
    return attempts, locked_until


def _register_failure(username: str) -> None:
    attempts, _ = _lockout_state()
    attempts += 1
    st.session_state["_auth_failed_attempts"] = attempts
    if attempts >= MAX_FAILED_ATTEMPTS:
        st.session_state["_auth_locked_until"] = time.time() + LOCKOUT_SECONDS
        st.session_state["_auth_failed_attempts"] = 0
        _audit("LOGIN_LOCKOUT" if _analytics is None else _analytics.AUDIT_EVENT_LOGIN_LOCKOUT,
               actor=username, detail=f"{MAX_FAILED_ATTEMPTS} failed attempts")


def _reset_failures() -> None:
    st.session_state["_auth_failed_attempts"] = 0
    st.session_state["_auth_locked_until"] = 0.0


def _session_expired() -> bool:
    login_at = st.session_state.get("_auth_login_at")
    if login_at is None:
        return False
    return (time.time() - login_at) > SESSION_TIMEOUT_MINUTES * 60


def require_login() -> None:
    """Call this as the very first thing app.py does. Returns immediately
    if already authenticated AND the session hasn't expired. Otherwise
    (re)initializes the auth-related session_state keys explicitly - never
    relies on an implicit default - and renders the login form,
    st.stop()-ing the script so nothing after this call (module layout,
    sidebar navigation, st.navigation, any page content) ever executes for
    an unauthenticated visitor."""
    # Explicit session-state initialization, not an implicit .get() default -
    # every key this gate depends on is guaranteed to exist before it is
    # ever read, so there is no code path where "authenticated" is
    # implicitly and silently treated as anything other than False.
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("_auth_username", "")
    st.session_state.setdefault("_auth_failed_attempts", 0)
    st.session_state.setdefault("_auth_locked_until", 0.0)

    if st.session_state["authenticated"]:
        if _session_expired():
            _audit(_analytics.AUDIT_EVENT_SESSION_EXPIRED if _analytics else "SESSION_EXPIRED",
                   actor=st.session_state.get("_auth_username", "unknown"))
            st.session_state["authenticated"] = False
            st.session_state["_auth_username"] = ""
        else:
            return

    st.set_page_config(page_title="MAKU - Connexion", page_icon="🔒", layout="centered")

    st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)
    col_l, col_mid, col_r = st.columns([1, 1.3, 1])

    with col_mid:
        if os.path.exists("logo_croquis.png"):
            st.image("logo_croquis.png", width="stretch")

        st.markdown("### 🔒 MAKU — Accès sécurisé")
        st.caption("Plateforme d'évaluation des risques cinétiques multi-environnement")

        configured_users = _configured_users()
        if not configured_users:
            # FAIL CLOSED: no credential source is configured anywhere.
            # This is a deployment/configuration error, not a "let anyone
            # in" situation - render an explanation and stop, with no
            # form at all, so there is nothing here for a visitor to
            # submit their way past.
            st.error(
                "Aucun identifiant n'est configuré pour cette instance MAKU. "
                "L'accès est désactivé par sécurité jusqu'à ce qu'un administrateur "
                "configure `st.secrets[\"auth\"]` (voir `.streamlit/secrets.toml.example`) "
                "ou les variables d'environnement MAKU_AUTH_USERNAME / MAKU_AUTH_PASSWORD "
                "(ou MAKU_AUTH_USERS pour plusieurs comptes).",
                icon="🔒",
            )
            _audit(_analytics.AUDIT_EVENT_CONFIG_ERROR if _analytics else "CONFIG_ERROR",
                   actor="system", detail="require_login: no credentials configured")
            st.stop()

        attempts, locked_until = _lockout_state()
        now = time.time()
        if locked_until and now < locked_until:
            remaining = int(locked_until - now)
            st.error(
                f"Trop de tentatives échouées. Réessayez dans {remaining} seconde(s).",
                icon="⏳",
            )
            st.stop()

        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", width="stretch")

        if submitted:
            if _verify_credentials(username, password):
                _reset_failures()
                st.session_state["authenticated"] = True
                st.session_state["_auth_username"] = username
                st.session_state["_auth_login_at"] = time.time()
                _audit(_analytics.AUDIT_EVENT_LOGIN_SUCCESS if _analytics else "LOGIN_SUCCESS",
                       actor=username)
                st.rerun()
            else:
                _register_failure(username or "(empty)")
                _audit(_analytics.AUDIT_EVENT_LOGIN_FAILURE if _analytics else "LOGIN_FAILURE",
                       actor=username or "(empty)")
                st.error("Identifiant ou mot de passe incorrect.")

    st.stop()


def render_deprecated_credential_banner(st_module) -> None:
    """Call once, post-login, from any page (e.g. right after
    render_logout_control()). Renders nothing when the current account
    authenticated with 'bcrypt:...' (the recommended format); renders a
    persistent warning when it authenticated with a deprecated sha256/
    plaintext credential - see _warn_if_deprecated_format()."""
    message = st_module.session_state.get("_auth_credential_format_warning")
    if message:
        st_module.warning(f"🔑 {message}", icon="⚠️")


def render_logout_control(st_module) -> None:
    """Small sidebar logout control. Call from the dashboard/pages once
    authenticated, if you want a visible way to sign out."""
    if st_module.sidebar.button("🔓 Se déconnecter"):
        username = st_module.session_state.get("_auth_username", "unknown")
        _audit(_analytics.AUDIT_EVENT_LOGOUT if _analytics else "LOGOUT", actor=username)
        st_module.session_state["authenticated"] = False
        st_module.session_state["_auth_username"] = ""
        st_module.rerun()
