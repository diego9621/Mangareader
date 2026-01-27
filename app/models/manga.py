from sqlmodel import SQLModel, Field

class Manga(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    title: str