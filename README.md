# [IP Clem](https://ipclem.com)

`clementine@server:~$ curl ipclem.com`

**IP Clem** is a simple Python web app that shows a visitor’s **public IP address**, approximate geolocation, ISP info, and related details. It includes an interactive map, a rolling photo/video slideshow, light/dark theming, and a privacy notice. This project is intended **for educational purposes only**.

**This project was developed with the assistance of AI (artificial intelligence) tools.**

---

## Features

- **Plain-text IP for the command line:** `curl ipclem.com` prints only the public IP. The app treats `curl`, `wget`, and HTTPie as command-line clients and answers `/` with the same `text/plain` body as `/curl`. Browsers still get the full page. The full Cloudflare and origin setup is in [Cloudflare](#cloudflare).
- Large, clear display of the visitor’s **public IP** (private/local addresses filtered out).
- Shows **approximate location** (city, region, country), **coordinates**, **timezone**, and **ISP / ASN** info when available from the offline database.
- Interactive **[Leaflet](https://leafletjs.com/)** map of the approximate IP location.
- **Rolling slideshow** of photos and videos from `static/slideshow/` (auto-discovered, shuffled each page load). Click a tile to snap it to center; left/right arrows for quick browsing; auto-scroll resumes after a short pause. Videos start muted with a per-video mute control (only one unmuted at a time).
- **Light / dark mode** that follows the device theme by default, with a header toggle that remembers a manual choice.
- Sticky **full-width top bar** (Facebook-style): brand on the left edge, centered links (GitHub, IPinfo, Leaflet), theme switch on the right edge; page content stays in a shared max-width column.
- Privacy policy page (`/privacy`) with matching styling; link in the footer.
- Offline geolocation via the **[IPinfo](https://ipinfo.io/)** Lite MMDB (path configured in `app.py`).
- Compatible with **NGINX**, **NGINX Proxy Manager**, or similar reverse proxies.

---

## Plain-text IP (`/curl`)

`/curl` responds with **`text/plain`**: your **public** IP and a newline. The homepage does the same when the client is a command-line tool, so this prints only the address, with no `-L`:

```bash
curl ipclem.com
```

`curl https://ipclem.com` and `curl https://ipclem.com/curl` do the same thing. Detection uses the `User-Agent` (`curl`, `wget`, `httpie`, `libcurl`). A request that asks for `text/plain` and does not ask for `text/html` gets the same body. Browsers still receive the page. The answer is status **200** on `/` itself. There is no redirect.

`curl ipclem.com` connects to Cloudflare on port 80. With **Full** or **Full (strict)**, Cloudflare then connects to the origin on port 80 as well. Allow that port only from [Cloudflare’s IP ranges](https://www.cloudflare.com/ips/). Details are in [Cloudflare](#cloudflare).

### Linux or macOS (Terminal)

```bash
curl ipclem.com
```

Local development (after [running the app locally](#run-locally-windows--powershell)):

```bash
curl http://127.0.0.1:5000/
```

### Windows (PowerShell, Command Prompt, or Windows Terminal)

**PowerShell:** `curl` is often an alias for `Invoke-WebRequest`. Call the real client:

```powershell
curl.exe ipclem.com
```

For local development:

```powershell
curl.exe http://127.0.0.1:5000/
```

**Command Prompt (`cmd.exe`):**

```cmd
curl ipclem.com
```

You should see only the IP, then the prompt.

---

## Prerequisites

- Python 3.9+
- [ipinfo Python library](https://pypi.org/project/ipinfo/)
- Virtualenv recommended
- NGINX Proxy Manager or NGINX (optional but recommended)

### Python libraries (`requirements.txt`)

Pinned third-party packages:

- **Flask** — web app and templates
- **gunicorn** — WSGI server for production-style runs
- **ipinfo** — IPinfo client; used with the local **IPinfo Lite** database path configured in `app.py`

The application code imports **`flask`**, **`ipinfo`**, and standard library modules including **`ipaddress`**, **`datetime`**, **`json`**, **`pathlib`**, and **`random`**. Visitor logging lives in `visitlog.py`.

### IPinfo Lite offline database

Offline geolocation uses **[IPinfo](https://ipinfo.io/)** and the **IPinfo Lite** database file you download from IPinfo (published as `ipinfo-lite.mmdb`). Point `IPINFO_DB_PATH` in `app.py` at that file (see [Flask App](#flask-app)). Lookups may include country/ASN and, depending on the file/build you use, city, region, coordinates, timezone, and related fields. Download and updates are covered in [Getting the IPinfo Lite Database](#getting-the-ipinfo-lite-database).

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

Or:

```powershell
python app.py
```

Then open:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/privacy`
- Plain-text IP: `http://127.0.0.1:5000/curl` (see [Plain-text IP (`/curl`)](#plain-text-ip-curl))
- Visitor logs: `http://127.0.0.1:5000/admin` (only from IPs listed in `config.json`; the example file allows localhost)

If PowerShell blocks virtualenv activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Slideshow media

Drop image and video files into **`static/slideshow/`**. On each homepage load the app:

1. Scans that folder for supported images (`.jpg`, `.jpeg`, `.png`, `.webp`, …) and videos (`.mp4`, `.webm`, `.mov`, …)
2. Groups same-name video formats into one slide (e.g. `clip.mp4` + `clip.mov`)
3. Shuffles the full set into a random order

**Prefer `.mp4` (H.264)** for browser playback. `.mov` (especially iPhone HEVC) often will not play in Chrome/Firefox/Edge—convert with ffmpeg if needed:

```powershell
ffmpeg -i input.MOV -c:v libx264 -pix_fmt yuv420p -movflags +faststart -c:a aac output.mp4
```

Compress large photos when you can; big media slows first load.

Brand assets for the header live under `static/brand/` (IPinfo pin, Leaflet leaf).

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
sudo ufw allow 'Nginx HTTPS'
sudo ufw enable
sudo ufw status verbose
```

``Nginx HTTPS`` allows port **443**. For ``curl yourdomain.com``, also allow port **80** from Cloudflare’s IP ranges only. Do not open port 80 to the whole internet. The commands are in [Cloudflare](#cloudflare).

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
| **443** (HTTPS) | **The origin’s public port.** TLS ends here, then nginx proxies to Gunicorn with ``proxy_pass http://unix:...``. The ``http://`` in that line is the socket, not a browser URL. Browsers get the page. ``curl``, ``wget``, and HTTPie get the plain IP. |
| **80** (HTTP) | **Cloudflare to the origin only.** In **Full** or **Full (strict)**, an HTTP visitor is fetched from the origin on this port. Nginx proxies it to the app and does not redirect. |

Nginx listens on **443** for HTTPS and on **80** for the Cloudflare HTTP fetch. Both set ``X-Real-IP``.

### Suggested order (so the doc matches what you run)

1. Deploy the app and Gunicorn (systemd) so the Unix socket exists.
2. Add a minimal nginx site that **proxies 443 → the socket** (or run **[Certbot](#obtain-ssl-certificate-using-certbot)** next—see below).
3. Run **Certbot** with ``--nginx``. It inserts **``ssl_certificate``** / **``ssl_certificate_key``** on **443**. **Keep those SSL lines** when you edit the file by hand later.
4. Reload nginx: ``sudo nginx -t`` then ``sudo systemctl reload nginx``.

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

Keep ``X-Real-IP``. Flask uses it for the address shown to the visitor. A command-line client gets the plain IP. A browser gets the page.

**Test against the origin**, replacing the host with the origin name or using the server’s own address:

```bash
curl https://YOURDOMAIN.com/
```

Through Cloudflare, the public check is ``curl yourdomain.com``. See [Cloudflare](#cloudflare).

Enable the site and test:

```bash
sudo ln -sf /etc/nginx/sites-available/ipclem /etc/nginx/sites-enabled/ipclem
sudo nginx -t
sudo systemctl reload nginx
```

## Cloudflare

This is the setup for `curl ipclem.com` with no `-L`. The origin is the Debian server. Cloudflare is in front of it. Do these steps in order.

### How the request moves

1. `curl ipclem.com` opens **port 80 on a Cloudflare address**. It does not open a connection to the Debian server, and it does not try port 443 on its own.
2. Cloudflare accepts that connection. With SSL/TLS mode **Full** or **Full (strict)**, Cloudflare then opens the **same scheme** toward the origin. An HTTP visitor is fetched from the origin on **port 80**. An HTTPS visitor is fetched from the origin on **port 443**.
3. nginx on the origin proxies that request to Gunicorn. It must not answer with a redirect.
4. The app looks at the `User-Agent`. `curl`, `wget`, and HTTPie get the IP as `text/plain` with status **200**. A browser gets the HTML page.

There is no Free, Pro, or Business control that skips step 2’s port 80 connection and still returns the IP as the first response. **Always Use HTTPS** does the opposite: Cloudflare answers with **301** and never asks the origin. curl stops on that 301 unless `-L` is added. **Strict (SSL-Only Origin Pull)** always uses port 443 to the origin, including for HTTP visitors, and it is **Enterprise only**.

`curl https://ipclem.com` only uses port 443 on both hops. It does not need the port 80 work below. The bare command does.

### 1. Proxy the DNS record

In the Cloudflare dashboard, open the domain, then **DNS** → **Records**.

The record people use (`ipclem.com`, and `www` if you use it) must be **Proxied**. The cloud icon is orange. A grey cloud sends clients straight to the origin, so `curl ipclem.com` hits the Debian server on port 80 and UFW will refuse it.

The record target is the origin’s public address. Leave the existing A, AAAA, or CNAME target as it is. Only the proxy status matters here.

### 2. Set the encryption mode

Open **SSL/TLS** → **Overview**.

Set the mode to **Full (strict)**. The origin must already be serving HTTPS on port 443 with a certificate Cloudflare will accept (Let’s Encrypt, or a Cloudflare Origin CA certificate). That is the [port 443 nginx block](#https-443-proxy-to-gunicorn) above.

Do not use **Flexible**. Flexible makes Cloudflare connect to the origin with HTTP even for HTTPS visitors. Do not use **Off**.

### 3. Turn off HTTP-to-HTTPS redirects

Open **SSL/TLS** → **Edge Certificates**.

Turn **Always Use HTTPS** **off**.

Then check for any other redirect that sends `http://` to `https://` before the request reaches the origin:

- **Rules** → **Redirect Rules**
- **Rules** → **Page Rules**, if a rule says “Always Use HTTPS”
- **Bulk Redirects**, if one covers this hostname

Delete or disable those for this hostname. One leftover 301 is enough to make curl print a redirect page instead of the IP.

**Automatic HTTPS Rewrites** can stay on. It rewrites `http://` links inside HTML pages. It does not change the first response to curl.

**HSTS** does not affect this command. curl does not upgrade `ipclem.com` to HTTPS because of HSTS. Browsers might. Leave HSTS as you want it for browsers.

### 4. Proxy port 80 on the origin

Certbot often leaves a port 80 server whose only job is `return 301 https://...`. Replace that server with a proxy. Do not redirect.

Edit ``/etc/nginx/sites-available/ipclem``. Keep the existing **443** server, including the `ssl_certificate` lines Certbot wrote. Add this server next to it. Use the real domain names.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name YOURDOMAIN.com www.YOURDOMAIN.com;

    location / {
        proxy_pass http://unix:/var/www/ipclem/ipclem.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`proxy_pass` uses `http://unix:`. Gunicorn speaks HTTP on the socket even when the visitor used HTTPS.

The app picks the visitor address from `X-Forwarded-For`. Cloudflare sets that header to the visitor, and `$proxy_add_x_forwarded_for` keeps it. If this header is dropped, the page shows a Cloudflare address instead of the visitor.

After every `certbot --nginx` run, open this file again. Certbot may put the port 80 redirect back. The port 80 block has to still proxy, with no `return 301`.

Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Allow Cloudflare to reach port 80

Port 443 can stay as ``ufw allow 'Nginx HTTPS'`` (open to the internet, or already limited however you run the site today).

Port 80 on the origin should accept **only Cloudflare**, not the whole internet. Cloudflare publishes the lists at <https://www.cloudflare.com/ips-v4> and <https://www.cloudflare.com/ips-v6>.

On the Debian server:

```bash
for ip in $(curl -fsS https://www.cloudflare.com/ips-v4); do
  sudo ufw allow from "$ip" to any port 80 proto tcp comment 'Cloudflare'
done
for ip in $(curl -fsS https://www.cloudflare.com/ips-v6); do
  sudo ufw allow from "$ip" to any port 80 proto tcp comment 'Cloudflare'
done
sudo ufw reload
sudo ufw status verbose
```

Do not run ``sudo ufw allow 80`` or ``sudo ufw allow 'Nginx Full'``. Those open port 80 to everyone.

The lists change. Before adding them again, delete the old Cloudflare port 80 rules so UFW does not fill up with duplicates. ``sudo ufw status numbered`` shows the numbers. Delete from the highest number downward:

```bash
sudo ufw delete NUMBER
```

Let’s Encrypt HTTP renewals still work while the DNS record is proxied. The validation request hits Cloudflare, and Cloudflare connects to the origin from a Cloudflare address, which this rule allows. If you turn the cloud grey and run certbot, Let’s Encrypt connects to the origin directly and this rule will block it.

### 6. Confirm it from outside the server

Run this from a machine that is not the origin:

```bash
curl -v ipclem.com
```

What you want:

- `Trying` shows a **Cloudflare** address, port **80**, not the origin’s own address.
- The status is `HTTP/1.1 200 OK`.
- `Content-Type` is `text/plain`.
- The body is one line, your public IP.
- There is no `Location:` header and no 301.

A browser opening `https://ipclem.com` still shows the full page. A browser opening `http://ipclem.com` also shows the page, over HTTP, because Always Use HTTPS is off. That matches ifconfig.io.

On Windows, `curl` in PowerShell is often `Invoke-WebRequest`. Use `curl.exe ipclem.com`.

### When the result is wrong

| What you see | What to fix |
|--------------|-------------|
| `301` and `Location: https://...` | **Always Use HTTPS**, a Redirect Rule, a Page Rule, or nginx `return 301` on port 80. curl will not follow it. |
| `522` | Origin port 80 is closed, UFW is missing a Cloudflare range, or nginx is not listening on port 80. |
| Connection hangs or “couldn’t connect” to the **origin** address | The DNS record is grey-clouded. Turn the proxy back on. |
| HTML in the terminal | The client is not curl, wget, or HTTPie. PowerShell’s `curl` alias does this. Use `curl.exe`. |
| A Cloudflare address as the “IP” | `X-Forwarded-For` is not being passed. Keep the `proxy_set_header` lines in both the port 80 and port 443 servers. |

### Enterprise only: leave origin port 80 closed

**Strict (SSL-Only Origin Pull)** makes Cloudflare use HTTPS to the origin for every visitor, including `curl ipclem.com`. Origin port 80 can stay closed. The option is under **SSL/TLS** → **Overview**, and only Enterprise zones have it. On any other plan, use the port 80 steps above.

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
- Ensure ``static/slideshow/`` is present on the server (and large media is deployed—git clone includes it if you commit those files).
- **Nginx:** See [Configure Nginx Reverse Proxy](#configure-nginx-reverse-proxy) and [Cloudflare](#cloudflare). The origin opens **443**, and port **80** only to Cloudflare. ``curl yourdomain.com`` is fetched from the origin on port 80. Browsers still get the page.

## Map Integration
- Uses Leaflet.js for interactive maps.
- Map coordinates come from the IPinfo database lookup (`loc`).
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

## Visitor logs and admin page

The homepage and `/curl` write a private log of what was shown to that visitor:

- UTC time
- Path (`/` or `/curl`)
- Public IP that was shown
- On homepage visits, the location, ISP, ASN, timezone, and coordinates shown on the page
- Browser user agent

The privacy page, the admin page, and static files are not logged.

Log files are JSON lines in `logs/` (not committed). The app opens a new file each UTC day (`visits-YYYY-MM-DD.jsonl`). When a file reaches `log_max_bytes`, the next lines go to `visits-YYYY-MM-DD.1.jsonl`, then `.2`, and so on. Files older than `log_retention_days` are deleted. That setting cannot be higher than **180**. If the folder grows past `log_max_total_bytes`, the oldest files are deleted until it fits. Gunicorn workers share the `logs/.write.lock` directory, so concurrent writes do not tear a line in half. A lock left behind by a crashed worker is removed after 15 seconds.

### Admin page

`/admin` shows visit totals, unique IPs, the last 14 days, top countries and ISPs, and the latest rows. It is not linked from the public pages.

A visitor can open it only when their IP is in `admin_allowed_ips`. That list is read from a file on the server. The page has no control that can change it. Put one address per entry. A CIDR range such as `203.0.113.0/24` works too, so more than one address can be allowed.

`config.json` is gitignored so a home IP is not committed. Copy the example and edit the copy:

```bash
cp config.example.json config.json
```

On Windows PowerShell:

```powershell
copy config.example.json config.json
```

Add the public IP this site shows when you are at home. A private `192.168.x.x` address will not match once the site is behind nginx. The file is read on every request, so an IP change does not need a restart. Until `config.json` exists, `config.example.json` is used, which allows localhost only.

On a direct connection the allowlist uses the peer address and ignores `X-Forwarded-For`, so a visitor cannot spoof an allowed IP. Through the gunicorn unix socket in this guide (or any proxy whose address is loopback or listed in `trusted_proxies`), the app uses `X-Real-IP`. Keep this line in nginx so a client-supplied value is replaced:

```nginx
proxy_set_header X-Real-IP $remote_addr;
```

`trusted_proxies` means “this host is a reverse proxy,” not “this host may open admin.” If nginx runs on another machine, add that machine’s address there. Your home IP belongs in `admin_allowed_ips`.

The service user has to be able to read the config and create `logs/`:

```bash
sudo chown ipclem-app:ipclem-app config.json
sudo chmod 640 config.json
```

# Privacy & Disclaimer
- Homepage and `/curl` visits are stored in a private server log for at most 180 days (IP, approximate location, ISP, and user agent). See [Visitor logs and admin page](#visitor-logs-and-admin-page).
- Theme preference may be stored in the browser via ``localStorage`` only.
- This website is for educational purposes only.
- Information may not be accurate.
- Privacy notice is accessible via the footer link on all pages.

## License
This project is open-source under the MIT License.

## Contact
Submit issues or pull requests on GitHub.
