"""
MAKU - stop-work push alerts (Firebase Cloud Messaging HTTP v1)
===============================================================
Devices register their FCM token through the mobile shell (mobile_bridge.
request_push_token -> register_device). When an assessment raises a SAFETY
OVERRIDE, notify_stop_work() sends an alert to every registered device in
the same organisation, on a background thread so the page never waits.

FCM delivers to Android directly and to iOS through APNs (upload your APNs
auth key in the Firebase console - see docs/DEPLOYMENT.md).

Configuration (environment):
    MAKU_FCM_SERVICE_ACCOUNT_FILE  path to the Firebase service-account JSON
    MAKU_FCM_PROJECT_ID            Firebase project id (defaults to the JSON's)
Push is simply disabled when these are not set.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

import analytics as _analytics

logger = logging.getLogger("maku.push")

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
FCM_SEND_URL = "https://fcm.googleapis.com/v1/projects/{project}/messages:send"
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="maku-push")
_CRED_LOCK = threading.Lock()
_credentials = None


def push_enabled() -> bool:
    path = os.environ.get("MAKU_FCM_SERVICE_ACCOUNT_FILE", "").strip()
    return bool(path) and os.path.exists(path)


def _project_id() -> str:
    explicit = os.environ.get("MAKU_FCM_PROJECT_ID", "").strip()
    if explicit:
        return explicit
    with open(os.environ["MAKU_FCM_SERVICE_ACCOUNT_FILE"], encoding="utf-8") as fh:
        return json.load(fh)["project_id"]


def _access_token() -> str:
    """OAuth2 access token for FCM, refreshed automatically when expired."""
    global _credentials
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    with _CRED_LOCK:
        if _credentials is None:
            _credentials = service_account.Credentials.from_service_account_file(
                os.environ["MAKU_FCM_SERVICE_ACCOUNT_FILE"], scopes=[FCM_SCOPE])
        if not _credentials.valid:
            _credentials.refresh(Request())
        return _credentials.token


# ---------------------------------------------------------------------------
# Device registry
# ---------------------------------------------------------------------------

def register_device(username: str, token: str, platform: str, organization: str) -> None:
    if not token or len(token) > 4096 or platform not in ("ios", "android"):
        raise ValueError("invalid device token")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _analytics._get_connection() as conn:
        conn.execute("DELETE FROM device_tokens WHERE token = ?", (token,))
        conn.execute(
            "INSERT INTO device_tokens (username, token, platform, organization, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, token, platform, organization or "", now, now),
        )


def _tokens_for_organization(organization: str) -> list[str]:
    with _analytics._get_connection() as conn:
        cur = conn.execute("SELECT token FROM device_tokens WHERE organization = ?", (organization or "",))
        return [row[0] for row in cur.fetchall()]


def _forget_token(token: str) -> None:
    with _analytics._get_connection() as conn:
        conn.execute("DELETE FROM device_tokens WHERE token = ?", (token,))


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------

def _send_one(token: str, title: str, body: str, data: dict) -> bool:
    message = {
        "message": {
            "token": token,
            "notification": {"title": title[:110], "body": body[:240]},
            "data": {k: str(v)[:500] for k, v in (data or {}).items()},
            "android": {"priority": "HIGH",
                        "notification": {"channel_id": "maku_stop_work", "default_sound": True}},
            "apns": {"headers": {"apns-priority": "10"},
                     "payload": {"aps": {"sound": "default", "interruption-level": "time-sensitive"}}},
        }
    }
    resp = requests.post(
        FCM_SEND_URL.format(project=_project_id()),
        headers={"Authorization": f"Bearer {_access_token()}", "Content-Type": "application/json"},
        json=message, timeout=10,
    )
    if resp.status_code == 200:
        return True
    if resp.status_code in (400, 404) and ("UNREGISTERED" in resp.text or "INVALID_ARGUMENT" in resp.text):
        _forget_token(token)  # app uninstalled or token rotated
    logger.warning("FCM send failed (%s): %s", resp.status_code, resp.text[:300])
    return False


def _send_to_organization(organization: str, title: str, body: str, data: dict) -> int:
    sent = 0
    for token in _tokens_for_organization(organization):
        try:
            sent += 1 if _send_one(token, title, body, data) else 0
        except Exception as exc:  # noqa: BLE001 - one bad token never stops the rest
            logger.warning("FCM send error: %s", exc)
    logger.info("Stop-work alert delivered to %d device(s) in '%s'", sent, organization)
    return sent


def notify_stop_work(result: dict, organization: str, site: str = "") -> bool:
    """Queue a stop-work alert for the organisation. Never raises and never
    blocks the page. Simulated assessments are never pushed."""
    if not push_enabled() or not result.get("safety_override"):
        return False
    if result.get("data_provenance") == "SIMULATED":
        return False
    module = result.get("module", "MAKU")
    title = f"STOP WORK - {module}"
    body = (f"Safety override at {site}. " if site else "Safety override. ") + \
           f"Risk {result.get('risk_band', '')}: {result.get('primary_hazard', '')}"
    data = {"module": module, "risk_band": result.get("risk_band", ""), "site": site,
            "kind": "stop_work"}
    try:
        _EXECUTOR.submit(_send_to_organization, organization, title, body, data)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not queue push: %s", exc)
        return False
