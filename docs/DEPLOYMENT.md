# MAKU — Deployment runbook

From an empty cloud account to a live `https://maku.ae` and signed iOS and Android builds. Every command can be copied as-is. Replace only the values shown in `UPPER_CASE` or `[brackets]`.

| Step | What you do | Time |
|---|---|---|
| 1 | Create the free Oracle Cloud server and point the domain at it | 45 min |
| 2 | Install Docker and start MAKU | 15 min |
| 3 | Create the administrator and the App Review account | 5 min |
| 4 | (Optional) Move old data from Streamlit Cloud | 5 min |
| 5 | Firebase (push alerts) | 20 min |
| 6 | Build the Android app | 30 min |
| 7 | Build the iOS app (needs a Mac) | 40 min |
| 8 | Fill in the store verification files | 10 min |
| 9 | Day-2 operations | — |

---

## 0. No-server option: Streamlit Community Cloud + Neon (US$0 per month)

Use this while no server is available (for example when Oracle's free ARM
capacity is full). The app stays on Streamlit Community Cloud; the data lives in
a free Neon PostgreSQL database with the same row-level security as the Docker
stack.

**Limits.**
- The address is `<name>.streamlit.app`; Streamlit's free plan has no custom domain.
- The app sleeps when idle and wakes in a few seconds.
- Neon's free plan is 1 GB per project, 100 compute-hours a month, and pauses after 5 minutes idle.
- Data is stored in the Neon region you choose (outside the UAE). Say so in the privacy policy.

**Neon**
1. On neon.com, sign up (Google sign-in is fine) and create a project named `maku`. Choose the region closest to the app: Streamlit Community Cloud runs in the US.
2. Open **Connect**, turn **Connection pooling OFF** and copy the connection string. It looks like `postgresql://neondb_owner:...@ep-....neon.tech/neondb?sslmode=require`. This is the **owner** string.

**GitHub** (repository → Settings → Secrets and variables → Actions → New repository secret)
- `MIGRATION_DATABASE_URL`: the owner string, unchanged.
- `DATABASE_URL`: the same string with the user changed to `maku_app` and the password changed to a new one you make up (letters and digits only, 24 or more characters): `postgresql://maku_app:NEWPASSWORD@ep-....neon.tech/neondb?sslmode=require`.

Then **Actions → Database migrate → Run workflow**. A green run means:
- the `maku_app` role exists;
- all migrations, including row-level security, are applied;
- the app role was verified not to bypass RLS.

**Streamlit Community Cloud** (app → Settings → Secrets). Add at the top level, above `[auth.users]`:

```toml
MAKU_ENV = "production"
DATABASE_URL = "postgresql://maku_app:NEWPASSWORD@ep-....neon.tech/neondb?sslmode=require"
```

Save; the app restarts. Re-run the workflow after every release that adds a migration.
Never put the owner string in Streamlit.

## 1. Server and domain: Oracle Cloud Always Free (US$0 per month)

The free server has 2 ARM CPU cores, 12 GB of memory and up to 200 GB of disk. That is enough for MAKU, PostgreSQL, Caddy and backups. Every MAKU component has an ARM (aarch64) build, so steps 2–9 are unchanged.

### 1.1 Create the account and choose the home region (permanent)

1. Go to <https://signup.cloud.oracle.com>, enter your country (**United Arab Emirates**), name and email, then verify the email.
2. **Home Region**: choose **UAE East (Dubai)** or **UAE Central (Abu Dhabi)**. This **cannot be changed later**, and free servers can only be created in the home region. Dubai or Abu Dhabi keeps the data in the UAE.
3. Enter the address and a credit card for identity verification. Oracle places a small temporary authorisation and does not charge you for Always Free resources. Accept the terms and **Start my free trial**. Account set-up takes 5–30 minutes; you get a "Your account is ready" email.

### 1.2 Upgrade to Pay As You Go (still US$0), and set a budget alarm

Free-only accounts can have idle servers reclaimed (Oracle reclaims an Always Free server that sits under 20% CPU, network and memory use for 7 days). A quiet MAKU deployment could look idle, so upgrade:

1. Console (top-right profile icon) → **Billing & Cost Management → Upgrade and Manage Payment** → **Upgrade to Pay As You Go** → confirm the card → **Upgrade**. Always Free resources stay free after the upgrade.
2. Safety net against accidental charges: **Billing & Cost Management → Budgets → Create Budget**. Name `maku-zero`, Target **Compartment**: your root compartment, Schedule **Monthly**, Amount **1** (US$), Alert rule threshold **1 %** of budget, your email → **Create**. If anything outside the free limits is ever created, you get an email straight away.

### 1.3 Create the server

1. Console menu ☰ → **Compute → Instances → Create instance**.
2. **Name**: `maku-prod`. **Placement**: keep the availability domain shown (the UAE regions have one).
3. **Image and shape → Change image → Ubuntu** → tick **Canonical Ubuntu 24.04** (the standard, not "Minimal", image; check the build says **aarch64**) → **Select image**.
4. **Change shape → Virtual machine → Ampere** → tick **VM.Standard.A1.Flex** → set **Number of OCPUs = 2** and **Amount of memory = 12 GB** → **Select shape**. The page should show the *Always Free-eligible* label.
5. **Networking**: **Create new virtual cloud network** and **Create new public subnet** (keep the suggested names). Make sure **Automatically assign public IPv4 address** is **on**.
6. **Add SSH keys**: **Generate a key pair for me** → **Download private key** (and **Download public key**). Save the `.key` file; it cannot be downloaded again.
7. **Boot volume**: tick **Specify a custom boot volume size** → **100 GB**. The free limit is 200 GB in total; 100 GB leaves room for backups.
8. **Create**. After 1–2 minutes the instance shows **Running**. Copy the **Public IP address** from the instance page.

**"Out of capacity for shape VM.Standard.A1.Flex"**: the free ARM servers in that region are temporarily all in use. Nothing is wrong with your settings. Wait and press **Create** again (early morning UAE time often works), or try 1 OCPU / 6 GB first and resize later from **Edit → Edit shape**.

The public IP stays the same through stops and restarts; it only changes if you terminate the instance.

### 1.4 Open ports 80 and 443 (two places, both required)

**A. Oracle's network firewall (security list)**

1. Instance page → **Primary VNIC** section → click the **Subnet** link → **Security** (or *Security Lists*) → **Default Security List for vcn-…** → **Security rules** (or *Ingress Rules*) → **Add Ingress Rules**.
2. Add three rules (use **+ Another Ingress Rule** between them):

| Source Type | Source CIDR | IP Protocol | Destination Port Range |
| --- | --- | --- | --- |
| CIDR | 0.0.0.0/0 | TCP | 80 |
| CIDR | 0.0.0.0/0 | TCP | 443 |
| CIDR | 0.0.0.0/0 | UDP | 443 |

3. **Add Ingress Rules**. Port 22 (SSH) is already open by default.

**B. The server's own firewall** (Oracle's Ubuntu images block everything except SSH with iptables, not ufw). From your laptop:

```bash
chmod 600 ~/Downloads/ssh-key-*.key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@PUBLIC_IP
```

Then on the server:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save
sudo iptables -L INPUT -n --line-numbers | head -12     # the ACCEPT rules for 80/443 must appear ABOVE the final REJECT line
```

### 1.5 Point the domain at the server

At your registrar's DNS settings for `maku.ae`:

- `A` record, host `@`, value = the instance's public IP, TTL 300
- `A` record, host `www`, value = the same IP, TTL 300

Wait until `nslookup maku.ae` returns that IP (usually 5–30 minutes), then continue with step 2.

### 1.6 Alternative: AWS (paid, about US$45 per month)

Choose AWS when you have paying customers and want an uptime guarantee. Moving later takes one backup and restore (step 9).

1. AWS console → **EC2** → region selector (top right) → **Middle East (UAE) me-central-1**.
2. **Launch instance**:
   - Name: `maku-prod`
   - AMI: **Ubuntu Server 24.04 LTS (64-bit x86)**
   - Instance type: **t3.medium** (2 vCPU, 4 GB RAM)
   - Key pair: **Create new key pair** → name `maku`, type RSA, `.pem` → download it.
   - Network settings → **Edit** → Security group rules:
     - SSH, TCP 22, Source **My IP**
     - HTTP, TCP 80, Source 0.0.0.0/0
     - HTTPS, TCP 443, Source 0.0.0.0/0
     - Custom UDP 443, Source 0.0.0.0/0 (HTTP/3)
   - Storage: **30 GiB gp3**, Encrypted = **Yes**
   - **Launch instance**.
3. EC2 → **Elastic IPs** → **Allocate Elastic IP address** → **Allocate** → **Actions → Associate** → choose `maku-prod`. Note the IP.
4. At your domain registrar's DNS settings for `maku.ae`, create:
   - `A` record, host `@`, value = the Elastic IP, TTL 300
   - `A` record, host `www`, value = the Elastic IP, TTL 300
5. Wait until `nslookup maku.ae` returns the Elastic IP (usually 5–30 minutes).

## 2. Install Docker and start MAKU

```bash
# from your laptop - set these two once per terminal
KEY=~/Downloads/ssh-key-2026-10-14.key     # Oracle key file name (AWS: ~/Downloads/maku.pem)
SERVER_IP=203.0.113.10                      # your server's public IP from step 1
chmod 600 $KEY
scp -i $KEY MAKU_production.zip ubuntu@$SERVER_IP:~
ssh -i $KEY ubuntu@$SERVER_IP

# on the server
sudo apt-get update && sudo apt-get install -y unzip
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && newgrp docker
unzip MAKU_production.zip && cd maku

cp .env.example .env
openssl rand -hex 24          # copy the output into POSTGRES_PASSWORD
openssl rand -hex 24          # a second, different one into MAKU_APP_DB_PASSWORD
nano .env                     # set MAKU_DOMAIN, ACME_EMAIL, POSTGRES_PASSWORD, MAKU_APP_DB_PASSWORD, MAKU_AI_API_KEY (optional)
```

Generate the first administrator's credential (Argon2id), then paste it into `.env`. The password needs at least 12 characters mixing three of lowercase, uppercase, digits and symbols; production refuses weaker ones at sign-in:

```bash
docker compose build app
docker compose run --rm --no-deps app python manage_users.py hash
#   type the admin password twice; copy the line starting with  argon2:$argon2id$...
nano .env
#   MAKU_AUTH_USERS='{"first.admin": "argon2:$argon2id$...PASTE..."}'
```

Start everything:

```bash
docker compose up -d --build
docker compose ps                        # db, app, caddy, backup -> "running"/"healthy"
docker compose logs -f caddy             # wait for "certificate obtained successfully"
curl -I https://maku.ae/healthz          # HTTP/2 200
```

Open `https://maku.ae`, sign in as `first.admin`, and make your privacy choices.

**Production database rules.** The image runs with `MAKU_ENV=production`:

- MAKU only uses PostgreSQL. If `DATABASE_URL` is missing or not PostgreSQL, the app container stops at start-up with `CRITICAL ... Refusing to fall back to a local SQLite file` in `docker compose logs app`.
- At every start, `scripts/init_db.py` applies the versioned migrations in `migrations/` (`alembic upgrade head`). The app refuses to use a database that is not at the expected revision.
- **Two database roles.** Migrations run as the table owner (`MIGRATION_DATABASE_URL`, the `POSTGRES_USER`). The app connects as `maku_app` (`DATABASE_URL`), which `init_db.py` creates and grants on first start. PostgreSQL row-level security (migration 0003) applies to `maku_app` only, so the app refuses to start if `DATABASE_URL` is the owner, a superuser or a `BYPASSRLS` role. `maku_app` cannot change or delete the audit log.
- Managed database (RDS, Azure, Supabase, Neon): create a login role for the app yourself if the owner may not create roles, then set both URLs in `.env`.
- If PostgreSQL goes down while running, every page shows **CRITICAL DATABASE ERROR** and nothing is saved anywhere else; the container turns *unhealthy* and the log shows a CRITICAL line. Pages work again automatically within seconds of the database coming back.

## 3. Accounts

Admins create staff accounts in the app under **Users (admin)**, or from the server:

```bash
docker compose exec app python manage_users.py create site.supervisor --role supervisor
docker compose exec app python manage_users.py list
```

**Every user must be a member of an organization** before they can use the module pages; each customer company is one organization, and nobody sees another organization's assessments, alerts or push notifications. Do this in **Users (admin) → Organizations and members**, or:

```bash
docker compose exec app python manage_users.py org-create "ACME Construction"
docker compose exec app python manage_users.py member-add site.supervisor "ACME Construction" --role supervisor
docker compose exec app python manage_users.py member-list
```

| Organization role | Can |
|---|---|
| `viewer` | See the organization's results; assessments are calculated but not saved |
| `supervisor` | Run and save assessments, import logs, receive stop-work alerts |
| `org_admin` | Everything above, plus add/remove `viewer` and `supervisor` members of that organization |

Platform administrators (`--role admin`, or the accounts in `MAKU_AUTH_USERS`) see every organization and create organizations. To receive an organization's stop-work alerts on a phone, an administrator adds themselves as a member of it.

**Create two reviewer accounts before submitting to the stores.** Reviewers test account deletion, and a deleted account can't be reused for the next review round.

```bash
docker compose exec app python manage_users.py create appreview1 --role supervisor
docker compose exec app python manage_users.py create appreview2 --role supervisor
```

Sign in once as each reviewer account and choose **AI briefings = On, Location = On**. The reviewer then sees every feature without a privacy prompt in the way.

## 4. Move data from the old Streamlit Cloud app (optional)

Download `maku_site_data.db` from the old deployment if you still have it, then:

```bash
scp -i $KEY maku_site_data.db ubuntu@$SERVER_IP:~/maku/
docker compose cp maku_site_data.db app:/app/data/import.db
docker compose exec app python scripts/migrate_sqlite_to_postgres.py --sqlite /app/data/import.db --dry-run
docker compose exec app python scripts/migrate_sqlite_to_postgres.py --sqlite /app/data/import.db
# ends with: Audit-log hash chain on PostgreSQL: VALID ... Migration complete.
```

## 5. Firebase (stop-work push alerts)

1. <https://console.firebase.google.com> → **Add project** → name `MAKU` → turn Google Analytics **off** → **Create project**.
2. Project overview → **Add app → Android** → package name `ae.maku.app` → **Register app** → download **google-services.json**. Skip the remaining SDK steps.
3. **Add app → iOS** → bundle ID `ae.maku.app` → download **GoogleService-Info.plist**. Skip the remaining SDK steps.
4. Apple side: <https://developer.apple.com/account> → **Certificates, IDs & Profiles → Keys → +** → name `MAKU APNs`, tick **Apple Push Notifications service (APNs)** → **Continue → Register → Download** the `.p8` file. Note the **Key ID** and your **Team ID** (top right).
5. Firebase → ⚙ **Project settings → Cloud Messaging** → *Apple app configuration* → **APNs Authentication Key → Upload** → the `.p8`, Key ID and Team ID.
6. Firebase → ⚙ **Project settings → Service accounts → Generate new private key** → save it on the server as `~/maku/secrets/firebase-service-account.json`, then:

```bash
chmod 600 secrets/firebase-service-account.json
docker compose up -d app        # push is enabled automatically when the file exists
```

## 6. Android build (any Windows/macOS/Linux computer)

> **No computer build needed:** GitHub Actions can build and upload both apps for you (no Mac required). See [`MOBILE_CI.md`](MOBILE_CI.md). Sections 6 and 7 are the manual alternative.

Install **Node.js 22 LTS** and **Android Studio Otter (2025.2.1) or newer**.

```bash
cd maku/mobile
npm install
npm run assets                   # generates icons/splash from mobile/assets/
npm run add:android              # creates android/ and applies MAKU's native settings
cp ~/Downloads/google-services.json android/app/
npm run sync
npm run open:android
```

In Android Studio:

1. Wait for **Gradle sync** to finish.
2. **Build → Generate Signed App Bundle or APK → Android App Bundle → Next**.
3. **Key store path → Create new…** → save as `maku-upload.jks` **outside the project folder**, set a strong password, alias `upload`, validity 25 years, fill the certificate fields → **OK**.
4. **Build variant: release → Create**. The file is `android/app/release/app-release.aab`.
5. **Back up `maku-upload.jks` and its passwords** in a password manager. Without them you cannot publish updates (Play App Signing can reset an upload key, but it takes days).

## 7. iOS build (Mac with Xcode 26 or newer)

```bash
cd maku/mobile
npm install
npm run assets
npm run add:ios
cp ~/Downloads/GoogleService-Info.plist ios/App/App/
npm run sync
npm run open:ios
```

In Xcode:

1. Left panel: drag **GoogleService-Info.plist** from Finder onto the **App** folder → tick **Copy items if needed** and target **App** → **Finish**.
2. Select the **App** project → **App** target → **Signing & Capabilities**:
   - **Team**: your Apple Developer team; **Automatically manage signing** on.
   - Bundle Identifier: `ae.maku.app`.
   - Confirm **Push Notifications**, **Associated Domains** (`applinks:maku.ae`, `webcredentials:maku.ae`) and **Background Modes → Remote notifications** are listed. They come from `App.entitlements`. If one is missing, add it with **+ Capability**.
3. **General** → Version `1.0.0`, Build `1`.
4. Device selector → **Any iOS Device (arm64)** → **Product → Archive**.
5. Organizer → **Distribute App → App Store Connect → Upload**.

## 8. Store verification files

Edit on the server, then run `docker compose restart caddy`.

- `deploy/well-known/apple-app-site-association`: replace **both** `TEAMID1234` with your 10-character Apple Team ID.
- `deploy/well-known/assetlinks.json`: after your first upload to Google Play, copy the SHA-256 from **Play Console → Test and release → App integrity → Play app signing → Settings → App signing key certificate**.

Check them:

```bash
curl -s https://maku.ae/.well-known/apple-app-site-association | head
curl -s https://maku.ae/.well-known/assetlinks.json | head
```

Then run `cd mobile && npm run check`. It should show no warnings.

Also fill in the `[BRACKETED]` values in `deploy/site/privacy.html` and `deploy/site/delete-account.html` (company legal name, address, hosting provider, audit-log retention period). Have counsel review them.

## 9. Day-2 operations

| Task | Command |
|---|---|
| Update after a code change | `git pull` (or upload a new zip) → `docker compose up -d --build` |
| Logs | `docker compose logs -f app` |
| Backups | nightly in `~/maku/backups/` (14 days). Copy them off the server, e.g. `aws s3 sync backups s3://YOUR-BUCKET/maku-backups` in a cron job |
| Restore a backup | `gunzip -c backups/maku-YYYYmmdd-HHMM.sql.gz \| docker compose exec -T db psql -U maku -d maku` |
| Erasure request by email | `docker compose exec app python manage_users.py delete USERNAME` |
| Run the test suite | `docker compose exec app python -m pytest -q test_app.py tests/` |
| Check every account's password storage | `docker compose exec app python scripts/audit_credentials.py` (prints no secrets; exit 1 if any account is unusable) |
| Database migration status | `docker compose exec app alembic current` (expected: the latest revision in `migrations/versions/`) |
| Why is the app unhealthy? | `docker inspect --format '{{json .State.Health.Log}}' $(docker compose ps -q app)` |
| Training/demo mode | set `MAKU_DEMO_MODE=1` in `.env` → `docker compose up -d app`. Red **SIMULATED DATA** banners appear. Never leave it on in production |

## Known limitations

- **Sessions:** Streamlit keeps the login in the browser session. A full page reload, or a deep link while the app is closed, asks the user to sign in again. Inside the mobile shell the session survives brief network drops.
- **Phone sidebar:** on narrow screens the Streamlit sidebar stays open after choosing a page. Tap « to close it.
- **iOS uploads:** inside the iOS shell, file *uploads* (the CSV log merge) can be blocked by WebKit's cross-site cookie rules. Downloads use the native **Share PDF** button instead. Everything else is unaffected.
- **Scaling:** a single `app` container serves about 50–100 concurrent users. For more, run several app containers behind sticky sessions (Streamlit is WebSocket-stateful).
