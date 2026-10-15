/*
 * MAKU native shell (Capacitor 8)
 * ================================
 * The hosted MAKU app (MAKU_CONFIG.APP_ORIGIN) runs inside a full-screen iframe.
 * This shell adds what a website alone cannot do, through a narrow,
 * origin-checked postMessage bridge:
 *
 *   app -> shell  {source:"maku-app",   id, type, ...}
 *   shell -> app  {source:"maku-shell", replyTo:id, type, ...}
 *
 *   type "hello"               -> platform / version / capabilities
 *   type "request-location"    -> native GPS fix (Geolocation plugin)
 *   type "request-photo"       -> native camera photo as a JPEG data URL
 *   type "request-push-token"  -> asks notification permission, returns the FCM token
 *   type "assessment"          -> stores the result on the device for offline viewing
 *   type "save-file"           -> writes a report (PDF/XLSX/CSV) and opens the share sheet
 *
 * Messages are accepted ONLY from MAKU_CONFIG.APP_ORIGIN, and replies are
 * posted ONLY to that origin. Nothing here ever evaluates code from the page.
 *
 * Offline: the shell watches connectivity (Network plugin) and probes the
 * server; with no network or no server it shows the last assessments cached
 * on the device (Preferences plugin). The iframe is kept alive underneath,
 * so the user's MAKU session resumes when the connection returns.
 */
(function () {
  "use strict";

  const CFG = window.MAKU_CONFIG;
  const Cap = window.Capacitor || null;
  const Plugins = (Cap && Cap.Plugins) || {};
  const isNative = !!(Cap && Cap.isNativePlatform && Cap.isNativePlatform());
  const platform = (Cap && Cap.getPlatform && Cap.getPlatform()) || "web";
  const { Network, Preferences, SplashScreen, StatusBar, App, Geolocation, Camera,
          Filesystem, Share, FirebaseMessaging } = Plugins;

  const HISTORY_KEY = "maku.assessments.v1";
  const PUSH_TOKEN_KEY = "maku.pushToken";

  const $ = (id) => document.getElementById(id);
  const frame = $("app-frame");
  const loading = $("loading");
  const offline = $("offline");

  const state = { online: true, frameLoaded: false, loadTimer: null, pushToken: null, splashHidden: false };

  // ------------------------------------------------------------------ utils
  function toast(message, ms = 3500) {
    const el = $("toast");
    el.textContent = message;
    el.classList.remove("hidden");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add("hidden"), ms);
  }

  async function hideSplash() {
    if (state.splashHidden) return;
    state.splashHidden = true;
    try { if (SplashScreen) await SplashScreen.hide({ fadeOutDuration: 250 }); } catch (_) { /* web */ }
  }

  async function storageGet(key) {
    try {
      if (Preferences) return (await Preferences.get({ key })).value;
      return window.localStorage.getItem(key);
    } catch (_) { return null; }
  }

  async function storageSet(key, value) {
    try {
      if (Preferences) return await Preferences.set({ key, value });
      window.localStorage.setItem(key, value);
    } catch (_) { /* storage unavailable - offline history simply not kept */ }
  }

  function timeAgo(iso) {
    const then = Date.parse(iso);
    if (Number.isNaN(then)) return "";
    const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
    if (mins < 1) return t("justNow");
    const units = mins < 60 ? [mins, "min"] : mins < 1440 ? [Math.round(mins / 60), "h"] : [Math.round(mins / 1440), "d"];
    const ago = t("ago");
    return ago ? `${units[0]} ${units[1]} ${ago}` : `${units[0]} ${units[1]}`;
  }

  function text(tag, className, value) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = value == null ? "" : String(value);
    return el;
  }

  // ------------------------------------------------------- offline history
  async function readHistory() {
    try { return JSON.parse((await storageGet(HISTORY_KEY)) || "[]"); } catch (_) { return []; }
  }

  function sanitizeAssessment(raw) {
    // Keep only known, display-safe fields; cap lengths.
    const s = (v, n = 200) => (v == null ? "" : String(v)).slice(0, n);
    const controls = Array.isArray(raw.controls) ? raw.controls.slice(0, 5).map((c) => s(c, 300)) : [];
    return {
      module: s(raw.module, 80), risk_band: s(raw.risk_band, 20).toUpperCase(),
      safety_override: !!raw.safety_override, key_metric_label: s(raw.key_metric_label, 80),
      key_metric_value: s(raw.key_metric_value, 40), site: s(raw.site, 120),
      data_provenance: s(raw.data_provenance, 20), controls,
      timestamp: s(raw.timestamp, 40) || new Date().toISOString()
    };
  }

  async function saveAssessment(raw) {
    const entry = sanitizeAssessment(raw || {});
    const history = (await readHistory()).filter((h) => h.timestamp !== entry.timestamp);
    history.unshift(entry);
    await storageSet(HISTORY_KEY, JSON.stringify(history.slice(0, CFG.OFFLINE_HISTORY_LIMIT)));
  }

  async function renderHistory() {
    const list = $("history");
    list.replaceChildren();
    const history = await readHistory();
    $("history-empty").classList.toggle("hidden", history.length > 0);
    for (const h of history) {
      const li = document.createElement("li");
      li.className = "card";
      const top = document.createElement("div");
      top.className = "card-top";
      top.append(text("h2", "", h.module + (h.site ? ` · ${h.site}` : "")), text("span", "age", timeAgo(h.timestamp)));
      li.append(top);
      const known = ["CRITICAL", "HIGH", "MODERATE", "LOW"].includes(h.risk_band);
      li.append(text("span", `band ${known ? h.risk_band : "OTHER"}`, h.risk_band || "-"));
      if (h.safety_override) li.append(text("p", "override", t("stopWork")));
      if (h.data_provenance === "SIMULATED") li.append(text("p", "simulated", t("simulated")));
      if (h.key_metric_label) li.append(text("p", "metric", `${h.key_metric_label}: ${h.key_metric_value}`));
      if (h.controls.length) {
        li.append(text("strong", "", t("controls")));
        const ul = document.createElement("ul");
        ul.className = "controls";
        h.controls.forEach((c) => ul.append(text("li", "", c)));
        li.append(ul);
      }
      list.append(li);
    }
  }

  async function showOffline(reasonKey) {
    $("offline-reason").textContent = t(reasonKey || "offlineBody");
    await renderHistory();
    offline.classList.remove("hidden");
    loading.classList.add("hidden");
    hideSplash();
  }

  function hideOffline() { offline.classList.add("hidden"); }

  // ---------------------------------------------------------- app loading
  async function serverReachable() {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 8000);
      await fetch(CFG.APP_ORIGIN + CFG.HEALTH_PATH, { mode: "no-cors", cache: "no-store", signal: ctrl.signal });
      clearTimeout(timer);
      return true;
    } catch (_) { return false; }
  }

  async function loadApp(path) {
    if (!(await serverReachable())) { showOffline("serverDown"); return; }
    loading.classList.remove("hidden");
    $("loading-text").textContent = t("loading");
    const url = new URL(path || "/", CFG.APP_ORIGIN);
    url.searchParams.set("shell", platform);
    url.searchParams.set("embed", "true");   // Streamlit Cloud: hide its own toolbar and badges
    clearTimeout(state.loadTimer);
    state.loadTimer = setTimeout(() => { if (!state.frameLoaded) showOffline("serverDown"); }, CFG.LOAD_TIMEOUT_MS);
    frame.src = url.toString();
  }

  frame.addEventListener("load", () => {
    if (!frame.src) return;
    state.frameLoaded = true;
    clearTimeout(state.loadTimer);
    loading.classList.add("hidden");
    hideOffline();
    hideSplash();
  });

  async function setOnline(connected) {
    const was = state.online;
    state.online = connected;
    if (!connected) { showOffline("offlineBody"); return; }
    if (!state.frameLoaded) { await loadApp("/"); return; }
    if (!was) {
      if (await serverReachable()) { hideOffline(); toast(t("backOnline")); }
      else showOffline("serverDown");
    }
  }

  // ------------------------------------------------------------ bridge
  const ALLOWED_TYPES = new Set(["hello", "request-location", "request-photo", "request-push-token",
                                 "assessment", "save-file"]);

  function reply(event, msg, payload) {
    if (!event.source) return;
    event.source.postMessage(Object.assign({ source: "maku-shell", replyTo: msg.id }, payload), CFG.APP_ORIGIN);
  }

  async function handleLocation() {
    if (!Geolocation) return { type: "location", error: { code: 2, message: "unavailable" } };
    try {
      let perm = await Geolocation.checkPermissions();
      if (perm.location !== "granted" && perm.coarseLocation !== "granted") {
        perm = await Geolocation.requestPermissions({ permissions: ["location", "coarseLocation"] });
      }
      if (perm.location !== "granted" && perm.coarseLocation !== "granted") {
        return { type: "location", error: { code: 1, message: "permission denied" } };
      }
      const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 });
      return { type: "location",
               coords: { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy },
               timestamp: pos.timestamp };
    } catch (err) {
      const msg = String((err && err.message) || err);
      const code = /denied|permission/i.test(msg) ? 1 : /timeout/i.test(msg) ? 3 : 2;
      return { type: "location", error: { code, message: code === 1 ? "permission denied" : code === 3 ? "timeout" : "unavailable" } };
    }
  }

  async function handlePhoto() {
    if (!Camera) return { type: "photo", error: "unavailable" };
    try {
      const photo = await Camera.getPhoto({ quality: 70, width: 1600, correctOrientation: true,
                                            resultType: "dataUrl", source: "CAMERA", saveToGallery: false });
      return { type: "photo", dataUrl: photo.dataUrl, format: photo.format };
    } catch (err) {
      return { type: "photo", error: /cancel/i.test(String(err && err.message)) ? "cancelled" : "unavailable" };
    }
  }

  async function handlePushToken() {
    if (!FirebaseMessaging) return { type: "push-token", error: "unavailable" };
    try {
      let perm = await FirebaseMessaging.checkPermissions();
      if (perm.receive === "prompt" || perm.receive === "prompt-with-rationale") {
        perm = await FirebaseMessaging.requestPermissions();
      }
      if (perm.receive !== "granted") return { type: "push-token", error: "denied" };
      const { token } = await FirebaseMessaging.getToken();
      state.pushToken = token;
      await storageSet(PUSH_TOKEN_KEY, token);
      return { type: "push-token", token, platform };
    } catch (_) {
      return { type: "push-token", error: "unavailable" };
    }
  }

  function safeFileName(name) {
    const clean = String(name || "maku-report").replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 80);
    return /\.(pdf|xlsx|csv|html|json)$/i.test(clean) ? clean : clean + ".pdf";
  }

  async function handleSaveFile(msg) {
    if (!Filesystem || !Share) return { type: "file", error: "unavailable" };
    const base64 = String(msg.base64 || "");
    if (!base64 || base64.length * 0.75 > CFG.MAX_BRIDGE_FILE_BYTES) return { type: "file", error: "too-large" };
    try {
      const path = safeFileName(msg.name);
      const written = await Filesystem.writeFile({ path, data: base64, directory: "CACHE" });
      await Share.share({ title: String(msg.title || "MAKU report").slice(0, 120), url: written.uri,
                          dialogTitle: String(msg.title || "MAKU report").slice(0, 120) });
      return { type: "file", ok: true };
    } catch (err) {
      return { type: "file", error: /cancel/i.test(String(err && err.message)) ? "cancelled" : "failed" };
    }
  }

  window.addEventListener("message", async (event) => {
    if (event.origin !== CFG.APP_ORIGIN) return;
    const msg = event.data;
    if (!msg || typeof msg !== "object" || msg.source !== "maku-app" || !ALLOWED_TYPES.has(msg.type)) return;
    switch (msg.type) {
      case "hello":
        reply(event, msg, { type: "hello", platform, native: isNative, version: CFG.SHELL_VERSION,
                            capabilities: { location: !!Geolocation, camera: !!Camera,
                                            push: !!FirebaseMessaging, share: !!(Filesystem && Share) } });
        break;
      case "request-location": reply(event, msg, await handleLocation()); break;
      case "request-photo": reply(event, msg, await handlePhoto()); break;
      case "request-push-token": reply(event, msg, await handlePushToken()); break;
      case "assessment":
        await saveAssessment(msg.payload);
        reply(event, msg, { type: "ack" });
        break;
      case "save-file":
        reply(event, msg, await handleSaveFile(msg));
        toast(t("fileShared"), 2000);
        break;
    }
  });

  // ------------------------------------------------------------- startup
  async function init() {
    $("retry").addEventListener("click", async () => {
      $("loading-text").textContent = t("reconnecting");
      if (state.frameLoaded) await setOnline(true); else await loadApp("/");
    });

    try { if (StatusBar) await StatusBar.setBackgroundColor({ color: "#0c5c63" }); } catch (_) { /* iOS */ }

    if (App) {
      App.addListener("backButton", () => {
        if (!offline.classList.contains("hidden") && state.frameLoaded && state.online) hideOffline();
        else App.minimizeApp();
      });
      App.addListener("resume", async () => {
        if (Network) setOnline((await Network.getStatus()).connected);
      });
      // Universal / App Links: honour the path only on a cold start so an open
      // MAKU session is never thrown away by a link tap.
      App.addListener("appUrlOpen", ({ url }) => {
        try {
          const target = new URL(url);
          if (target.origin === CFG.APP_ORIGIN && !state.frameLoaded) loadApp(target.pathname);
        } catch (_) { /* ignore malformed links */ }
      });
    }

    if (FirebaseMessaging) {
      if (platform === "android") {
        // Must match the channel_id the server sends (push.py: "maku_stop_work").
        try {
          await FirebaseMessaging.createChannel({
            id: "maku_stop_work", name: "Stop-work alerts",
            description: "Safety overrides raised by assessments in your organisation",
            importance: 5, visibility: 1, vibration: true, lights: true, lightColor: "#B00020"
          });
        } catch (_) { /* older Android - default channel is used */ }
      }
      FirebaseMessaging.addListener("notificationReceived", ({ notification }) => {
        if (notification) toast(`${notification.title || "MAKU"} - ${notification.body || ""}`, 8000);
      });
      FirebaseMessaging.addListener("tokenReceived", async ({ token }) => {
        state.pushToken = token;
        await storageSet(PUSH_TOKEN_KEY, token);
      });
    }

    let connected = navigator.onLine;
    if (Network) {
      try { connected = (await Network.getStatus()).connected; } catch (_) { /* keep navigator.onLine */ }
      Network.addListener("networkStatusChange", (s) => setOnline(s.connected));
    } else {
      window.addEventListener("online", () => setOnline(true));
      window.addEventListener("offline", () => setOnline(false));
    }
    state.online = connected;
    if (connected) await loadApp("/"); else await showOffline("offlineBody");

    setTimeout(hideSplash, 6000); // never leave the splash up
  }

  document.addEventListener("DOMContentLoaded", init);
})();
