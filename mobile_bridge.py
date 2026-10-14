"""
MAKU - bridge between the hosted Streamlit app and the native mobile shell
==========================================================================
When MAKU runs inside the iOS/Android shell (mobile/www/js/app.js), the
shell loads https://<domain>/?shell=ios|android in an iframe and answers a
small set of postMessage requests with native device features.

From Python, each request is a promise evaluated by streamlit_js_eval in a
same-origin component iframe:

    component iframe --postMessage--> shell (window.top)
    component iframe <--postMessage-- shell replies to event.source

Like every streamlit_js_eval call, a request returns None on the first run
and the shell's reply on the automatic rerun that follows. Outside the shell
(normal browser) every helper returns {"error": "not-in-shell"} immediately
and the app falls back to its web behaviour.
"""

from __future__ import annotations

import base64
import json
import logging
import time

import streamlit as st

logger = logging.getLogger("maku.mobile_bridge")

SHELL_KEY = "_mobile_shell_platform"
SHELL_ORIGINS = ("capacitor://localhost", "https://localhost")
SUPPORTED_PLATFORMS = ("ios", "android")

try:
    from streamlit_js_eval import streamlit_js_eval
    BRIDGE_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency is in requirements.txt
    BRIDGE_AVAILABLE = False


def detect_shell() -> None:
    """Call once at the very top of app.py (before login): remembers for the
    whole session that the page was opened by the native shell."""
    try:
        platform = st.query_params.get("shell")
    except Exception:  # noqa: BLE001
        platform = None
    if platform in SUPPORTED_PLATFORMS:
        st.session_state[SHELL_KEY] = platform


def shell_platform() -> str | None:
    return st.session_state.get(SHELL_KEY)


def in_mobile_shell() -> bool:
    return shell_platform() in SUPPORTED_PLATFORMS


def _request_js(message_type: str, payload: dict | None, timeout_ms: int) -> str:
    message = json.dumps({"source": "maku-app", "type": message_type, **(payload or {})})
    origins = json.dumps(list(SHELL_ORIGINS))
    return f"""
new Promise((resolve) => {{
  if (window.top === window.parent) {{ resolve({{error: "not-in-shell"}}); return; }}
  const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
  const msg = Object.assign({message}, {{id}});
  const done = (value) => {{ window.removeEventListener("message", onMsg); clearTimeout(timer); resolve(value); }};
  const onMsg = (e) => {{
    if (!{origins}.includes(e.origin)) return;
    if (e.data && e.data.source === "maku-shell" && e.data.replyTo === id) done(e.data);
  }};
  window.addEventListener("message", onMsg);
  const timer = setTimeout(() => done({{error: "timeout"}}), {int(timeout_ms)});
  for (const o of {origins}) {{ try {{ window.top.postMessage(msg, o); }} catch (_) {{}} }}
}})
"""


def bridge_request(message_type: str, key: str, payload: dict | None = None,
                   timeout_ms: int = 20000) -> dict | None:
    """Sends one request to the shell. Returns the reply dict, None while the
    reply is pending (first run), or {"error": ...}."""
    if not in_mobile_shell():
        return {"error": "not-in-shell"}
    if not BRIDGE_AVAILABLE:
        return {"error": "unavailable"}
    try:
        return streamlit_js_eval(js_expressions=_request_js(message_type, payload, timeout_ms), key=key)
    except Exception as exc:  # noqa: BLE001 - the bridge must never break a page
        logger.warning("bridge request %s failed: %s", message_type, exc)
        return {"error": "unavailable"}


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------

def request_native_location(key: str = "native_gps") -> dict | None:
    """Native GPS fix, normalised to the same shape as the browser
    Geolocation payload app.py already handles:
    {"coords": {"latitude", "longitude", "accuracy"}} or {"error": {"code", "message"}}."""
    reply = bridge_request("request-location", key=key, timeout_ms=20000)
    if reply is None:
        return None
    if "coords" in reply:
        return {"coords": reply["coords"], "timestamp": reply.get("timestamp")}
    err = reply.get("error")
    if isinstance(err, dict):
        return {"error": err}
    return {"error": {"code": 3 if err == "timeout" else 2, "message": str(err or "unavailable")}}


def request_native_photo(key: str) -> bytes | None | dict:
    """JPEG bytes from the native camera, None while pending, or {"error": ...}."""
    reply = bridge_request("request-photo", key=key, timeout_ms=120000)
    if reply is None:
        return None
    data_url = reply.get("dataUrl") if isinstance(reply, dict) else None
    if not data_url or "," not in data_url:
        return {"error": (reply or {}).get("error", "unavailable")}
    try:
        return base64.b64decode(data_url.split(",", 1)[1], validate=False)
    except Exception:  # noqa: BLE001
        return {"error": "invalid-image"}


def request_push_token(key: str = "native_push_token") -> dict | None:
    return bridge_request("request-push-token", key=key, timeout_ms=60000)


def send_assessment_to_shell(result: dict, controls: list, key_metric_label: str = "",
                             key_metric_value=None) -> None:
    """Caches a compact summary on the phone for the shell's offline view.
    Fire-and-forget; called once per new assessment."""
    if not in_mobile_shell():
        return
    payload = {
        "module": result.get("module", ""),
        "risk_band": str(result.get("risk_band", "")),
        "safety_override": bool(result.get("safety_override")),
        "key_metric_label": key_metric_label,
        "key_metric_value": "" if key_metric_value is None else str(key_metric_value),
        "site": st.session_state.get("_analytics_org_context", {}).get("site", "") if isinstance(
            st.session_state.get("_analytics_org_context"), dict) else "",
        "data_provenance": result.get("data_provenance", "MANUAL"),
        "controls": [str(c) for c in (controls or [])[:5]],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    stamp = f"{payload['module']}|{payload['timestamp'][:16]}|{payload['risk_band']}"
    if st.session_state.get("_last_shell_sync") == stamp:
        return
    st.session_state["_last_shell_sync"] = stamp
    bridge_request("assessment", key=f"shell_sync_{abs(hash(stamp))}", payload={"payload": payload},
                   timeout_ms=5000)


def share_file_via_shell(data: bytes, file_name: str, title: str, key: str) -> dict | None:
    """Writes a report on the phone and opens the native share sheet
    (WebView downloads are unreliable inside native apps)."""
    return bridge_request(
        "save-file", key=key, timeout_ms=120000,
        payload={"name": file_name, "title": title, "base64": base64.b64encode(data).decode("ascii")},
    )
