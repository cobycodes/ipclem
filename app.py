from flask import Flask, request, render_template
import ipaddress
import ipinfo

app = Flask(__name__)

# -----------------------------
#  SETTINGS – OFFLINE IPINFO DB
# -----------------------------
IPINFO_DB_PATH = "/opt/ipclem/ipinfo_lite.mmdb"
IPINFO_TOKEN = ""  # Offline mode

# Create handler for offline DB (synchronous)
handler = ipinfo.getHandler(
    IPINFO_TOKEN,
    settings={
        "cache_maxsize": 1024,
        "country_file": IPINFO_DB_PATH,
        "asn_file": IPINFO_DB_PATH,
        "location_file": IPINFO_DB_PATH,
        "ip_address_file": IPINFO_DB_PATH
    },
    config={
        "ipinfo_downloads": {
            "enabled": False,
            "path": "/opt/ipclem"
        }
    }
)

# -----------------------------
#  HELPER: GET PUBLIC IP ONLY
# -----------------------------
def extract_public_ip(headers, remote_addr):
    """
    Returns the **public** client IP, ignoring internal/private ones.
    """
    # Check X-Forwarded-For first (Nginx)
    xff = headers.get("X-Forwarded-For", "")
    if xff:
        candidates = [ip.strip() for ip in xff.split(",")]
        for ip in candidates:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if not ip_obj.is_private:
                    return ip  # first public IP
            except ValueError:
                continue

    # Fallback: remote_addr if it is public
    try:
        ip_obj = ipaddress.ip_address(remote_addr)
        if not ip_obj.is_private:
            return remote_addr
    except:
        pass

    # If all else fails
    return remote_addr

# -----------------------------
#  ROUTES
# -----------------------------
@app.route("/")
def index():
    # Get the real client IP
    client_ip = extract_public_ip(request.headers, request.remote_addr)

    # Safely query offline IPinfo database
    try:
        details = handler.getDetails(client_ip)
        geo = details.all
    except Exception as e:
        print("Geo lookup failed:", e)
        geo = {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "loc": "0,0",
            "org": "Unknown",
            "asn": "N/A",
            "as_name": "N/A",
            "timezone": "Unknown"
        }

    # Browser info
    user_agent = request.headers.get("User-Agent", "Unknown")
    client_port = request.environ.get("REMOTE_PORT", "Unknown")

    return render_template(
        "index.html",
        client_ip=client_ip,
        client_port=client_port,
        geo=geo,
        user_agent=user_agent
    )

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# -----------------------------
#  MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
