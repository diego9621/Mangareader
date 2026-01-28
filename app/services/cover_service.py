from pathlib import Path
import hashlib
from PIL import Image

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
COVER_DIR = Path("data/covers")

def cover_path_for_manga_dir(manga_dir: Path) -> Path:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(str(manga_dir).encode("utf-8")).hexdigest()
    return COVER_DIR / f"{h}.jpg"

def find_first_image_in_tree(chapter_dir: Path) -> Path | None:
    for p in sorted(chapter_dir.rglob("*"), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            return p
    return None

def build_cover(manga_dir: Path, first_chapter_name: str) -> Path | None:
    out = cover_path_for_manga_dir(manga_dir)
    if out.exists():
        return None
    
    chapter_dir = manga_dir / first_chapter_name
    if not chapter_dir.exists():
        return None
    
    img_path = find_first_image_in_tree(chapter_dir)
    if not img_path:
        return None
    
    img = Image.open(img_path).convert("RGB")
    img.thumbnail((600, 900))
    img.save(out, "JPEG", quality=85, optimize=True)
    return out