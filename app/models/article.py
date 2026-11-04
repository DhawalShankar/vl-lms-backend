from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedModel


class Article(TimeStampedModel):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_display: Mapped[str] = mapped_column(String(50), nullable=False, default="Sep 2026")
    read_time: Mapped[str] = mapped_column(String(50), nullable=False, default="5 min read")
    tag: Mapped[str] = mapped_column(String(50), nullable=False, default="General", index=True)
    color: Mapped[str] = mapped_column(String(100), nullable=False, default="from-orange-500 to-red-500")
    emoji: Mapped[str] = mapped_column(String(20), nullable=False, default="📚")
    author_name: Mapped[str] = mapped_column(String(100), nullable=False, default="VartaLang Editorial")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Article {self.title} ({self.slug})>"

