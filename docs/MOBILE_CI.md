# Automatic store uploads (Fastlane + GitHub Actions)

Every push to `main` that changes `mobile/` builds the MAKU app and uploads it to:

| Store | Destination | Runner |
|---|---|---|
| Google Play | **Internal testing** track | `ubuntu-24.04` |
| Apple | **TestFlight** | `macos-26` (Xcode 26) |

Changes to the Python web app do **not** trigger a store build. The app loads `https://maku.ae`, so web changes reach phones as soon as the server is updated. To build anyway, open **Actions → Deploy mobile apps → Run workflow**.

Until a store's secrets are added, its job is **skipped with a warning** instead of failing. If only some of the secrets are set, the job **fails** and lists the missing ones.

## How it works

| File | Role |
|---|---|
| `.github/workflows/deploy.yml` | Generates `android/` and `ios/` (`npm run add:*`), restores secrets into temporary files, then runs Fastlane |
| `mobile/fastlane/Fastfile` | `android internal`, `ios signing` (one-time) and `ios beta` lanes |
| `mobile/fastlane/ios_project.rb` | Prepares the generated Xcode project for CI: writes a shared scheme, adds `GoogleService-Info.plist` to the build, sets push to production |
| `mobile/fastlane/Appfile`, `Matchfile` | App identifiers, plus where iOS certificates are stored |
| `mobile/Gemfile` | Pins Fastlane 2.241.x |

- **Version name**: `"version"` in `mobile/package.json`. Change it there for a new store version, such as 1.1.0.
- **Build number / version code**: read from the stores on every run as *highest already uploaded + 1*, so it never collides.
- **iOS signing**: [fastlane match](https://docs.fastlane.tools/actions/match/). The distribution certificate and profile are stored encrypted in a second, **private** GitHub repository.
- **Android signing**: your upload keystore, stored as a secret and decoded only for the build.

The `Menga1/maku-platform` repository is public, so GitHub Actions minutes (macOS included) are free. If you make it private, macOS minutes count 10× against your plan. Secrets are never shown in logs or given to pull requests from forks.

## Add the secrets

Go to **GitHub → `maku-platform` → Settings → Secrets and variables → Actions → New repository secret**. The names must match exactly.

### Google Play: 5 secrets, plus 1 optional

**1. Create the upload key** on your computer, once. `keytool` comes with Android Studio and with any Java install.

```bash
keytool -genkeypair -v -keystore maku-upload.jks -alias maku-upload \
        -keyalg RSA -keysize 4096 -validity 10000
```

Store `maku-upload.jks` and its password in your password manager. If you lose it, Google can reset the upload key, but that takes a few days.

**2. Turn the keystore into text:**
- **Mac:** `base64 -i maku-upload.jks | pbcopy`
- **Windows (PowerShell):** `[Convert]::ToBase64String([IO.File]::ReadAllBytes("maku-upload.jks")) | Set-Clipboard`

**3. Create the Play API account:**
1. In **console.cloud.google.com**, create a project, then open **APIs & Services → Library** and enable the **Google Play Android Developer API**.
2. Open **IAM & Admin → Service accounts → Create**, name it `maku-ci`, and skip the roles step. Then go to **Keys → Add key → JSON** and download the file.
3. In **Play Console → Users and permissions → Invite new users**, paste the service account's e-mail. Under **App permissions**, add MAKU with **Release apps to testing tracks** and **View app information**, then **Invite**.

| Secret | Value |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | the text from step 2 |
| `ANDROID_KEYSTORE_PASSWORD` | the keystore password |
| `ANDROID_KEY_ALIAS` | `maku-upload` |
| `ANDROID_KEY_PASSWORD` | the same password (keytool uses one password for both) |
| `PLAY_SERVICE_ACCOUNT_JSON` | the whole JSON file from step 3, pasted as-is |
| `GOOGLE_SERVICES_JSON` *(optional)* | the whole `google-services.json` from Firebase. Without it, push alerts are off |

**4. First upload, by hand (Google requires this once):**
1. In **Play Console**, go to **Create app** and choose **MAKU**, **App**, **Free**.
2. In GitHub, open **Actions → Deploy mobile apps → Run workflow**, tick **Android one-time: build the signed AAB only**, set Platform to `android`, and click **Run**.
3. When it finishes, open the run and download **maku-android-aab** under **Artifacts**.
4. In **Play Console → Testing → Internal testing → Create new release**, upload that `.aab`, add testers, then **Save → Review → Start rollout**.

From then on, every push uploads automatically. While the app has never been rolled out (it's still a *draft app*), Google only accepts draft releases. If you see *"Only releases with status draft may be created on draft app"*, go to **Settings → Secrets and variables → Actions → Variables** and add `PLAY_RELEASE_STATUS` = `draft`. Delete the variable after your first rollout.

### Apple: 7 secrets, plus 1 optional

**1. Register the app (once):**
1. At **developer.apple.com → Certificates, IDs & Profiles → Identifiers → +**, choose **App IDs → App**, set Bundle ID **Explicit** to `ae.maku.app`, and tick **Push Notifications** and **Associated Domains**. Then **Register**.
2. At **appstoreconnect.apple.com → Apps → + → New App**, choose iOS, name **MAKU**, bundle ID `ae.maku.app`, and SKU `maku-ios`.

**2. Create an API key:** in **App Store Connect → Users and Access → Integrations → App Store Connect API → Team Keys → +**, name it `maku-ci`, give it the **Admin** role (needed to create the certificate), then **Generate**. Download the `.p8` file; Apple only lets you download it once. Note the **Key ID** and the **Issuer ID** shown above the table.

**3. Create the certificate store:** a new **private**, empty GitHub repository named `maku-certificates`. Then create a token at **github.com → Settings → Developer settings → Fine-grained tokens**: Repository access = only `maku-certificates`, Permissions → **Contents: Read and write**. Turn `Menga1:<token>` into text:
- **Mac:** `printf 'Menga1:PASTE_TOKEN' | base64`
- **Windows (PowerShell):** `[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("Menga1:PASTE_TOKEN"))`

| Secret | Value |
|---|---|
| `ASC_KEY_ID` | Key ID from step 2 |
| `ASC_ISSUER_ID` | Issuer ID from step 2 |
| `ASC_PRIVATE_KEY` | the full `.p8` file contents, including the `-----BEGIN/END PRIVATE KEY-----` lines |
| `APPLE_TEAM_ID` | developer.apple.com → **Membership details → Team ID** (10 characters) |
| `MATCH_GIT_URL` | `https://github.com/Menga1/maku-certificates.git` |
| `MATCH_PASSWORD` | a long passphrase you invent. It encrypts the certificates, so keep it in your password manager |
| `MATCH_GIT_BASIC_AUTHORIZATION` | the text from step 3 |
| `GOOGLE_SERVICE_INFO_PLIST` *(optional)* | the whole `GoogleService-Info.plist` from Firebase. Without it, push alerts are off |

**4. First run:** in **Actions → Deploy mobile apps → Run workflow**, tick **iOS one-time setup**, set Platform to `ios`, and click **Run**. This turns on the App ID capabilities, creates the distribution certificate and profile in `maku-certificates`, then builds and uploads to TestFlight. Later runs only read the certificates.

**5. Testers:** in **App Store Connect → MAKU → TestFlight → Internal Testing → +**, create a group, turn on **automatic distribution**, and add yourself. Each new build reaches the group once Apple finishes processing it, which takes about 10–30 minutes.

## Day to day

| You want to | Do this |
|---|---|
| Ship a new test build | Push a change under `mobile/`, or use **Run workflow** |
| Change the version shown in the stores | Edit `"version"` in `mobile/package.json` |
| Build one store only | **Run workflow** → Platform `android` or `ios` |
| Move a build to production | Promote it by hand in Play Console or App Store Connect. Production releases are never automatic |

## Troubleshooting

| Message | Fix |
|---|---|
| `Missing GitHub secret(s): …` | Add the named secrets. Names are case-sensitive |
| `Package not found: ae.maku.app` | The first manual upload hasn't happened yet (Google Play step 4) |
| `Only releases with status draft may be created on draft app` | Set the `PLAY_RELEASE_STATUS` variable to `draft` until the first rollout |
| `The caller does not have permission` (Play) | The service account wasn't invited in Play Console, or is missing **Release apps to testing tracks** |
| `Could not find app with bundle identifier` (Apple) | Create the app record in App Store Connect (Apple step 1) |
| `No matching provisioning profiles found` / `Couldn't decrypt the repo` | Run the workflow once with **iOS one-time setup** ticked; check that `MATCH_PASSWORD` is unchanged |
| `Provisioning profile doesn't include the … entitlement` | Run **iOS one-time setup** again. It regenerates the profile with Push and Associated Domains |
