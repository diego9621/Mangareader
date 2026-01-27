from sqlmodel import SQLModel, Field

class Progress(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chapter_path: str = Field(index=True, unique=True)
    page_index: int