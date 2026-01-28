from pathlib import Path
import re

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
CH_RE = re.compile(r"(chapter|chap)\s*(\d+)", re.IGNORECASE)

def _chapter_sort_key(name: str):
    m = CH_RE.search(name)
    if m:
        return (0, int(m.group(2)))
    return (1, name.lower())

def list_chapters(manga_dir: Path) -> list[str]:
    if not manga_dir or not manga_dir.exists():
        return []
    out = []
    for p in manga_dir.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            out.append(p.name)
    return sorted(out, key=_chapter_sort_key)

def list_pages(chapter_dir: Path) -> list[Path]:
    if not chapter_dir or not chapter_dir.exists():
        return []
    pages = [p for p in chapter_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXTS]
    return sorted(pages, key=lambda p: p.name.lower())