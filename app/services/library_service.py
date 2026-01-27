from app.core.config import MANGA_DIR
from app.core.filesystem import list_dirs

def get_library() -> dict:
    return {"root": str(MANGA_DIR), "manga": list_dirs(MANGA_DIR)}

#retrieve list from core, return response structure

