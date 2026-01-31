import asyncio
from sqlmodel import select
from app.models import Manga, Chapter, Page
from app.db.session import get_session
from app.sources.mangadex import MangaDexSource

async def fetch_and_store_chapters(manga_id: int) -> list[Chapter]:
    with get_session() as session:
        manga = session.get(Manga, manga_id)
        if not manga:
            raise ValueError(f"Manga {manga_id} not found")

        existing_chapters = session.exec(
            select(Chapter).where(Chapter.manga_id == manga_id)
        ).all()

        if existing_chapters:
            return list(existing_chapters)

        if manga.source == "mangadex" and manga.mangadex_id:
            async with MangaDexSource() as source:
                chapter_metadata_list = await source.get_chapters(manga.mangadex_id)

                chapters = []
                for meta in chapter_metadata_list:
                    chapter = Chapter(
                        manga_id=manga_id,
                        chapter_number=meta.chapter_number,
                        title=meta.title,
                        source="mangadex",
                        source_chapter_id=meta.source_chapter_id,
                        page_count=meta.page_count,
                        language=meta.language,
                        scanlation_group=meta.scanlation_group,
                        published_at=meta.published_at,
                        is_downloaded=False,
                    )
                    chapters.append(chapter)

                for chapter in chapters:
                    session.add(chapter)

                session.commit()

                for chapter in chapters:
                    session.refresh(chapter)

                return chapters

        return []

def get_manga_chapters(manga_id: int) -> list[Chapter]:
    with get_session() as session:
        chapters = session.exec(
            select(Chapter)
            .where(Chapter.manga_id == manga_id)
            .order_by(Chapter.chapter_number)
        ).all()
        return list(chapters)

async def fetch_and_store_pages(chapter_id: int) -> list[Page]:
    with get_session() as session:
        chapter = session.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        existing_pages = session.exec(
            select(Page).where(Page.chapter_id == chapter_id)
        ).all()

        if existing_pages:
            return list(existing_pages)

        if chapter.source == "mangadex" and chapter.source_chapter_id:
            async with MangaDexSource() as source:
                page_info_list = await source.get_pages(chapter.source_chapter_id)

                pages = []
                for info in page_info_list:
                    page = Page(
                        chapter_id=chapter_id,
                        page_number=info.page_number,
                        remote_url=info.url,
                        is_downloaded=False,
                        is_cached=False,
                    )
                    pages.append(page)

                for page in pages:
                    session.add(page)

                chapter.page_count = len(pages)

                session.commit()

                for page in pages:
                    session.refresh(page)

                return pages

        return []

def get_chapter_pages(chapter_id: int) -> list[Page]:
    with get_session() as session:
        pages = session.exec(
            select(Page)
            .where(Page.chapter_id == chapter_id)
            .order_by(Page.page_number)
        ).all()
        return list(pages)

def sync_fetch_chapters(manga_id: int) -> list[Chapter]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fetch_and_store_chapters(manga_id))
    finally:
        loop.close()

def sync_fetch_pages(chapter_id: int) -> list[Page]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fetch_and_store_pages(chapter_id))
    finally:
        loop.close()
