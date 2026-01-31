
import sqlite3
from pathlib import Path
from datetime import datetime


def migrate_database(db_path: str = "data/mangareader.db"):


    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Database not found at {db_path}. Will create new database.")
        return

    print(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:

        print("Creating backup tables...")
        cursor.execute("CREATE TABLE IF NOT EXISTS manga_backup AS SELECT * FROM manga")
        cursor.execute("CREATE TABLE IF NOT EXISTS progress_backup AS SELECT * FROM progress")


        cursor.execute("PRAGMA table_info(manga)")
        manga_columns = {row[1] for row in cursor.fetchall()}


        new_manga_columns = [
            ("source", "VARCHAR", "local"),
            ("source_id", "VARCHAR", None),
            ("cover_url", "VARCHAR", None),
            ("description", "TEXT", None),
            ("author", "VARCHAR", None),
            ("artist", "VARCHAR", None),
            ("genres", "VARCHAR", None),
            ("tags", "VARCHAR", None),
            ("status", "VARCHAR", None),
            ("anilist_id", "INTEGER", None),
            ("mal_id", "INTEGER", None),
            ("mangadex_id", "VARCHAR", None),
            ("is_downloaded", "BOOLEAN", "0"),
            ("download_path", "VARCHAR", None),
            ("created_at", "TIMESTAMP", None),
            ("updated_at", "TIMESTAMP", None),
        ]

        print("Updating manga table schema...")
        for col_name, col_type, default_value in new_manga_columns:
            if col_name not in manga_columns:
                if default_value is not None:
                    cursor.execute(f"ALTER TABLE manga ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'")
                else:
                    cursor.execute(f"ALTER TABLE manga ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name}")


        print("Making manga.path nullable...")
        try:
            cursor.execute("""
                CREATE TABLE manga_new (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    source VARCHAR DEFAULT 'local',
                    source_id VARCHAR,
                    cover_url VARCHAR,
                    description TEXT,
                    author VARCHAR,
                    artist VARCHAR,
                    genres VARCHAR,
                    tags VARCHAR,
                    status VARCHAR,
                    anilist_id INTEGER,
                    mal_id INTEGER,
                    mangadex_id VARCHAR,
                    is_downloaded BOOLEAN DEFAULT 0,
                    download_path VARCHAR,
                    path VARCHAR,
                    is_favorite BOOLEAN DEFAULT 0,
                    last_opened TIMESTAMP,
                    open_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                INSERT INTO manga_new 
                SELECT id, title, source, source_id, cover_url, description, author, artist,
                       genres, tags, status, anilist_id, mal_id, mangadex_id, is_downloaded,
                       download_path, path, is_favorite, last_opened, open_count, created_at, updated_at
                FROM manga
            CREATE TABLE IF NOT EXISTS chapter (
                id INTEGER PRIMARY KEY,
                manga_id INTEGER NOT NULL,
                chapter_number VARCHAR NOT NULL,
                title VARCHAR,
                source VARCHAR DEFAULT 'local',
                source_chapter_id VARCHAR,
                is_downloaded BOOLEAN DEFAULT 0,
                download_path VARCHAR,
                page_count INTEGER DEFAULT 0,
                language VARCHAR DEFAULT 'en',
                scanlation_group VARCHAR,
                published_at TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (manga_id) REFERENCES manga(id)
            )
            CREATE TABLE IF NOT EXISTS page (
                id INTEGER PRIMARY KEY,
                chapter_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                local_path VARCHAR,
                remote_url VARCHAR,
                is_downloaded BOOLEAN DEFAULT 0,
                is_cached BOOLEAN DEFAULT 0,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                FOREIGN KEY (chapter_id) REFERENCES chapter(id)
            )
            CREATE TABLE IF NOT EXISTS downloadqueue (
                id INTEGER PRIMARY KEY,
                manga_id INTEGER,
                chapter_id INTEGER,
                status VARCHAR DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                progress_percent REAL DEFAULT 0.0,
                downloaded_pages INTEGER DEFAULT 0,
                total_pages INTEGER DEFAULT 0,
                error_message VARCHAR,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (manga_id) REFERENCES manga(id),
                FOREIGN KEY (chapter_id) REFERENCES chapter(id)
            )
        """)
        print("  Created downloadqueue table")


        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_manga_source ON manga(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapter_manga ON chapter(manga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_page_chapter ON page(chapter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_manga ON progress(manga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_chapter ON progress(chapter_id)")


        conn.commit()
        print("✓ Migration completed successfully!")


        cursor.execute("SELECT COUNT(*) FROM manga")
        manga_count = cursor.fetchone()[0]
        print(f"\nDatabase statistics:")
        print(f"  Manga: {manga_count}")
        cursor.execute("SELECT COUNT(*) FROM progress")
        progress_count = cursor.fetchone()[0]
        print(f"  Progress records: {progress_count}")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/mangareader.db"
    migrate_database(db_path)
