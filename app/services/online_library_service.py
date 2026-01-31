import json
from datetime import datetime
from sqlmodel import select
from app.models import Manga
from app.db.session import get_session


def add_manga_to_library(manga_data: dict) -> tuple[Manga, bool]:
    with get_session() as session:
        source = manga_data.get("source", "mangadex")
        source_id = manga_data.get("mangadex_id") or manga_data.get("id")

        if source == "mangadex":
            existing = session.exec(
                select(Manga).where(Manga.mangadex_id == source_id)
            ).first()
        else:
            existing = session.exec(
                select(Manga).where(
                    Manga.source == source,
                    Manga.source_id == source_id
                )
            ).first()

        if existing:
            return existing, False

        title_obj = manga_data.get("title", {})
        if isinstance(title_obj, dict):
            title = (
                title_obj.get("english") or 
                title_obj.get("romaji") or 
                title_obj.get("native") or 
                "Untitled"
            )
        else:
            title = str(title_obj) if title_obj else "Untitled"

        cover_img = manga_data.get("coverImage", {})
        cover_url = cover_img.get("large") if isinstance(cover_img, dict) else None
        genres = manga_data.get("genres", [])
        genres_json = json.dumps(genres) if genres else None
        tags = manga_data.get("tags", [])
        if tags and isinstance(tags[0], dict):
            tags = [t.get("name", "") for t in tags]
        tags_json = json.dumps(tags) if tags else None

        start_date = manga_data.get("startDate", {})
        year = start_date.get("year") if isinstance(start_date, dict) else None

        new_manga = Manga(
            title=title,
            source=source,
            source_id=source_id,
            cover_url=cover_url,
            description=manga_data.get("description"),
            author=manga_data.get("author"),
            artist=manga_data.get("artist"),
            genres=genres_json,
            tags=tags_json,
            status=manga_data.get("status"),
            anilist_id=manga_data.get("anilist_id"),
            mal_id=manga_data.get("mal_id"),
            mangadex_id=source_id if source == "mangadex" else None,
            is_downloaded=False,
            is_favorite=False,
        )

        session.add(new_manga)
        session.commit()
        session.refresh(new_manga)

        return new_manga, True


def remove_manga_from_library(manga_id: int) -> bool:
    with get_session() as session:
        manga = session.get(Manga, manga_id)
        if not manga:
            return False

        session.delete(manga)
        session.commit()
        return True


def is_in_library(source: str, source_id: str) -> bool:
    with get_session() as session:
        if source == "mangadex":
            manga = session.exec(
                select(Manga).where(Manga.mangadex_id == source_id)
            ).first()
        else:
            manga = session.exec(
                select(Manga).where(
                    Manga.source == source,
                    Manga.source_id == source_id
                )
            ).first()

        return manga is not None
