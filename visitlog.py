"""Private visit log for the homepage and /curl.

JSON lines under logs/, one file per UTC day, with size rollover, a 180-day
maximum age, and a folder size cap. Writes are locked so several gunicorn
workers can append without mixing lines.
"""

import json
import re
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network
from pathlib import Path

MAX_RETENTION_DAYS = 180
DEFAULT_RETENTION_DAYS = 180
DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 128 * 1024 * 1024
MIN_MAX_BYTES = 4096
MAX_MAX_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES_CAP = 2 * 1024 * 1024 * 1024
RECENT_LIMIT = 150
CHART_DAYS = 14
MAINTENANCE_EVERY_SECONDS = 3600
_VISIT_FILE = re.compile(r"^visits-(\d{4}-\d{2}-\d{2})(?:\.(\d+))?\.jsonl$")

_config_warning = None


def _warn_config(message):
    global _config_warning
    if _config_warning == message:
        return
    _config_warning = message
    print(message, file=sys.stderr)


def _clear_config_warning():
    global _config_warning
    _config_warning = None


def _string_list(value):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def _bounded_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < minimum:
        return minimum
    if number > maximum:
        return maximum
    return number


def load_settings(root):
    """Read config.json, or config.example.json when the local file is absent."""
    root = Path(root)
    config_path = root / "config.json"
    example_path = root / "config.example.json"
    using_example = False
    config_ok = True
    data = {}

    if config_path.is_file():
        source = config_path
    elif example_path.is_file():
        source = example_path
        using_example = True
    else:
        source = None

    if source is not None:
        try:
            loaded = json.loads(source.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            _warn_config(
                f"Could not read {source.name} ({exc}). Admin access is closed until it is valid JSON."
            )
            config_ok = False
            loaded = {}
        if not isinstance(loaded, dict):
            _warn_config(f"{source.name} must be a JSON object. Admin access is closed.")
            config_ok = False
            loaded = {}
        data = loaded
        if config_ok:
            _clear_config_warning()

    if not config_ok:
        allow = []
    elif "admin_allowed_ips" in data:
        allow = _string_list(data.get("admin_allowed_ips"))
    elif using_example or source is None:
        allow = ["127.0.0.1", "::1"]
    else:
        allow = []

    if "trusted_proxies" in data:
        proxies = _string_list(data.get("trusted_proxies"))
    else:
        proxies = ["127.0.0.1", "::1"]

    max_bytes = _bounded_int(
        data.get("log_max_bytes", DEFAULT_MAX_BYTES),
        DEFAULT_MAX_BYTES,
        MIN_MAX_BYTES,
        MAX_MAX_BYTES,
    )
    max_total = _bounded_int(
        data.get("log_max_total_bytes", DEFAULT_MAX_TOTAL_BYTES),
        DEFAULT_MAX_TOTAL_BYTES,
        max_bytes,
        MAX_TOTAL_BYTES_CAP,
    )
    retention = _bounded_int(
        data.get("log_retention_days", DEFAULT_RETENTION_DAYS),
        DEFAULT_RETENTION_DAYS,
        1,
        MAX_RETENTION_DAYS,
    )
    log_dir = data.get("log_dir") or "logs"
    if not isinstance(log_dir, str) or not log_dir.strip():
        log_dir = "logs"

    return {
        "admin_allowed_ips": allow,
        "trusted_proxies": proxies,
        "log_dir": log_dir.strip(),
        "log_retention_days": retention,
        "log_max_bytes": max_bytes,
        "log_max_total_bytes": max_total,
        "using_example_config": using_example and config_ok,
        "config_ok": config_ok,
    }


def _parse_ip(value):
    if value is None:
        return None
    text = str(value).strip()
    if text.startswith("[") and "]" in text:
        text = text[1 : text.index("]")]
    try:
        parsed = ip_address(text)
    except ValueError:
        return None
    mapped = getattr(parsed, "ipv4_mapped", None)
    if mapped is not None:
        return mapped
    return parsed


def _last_valid_ip(header_value):
    found = None
    for part in str(header_value or "").split(","):
        parsed = _parse_ip(part)
        if parsed is not None:
            found = parsed
    return found


def ip_allowed(client_ip, allowlist):
    """True when client_ip equals an entry or falls inside a CIDR entry."""
    candidate = _parse_ip(client_ip)
    if candidate is None:
        return False
    for entry in allowlist or []:
        text = str(entry).strip()
        if not text:
            continue
        try:
            if "/" in text:
                network = ip_network(text, strict=False)
                if candidate.version == network.version and candidate in network:
                    return True
            else:
                allowed = _parse_ip(text)
                if allowed is not None and candidate == allowed:
                    return True
        except (TypeError, ValueError):
            continue
    return False


def _is_trusted_peer(remote_addr, trusted_proxies):
    if remote_addr is None or str(remote_addr).strip() in {"", "-"}:
        return True
    peer = _parse_ip(remote_addr)
    if peer is None:
        return False
    if peer.is_loopback:
        return True
    return ip_allowed(peer.compressed, trusted_proxies)


def request_ip_for_admin(headers, remote_addr, trusted_proxies):
    """IP used for the admin allowlist.

    Forwarded headers count only when the direct peer is this machine or a
    configured proxy. A public client cannot grant itself access by sending
    X-Forwarded-For. The last address in the header wins, which is the one
    nginx appends, and X-Real-IP is preferred because the sample config sets
    it from $remote_addr.
    """
    peer = _parse_ip(remote_addr)
    if _is_trusted_peer(remote_addr, trusted_proxies):
        for key in ("X-Real-IP", "X-Forwarded-For"):
            forwarded = _last_valid_ip(headers.get(key, ""))
            if forwarded is not None:
                return forwarded.compressed
    if peer is not None:
        return peer.compressed
    return "Unknown"


def _clip(value, limit):
    if value is None:
        return ""
    text = str(value).replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) > limit:
        return text[:limit]
    return text


def _file_key(path):
    match = _VISIT_FILE.match(path.name)
    if not match:
        return None
    try:
        day = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None
    suffix = int(match.group(2) or 0)
    return (day, suffix)


def _parse_ts(value):
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _location(record):
    parts = [record.get("city") or "", record.get("region") or "", record.get("country") or ""]
    if not any(str(part).strip() for part in parts):
        return ""
    return ", ".join(str(part).strip() or "-" for part in parts)


def _unlink(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _lock_is_stale(path):
    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return False
    return age > 15


def _release_lock(path):
    try:
        if path.is_dir():
            path.rmdir()
        elif path.exists():
            path.unlink()
    except OSError:
        pass


class _FileLock:
    """Cross-process lock. mkdir is atomic on Windows and Linux.

    The lock is a directory so it does not depend on byte-range locks, which
    reject reads on Windows. A directory older than 15 seconds is removed so a
    crashed worker cannot block logging forever. The critical section is one
    append plus a small folder scan, so a live writer does not look stale.
    """

    def __init__(self, path):
        self.path = Path(path)
        self._held = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + 30
        while True:
            try:
                self.path.mkdir()
                self._held = True
                return self
            except FileExistsError:
                if _lock_is_stale(self.path):
                    _release_lock(self.path)
                    continue
                if time.monotonic() > deadline:
                    raise TimeoutError(f"Timed out waiting for {self.path.name}")
                time.sleep(0.02)

    def __exit__(self, exc_type, exc, tb):
        if self._held:
            _release_lock(self.path)
            self._held = False
        return False


class VisitLog:
    def __init__(self, root):
        self.root = Path(root)
        self._thread_lock = threading.Lock()
        self._last_maintenance = 0.0

    def settings(self):
        return load_settings(self.root)

    def _log_dir(self, settings):
        raw = Path(settings["log_dir"])
        if not raw.is_absolute():
            raw = self.root / raw
        raw.mkdir(parents=True, exist_ok=True)
        return raw

    def record(self, entry):
        with self._thread_lock:
            settings = self.settings()
            log_dir = self._log_dir(settings)
            with _FileLock(log_dir / ".write.lock"):
                self._append_locked(log_dir, settings, entry)
                self._maintain_locked(log_dir, settings, force=False)

    def maintain(self, force=False):
        with self._thread_lock:
            settings = self.settings()
            log_dir = self._log_dir(settings)
            with _FileLock(log_dir / ".write.lock"):
                self._maintain_locked(log_dir, settings, force=force)

    def _append_locked(self, log_dir, settings, entry):
        path = self._active_path(log_dir, settings["log_max_bytes"])
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "path": _clip(entry.get("path"), 32),
            "ip": _clip(entry.get("ip"), 64),
            "city": _clip(entry.get("city"), 120),
            "region": _clip(entry.get("region"), 120),
            "country": _clip(entry.get("country"), 120),
            "isp": _clip(entry.get("isp"), 160),
            "asn": _clip(entry.get("asn"), 40),
            "timezone": _clip(entry.get("timezone"), 80),
            "loc": _clip(entry.get("loc"), 64),
            "user_agent": _clip(entry.get("user_agent"), 512),
        }
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")

    def _active_path(self, log_dir, max_bytes):
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = log_dir / f"visits-{day}.jsonl"
        suffix = 0
        while path.exists() and path.stat().st_size >= max_bytes and suffix < 100000:
            suffix += 1
            path = log_dir / f"visits-{day}.{suffix}.jsonl"
        return path

    def _maintain_locked(self, log_dir, settings, force):
        now_mono = time.monotonic()
        if not force and (now_mono - self._last_maintenance) < MAINTENANCE_EVERY_SECONDS:
            return
        self._last_maintenance = now_mono
        files = []
        for path in log_dir.glob("visits-*.jsonl"):
            key = _file_key(path)
            if key is not None:
                files.append((key, path))
        files.sort(key=lambda item: item[0])
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=settings["log_retention_days"])
        kept = []
        for key, path in files:
            if key[0] < cutoff:
                _unlink(path)
            else:
                kept.append(path)
        total = sum(path.stat().st_size for path in kept if path.exists())
        limit = settings["log_max_total_bytes"]
        while len(kept) > 1 and total > limit:
            oldest = kept.pop(0)
            try:
                size = oldest.stat().st_size
            except FileNotFoundError:
                continue
            _unlink(oldest)
            total -= size

    def _read_records(self, settings):
        log_dir = self._log_dir(settings)
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings["log_retention_days"])
        files = []
        for path in log_dir.glob("visits-*.jsonl"):
            key = _file_key(path)
            if key is not None:
                files.append((key, path))
        files.sort(key=lambda item: item[0])
        records = []
        for _, path in files:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(item, dict):
                    continue
                ts = _parse_ts(item.get("ts"))
                if ts is None or ts < cutoff:
                    continue
                item["_dt"] = ts
                records.append(item)
        records.sort(key=lambda item: item["_dt"], reverse=True)
        return records

    def summary(self):
        self.maintain(force=False)
        settings = self.settings()
        records = self._read_records(settings)
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        countries = Counter()
        isps = Counter()
        by_day = Counter()
        for record in records:
            country = (record.get("country") or "").strip()
            isp = (record.get("isp") or "").strip()
            if country:
                countries[country] += 1
            if isp:
                isps[isp] += 1
            by_day[record["_dt"].date()] += 1

        today = now.date()
        days = []
        for offset in range(CHART_DAYS - 1, -1, -1):
            day = today - timedelta(days=offset)
            days.append(
                {
                    "label": day.strftime("%b %d"),
                    "count": by_day.get(day, 0),
                }
            )
        peak = max((day["count"] for day in days), default=0)
        for day in days:
            day["pct"] = 0 if peak == 0 else int(round(100 * day["count"] / peak))

        recent = []
        for record in records[:RECENT_LIMIT]:
            recent.append(
                {
                    "time": record["_dt"].strftime("%Y-%m-%d %H:%M:%S"),
                    "path": record.get("path") or "",
                    "ip": record.get("ip") or "",
                    "location": _location(record),
                    "isp": record.get("isp") or "",
                    "asn": record.get("asn") or "",
                    "timezone": record.get("timezone") or "",
                    "loc": record.get("loc") or "",
                    "user_agent": record.get("user_agent") or "",
                }
            )

        return {
            "total": len(records),
            "unique_ips": len({record.get("ip") for record in records if record.get("ip")}),
            "last_24h": sum(1 for record in records if record["_dt"] >= day_ago),
            "last_7d": sum(1 for record in records if record["_dt"] >= week_ago),
            "homepage": sum(1 for record in records if record.get("path") == "/"),
            "curl": sum(1 for record in records if record.get("path") == "/curl"),
            "top_countries": [
                {"name": name, "count": count} for name, count in countries.most_common(8)
            ],
            "top_isps": [
                {"name": name, "count": count} for name, count in isps.most_common(8)
            ],
            "days": days,
            "recent": recent,
            "recent_limit": RECENT_LIMIT,
            "retention_days": settings["log_retention_days"],
            "max_total_mb": max(1, int(round(settings["log_max_total_bytes"] / (1024 * 1024)))),
            "using_example_config": settings["using_example_config"],
            "config_ok": settings["config_ok"],
        }
