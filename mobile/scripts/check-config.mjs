#!/usr/bin/env node
/** Pre-flight checks run by `npm run sync`. Fails on errors, prints warnings. */
import fs from "node:fs";

const errors = [];
const warnings = [];
const cfgSrc = fs.readFileSync("www/js/config.js", "utf8");
const origin = /APP_ORIGIN:\s*"([^"]+)"/.exec(cfgSrc)?.[1];
const cap = JSON.parse(fs.readFileSync("capacitor.config.json", "utf8"));
const html = fs.readFileSync("www/index.html", "utf8");

if (!origin || !origin.startsWith("https://")) errors.push("APP_ORIGIN in www/js/config.js must be an https:// URL");
if (origin && !html.includes(`frame-src ${origin}`)) errors.push(`index.html CSP frame-src must be ${origin}`);
if (origin && origin.endsWith("/")) errors.push("APP_ORIGIN must not end with '/'");

const wk = "../deploy/well-known";
if (fs.existsSync(wk)) {
  const aasa = fs.readFileSync(`${wk}/apple-app-site-association`, "utf8");
  const links = fs.readFileSync(`${wk}/assetlinks.json`, "utf8");
  if (!aasa.includes(cap.appId)) errors.push(`apple-app-site-association does not mention appId ${cap.appId}`);
  if (aasa.includes("TEAMID1234")) warnings.push("apple-app-site-association still has the TEAMID1234 placeholder");
  if (!links.includes(cap.appId)) errors.push(`assetlinks.json does not mention package ${cap.appId}`);
  if (links.includes("REPLACE:WITH")) warnings.push("assetlinks.json still has the placeholder SHA-256 fingerprint");
}
if (cap.android?.webContentsDebuggingEnabled) warnings.push("android.webContentsDebuggingEnabled is true - disable for release");
if (fs.existsSync("android") && !fs.existsSync("android/app/google-services.json"))
  warnings.push("android/app/google-services.json missing - push notifications disabled on Android");
if (fs.existsSync("ios") && !fs.existsSync("ios/App/App/GoogleService-Info.plist"))
  warnings.push("ios/App/App/GoogleService-Info.plist missing - push notifications disabled on iOS");

warnings.forEach((w) => console.log(`  ! ${w}`));
errors.forEach((e) => console.error(`  ✗ ${e}`));
if (errors.length) process.exit(1);
console.log(`  ✓ shell config OK (${origin}, ${cap.appId})`);
