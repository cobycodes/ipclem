from flask import Flask, make_response, request, render_template, Response, url_for
import ipaddress
import ipinfo
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from visitlog import VisitLog, ip_allowed, request_ip_for_admin

app = Flask(__name__)
# Without this, Jinja keeps the first compiled copy of each template while DEBUG is off,
# so HTML edits do not show until the process restarts.
app.config["TEMPLATES_AUTO_RELOAD"] = True
visit_log = VisitLog(Path(app.root_path))

# -----------------------------
#  SETTINGS – OFFLINE IPINFO DB
# -----------------------------
IPINFO_DB_PATH = "/opt/ipclem/ipinfo_lite.mmdb"
IPINFO_TOKEN = ""  # Offline mode

SLIDESHOW_DIR = Path(app.root_path) / "static" / "slideshow"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v", ".ogv"}
VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".m4v": "video/mp4",
    ".ogv": "video/ogg",
}


def load_slideshow_items():
    """
    Build slideshow entries from every image/video in static/slideshow/.
    Videos that share a filename stem (e.g. clem.mp4 + clem.mov) become one
    slide with multiple <source> options; everything else is its own slide.
    """
    if not SLIDESHOW_DIR.is_dir():
        return []

    files = sorted(
        (p for p in SLIDESHOW_DIR.iterdir() if p.is_file()),
        key=lambda p: p.name.lower(),
    )
    slides = []
    seen_video_stems = set()

    for path in files:
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            slides.append(
                {
                    "type": "image",
                    "src": url_for("static", filename=f"slideshow/{path.name}"),
                }
            )
        elif ext in VIDEO_EXTS:
            stem = path.stem.lower()
            if stem in seen_video_stems:
                continue
            seen_video_stems.add(stem)

            candidates = [
                p
                for p in files
                if p.stem.lower() == stem and p.suffix.lower() in VIDEO_EXTS
            ]
            # Prefer mp4 first for broadest browser support
            candidates.sort(
                key=lambda p: (0 if p.suffix.lower() == ".mp4" else 1, p.name.lower())
            )
            sources = [
                {
                    "src": url_for("static", filename=f"slideshow/{c.name}"),
                    "type": VIDEO_MIME.get(
                        c.suffix.lower(), f"video/{c.suffix.lower().lstrip('.')}"
                    ),
                }
                for c in candidates
            ]
            slides.append({"type": "video", "sources": sources})

    random.shuffle(slides)
    return slides


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


# curl, wget, HTTPie, and libcurl. A browser User-Agent does not match.
_CLI_CLIENT = re.compile(
    r"(?:^|[^a-z0-9])(?:curl|wget|httpie|libcurl)(?:/|\s|$)",
    re.IGNORECASE,
)


def client_wants_plain_ip(headers):
    """Return the plain IP instead of the homepage.

    This has to be the first response body. Sending the client to /curl with a
    redirect still requires curl -L, which is the case we are avoiding.
    """
    if _CLI_CLIENT.search(headers.get("User-Agent") or ""):
        return True
    accept = (headers.get("Accept") or "").lower()
    return "text/plain" in accept and "text/html" not in accept


def record_presented_visit(path, client_ip, geo=None, user_agent=""):
    """Store the details this response is about to show. Failures stay off the page."""
    if request.method != "GET":
        return
    details = geo or {}
    try:
        visit_log.record(
            {
                "path": path,
                "ip": client_ip,
                "city": details.get("city", ""),
                "region": details.get("region", ""),
                "country": details.get("country", ""),
                "isp": details.get("isp_name", ""),
                "asn": details.get("asn", ""),
                "timezone": details.get("timezone", ""),
                "loc": details.get("loc", ""),
                "user_agent": user_agent,
            }
        )
    except Exception as exc:
        print("Visit log failed:", exc, file=sys.stderr)


def _private_page(body, status=200):
    response = make_response(body)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    return response

# -----------------------------
#  ROUTES
# -----------------------------
@app.route("/")
def index():
    if client_wants_plain_ip(request.headers):
        return plain_ip()

    # Get the real client IP
    client_ip = extract_public_ip(request.headers, request.remote_addr)

    # Safely query offline IPinfo database
    try:
        details = handler.getDetails(client_ip)
        geo = details.all

        # Split geo["org"] into ASN and ISP name
        if geo.get("org"):
            org_parts = geo["org"].split(" ", 1)
            geo["asn"] = org_parts[0]                     # e.g., AS396253
            geo["isp_name"] = org_parts[1] if len(org_parts) > 1 else ""
        else:
            geo["asn"] = "N/A"
            geo["isp_name"] = "Unknown"

        geo["timezone"] = geo.get("timezone") or "Unknown"
        geo["loc"] = geo.get("loc") or "Unknown"

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
            "as_domain": "N/A",
            "isp_name": "Unknown",
            "timezone": "Unknown",
        }

    # Browser info
    user_agent = request.headers.get("User-Agent", "Unknown")
    record_presented_visit("/", client_ip, geo, user_agent)

    return render_template(
        "index.html",
        client_ip=client_ip,
        geo=geo,
        user_agent=user_agent,
        current_year=datetime.now().year,
        slideshow_items=load_slideshow_items(),
    )


@app.route("/curl")
def plain_ip():
    """Plain-text client IP for scripts and `curl` (ifconfig.io-style)."""
    client_ip = extract_public_ip(request.headers, request.remote_addr)
    record_presented_visit(
        "/curl",
        client_ip,
        user_agent=request.headers.get("User-Agent", ""),
    )
    return Response(
        f"{client_ip}\n",
        mimetype="text/plain",
        headers={"Cache-Control": "no-store"},
    )


@app.route("/privacy")
def privacy():
    return render_template("privacy.html", current_year=datetime.now().year)


@app.route("/admin")
def admin():
    settings = visit_log.settings()
    client_ip = request_ip_for_admin(
        request.headers,
        request.remote_addr,
        settings["trusted_proxies"],
    )
    year = datetime.now().year
    if not settings["config_ok"] or not ip_allowed(client_ip, settings["admin_allowed_ips"]):
        page = render_template(
            "forbidden.html",
            client_ip=client_ip,
            config_ok=settings["config_ok"],
            current_year=year,
        )
        return _private_page(page, status=403)

    page = render_template(
        "admin.html",
        stats=visit_log.summary(),
        client_ip=client_ip,
        current_year=year,
    )
    return _private_page(page)

# -----------------------------
#  MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
