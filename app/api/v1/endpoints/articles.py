from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_optional_current_user, require_role
from app.core.database import get_db
from app.models.article import Article
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleOut

router = APIRouter()

DEFAULT_ARTICLES = [
    {
        "id": "art-1",
        "title": "Why Learning Hindi Opens Doors Across India",
        "slug": "why-learning-hindi-opens-doors-across-india",
        "excerpt": "With over 500 million speakers, Hindi connects opportunities in government, media, commerce, and culture across northern and central states.",
        "date": "Sep 2026",
        "readTime": "5 min read",
        "tag": "Hindi",
        "color": "from-orange-500 to-red-500",
        "emoji": "📚",
        "author_name": "VartaLang Editorial",
    },
    {
        "id": "art-2",
        "title": "Tamil: Classical Heritage & Contemporary Usage",
        "slug": "tamil-classical-heritage-contemporary-usage",
        "excerpt": "Discover the deep literary history of one of the world's oldest surviving classical languages and why mastering it unlocks deep cultural nuance.",
        "date": "Sep 2026",
        "readTime": "6 min read",
        "tag": "Tamil",
        "color": "from-red-500 to-pink-500",
        "emoji": "🌴",
        "author_name": "VartaLang Editorial",
    },
    {
        "id": "art-3",
        "title": "5 Proven Strategies for Rapid Vernacular Acquisition",
        "slug": "5-proven-strategies-for-rapid-vernacular-acquisition",
        "excerpt": "Practical insights from polyglots and educators — from spaced repetition to daily voice practice — to accelerate your language retention.",
        "date": "Aug 2026",
        "readTime": "7 min read",
        "tag": "Learning Tips",
        "color": "from-blue-500 to-cyan-500",
        "emoji": "🧠",
        "author_name": "VartaLang Editorial",
    },
]


@router.get(
    "",
    response_model=List[ArticleOut],
    summary="List all published articles and linguistic guides",
)
def list_articles(
    tag: Optional[str] = Query(None, description="Filter articles by tag"),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Article).filter(Article.is_published == True)
        if tag:
            query = query.filter(Article.tag.ilike(tag))
        articles = query.order_by(Article.created_at.desc()).all()
        if articles:
            return [
                ArticleOut(
                    id=str(a.id),
                    title=a.title,
                    slug=a.slug,
                    excerpt=a.excerpt,
                    content=a.content,
                    date=a.date_display,
                    readTime=a.read_time,
                    tag=a.tag,
                    color=a.color,
                    emoji=a.emoji,
                    author_name=a.author_name,
                )
                for a in articles
            ]
    except Exception:
        pass

    if tag:
        return [
            ArticleOut(**a) for a in DEFAULT_ARTICLES if a["tag"].lower() == tag.lower()
        ]
    return [ArticleOut(**a) for a in DEFAULT_ARTICLES]


@router.get(
    "/{slug_or_id}",
    response_model=ArticleOut,
    summary="Get article details by slug or id",
)
def get_article(
    slug_or_id: str,
    db: Session = Depends(get_db),
):
    try:
        article = (
            db.query(Article)
            .filter((Article.slug == slug_or_id) | (Article.id == slug_or_id))
            .first()
        )
        if article:
            return ArticleOut(
                id=str(article.id),
                title=article.title,
                slug=article.slug,
                excerpt=article.excerpt,
                content=article.content,
                date=article.date_display,
                readTime=article.read_time,
                tag=article.tag,
                color=article.color,
                emoji=article.emoji,
                author_name=article.author_name,
            )
    except Exception:
        pass

    # Fallback to in-memory items
    for a in DEFAULT_ARTICLES:
        if a["slug"] == slug_or_id or a["id"] == slug_or_id:
            return ArticleOut(**a)

    raise HTTPException(status_code=404, detail="Article not found")


@router.post(
    "",
    response_model=ArticleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new article (Admin / Instructor)",
)
def create_article(
    payload: ArticleCreate,
    current_user: User = Depends(require_role(["admin", "instructor"])),
    db: Session = Depends(get_db),
):
    slug = payload.slug or payload.title.lower().replace(" ", "-").replace(":", "")
    article = Article(
        title=payload.title,
        slug=slug,
        excerpt=payload.excerpt,
        content=payload.content,
        date_display=payload.date,
        read_time=payload.readTime,
        tag=payload.tag,
        color=payload.color,
        emoji=payload.emoji,
        author_name=payload.author_name or current_user.full_name,
        is_published=True,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return ArticleOut(
        id=str(article.id),
        title=article.title,
        slug=article.slug,
        excerpt=article.excerpt,
        content=article.content,
        date=article.date_display,
        readTime=article.read_time,
        tag=article.tag,
        color=article.color,
        emoji=article.emoji,
        author_name=article.author_name,
    )

