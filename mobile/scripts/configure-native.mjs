#!/usr/bin/env node
/**
 * Idempotent native-project configuration for the MAKU shell.
 * Run automatically by `npm run add:ios` / `npm run add:android`, and safe to
 * re-run any time (e.g. after `npx cap sync`):
 *     node scripts/configure-native.mjs ios
 *     node scripts/configure-native.mjs android
 *
 * iOS     : usage-description strings, push background mode, export-compliance
 *           flag, Firebase auto-init OFF (privacy), AppDelegate push hooks,
 *           entitlements file (Associated Domains + Push) wired into the project.
 * Android : permissions, verified App Link for the MAKU domain, Firebase
 *           auto-init/analytics OFF, monochrome notification icon.
 */
import fs from "node:fs";
import path from "node:path";

const DOMAIN = new URL(
  /APP_ORIGIN:\s*"([^"]+)"/.exec(fs.readFileSync("www/js/config.js", "utf8"))[1]
).host;
const platform = process.argv[2];
const done = (msg) => console.log(`  ✓ ${msg}`);
const skip = (msg) => console.log(`  · ${msg} (already present)`);

function patchFile(file, marker, apply, label) {
  const src = fs.readFileSync(file, "utf8");
  if (src.includes(marker)) return skip(label);
  fs.writeFileSync(file, apply(src));
  done(label);
}

// ----------------------------------------------------------------- iOS
function configureIos() {
  const appDir = "ios/App/App";
  const plist = path.join(appDir, "Info.plist");
  if (!fs.existsSync(plist)) throw new Error("ios/ not found - run `npx cap add ios` first");

  const plistEntries = [
    ["NSLocationWhenInUseUsageDescription",
     "<string>MAKU uses your location to select the nearest site, local weather and the safety regulations that apply where you are working.</string>"],
    ["NSCameraUsageDescription",
     "<string>MAKU uses the camera to attach site photos to your HSE inspection report.</string>"],
    ["UIBackgroundModes", "<array>\n\t\t<string>remote-notification</string>\n\t</array>"],
    ["ITSAppUsesNonExemptEncryption", "<false/>"],
    ["FirebaseMessagingAutoInitEnabled", "<false/>"],
  ];
  for (const [key, value] of plistEntries) {
    patchFile(plist, `<key>${key}</key>`,
      (s) => s.replace(/<\/dict>\s*<\/plist>\s*$/, `\t<key>${key}</key>\n\t${value}\n</dict>\n</plist>\n`),
      `Info.plist ${key}`);
  }

  const delegate = path.join(appDir, "AppDelegate.swift");
  patchFile(delegate, "capacitorDidRegisterForRemoteNotifications", (s) => {
    const hooks = `
    // MARK: Push notifications (@capacitor-firebase/messaging)
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        NotificationCenter.default.post(name: .capacitorDidRegisterForRemoteNotifications, object: deviceToken)
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        NotificationCenter.default.post(name: .capacitorDidFailToRegisterForRemoteNotifications, object: error)
    }

    func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable: Any],
                     fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        NotificationCenter.default.post(name: Notification.Name.init("didReceiveRemoteNotification"),
                                        object: completionHandler, userInfo: userInfo)
    }
`;
    const idx = s.lastIndexOf("}");
    return s.slice(0, idx) + hooks + s.slice(idx);
  }, "AppDelegate push hooks");

  const entitlements = path.join(appDir, "App.entitlements");
  if (!fs.existsSync(entitlements)) {
    fs.writeFileSync(entitlements, `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>aps-environment</key>
\t<string>development</string>
\t<key>com.apple.developer.associated-domains</key>
\t<array>
\t\t<string>applinks:${DOMAIN}</string>
\t\t<string>webcredentials:${DOMAIN}</string>
\t</array>
</dict>
</plist>
`);
    done("App.entitlements (Push + Associated Domains)");
  } else skip("App.entitlements");

  const pbx = "ios/App/App.xcodeproj/project.pbxproj";
  patchFile(pbx, "CODE_SIGN_ENTITLEMENTS", (s) =>
    s.replace(/(\n(\s*)INFOPLIST_FILE = App\/Info\.plist;)/g, "\n$2CODE_SIGN_ENTITLEMENTS = App/App.entitlements;$1"),
    "Xcode build setting CODE_SIGN_ENTITLEMENTS");

  if (!fs.existsSync(path.join(appDir, "GoogleService-Info.plist"))) {
    console.log("  ! Add GoogleService-Info.plist to ios/App/App (drag it into Xcode > App target) to enable push.");
  }
}

// ------------------------------------------------------------- Android
function configureAndroid() {
  const manifest = "android/app/src/main/AndroidManifest.xml";
  if (!fs.existsSync(manifest)) throw new Error("android/ not found - run `npx cap add android` first");

  const permissions = [
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.CAMERA",
    "android.permission.POST_NOTIFICATIONS",
  ];
  for (const perm of permissions) {
    patchFile(manifest, `android:name="${perm}"`,
      (s) => s.replace(/(\s*)<\/manifest>/, `$1    <uses-permission android:name="${perm}" />$1</manifest>`),
      `permission ${perm.split(".").pop()}`);
  }
  patchFile(manifest, 'android:name="android.hardware.camera"',
    (s) => s.replace(/(\s*)<\/manifest>/, `$1    <uses-feature android:name="android.hardware.camera" android:required="false" />$1</manifest>`),
    "camera feature optional");

  patchFile(manifest, `android:host="${DOMAIN}"`, (s) => s.replace(
    /(<activity[\s\S]*?android:name="\.MainActivity"[\s\S]*?>)/,
    `$1
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="https" android:host="${DOMAIN}" />
            </intent-filter>`), `verified App Link https://${DOMAIN}`);

  const meta = [
    ["firebase_messaging_auto_init_enabled", 'android:value="false"'],
    ["firebase_analytics_collection_enabled", 'android:value="false"'],
    ["com.google.firebase.messaging.default_notification_icon", 'android:resource="@drawable/ic_stat_maku"'],
    ["com.google.firebase.messaging.default_notification_color", 'android:resource="@color/maku_brand"'],
  ];
  for (const [name, attr] of meta) {
    patchFile(manifest, `android:name="${name}"`,
      (s) => s.replace(/(\s*)<\/application>/, `$1    <meta-data android:name="${name}" ${attr} />$1</application>`),
      `meta-data ${name}`);
  }

  const res = "android/app/src/main/res";
  fs.mkdirSync(path.join(res, "drawable"), { recursive: true });
  fs.mkdirSync(path.join(res, "values"), { recursive: true });
  const icon = path.join(res, "drawable", "ic_stat_maku.xml");
  if (!fs.existsSync(icon)) {
    fs.writeFileSync(icon, `<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M12,1L3,4.5V11c0,5.55 3.84,10.74 9,12 5.16,-1.26 9,-6.45 9,-12V4.5L12,1zM16.5,17h-2v-6.2l-2.5,4.2 -2.5,-4.2V17h-2V7h2l2.5,4.4L14.5,7h2v10z" />
</vector>
`);
    done("notification icon ic_stat_maku");
  } else skip("notification icon");
  const colors = path.join(res, "values", "maku_colors.xml");
  if (!fs.existsSync(colors)) {
    fs.writeFileSync(colors, `<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="maku_brand">#0C5C63</color>\n</resources>\n`);
    done("brand colour resource");
  } else skip("brand colour resource");

  const vars = "android/variables.gradle";
  if (fs.existsSync(vars)) {
    const v = fs.readFileSync(vars, "utf8");
    const target = /targetSdkVersion\s*=\s*(\d+)/.exec(v);
    if (target && Number(target[1]) < 36) {
      fs.writeFileSync(vars, v.replace(/targetSdkVersion\s*=\s*\d+/, "targetSdkVersion = 36")
                              .replace(/compileSdkVersion\s*=\s*\d+/, "compileSdkVersion = 36"));
      done("targetSdk/compileSdk raised to 36 (Google Play requirement)");
    } else skip(`targetSdkVersion ${target ? target[1] : "?"}`);
  }
  if (!fs.existsSync("android/app/google-services.json")) {
    console.log("  ! Copy google-services.json from Firebase into android/app/ to enable push.");
  }
}

console.log(`Configuring ${platform} for ${DOMAIN}`);
if (platform === "ios") configureIos();
else if (platform === "android") configureAndroid();
else { console.error("usage: node scripts/configure-native.mjs ios|android"); process.exit(1); }
