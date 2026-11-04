from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    slug: Optional[str] = None
    excerpt: str = Field(..., min_length=10)
    content: Optional[str] = None
    date: str = "Sep 2026"
    readTime: str = "5 min read"
    tag: str = "Hindi"
    color: str = "from-orange-500 to-red-500"
    emoji: str = "📚"
    author_name: str = "VartaLang Editorial"


class ArticleCreate(ArticleBase):
    pass


class ArticleOut(ArticleBase):
    id: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

