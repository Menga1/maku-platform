"""
MAKU - bridge between the hosted Streamlit app and the native mobile shell
==========================================================================
When MAKU runs inside the iOS/Android shell (mobile/www/js/app.js), the
shell loads https://<domain>/?shell=ios|android in an iframe and answers a
small set of postMessage requests with native device features.

From Python, each request is a promise evaluated by streamlit_js_eval in a
same-origin component iframe. Two transports, same request/reply shapes:

* iframe mode (Android): the shell page is window.top and answers
      component iframe --postMessage--> shell (window.top)
      component iframe <--postMessage-- shell replies to event.source
* top-level mode (iOS): WebKit blocks Streamlit Cloud's cookies inside a
  cross-site iframe, so the iOS shell opens MAKU as the WebView's main page.
  Capacitor then injects its native bridge into that page (window.top is
  this same-origin MAKU page), and _NATIVE_HANDLER_JS calls the plugins
  directly - mirroring the handlers in mobile/www/js/app.js.

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


# Keep in sync with mobile/www/js/app.js (handlers + HISTORY_KEY + limits):
# the offline view of the shell reads the same Preferences entry.
_NATIVE_HANDLER_JS = r"""
async (Cap, msg) => {
  const P = Cap.Plugins || {};
  const platform = (Cap.getPlatform && Cap.getPlatform()) || "ios";
  const HISTORY_KEY = "maku.assessments.v1", HISTORY_LIMIT = 10, MAX_FILE_BYTES = 15 * 1024 * 1024;
  const s = (v, n = 200) => (v == null ? "" : String(v)).slice(0, n);
  switch (msg.type) {
    case "hello":
      return { type: "hello", platform, native: true, version: "top-level",
               capabilities: { location: !!P.Geolocation, camera: !!P.Camera,
                               push: !!P.FirebaseMessaging, share: !!(P.Filesystem && P.Share) } };
    case "request-location": {
      const G = P.Geolocation;
      if (!G) return { type: "location", error: { code: 2, message: "unavailable" } };
      try {
        let perm = await G.checkPermissions();
        if (perm.location !== "granted" && perm.coarseLocation !== "granted")
          perm = await G.requestPermissions({ permissions: ["location", "coarseLocation"] });
        if (perm.location !== "granted" && perm.coarseLocation !== "granted")
          return { type: "location", error: { code: 1, message: "permission denied" } };
        const pos = await G.getCurrentPosition({ enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 });
        return { type: "location", timestamp: pos.timestamp,
                 coords: { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy } };
      } catch (err) {
        const m = String((err && err.message) || err);
        const code = /denied|permission/i.test(m) ? 1 : /timeout/i.test(m) ? 3 : 2;
        return { type: "location", error: { code, message: code === 1 ? "permission denied" : code === 3 ? "timeout" : "unavailable" } };
      }
    }
    case "request-photo": {
      if (!P.Camera) return { type: "photo", error: "unavailable" };
      try {
        const photo = await P.Camera.getPhoto({ quality: 70, width: 1600, correctOrientation: true,
                                                resultType: "dataUrl", source: "CAMERA", saveToGallery: false });
        return { type: "photo", dataUrl: photo.dataUrl, format: photo.format };
      } catch (err) {
        return { type: "photo", error: /cancel/i.test(String(err && err.message)) ? "cancelled" : "unavailable" };
      }
    }
    case "request-push-token": {
      const F = P.FirebaseMessaging;
      if (!F) return { type: "push-token", error: "unavailable" };
      try {
        let perm = await F.checkPermissions();
        if (perm.receive === "prompt" || perm.receive === "prompt-with-rationale") perm = await F.requestPermissions();
        if (perm.receive !== "granted") return { type: "push-token", error: "denied" };
        const { token } = await F.getToken();
        if (P.Preferences) await P.Preferences.set({ key: "maku.pushToken", value: token });
        return { type: "push-token", token, platform };
      } catch (_) { return { type: "push-token", error: "unavailable" }; }
    }
    case "assessment": {
      if (!P.Preferences) return { type: "ack" };
      const raw = msg.payload || {};
      const entry = {
        module: s(raw.module, 80), risk_band: s(raw.risk_band, 20).toUpperCase(),
        safety_override: !!raw.safety_override, key_metric_label: s(raw.key_metric_label, 80),
        key_metric_value: s(raw.key_metric_value, 40), site: s(raw.site, 120),
        data_provenance: s(raw.data_provenance, 20),
        controls: Array.isArray(raw.controls) ? raw.controls.slice(0, 5).map((c) => s(c, 300)) : [],
        timestamp: s(raw.timestamp, 40) || new Date().toISOString()
      };
      let history = [];
      try { history = JSON.parse((await P.Preferences.get({ key: HISTORY_KEY })).value || "[]"); } catch (_) { history = []; }
      history = (Array.isArray(history) ? history : []).filter((h) => h && h.timestamp !== entry.timestamp);
      history.unshift(entry);
      await P.Preferences.set({ key: HISTORY_KEY, value: JSON.stringify(history.slice(0, HISTORY_LIMIT)) });
      return { type: "ack" };
    }
    case "save-file": {
      if (!P.Filesystem || !P.Share) return { type: "file", error: "unavailable" };
      const b64 = String(msg.base64 || "");
      if (!b64 || b64.length * 0.75 > MAX_FILE_BYTES) return { type: "file", error: "too-large" };
      let path = String(msg.name || "maku-report").replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 80);
      if (!/\.(pdf|xlsx|csv|html|json)$/i.test(path)) path += ".pdf";
      const title = String(msg.title || "MAKU report").slice(0, 120);
      try {
        const written = await P.Filesystem.writeFile({ path, data: b64, directory: "CACHE" });
        await P.Share.share({ title, url: written.uri, dialogTitle: title });
        return { type: "file", ok: true };
      } catch (err) {
        return { type: "file", error: /cancel/i.test(String(err && err.message)) ? "cancelled" : "failed" };
      }
    }
  }
  return { error: "unsupported" };
}
"""


def _request_js(message_type: str, payload: dict | None, timeout_ms: int) -> str:
    message = json.dumps({"source": "maku-app", "type": message_type, **(payload or {})})
    origins = json.dumps(list(SHELL_ORIGINS))
    return f"""
new Promise((resolve) => {{
  const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
  const msg = Object.assign({message}, {{id}});
  // Top-level mode (iOS): MAKU itself is the WebView's main page and carries
  // the Capacitor bridge. Cross-origin (iframe mode) access throws -> skipped.
  let nativeCap = null;
  try {{
    const C = window.top.Capacitor;
    if (C && C.isNativePlatform && C.isNativePlatform() && C.Plugins) nativeCap = C;
  }} catch (_) {{ nativeCap = null; }}
  if (nativeCap) {{
    const t = setTimeout(() => resolve({{error: "timeout"}}), {int(timeout_ms)});
    ({_NATIVE_HANDLER_JS.strip()})(nativeCap, msg)
      .then((v) => {{ clearTimeout(t); resolve(Object.assign({{source: "maku-shell", replyTo: id}}, v)); }},
            () => {{ clearTimeout(t); resolve({{error: "unavailable"}}); }});
    return;
  }}
  if (window.top === window.parent) {{ resolve({{error: "not-in-shell"}}); return; }}
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
