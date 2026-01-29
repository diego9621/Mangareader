import hashlib
from pathlib import Path
import requests

COV_DIR = Path.home() / ".cache" / "mangareader" / "anilist_covers"
COV_DIR.mkdir(parents=True, exist_ok=True)

def cover_path_for_url(url: str) -> Path:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return COV_DIR / f"{h}.jpg"

def ensure_cover(url: str) -> Path | None:
    p = cover_path_for_url(url)
    if p.exists():
        return p
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        p.write_bytes(r.content)
        return p
    except Exception:
        return None