# Hostinger VPS pe deploy — step by step

Ubuntu 22.04 / 24.04 VPS ke liye. **Nginx + Gunicorn + PostgreSQL + systemd.**

Har command copy-paste karne layak hai. Jahan `<...>` likha hai wahan apni value daalo.

---

## Pehle 3 jawab

**Gunicorn use karna hai ya nahi?** — **Haan, zaroori hai.**
`manage.py runserver` sirf development ke liye hai — single-threaded, insecure, aur Django khud kehta hai isse production mein mat chalao. Gunicorn already `requirements.txt` mein hai (line 11).

**FileZilla se ya GitHub se?** — **GitHub se clone karo.**
FileZilla se `venv/` aur `__pycache__` bhi chale jaate hain (450 MB+ bekaar), aur update karne ke liye har baar dobara upload karna padega. Git se `git pull` = 2 second mein update.

**Konsa port?** — VPS pe **80 (HTTP)** aur **443 (HTTPS)** hi public hone chahiye.
Gunicorn ko public port pe **mat** chalao — woh andar se Nginx se baat karega (Unix socket, koi port hi nahi). PostgreSQL bhi `localhost` pe hi rahega. Step 2 mein check karna sikhaya hai.

---

## Step 0 — Local pe cleanup (deploy se pehle)

Yeh cheezein server pe **kabhi nahi jaani chahiye**:

| Cheez | Kyun |
|---|---|
| `.env` | Isme aapke asli passwords/tokens hain. Server pe **naya** banega (Step 5) |
| `venv/` | Linux pe naya banega — Windows ka venv chalega hi nahi |
| `data/fusehealth.db`, `django_internal.db` | SQLite. Server Postgres use karega |
| `__pycache__/`, `.pytest_cache/` | Auto-generate hote hain |
| `logs/` | Server pe apni jagah banegi |
| `staticfiles/` | Server pe `collectstatic` se banega |

Achhi baat: yeh **sab already `.gitignore` mein hain**, toh `git clone` mein aayenge hi nahi. Confirm karne ke liye:

```bash
git status --porcelain     # kuch bhi secret dikhe toh commit mat karna
git ls-files | grep -iE "\.env$|\.db$|venv/"    # khaali aana chahiye
```

Agar khaali aaya — aap ready ho.

---

## Step 1 — VPS se connect karo

Hostinger panel → VPS → **SSH details**. Phir local terminal se:

```bash
ssh root@<VPS_IP>
```

Pehla kaam, system update:

```bash
apt update && apt upgrade -y
```

---

## Step 2 — Ports check karo (aapne yahi poocha tha)

**Abhi kya khula hai dekho:**

```bash
ss -tulpn | grep LISTEN
```

Yeh dikhayega konsa program konse port pe hai. Aam taur pe sirf `22` (SSH) hoga.

**Firewall ka status:**

```bash
ufw status verbose
```

**Jo chahiye woh kholo — sirf teen:**

```bash
ufw allow 22/tcp      # SSH — yeh band mat karna warna aap hi lock ho jaoge
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw enable
ufw status numbered
```

> ⚠️ **PostgreSQL ka 5432 kabhi bahar mat kholo.** Woh sirf `localhost` pe sunega. Internet pe khula Postgres ghante bhar mein attack ho jaata hai.
>
> ⚠️ **Gunicorn ka koi port nahi khulega** — hum Unix socket use karenge, jo file hai, port nahi. Isse woh bahar se pahunch hi nahi sakta.

Port khaali hai ya nahi check karna ho:

```bash
ss -tulpn | grep :8000        # kuch na aaye = khaali hai
```

---

## Step 3 — Zaroori software install karo

```bash
apt install -y python3.12 python3.12-venv python3-pip \
               postgresql postgresql-contrib \
               nginx git curl
```

Versions confirm karo:

```bash
python3.12 --version
psql --version
nginx -v
```

---

## Step 4 — PostgreSQL setup

```bash
sudo -u postgres psql
```

Ab Postgres ke andar (apna asli strong password daalo):

```sql
CREATE DATABASE limitlesshealth;
CREATE USER fuseuser WITH PASSWORD '<STRONG_PASSWORD_YAHAN>';
ALTER ROLE fuseuser SET client_encoding TO 'utf8';
ALTER ROLE fuseuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE fuseuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE limitlesshealth TO fuseuser;
\c limitlesshealth
GRANT ALL ON SCHEMA public TO fuseuser;
\q
```

> **Note:** aakhri do lines (`\c` aur `GRANT ON SCHEMA`) PostgreSQL 15+ ke liye zaroori hain. Inke bina `migrate` "permission denied for schema public" dega.

Test karo ki login ho raha hai:

```bash
psql -h localhost -U fuseuser -d limitlesshealth -c "SELECT version();"
```

---

## Step 5 — Code clone + venv

```bash
mkdir -p /var/www && cd /var/www
git clone https://github.com/<aapka-username>/<repo-name>.git fusehealth
cd fusehealth

python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 6 — `.env` banao (server pe naya)

```bash
nano /var/www/fusehealth/.env
```

Yeh daalo — **`<...>` apni values se badlo**:

```ini
# --- Django ---
DJANGO_SECRET_KEY=<niche wale command se generate karo>
DJANGO_ALLOWED_HOSTS=limitless.vashstudios.cloud,<VPS_IP>
DJANGO_CSRF_TRUSTED_ORIGINS=https://limitless.vashstudios.cloud

# --- PostgreSQL (POSTGRES_DB hi master switch hai) ---
POSTGRES_DB=limitlesshealth
POSTGRES_USER=fuseuser
POSTGRES_PASSWORD=<Step 4 wala password>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# --- Logs: project folder ke BAHAR rakhna ---
FUSEHEALTH_LOG_DIR=/var/log/fusehealth

# --- Google ---
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GOOGLE_API_KEY=

# --- DataForSEO ---
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=

# --- OpenAI ---
OPENAI_API_KEY=

# --- Email ---
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=
FRONTEND_URL=https://limitless.vashstudios.cloud

# --- Google Ads (Standard Access milne ke baad) ---
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
```

SECRET_KEY generate karne ke liye:

```bash
cd /var/www/fusehealth && source venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Permissions (baaki users `.env` na padh sakein):

```bash
chmod 600 /var/www/fusehealth/.env
mkdir -p /var/log/fusehealth
```

> **⚠️ Do cheezein jo local `.env` se copy karne pe TOOT jaayengi:**
> 1. `FUSEHEALTH_LOG_DIR` mein Windows path (`F:/...`) hai — Linux pe `/var/log/fusehealth` hona chahiye
> 2. `POSTGRES_PORT` local pe `5433` hai (kyunki aapke laptop pe do Postgres chal rahe the) — server pe `5432` hoga

---

## Step 7 — Database migrate + static files

```bash
cd /var/www/fusehealth && source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_users        # login accounts banata hai
```

> `collectstatic` **zaroori hai** — production mein `CompressedManifestStaticFilesStorage` use hota hai. Iske bina har page 500 dega.

**Local ka data le jaana hai?** Local pe:

```bash
pg_dump -h localhost -p 5433 -U postgres limitlesshealth -F c -f dump.backup
```

Server pe bhejo aur restore karo:

```bash
scp dump.backup root@<VPS_IP>:/tmp/
# phir server pe:
pg_restore -h localhost -U fuseuser -d limitlesshealth --no-owner --clean /tmp/dump.backup
rm /tmp/dump.backup
```

---

## Step 8 — Gunicorn (systemd service)

Socket file:

```bash
nano /etc/systemd/system/fusehealth.socket
```

```ini
[Unit]
Description=fusehealth gunicorn socket

[Socket]
ListenStream=/run/fusehealth.sock

[Install]
WantedBy=sockets.target
```

Service file:

```bash
nano /etc/systemd/system/fusehealth.service
```

```ini
[Unit]
Description=FuseHealth dashboard (Gunicorn)
Requires=fusehealth.socket
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/fusehealth
EnvironmentFile=/var/www/fusehealth/.env
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/var/www/fusehealth/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --timeout 120 \
          --graceful-timeout 30 \
          --bind unix:/run/fusehealth.sock \
          config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

> **`--workers 3` kyun?** Formula hai `(2 × CPU cores) + 1`. Hostinger ke 1-core VPS pe 3 theek hai, 2-core pe 5 kar dena. Cores dekhne ke liye: `nproc`
>
> **`--timeout 120` kyun?** Ye ek REQUEST timeout nahi hai — ye gunicorn ka WORKER watchdog hai: koi bhi worker jo 120 second tak arbiter ko heartbeat nahi bhejta, SIGKILL ho jata hai. Pehle yahan likha tha "sync background thread mein chalta hai isliye request block nahi hoti" — ye galat tha. Sync pehle sach me ek daemon thread ke andar chalta tha, **usi worker process ke andar jisne request serve ki thi**, aur woh worker normal page requests bhi serve karta hai. Isliye jab bhi us worker ne ek slow request handle ki (ya `systemctl restart` hua, ya deploy hua), sync bhi turant mar jata tha — chahe woh 20 minute se chal raha ho.
>
> Ab sync `manage.py run_sync` ke through apna **alag OS process** banata hai (`subprocess.Popen`, detached) — koi bhi gunicorn worker ka restart ya SIGKILL ab sync ko touch nahi karta, kyoki sync us worker ke andar chalta hi nahi. `--timeout 120` ab bhi zaroori hai (kisi genuinely stuck worker ko replace karne ke liye), bas iska sync se koi lena-dena nahi hai.
>
> **`--graceful-timeout 30` kyun?** Deploy/restart ke time worker ko SIGTERM milta hai; ye us worker ko in-flight HTTP requests khatam karne ke liye 30 second deta hai before force-kill. Sync isme cover nahi hota (woh alag process hai), ye sirf normal page requests ke liye hai.

Permissions aur start:

```bash
chown -R www-data:www-data /var/www/fusehealth /var/log/fusehealth
systemctl daemon-reload
systemctl enable --now fusehealth.socket
systemctl start fusehealth.service
systemctl status fusehealth.service     # "active (running)" dikhna chahiye
```

Socket kaam kar raha hai ya nahi:

```bash
curl --unix-socket /run/fusehealth.sock http://localhost/login/ -I
```

---

## Step 9 — Nginx

```bash
nano /etc/nginx/sites-available/fusehealth
```

```nginx
server {
    listen 80;
    server_name limitless.vashstudios.cloud;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/fusehealth/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 120s;
        proxy_pass http://unix:/run/fusehealth.sock;
    }
}
```

Enable karo:

```bash
ln -s /etc/nginx/sites-available/fusehealth /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t              # "syntax is ok" aana chahiye
systemctl restart nginx
```

> `X-Forwarded-Proto` header **zaroori hai** — `production.py` mein `SECURE_PROXY_SSL_HEADER` isi ko padhta hai. Iske bina Django infinite redirect loop mein chala jaayega.

---

## Step 10 — HTTPS (free SSL)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d limitless.vashstudios.cloud
```

Auto-renew test:

```bash
certbot renew --dry-run
```

> `production.py` mein `SECURE_SSL_REDIRECT = True` hai — matlab **HTTPS setup kiye bina site redirect loop mein fasegi**. Certbot chalane ke baad hi domain se kholna.

---

## Step 11 — Auto sync (cron)

Windows Task Scheduler ki jagah Linux pe cron:

```bash
crontab -e
```

Yeh line add karo (har ghante chalega, khud decide karega kya due hai):

```cron
0 * * * * cd /var/www/fusehealth && /var/www/fusehealth/venv/bin/python manage.py run_scheduled_syncs >> /var/log/fusehealth/cron.log 2>&1
```

Pehle test karo ki kya chalega (kuch chalega nahi, sirf batayega):

```bash
cd /var/www/fusehealth && source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py run_scheduled_syncs --dry-run
```

> ⚠️ Cron lagane se **pehle** Settings → Usage & Budget mein cost cap set kar lena. DataForSEO ke sync paise kharch karte hain.

---

## Step 12 — Final check

```bash
systemctl status fusehealth nginx postgresql    # teeno active
ufw status                                       # sirf 22, 80, 443
curl -I https://limitless.vashstudios.cloud/login/        # 200 aana chahiye
tail -f /var/log/fusehealth/fusehealth.log      # live logs
```

Browser mein `https://limitless.vashstudios.cloud` kholo → login page dikhna chahiye, **CSS ke saath**.

---

## Update kaise karein (baad mein)

```bash
cd /var/www/fusehealth
git pull
source venv/bin/activate
pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py collectstatic --noinput
systemctl restart fusehealth
```

---

## Kuch galat ho toh

| Problem | Dekho |
|---|---|
| 502 Bad Gateway | `systemctl status fusehealth` aur `journalctl -u fusehealth -n 50` |
| CSS/JS nahi aa raha | `collectstatic` chala? Nginx ka `alias` path sahi hai? |
| Infinite redirect | HTTPS setup hua? Nginx mein `X-Forwarded-Proto` hai? |
| `DisallowedHost` | `.env` ke `DJANGO_ALLOWED_HOSTS` mein domain daalo |
| DB connection refused | `systemctl status postgresql`, `.env` mein `POSTGRES_PORT=5432` |
| Permission denied schema public | Step 4 ke aakhri do GRANT commands chalao |
