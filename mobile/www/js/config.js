/* MAKU shell configuration - the only file to edit per environment. */
window.MAKU_CONFIG = Object.freeze({
  APP_ORIGIN: "https://maku-platform-kn2dmt4u75pyb2ck5dtkbd.streamlit.app", // hosted Streamlit app (no trailing slash)
  HEALTH_PATH: "/",                        // reachability probe ("/healthz" on the Docker/Caddy stack)
  LOAD_TIMEOUT_MS: 20000,                  // show the offline view if the app hasn't loaded by then
  OFFLINE_HISTORY_LIMIT: 10,               // assessments kept on the device
  MAX_BRIDGE_FILE_BYTES: 15 * 1024 * 1024, // largest report the app may hand to the share sheet
  SHELL_VERSION: "1.0.2"
});
