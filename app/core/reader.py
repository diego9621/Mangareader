from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def list_chapters(manga_dir: Path) -> list[str]:
    if not manga_dir.exists():
        return []
    return sorted([p.name for p in manga_dir.iterdir() if p.is_dir()])

def list_pages(chapter_dir: Path) -> list[Path]:
    if not chapter_dir.exists():
        return []
    pages = [p for p in chapter_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]
    return sorted(pages, key=lambda p: p.name.lower())
