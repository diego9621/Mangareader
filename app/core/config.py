from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MANGA_DIR = DATA_DIR / "manga"
DB_PATH = DATA_DIR / "app.db"
