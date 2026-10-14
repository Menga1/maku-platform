"""
MAKU - Authentication, privacy consent and account self-service
================================================================
Login gate for app.py plus the account pages required by the app stores
(Apple 5.1.1(v), Google Play account-deletion policy) and by GDPR / UAE PDPL.

SECURITY MODEL
--------------
* FAIL CLOSED, NO HARDCODED CREDENTIALS. Accounts come from:
    1. the database `users` table (accounts.py) - normal staff accounts,
       created by an administrator in-app or with manage_users.py;
    2. deployment-managed bootstrap accounts from st.secrets["auth"] or the
       MAKU_AUTH_USERS / MAKU_AUTH_USERNAME+MAKU_AUTH_PASSWORD environment
       variables - for the first administrator only.
  If neither yields an account, no login form is rendered at all.
* ARGON2ID (bcrypt still accepted). New credentials are "argon2:<hash>"
  (Argon2id, RFC 9106 parameters). "bcrypt:<hash>" values still work and
  database accounts are upgraded to Argon2id at their next sign-in. Plaintext
  and unsalted "sha256:" values are REJECTED: the login fails and a
  REJECTED_CREDENTIAL_FORMAT audit event is written. Generate a value with:
      python3 manage_users.py hash
* PASSWORD POLICY FOR DEPLOYMENT ACCOUNTS. Accounts from secrets/env can't
  be checked when configured (only the hash is stored), so the password is
  checked at sign-in. In strict mode (MAKU_ENV=production/staging) a password
  that fails the policy is refused with an explicit message; elsewhere a
  warning banner asks the operator to replace it.
* SESSIONS end after MAKU_SESSION_TIMEOUT_MINUTES (default 480) in total, or
  MAKU_SESSION_IDLE_MINUTES (default 30) without any interaction.
* SERVER-SIDE BRUTE-FORCE LOCKOUT. Attempts are recorded in the database
  (accounts.login_attempts) and evaluated per username AND per client IP,
  so refreshing the page, opening a new tab, or switching devices does not
  reset the counter. If the account store is unreachable, login fails
  closed.
* Timing-equalized responses for unknown usernames (a real bcrypt check
  against a decoy hash), session expiry, explicit logout, and every
  security event written to the hash-chained audit log.
"""

from __future__ import annotations

import json
import logging
import os
import time

import streamlit as st

import accounts

try:
    import analytics as _analytics
except Exception:  # noqa: BLE001 - auth must never fail to import because analytics did
    _analytics = None

logger = logging.getLogger("maku.auth")

_SHA256_PREFIX = "sha256:"
_BCRYPT_PREFIX = accounts.BCRYPT_PREFIX
SESSION_TIMEOUT_MINUTES = int(os.environ.get("MAKU_SESSION_TIMEOUT_MINUTES", "480"))  # 8 hours default
SESSION_IDLE_MINUTES = int(os.environ.get("MAKU_SESSION_IDLE_MINUTES", "30"))
AUDIT_EVENT_WEAK_DEPLOYMENT_PASSWORD = "WEAK_DEPLOYMENT_PASSWORD"
AUDIT_EVENT_SESSION_IDLE_TIMEOUT = "SESSION_IDLE_TIMEOUT"
BOOTSTRAP_ROLE = "admin"


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------

def hash_password(plaintext: str) -> str:
    """'argon2:<hash>' - paste into st.secrets / MAKU_AUTH_USERS. Provisioning
    helper; not part of the login request path."""
    return accounts.hash_password(plaintext)


def _credential_format(configured: str) -> str:
    return accounts.credential_format(configured)


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
    """Deployment-managed bootstrap accounts {username: credential}, in
    priority order: st.secrets users table, st.secrets single account,
    MAKU_AUTH_USERS JSON, MAKU_AUTH_USERNAME/PASSWORD. {} if none."""
    try:
        users = st.secrets["auth"]["users"]
        if users:
            return {str(k): str(v) for k, v in dict(users).items()}
    except Exception:  # noqa: BLE001
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
    """Argon2id or bcrypt only. Any other stored format fails closed."""
    if _credential_format(configured) not in accounts.ACCEPTED_FORMATS:
        return False
    return accounts.verify_password(configured, supplied)


def _database_accounts_available() -> bool:
    try:
        return bool(accounts.list_users())
    except accounts.AccountStoreUnavailable:
        return False


def _verify_credentials(username: str, password: str) -> bool:
    """True when (username, password) matches a database account or a
    deployment bootstrap account. Sets the session role on success."""
    username = (username or "").strip()

    # 1. Database-managed account
    try:
        user = accounts.get_user(username) if username else None
    except accounts.AccountStoreUnavailable:
        user = None
    if user is not None:
        ok = accounts.verify_password(user["password_hash"], password)
        if ok:
            st.session_state["_auth_role"] = user["role"]
            st.session_state["_auth_source"] = "database"
            if accounts.needs_rehash(user["password_hash"]):
                accounts.upgrade_stored_hash(username, password)
        return ok

    # 2. Deployment-managed bootstrap account
    configured = _configured_users().get(username)
    if configured is None:
        accounts.burn_equal_time(password)
        return False
    if _credential_format(configured) not in accounts.ACCEPTED_FORMATS:
        accounts.burn_equal_time(password)
        message = (f"Account '{username}' is configured with a rejected "
                   f"{'SHA-256' if _credential_format(configured) == 'sha256' else 'plaintext'} credential. "
                   "Only 'argon2:<hash>' or 'bcrypt:<hash>' values are accepted - run `python3 manage_users.py hash`.")
        logger.error(message)
        _audit(_analytics.AUDIT_EVENT_REJECTED_CREDENTIAL_FORMAT if _analytics else "REJECTED_CREDENTIAL_FORMAT",
               actor=username, detail=message)
        return False
    ok = accounts.verify_password(configured, password)
    if not ok:
        return False
    problems = accounts.password_policy_problems(password)
    if problems:
        import db
        detail = f"deployment account password fails policy: {problems[0]}"
        logger.warning("Account '%s': %s", username, detail)
        _audit(AUDIT_EVENT_WEAK_DEPLOYMENT_PASSWORD, actor=username, detail=detail)
        if db.strict_persistence():
            st.session_state["_auth_refused_reason"] = "weak_deployment_password"
            return False
        st.session_state["_auth_weak_password_warning"] = problems[0]
    if accounts.needs_rehash(configured):
        logger.info("Account '%s' uses a %s credential - replace it with `python3 manage_users.py hash` "
                    "(Argon2id)", username, _credential_format(configured))
    st.session_state["_auth_role"] = BOOTSTRAP_ROLE
    st.session_state["_auth_source"] = "deployment"
    return True


def get_client_ip() -> str | None:
    """Visitor IP from the reverse proxy's X-Forwarded-For / X-Real-IP."""
    try:
        headers = st.context.headers
    except Exception:  # noqa: BLE001 - outside a Streamlit runtime (tests)
        return None
    from data_feeds import client_ip_from_headers
    return client_ip_from_headers(headers)


def _session_expired() -> bool:
    login_at = st.session_state.get("_auth_login_at")
    if login_at is None:
        return False
    return (time.time() - login_at) > SESSION_TIMEOUT_MINUTES * 60


def _session_idle() -> bool:
    """True when the last interaction is older than SESSION_IDLE_MINUTES.
    Every rerun (any click or input) counts as an interaction."""
    last_seen = st.session_state.get("_auth_last_seen")
    if last_seen is None or SESSION_IDLE_MINUTES <= 0:
        return False
    return (time.time() - last_seen) > SESSION_IDLE_MINUTES * 60


def current_username() -> str:
    return st.session_state.get("_auth_username", "") or ""


def current_role() -> str:
    return st.session_state.get("_auth_role", "viewer") or "viewer"


def is_admin() -> bool:
    return current_role() == "admin"


def _clear_session_identity() -> None:
    for key in ("authenticated", "_auth_username", "_auth_role", "_auth_source", "_auth_login_at",
                "_auth_last_seen", "_auth_consents", "_auth_weak_password_warning"):
        st.session_state.pop(key, None)
    st.session_state["authenticated"] = False


# ---------------------------------------------------------------------------
# Login gate
# ---------------------------------------------------------------------------

def require_login() -> None:
    """First call in app.py. Returns only for an authenticated, unexpired
    session; otherwise renders the login form and st.stop()s."""
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("_auth_username", "")

    if st.session_state["authenticated"]:
        if _session_expired():
            _audit(_analytics.AUDIT_EVENT_SESSION_EXPIRED if _analytics else "SESSION_EXPIRED",
                   actor=current_username() or "unknown")
            _clear_session_identity()
        elif _session_idle():
            _audit(AUDIT_EVENT_SESSION_IDLE_TIMEOUT, actor=current_username() or "unknown",
                   detail=f"idle > {SESSION_IDLE_MINUTES} min")
            _clear_session_identity()
            st.session_state["_auth_idle_notice"] = True
        else:
            st.session_state["_auth_last_seen"] = time.time()
            return

    st.set_page_config(page_title="MAKU - Connexion", page_icon="🔒", layout="centered")
    st.markdown("<div style='height: 6vh'></div>", unsafe_allow_html=True)
    _, col_mid, _ = st.columns([1, 1.3, 1])

    with col_mid:
        for logo in ("assets/logo_croquis.webp",):
            if os.path.exists(logo):
                st.image(logo, width="stretch")
                break

        if st.session_state.pop("_account_deleted_notice", False):
            st.success("Votre compte a été supprimé. / Your account has been deleted.")
        if st.session_state.pop("_auth_idle_notice", False):
            st.info(f"Déconnecté après {SESSION_IDLE_MINUTES} min d'inactivité. / "
                    f"Signed out after {SESSION_IDLE_MINUTES} min without activity.")
        st.markdown("### 🔒 MAKU — Accès sécurisé / Secure access")
        st.caption("Plateforme d'évaluation des risques cinétiques multi-environnement")

        if not _configured_users() and not _database_accounts_available():
            st.error(
                "Aucun identifiant n'est configuré pour cette instance MAKU. L'accès est désactivé "
                "jusqu'à ce qu'un administrateur crée un compte (manage_users.py) ou configure "
                "st.secrets[\"auth\"] / MAKU_AUTH_USERS.",
                icon="🔒",
            )
            _audit(_analytics.AUDIT_EVENT_CONFIG_ERROR if _analytics else "CONFIG_ERROR",
                   actor="system", detail="require_login: no credentials configured")
            st.stop()

        with st.form("login_form"):
            username = st.text_input("Identifiant / Username", autocomplete="username")
            password = st.text_input("Mot de passe / Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Se connecter / Sign in", width="stretch")

        st.caption(f"[Politique de confidentialité / Privacy policy]({accounts.PRIVACY_POLICY_URL})")

        if submitted:
            username = (username or "").strip()
            client_ip = get_client_ip()
            try:
                locked, retry_after = accounts.lockout_status(username, client_ip)
            except accounts.AccountStoreUnavailable:
                st.error("Connexion temporairement indisponible. Réessayez dans quelques minutes. / "
                         "Sign-in is temporarily unavailable. Please try again in a few minutes.")
                st.stop()

            if locked:
                _audit(_analytics.AUDIT_EVENT_LOGIN_LOCKOUT if _analytics else "LOGIN_LOCKOUT",
                       actor=username or "(empty)", detail=f"ip={client_ip} retry_after={retry_after}s")
                minutes = max(1, (retry_after + 59) // 60)
                st.error(f"Trop de tentatives échouées. Réessayez dans {minutes} min. / "
                         f"Too many failed attempts. Try again in {minutes} min.", icon="⏳")
                st.stop()

            if _verify_credentials(username, password):
                try:
                    accounts.record_login_attempt(username, client_ip, succeeded=True)
                    if st.session_state.get("_auth_source") == "database":
                        accounts.mark_login(username)
                except accounts.AccountStoreUnavailable:
                    pass
                st.session_state["authenticated"] = True
                st.session_state["_auth_username"] = username
                st.session_state["_auth_login_at"] = time.time()
                st.session_state["_auth_last_seen"] = time.time()
                _audit(_analytics.AUDIT_EVENT_LOGIN_SUCCESS if _analytics else "LOGIN_SUCCESS",
                       actor=username, detail=f"ip={client_ip}")
                st.rerun()
            else:
                try:
                    accounts.record_login_attempt(username or "(empty)", client_ip, succeeded=False)
                except accounts.AccountStoreUnavailable:
                    pass
                _audit(_analytics.AUDIT_EVENT_LOGIN_FAILURE if _analytics else "LOGIN_FAILURE",
                       actor=username or "(empty)", detail=f"ip={client_ip}")
                if st.session_state.pop("_auth_refused_reason", None) == "weak_deployment_password":
                    st.error("Ce mot de passe administrateur ne respecte plus la politique de sécurité "
                             f"(≥ {accounts.MIN_PASSWORD_LENGTH} caractères, 3 types). L'exploitant du serveur doit "
                             "en définir un nouveau. / This administrator password no longer meets the password "
                             "policy. The server operator must set a new one (manage_users.py hash).")
                else:
                    st.error("Identifiant ou mot de passe incorrect. / Incorrect username or password.")

    st.stop()


def render_deprecated_credential_banner(st_module) -> None:
    """Outside strict mode, warns an administrator signed in with a
    deployment account whose password fails the policy (in strict mode such
    a sign-in is refused - see _verify_credentials)."""
    problem = st_module.session_state.get("_auth_weak_password_warning")
    if problem:
        st_module.sidebar.warning(
            "Mot de passe administrateur trop faible - remplacez-le (manage_users.py hash). / "
            f"Weak administrator password - replace it (manage_users.py hash). {problem}", icon="🔑")


def render_logout_control(st_module) -> None:
    if st_module.sidebar.button("🔓 Se déconnecter / Sign out"):
        _audit(_analytics.AUDIT_EVENT_LOGOUT if _analytics else "LOGOUT", actor=current_username() or "unknown")
        _clear_session_identity()
        st_module.rerun()


# ---------------------------------------------------------------------------
# Privacy consent (GDPR / UAE PDPL)
# ---------------------------------------------------------------------------

_CONSENT_TEXT = {
    accounts.CONSENT_AI: {
        "en": ("AI briefings (optional)",
               "Send the assessment results for this session (risk scores, module, site name, and "
               "anonymised worker-strain summaries) to Anthropic, PBC to generate a written AI briefing. "
               "No name, email or GPS coordinates are sent. Without consent you still get the full "
               "rule-based briefing."),
        "fr": ("Briefings IA (facultatif)",
               "Envoyer les résultats d'évaluation (scores, module, nom du site, résumés anonymisés de "
               "charge physiologique) à Anthropic, PBC pour générer un briefing IA rédigé. Aucun nom, "
               "e-mail ni coordonnée GPS n'est envoyé. Sans consentement, le briefing réglementaire "
               "complet reste disponible."),
    },
    accounts.CONSENT_LOCATION: {
        "en": ("Location (optional)",
               "Use this device's GPS position (or, if GPS is denied, an approximate location from "
               "your IP address) to pick the nearest site, local weather and the applicable country "
               "regulations. Location is used for the current session only and is not stored."),
        "fr": ("Localisation (facultatif)",
               "Utiliser la position GPS de l'appareil (ou, si refusée, une position approximative "
               "issue de l'adresse IP) pour choisir le site le plus proche, la météo locale et la "
               "réglementation applicable. La position n'est utilisée que pour la session en cours "
               "et n'est pas conservée."),
    },
}


def _consent_text(purpose: str, lang: str) -> tuple[str, str]:
    texts = _CONSENT_TEXT[purpose]
    return texts.get(lang, texts["en"])


def session_consents() -> dict:
    """Cached per session; refreshed whenever the user changes a toggle."""
    if "_auth_consents" not in st.session_state:
        try:
            st.session_state["_auth_consents"] = accounts.get_consents(current_username())
        except accounts.AccountStoreUnavailable:
            st.session_state["_auth_consents"] = {p: None for p in accounts.CONSENT_PURPOSES}
    return st.session_state["_auth_consents"]


def has_consent(purpose: str) -> bool:
    return bool(session_consents().get(purpose))


def require_privacy_choices(lang: str = "fr") -> None:
    """Shown once after login (and again if the privacy policy version
    changes): the user must make an explicit choice for each optional
    purpose before using the app. Both toggles start OFF - no pre-ticked
    consent. Choosing 'off' is always allowed and the app remains fully
    usable."""
    consents = session_consents()
    if all(v is not None for v in consents.values()):
        return

    st.title("🔐 " + ("Vos choix de confidentialité" if lang == "fr" else "Your privacy choices"))
    st.write(
        "MAKU traite vos données conformément au RGPD et à la loi émiratie PDPL. Choisissez ci-dessous ; "
        "vous pourrez changer d'avis à tout moment dans « Mon compte »."
        if lang == "fr" else
        "MAKU processes your data under the GDPR and the UAE PDPL. Make your choices below; you can "
        "change them at any time under 'My account'."
    )
    st.markdown(f"[{'Politique de confidentialité' if lang == 'fr' else 'Privacy policy'}]"
                f"({accounts.PRIVACY_POLICY_URL}) · v{accounts.PRIVACY_POLICY_VERSION}")
    with st.form("privacy_choices"):
        choices = {}
        for purpose in accounts.CONSENT_PURPOSES:
            title, body = _consent_text(purpose, lang)
            choices[purpose] = st.toggle(title, value=False, key=f"consent_init_{purpose}")
            st.caption(body)
        if st.form_submit_button("Enregistrer et continuer" if lang == "fr" else "Save and continue",
                                 type="primary", width="stretch"):
            try:
                for purpose, granted in choices.items():
                    accounts.set_consent(current_username(), purpose, granted)
                st.session_state.pop("_auth_consents", None)
                st.rerun()
            except accounts.AccountStoreUnavailable:
                st.error("Impossible d'enregistrer vos choix pour le moment." if lang == "fr"
                         else "Could not save your choices right now. Please try again.")
    st.stop()


# ---------------------------------------------------------------------------
# "My account" page: consent toggles, data export, password, deletion
# ---------------------------------------------------------------------------

def render_account_page(lang: str = "fr") -> None:
    fr = lang == "fr"
    username = current_username()
    st.title("👤 " + ("Mon compte" if fr else "My account"))
    st.caption(f"{'Connecté en tant que' if fr else 'Signed in as'} **{username}** · "
               f"{'rôle' if fr else 'role'}: {current_role()}")

    # --- Privacy -----------------------------------------------------------
    st.subheader("🔐 " + ("Confidentialité et consentements" if fr else "Privacy and consent"))
    consents = session_consents()
    for purpose in accounts.CONSENT_PURPOSES:
        title, body = _consent_text(purpose, lang)
        current = bool(consents.get(purpose))
        new_value = st.toggle(title, value=current, key=f"consent_toggle_{purpose}")
        st.caption(body)
        if new_value != current:
            try:
                accounts.set_consent(username, purpose, new_value)
                st.session_state.pop("_auth_consents", None)
                st.toast("✅ " + ("Préférence enregistrée" if fr else "Preference saved"))
                st.rerun()
            except accounts.AccountStoreUnavailable:
                st.error("Impossible d'enregistrer." if fr else "Could not save. Please retry.")
    st.markdown(f"[{'Lire la politique de confidentialité' if fr else 'Read the privacy policy'}]"
                f"({accounts.PRIVACY_POLICY_URL})")

    # --- Data export -------------------------------------------------------
    st.subheader("📦 " + ("Exporter mes données" if fr else "Export my data"))
    st.caption("Copie JSON de toutes les données personnelles associées à votre compte (RGPD art. 15/20)."
               if fr else "A JSON copy of all personal data linked to your account (GDPR Art. 15/20).")
    if st.button("Préparer l'export" if fr else "Prepare export", key="export_prepare"):
        try:
            st.session_state["_account_export"] = accounts.export_user_data(username)
        except accounts.AccountStoreUnavailable:
            st.error("Export indisponible pour le moment." if fr else "Export unavailable right now.")
    if st.session_state.get("_account_export"):
        st.download_button("⬇️ " + ("Télécharger (JSON)" if fr else "Download (JSON)"),
                           data=st.session_state["_account_export"],
                           file_name=f"maku-data-{username}.json", mime="application/json")

    if st.session_state.get("_auth_source") != "database":
        st.info("Ce compte est géré par la configuration du déploiement. Contactez votre administrateur MAKU "
                "pour toute modification ou suppression." if fr else
                "This account is managed by the deployment configuration. Contact your MAKU administrator "
                "to change or delete it.")
        return

    # --- Password ----------------------------------------------------------
    st.subheader("🔑 " + ("Changer le mot de passe" if fr else "Change password"))
    with st.form("change_password"):
        current_pw = st.text_input("Mot de passe actuel" if fr else "Current password", type="password")
        new_pw = st.text_input("Nouveau mot de passe" if fr else "New password", type="password",
                               help=f"≥ {accounts.MIN_PASSWORD_LENGTH} caractères / characters")
        new_pw2 = st.text_input("Confirmer" if fr else "Confirm new password", type="password")
        if st.form_submit_button("Mettre à jour" if fr else "Update password"):
            if new_pw != new_pw2:
                st.error("Les mots de passe ne correspondent pas." if fr else "Passwords do not match.")
            else:
                try:
                    accounts.change_password(username, current_pw, new_pw)
                    st.success("Mot de passe mis à jour." if fr else "Password updated.")
                except accounts.AccountError as exc:
                    st.error(str(exc))
                except accounts.AccountStoreUnavailable:
                    st.error("Service indisponible." if fr else "Service unavailable.")

    # --- Delete account ----------------------------------------------------
    st.subheader("🗑️ " + ("Supprimer mon compte" if fr else "Delete my account"))
    st.warning(
        "Supprime définitivement votre compte, vos consentements et toutes les évaluations que vous avez "
        "réalisées. Les journaux de sécurité horodatés sont conservés comme indiqué dans la politique de "
        "confidentialité. Cette action est irréversible."
        if fr else
        "Permanently deletes your account, your consent records and every assessment you ran. Time-stamped "
        "security log entries are retained as described in the privacy policy. This cannot be undone."
    )
    with st.form("delete_account"):
        confirm_name = st.text_input(("Tapez votre identifiant pour confirmer" if fr
                                      else "Type your username to confirm"))
        confirm_pw = st.text_input("Mot de passe" if fr else "Password", type="password")
        if st.form_submit_button("Supprimer définitivement" if fr else "Delete permanently", type="primary"):
            if confirm_name.strip() != username:
                st.error("L'identifiant ne correspond pas." if fr else "Username does not match.")
            else:
                try:
                    accounts.delete_account(username, confirm_pw, requested_via="in_app")
                    _clear_session_identity()
                    st.session_state["_account_deleted_notice"] = True
                    st.rerun()
                except accounts.AccountError as exc:
                    st.error(str(exc))
                except accounts.AccountStoreUnavailable:
                    st.error("Service indisponible - rien n'a été supprimé." if fr
                             else "Service unavailable - nothing was deleted.")


# ---------------------------------------------------------------------------
# Admin: user management
# ---------------------------------------------------------------------------

def render_admin_users_page(lang: str = "fr") -> None:
    fr = lang == "fr"
    st.title("🛠️ " + ("Utilisateurs" if fr else "Users"))
    if not is_admin():
        st.error("Accès réservé aux administrateurs." if fr else "Administrators only.")
        return
    try:
        users = accounts.list_users()
    except accounts.AccountStoreUnavailable:
        st.error("Base de données indisponible." if fr else "Database unavailable.")
        return
    if users:
        st.dataframe(users, hide_index=True, width="stretch")
    else:
        st.info("Aucun compte en base pour l'instant." if fr else "No database accounts yet.")

    st.subheader("➕ " + ("Créer un compte" if fr else "Create account"))
    with st.form("create_user", clear_on_submit=True):
        new_username = st.text_input("Identifiant" if fr else "Username")
        new_email = st.text_input("E-mail (facultatif)" if fr else "Email (optional)")
        new_role = st.selectbox("Rôle" if fr else "Role", accounts.ROLES, index=accounts.ROLES.index("supervisor"))
        new_password = st.text_input("Mot de passe initial" if fr else "Initial password", type="password",
                                     help=f"≥ {accounts.MIN_PASSWORD_LENGTH}")
        if st.form_submit_button("Créer" if fr else "Create", type="primary"):
            try:
                accounts.create_user(new_username, new_password, new_role, created_by=current_username(),
                                     email=new_email or None)
                st.success(("Compte créé : " if fr else "Account created: ") + new_username)
            except accounts.AccountError as exc:
                st.error(str(exc))
            except accounts.AccountStoreUnavailable:
                st.error("Base de données indisponible." if fr else "Database unavailable.")

    _render_membership_admin(fr)


def _render_membership_admin(fr: bool) -> None:
    """Organizations and memberships (tenant isolation, finding F2). Only a
    platform administrator reaches this page (is_admin() check above), and
    tenancy.py re-checks that on every change."""
    import tenancy

    actor = tenancy.principal_from_session(st)
    st.subheader("🏢 " + ("Organisations et membres" if fr else "Organizations and members"))
    st.caption("Un utilisateur ne voit et ne modifie que les données des organisations dont il est membre."
               if fr else "A user only sees and changes data of the organizations they are a member of.")
    try:
        orgs = tenancy.accessible_organizations(actor)
        members = tenancy.list_memberships()
    except Exception:  # noqa: BLE001
        st.error("Base de données indisponible." if fr else "Database unavailable.")
        return
    if members:
        st.dataframe(members, hide_index=True, width="stretch")

    with st.form("create_org", clear_on_submit=True):
        org_name = st.text_input("Nouvelle organisation" if fr else "New organization")
        if st.form_submit_button("Créer l'organisation" if fr else "Create organization") and org_name.strip():
            try:
                tenancy.create_organization(actor, org_name)
                st.success(("Organisation créée : " if fr else "Organization created: ") + org_name.strip())
                st.rerun()
            except (tenancy.TenancyError, tenancy.TenantAccessDenied) as exc:
                st.error(str(exc))

    if not orgs:
        return
    names = {o["name"]: o["id"] for o in orgs}
    role_labels = {"viewer": "viewer - lecture seule" if fr else "viewer - read only",
                   "supervisor": "supervisor - évaluations" if fr else "supervisor - runs assessments",
                   "org_admin": "org_admin - gère l'organisation" if fr else "org_admin - manages the organization"}
    with st.form("set_membership", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        member_user = c1.text_input("Identifiant" if fr else "Username")
        member_org = c2.selectbox("Organisation" if fr else "Organization", list(names))
        member_role = c3.selectbox("Rôle" if fr else "Role", list(tenancy.ORG_ROLES),
                                   index=list(tenancy.ORG_ROLES).index(tenancy.DEFAULT_ORG_ROLE),
                                   format_func=lambda r: role_labels[r])
        b1, b2 = st.columns(2)
        add = b1.form_submit_button("Ajouter / changer le rôle" if fr else "Add / change role", type="primary")
        remove = b2.form_submit_button("Retirer de l'organisation" if fr else "Remove from organization")
        if (add or remove) and member_user.strip():
            try:
                if add:
                    tenancy.set_membership(actor, member_user.strip(), names[member_org], member_role)
                    st.success(("Membre enregistré : " if fr else "Membership saved: ")
                               + f"{member_user.strip()} → {member_org} ({member_role})")
                elif tenancy.remove_membership(actor, member_user.strip(), names[member_org]):
                    st.success(("Retiré : " if fr else "Removed: ") + f"{member_user.strip()} / {member_org}")
                else:
                    st.info("Aucune adhésion à retirer." if fr else "No such membership.")
                st.rerun()
            except (tenancy.TenancyError, tenancy.TenantAccessDenied) as exc:
                st.error(str(exc))
