# [IP Clem](https://ipclem.com)

**IP Clem** is a simple python-based web application that displays the visitor’s **public IP address**, geolocation, ISP info, and other details. It includes a dynamic map and a privacy notice. This project is intended **for educational purposes only**.

**This project was developed with the assistance of AI (artificial intelligence) tools.**

---

## Features

- **New — plain-text IP at `/curl`:** This is **probably the most useful** feature for quick checks and automation: a **`text/plain`** response with only your public IP (plus a newline), like [ifconfig.io](https://ifconfig.io). In practice you will often use **`curl -L`** (follow redirects)—for example **`curl -L ipclem.com`**—because **`curl` does not follow HTTP→HTTPS redirects by default**, or use **`curl https://ipclem.com/curl`** to skip redirects. Details and nginx options are in [Plain-text IP (`/curl`)](#plain-text-ip-curl).  
- Displays **public IP address** only (filters out private/local IPs).  
- Shows **geolocation**, **city**, **region**, **country**, **coordinates**, **timezone**, and **ISP info**.  
- Interactive **Leaflet map** showing IP location.  
- Landing page hero **video loop** (muted by default) with **Unmute/Mute** toggle and **click-to-pause/play**.  
- Privacy policy page (`/privacy`) styled consistently with the landing page and accessible from the footer.  
- Supports a **video fallback** source for better browser compatibility (`static/clem.mp4` preferred, falls back to `static/clem.mov`).  
- Optional: use the **IPinfo Lite database** for offline geolocation lookups.  
- Fully compatible with **NGINX Proxy Manager**, NGINX, or a combination of both.


## Plain-text IP (`/curl`)

The `/curl` route responds with **`text/plain`**: a single line containing your **public** IP as seen by the server (same logic as the main page), followed by a newline. Use it from any terminal when you want the address without HTML or JSON.

Replace the example host with your own domain when self-hosting (for example `https://yourdomain.com/curl`).

**Redirects and `curl`:** A **301/302 is still a redirect**—the first HTTP response does **not** contain your Flask body; it tells the client to go somewhere else. **`curl` does not follow redirects unless you pass `-L`.** So `curl ipclem.com` (usually `http://yourdomain.com/`) stops at that redirect: you see the **301**, not the IP. To print the IP in one command you can use **`curl -L http://yourdomain.com/`** (follow to `https://…/curl` if you use [the apex redirect](#optional-http-apex-redirects-to-https-curl)), or **`curl https://yourdomain.com/curl`** (no redirect). If you want **bare `curl yourdomain.com` to print the IP with no `-L`**, you need an **HTTP 200** on port 80 (see [optional instant plain-text on HTTP `/`](#optional-http-200-plain-text-ip-on-port-80-root)); that is different from a redirect-only setup.

### Linux or macOS (Terminal)

In a typical terminal, `curl` is already available. Example using the public site:

```bash
curl https://ipclem.com/curl
```

If you omit **`https://`** or use plain **`http://`**, nginx may respond with a **redirect** first. **`curl` does not follow redirects by default**, so you can get a **301** and HTML instead of the IP. In that case use **`-L`** (location) so `curl` follows the redirect—for example:

```bash
curl -L ipclem.com
```

```bash
curl -L http://ipclem.com/curl
```

(Adjust the host if you self-host.)

Local development (after [running the app locally](#run-locally-windows--powershell)):

```bash
curl http://127.0.0.1:5000/curl
```

### Windows (PowerShell, Command Prompt, or Windows Terminal)

**PowerShell:** On Windows, `curl` is often an alias for `Invoke-WebRequest`. Call the real client explicitly:

```powershell
curl.exe https://ipclem.com/curl
```

For local development:

```powershell
curl.exe http://127.0.0.1:5000/curl
```

If you see a **301** instead of the IP, use **`curl.exe -L`**, e.g. **`curl.exe -L ipclem.com`** or **`curl.exe -L http://ipclem.com/curl`**.

**Command Prompt (`cmd.exe`):** `curl` is available on Windows 10 and later:

```cmd
curl https://ipclem.com/curl
```

```cmd
curl http://127.0.0.1:5000/curl
```

If you hit a **redirect** instead of the IP (common with **HTTP** or no scheme), use **`curl.exe -L`**, e.g. **`curl.exe -L ipclem.com`** or **`curl.exe -L http://ipclem.com/curl`**.

You should see only the IP address printed, then return to the prompt (after any redirects, if you used **`-L`**).


## Prerequisites

- Python 3.9+   
- [ipinfo Python library](https://pypi.org/project/ipinfo/)  
- Virtualenv recommended  
- NGINX Proxy Manager or NGINX (optional but recommended)

### Python libraries (`requirements.txt`)

Pinned third-party packages:

- **Flask** — web app and templates  
- **gunicorn** — WSGI server for production-style runs  
- **ipinfo** — IPinfo API client; also used with the local **IPinfo Lite** database path configured in `app.py`

The application code imports **`flask`**, **`ipinfo`**, and the standard library modules **`ipaddress`** and **`datetime`** (no separate MMDB reader package).

### IPinfo Lite offline database

Offline geolocation uses **[IPinfo](https://ipinfo.io/)** and the **IPinfo Lite** database file you download from IPinfo (published as `ipinfo-lite.mmdb`). Point `IPINFO_DB_PATH` in `app.py` at that file (see [Flask App](#flask-app)). The **ipinfo** library performs lookups for city, region, country, coordinates, timezone, and related fields. Download and updates are covered in [Getting the IPinfo Lite Database](#getting-the-ipinfo-lite-database).

---

## Run Locally (Windows / PowerShell)

From the project root:

```powershell
cd d:\git\ipclem-test

py -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run --host 127.0.0.1 --port 5000
```

Then open:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/privacy`
- Plain-text IP: `http://127.0.0.1:5000/curl` (see [Plain-text IP (`/curl`)](#plain-text-ip-curl))

If PowerShell blocks virtualenv activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Local video files

Place your hero video files in `static/`:

- `static/clem.mp4` (recommended for widest compatibility)
- `static/clem.mov` (fallback)

---

## Getting the IPinfo Lite Database

To use offline geolocation with IPinfo, you need the **IPinfo Lite** database file:

1. **Create an IPinfo account**:

    - Go to [https://ipinfo.io/signup](https://ipinfo.io/signup)  
    - Sign up for a free account. The free plan includes access to the Lite database.

2. **Obtain a token**:

    - After creating your account, log in and go to your **API Tokens** page.  
    - Copy your token — it will be used for downloading the database.

3. **Download the Lite database**:

    - Visit the IPinfo [database download page](https://ipinfo.io/developers/database-download)  
    - Use the Lite database download link with your token, for example:

```bash
curl -L "https://ipinfo.io/data/ipinfo-lite.mmdb?token=YOUR_IPINFO_TOKEN" -o /opt/ipclem/ipinfo_lite.mmdb
```
Replace YOUR_IPINFO_TOKEN with the token from your account. Place the downloaded file at ``/opt/ipclem/ipinfo_lite.mmdb`` or update ``app.py`` accordingly.

**Note:** The Lite database is updated regularly. We recommend setting up a cron job to download updates automatically.


# Configuration & Deployment
The following guide is referencing a Debian 12 (Bookworm) system.

## Install the Required Packages
```bash
sudo apt update
sudo apt install -y git nginx python3 python3-venv python3-pip ufw certbot python3-certbot-nginx
```

## Configure the Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status verbose
```

## Git Clone the Application
```bash
sudo mkdir -p /var/www/ipclem
sudo chown $USER:$USER /var/www/ipclem
cd /var/www/ipclem
git clone https://github.com/cobycodes/ipclem.git .
```

## Create a Service User & Group
```bash
sudo addgroup --system ipclem-app
sudo adduser --system --no-create-home --shell /usr/sbin/nologin --ingroup ipclem-app ipclem-app
sudo chown -R ipclem-app:ipclem-app /var/www/ipclem
```

## Create Python Virtual Environment & Install Libraries
```bash
cd /var/www/ipclem
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Create ``systemd`` Service File
```ini
[Unit]
Description=IP Location Lookup Web App (ipclem)
After=network.target

[Service]
User=ipclem-app
Group=ipclem-app
WorkingDirectory=/var/www/ipclem
Environment="PATH=/var/www/ipclem/venv/bin"
ExecStart=/var/www/ipclem/venv/bin/gunicorn --workers 3 --bind unix:/var/www/ipclem/ipclem.sock app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ipclem
sudo systemctl status ipclem
```

## Configure Nginx Reverse Proxy

Nginx sits in front of Gunicorn. You normally edit the site file at ``/etc/nginx/sites-available/ipclem`` (enable it under ``sites-enabled``).

### What the two ports do

| Port | Role |
|------|------|
| **80** (HTTP) | **Redirects only.** Browsers and `curl` may hit this first. Nothing here is sent to Flask; you return **301** to an HTTPS URL. |
| **443** (HTTPS) | **TLS + proxy.** This is where requests are forwarded to Gunicorn with ``proxy_pass http://unix:...``. The ``http://`` here means “HTTP to the Unix socket,” not “users use HTTP in the browser.” |

Flask never sees cleartext HTTP in production if everyone uses HTTPS links—nginx handles TLS and sets ``X-Forwarded-*`` headers so the app knows the client IP.

### Suggested order (so the doc matches what you run)

1. Deploy the app and Gunicorn (systemd) so the Unix socket exists.
2. Add a minimal nginx site that **proxies 443 → the socket** (or run **[Certbot](#obtain-ssl-certificate-using-certbot)** next—see below).
3. Run **Certbot** with ``--nginx``. It usually **creates or updates** both the **:80** and **:443** blocks and inserts **``ssl_certificate``** / **``ssl_certificate_key``** on **443**. **Keep those SSL lines** when you edit the file by hand later.
4. **Optional:** If you want the [HTTP apex → `/curl`](#optional-http-apex-redirects-to-https-curl) behavior, adjust only the **port 80** block after Certbot (see that subsection).
5. Reload nginx: ``sudo nginx -t`` then ``sudo systemctl reload nginx``.

If you run Certbot **before** step 2, ensure the **443** block includes a ``location /`` that proxies to the socket—Certbot does not add ``proxy_pass`` for you.

### HTTPS (443): proxy to Gunicorn

This block terminates TLS and forwards to the app. **Certbot** normally adds the ``ssl_certificate`` lines; the example shows placeholders—**do not delete** the real paths Certbot wrote.

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name YOURDOMAIN.com www.YOURDOMAIN.com;

    # SSL: added by Certbot (example paths—use your real files):
    # ssl_certificate /etc/letsencrypt/live/YOURDOMAIN.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/YOURDOMAIN.com/privkey.pem;
    # include /etc/letsencrypt/options-ssl-nginx.conf;
    # ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://unix:/var/www/ipclem/ipclem.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Use **`http://unix:`** in ``proxy_pass``, not ``https://unix:``—Gunicorn speaks HTTP on the socket.

### Optional: HTTP apex redirects to HTTPS /curl

**Still uses HTTP→HTTPS redirects (301).** This does **not** remove the redirect: it only changes the **target** so that, **after** `curl -L`, the client ends at **`https://YOURDOMAIN.com/curl`** instead of **`https://YOURDOMAIN.com/`**.

If you skip this, Certbot’s default—``return 301 https://$host$request_uri;`` on port 80—is fine: every HTTP URL jumps to the **same path** on HTTPS.

**With this snippet:** only the **exact** path **`/`** on **HTTP** redirects to **`https://YOURDOMAIN.com/curl`**. Other HTTP paths (``/privacy``, ``/curl``, etc.) still redirect to the **same path** on HTTPS.

**Unchanged:** **`https://YOURDOMAIN.com/`** (HTTPS, path `/`) still serves the **full Flask homepage**—this applies only to **cleartext** HTTP with path **`/`**.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name YOURDOMAIN.com www.YOURDOMAIN.com;

    location = / {
        return 301 https://$host/curl;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

If Certbot left port 80 as one line—``return 301 https://$host$request_uri;``—replace that **server** block with the version above so ``location = /`` can run first.

**Test:** ``curl -i http://YOURDOMAIN.com/`` shows **301** and ``Location: https://…/curl``. **``curl -L http://YOURDOMAIN.com/``** follows it and prints the IP.

### Optional: proxy HTTP /curl on port 80 for plain curl

**Why you still see 301:** ``curl ipclem.com/curl`` is **HTTP** (``http://ipclem.com/curl``). If port **80** only does **``return 301``** to HTTPS, the **first** response is always a **redirect**. **`curl` does not follow redirects unless you add ``-L``**, so you see the small HTML 301 page, not the IP. That is expected—not a misconfiguration.

**Ways to get the IP immediately:** use **`curl https://ipclem.com/curl`**, or **`curl -L http://ipclem.com/curl`**, or add the block below so **HTTP** ``/curl`` is **proxied** to Flask (same app as HTTPS) and returns **200** with **no redirect**.

On port **80**, add **`location = /curl`** (exact match **before** the catch-all ``location /``):

```nginx
    location = /curl {
        proxy_pass http://unix:/var/www/ipclem/ipclem.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

**Full port 80 example** (apex redirect + HTTP `/curl` proxy + everything else → HTTPS):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name YOURDOMAIN.com www.YOURDOMAIN.com;

    location = / {
        return 301 https://$host/curl;
    }

    location = /curl {
        proxy_pass http://unix:/var/www/ipclem/ipclem.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

The first hop is still **HTTP** for ``/curl`` (not TLS); the app still runs your Flask ``extract_public_ip`` logic via the proxy headers.

### Optional: HTTP 200 plain-text IP on port 80 root

Use this **instead of** the [301 apex redirect](#optional-http-apex-redirects-to-https-curl) for ``location = /`` on port **80**—you cannot combine both for the same path.

**Goal:** ``curl yourdomain.com`` (HTTP `/`) returns **200** with the IP in the body on the **first** response—no redirect, so **no ``curl -L``** needed.

Nginx answers directly with the client address it sees (**``$remote_addr``**). That matches a direct Internet client when nginx is the first hop; if you use **Cloudflare**, **another reverse proxy**, or **NGINX Proxy Manager** in front, you may need ``real_ip`` / trusted proxy settings or you will see the wrong address.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name YOURDOMAIN.com www.YOURDOMAIN.com;

    location = / {
        default_type text/plain;
        return 200 "$remote_addr\n";
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

**Tradeoffs:** Response is **only over HTTP** for that URL (not TLS). Flask’s ``extract_public_ip`` / ``/curl`` logic (e.g. ``X-Forwarded-For``) is **not** used here—only nginx’s view of the peer. For a stricter match to your app, stick to **`https://…/curl`** or **`-L`**.

Enable the site and test:

```bash
sudo ln -sf /etc/nginx/sites-available/ipclem /etc/nginx/sites-enabled/ipclem
sudo nginx -t
sudo systemctl reload nginx
```

## Obtain SSL Certificate using ``certbot``
```bash
sudo certbot --nginx -d YOURDOMAIN.com www.YOURDOMAIN.com
```
Follow the prompts to complete the registration for the certificate.

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

## Flask App
Update ``app.py`` if your database path differs:

```python
IPINFO_DB_PATH = "/opt/ipclem/ipinfo_lite.mmdb"
IPINFO_TOKEN = ""  # Offline mode
```

## Deployment Notes

- The web server is best installed in ``/var/www/ipclem``.
- Reverse proxy is recommended for HTTPS, caching, and header handling, but direct access works too.
- Ensure the Flask process can read ``/opt/ipclem/ipinfo_lite.mmdb``.
- **Nginx:** See [Configure Nginx Reverse Proxy](#configure-nginx-reverse-proxy): **443** proxies to Gunicorn with ``proxy_pass http://unix:...``; **80** is usually redirects—optional [301 apex → HTTPS `/curl`](#optional-http-apex-redirects-to-https-curl), optional [proxy HTTP /curl on port 80](#optional-proxy-http-curl-on-port-80-for-plain-curl) so ``curl http://…/curl`` returns the IP without ``-L``, or [HTTP 200 plain-text IP on port 80](#optional-http-200-plain-text-ip-on-port-80-root) for the apex only (tradeoffs apply).

## Map Integration
- Uses Leaflet.js for interactive maps.
- Map coordinates come from the IPinfo Lite database.
- Fully responsive and works on mobile and desktop.

## Automatic Database Updates
- The IPinfo Lite database can be regularly updated using a cron job.

Update script: ``/opt/ipclem/update_ipinfo.sh``
```bash
#!/bin/bash

IPINFO_DB_DIR="/opt/ipclem"
IPINFO_DB_FILE="ipinfo_lite.mmdb"
TMP_FILE="$IPINFO_DB_DIR/ipinfo_lite_tmp.mmdb"
TOKEN="YOUR_IPINFO_TOKEN"

curl -L "https://ipinfo.io/data/ipinfo-lite.mmdb?token=$TOKEN" -o "$TMP_FILE"

if [ $? -eq 0 ] && [ -f "$TMP_FILE" ]; then
    mv "$TMP_FILE" "$IPINFO_DB_DIR/$IPINFO_DB_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Updated IPinfo Lite DB." >> "$IPINFO_DB_DIR/update_ipinfo.log"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to update IPinfo Lite DB." >> "$IPINFO_DB_DIR/update_ipinfo.log"
    rm -f "$TMP_FILE"
fi
```

Make it executable:
```bash
chmod +x /opt/ipclem/update_ipinfo.sh
```
Set up a cron job (runs weekly at 3 AM):
``` bash
crontab -e
```
Add:
```bash
0 3 * * 0 /opt/ipclem/update_ipinfo.sh
```
- Logs are saved to ``/opt/ipclem/update_ipinfo.log``.
- No Flask restart is needed as the DB is read on each request.

# Privacy & Disclaimer
- No IP data is stored by the server.
- This website is for educational purposes only.
- Information may not be accurate.
- Privacy notice is accessible via the footer link on all pages.

## License
This project is open-source under the MIT License.

## Contact
Submit issues or pull requests on GitHub.
