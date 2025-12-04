# [IP Clem](https://ipclem.com)

**IP Clem** is a simple Flask web application that displays the visitor’s **public IP address**, geolocation, ISP info, and other details. It includes a dynamic map and a privacy notice. This project is intended **for educational purposes only**.

---

## Features

- Displays **public IP address** only (filters out private/local IPs).  
- Shows **geolocation**, **city**, **region**, **country**, **coordinates**, **timezone**, and **ISP info**.  
- Interactive **Leaflet map** showing IP location.  
- Privacy notice page accessible from the footer.  
- Automatically updates the **IPinfo Lite database** for offline geolocation lookups.  
- Fully compatible with **NGINX Proxy Manager**, NGINX, or a combination of both.


## Prerequisites

- Python 3.9+   
- [ipinfo Python library](https://pypi.org/project/ipinfo/)  
- Virtualenv recommended  
- NGINX Proxy Manager or NGINX (optional but recommended)

### Python Libraries
- Flask==3.1.0
- gunicorn==23.0.0
- ipinfo==5.3.0
- maxminddb==3.0.0

---

## Getting the IPinfo Lite Database

To use offline geolocation with IPinfo, you need the **IPinfo Lite MMDB**:

1. **Create an IPinfo account**:

    - Go to [https://ipinfo.io/signup](https://ipinfo.io/signup)  
    - Sign up for a free account. The free plan includes access to the Lite database.

2. **Obtain a token**:

    - After creating your account, log in and go to your **API Tokens** page.  
    - Copy your token — it will be used for downloading the MMDB.

3. **Download the Lite MMDB**:

    - Visit the IPinfo [database download page](https://ipinfo.io/developers/database-download)  
    - Use the link for the Lite MMDB with your token, for example:

```bash
curl -L "https://ipinfo.io/data/ipinfo-lite.mmdb?token=YOUR_IPINFO_TOKEN" -o /opt/ipclem/ipinfo_lite.mmdb
```
Replace YOUR_IPINFO_TOKEN with the token from your account. Place the downloaded file at ``/opt/ipclem/ipinfo_lite.mmdb`` or update ``app.py`` accordingly.

**Note:** The Lite MMDB is updated regularly. We recommend setting up a cron job to download updates automatically.


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
Create / edit the nginx configuration at ``etc/nginx/sites-available/ipclem``:
```nginx
server {
    listen 443;
    server_name YOURDOMAIN.com;

    location / {
        proxy_pass https://unix:/var/www/ipclem/ipclem.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the nginx configuration:
```bash
sudo ln -s /etc/nginx/sites-available/ipclem /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Obtain SSL Certificate using ``certbot``
```bash
sudo certbot --nginx -d YOURDOMAIN.com
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

## Map Integration
- Uses Leaflet.js for interactive maps.
- Map coordinates come from the IPinfo Lite MMDB.
- Fully responsive and works on mobile and desktop.

## Automatic Database Updates
- IPinfo Lite MMDB is regularly updated using a cron job.

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
