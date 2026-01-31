from dataclasses import dataclass
from typing import Literal, Optional

SourceType = Literal["local", "mangadex"]

@dataclass(frozen=True)
class ReaderEntry:
    source: SourceType
    chapter_id: str
    manga_id: Optional[str]
    title: str
    chapter_title: str
    