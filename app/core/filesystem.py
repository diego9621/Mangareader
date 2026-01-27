from pathlib import Path

def list_dirs(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])

## scan dirs and sort. if no exists return empty list
