from sqlmodel import SQLModel, Field
from typing import Optional

class Page(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id", index=True)
    page_number: int  
    local_path: Optional[str] = None
    remote_url: Optional[str] = None
    is_downloaded: bool = Field(default=False)
    is_cached: bool = Field(default=False)
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None  
    def __repr__(self):
        return f"Page(id={self.id}, chapter_id={self.chapter_id}, page_number={self.page_number})"
