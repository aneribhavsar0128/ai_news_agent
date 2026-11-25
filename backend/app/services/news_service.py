import feedparser
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from app.config import RSS_FEEDS
from app.models import NewsArticle


def fetch_rss_news(db):
    saved_articles = []
    seen_urls = set()
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        source = feed.feed.get("title", "Unknown Source")

        for entry in feed.entries[:30]:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            summary = entry.get("summary", "")
            published_at = entry.get("published", "")

            if not title or not url:
                continue

            if url in seen_urls or title in seen_titles:
                continue

            seen_urls.add(url)
            seen_titles.add(title)

            existing = db.query(NewsArticle).filter(
                or_(
                    NewsArticle.url == url,
                    NewsArticle.title == title
                )
            ).first()

            if existing:
                continue

            article = NewsArticle(
                title=title,
                source=source,
                url=url,
                summary=summary,
                published_at=published_at
            )

            db.add(article)

            try:
                db.commit()
                db.refresh(article)
                saved_articles.append(article)
            except IntegrityError:
                db.rollback()
                continue

    return saved_articles