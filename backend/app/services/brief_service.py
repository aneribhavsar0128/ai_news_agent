import json
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.config import settings
from app.models import DailyBrief, NewsArticle
from app.services.editor_service import build_editor_brief
from app.services.email_template_service import generate_email_html


load_dotenv()

llm = ChatGroq(
    model=settings.groq_model,
    temperature=0.1,
    max_tokens=600,
)

def generate_llm_summary(
    articles: list[NewsArticle],
) -> str:
    """
    Generate a concise summary from the most important articles.
    """

    if not articles:
        return (
            "No significant processed news was available "
            "for today's briefing."
        )

    context_lines = []

    for article in articles[:15]:
        context_lines.append(
            (
                f"- {article.title} | "
                f"Category: {article.category or 'Other'} | "
                f"Importance: {article.importance_score}"
            )
        )

    prompt = f"""
You are a professional news editor.

Using only the headlines below, write one concise executive summary
of today's important news.

Requirements:
- Keep it below 180 words.
- Mention the most important developments first.
- Cover India, world affairs, technology, business, or science only
  when supported by the headlines.
- Do not invent facts.
- Do not include headings such as "Executive Summary".
- Do not include markdown.
- Do not repeat every headline individually.

Headlines:
{chr(10).join(context_lines)}
""".strip()

    try:
        response = llm.invoke(prompt)

        summary = (
            response.content.strip()
            if response.content
            else ""
        )

        if summary:
            return summary

    except Exception as error:
        print(
            "Daily brief summary generation failed:",
            f"{type(error).__name__}: {error}",
            flush=True,
        )

    return (
        "Today's briefing covers important developments "
        "across India, world affairs, technology, business, "
        "and public interest news."
    )


def generate_daily_brief(db) -> dict:
    """
    Build, save, and return today's daily brief.

    Articles are selected from the last 24 hours and must already
    have completed AI processing.
    """

    today = date.today()
    cutoff_time = datetime.utcnow() - timedelta(
        hours=24
    )

    articles = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.processed_at.isnot(None),
            NewsArticle.importance_score >= 6,
            NewsArticle.processed_at >= cutoff_time,
        )
        .order_by(
            NewsArticle.importance_score.desc(),
            NewsArticle.processed_at.desc(),
        )
        .limit(40)
        .all()
    )

    if not articles:
        cutoff_48h = datetime.utcnow() - timedelta(hours=48)
        articles = (
            db.query(NewsArticle)
            .filter(
                NewsArticle.processed_at.isnot(None),
                NewsArticle.importance_score >= 5,
                NewsArticle.processed_at >= cutoff_48h,
            )
            .order_by(
                NewsArticle.importance_score.desc(),
                NewsArticle.processed_at.desc(),
            )
            .limit(40)
            .all()
        )

    if not articles:
        articles = (
            db.query(NewsArticle)
            .filter(
                NewsArticle.processed_at.isnot(None),
                NewsArticle.importance_score > 0,
            )
            .order_by(
                NewsArticle.created_at.desc(),
                NewsArticle.importance_score.desc(),
            )
            .limit(40)
            .all()
        )

    if not articles:
        return {
            "message": (
                "No processed articles "
                "were found for today's briefing."
            ),
            "articles_used": 0,
            "brief": None,
        }

    grouped = build_editor_brief(
        articles
    )

    brief = {
        "title": "Daily News Brief",
        "date": today.isoformat(),
        "summary": generate_llm_summary(
            articles
        ),
        "top_stories": grouped.get(
            "top_stories",
            [],
        ),
        "india": grouped.get(
            "india",
            [],
        ),
        "world": grouped.get(
            "world",
            [],
        ),
        "technology_ai": grouped.get(
            "technology_ai",
            [],
        ),
        "business": grouped.get(
            "business",
            [],
        ),
        "health_science": grouped.get(
            "health_science",
            [],
        ),
        "key_trends": [
            (
                "High-impact developments span public affairs, "
                "technology, business, and international news."
            ),
            (
                "Technology and AI continue to influence policy, "
                "industry, and markets."
            ),
            (
                "Several major stories may produce follow-up "
                "developments during the coming days."
            ),
        ],
        "what_to_watch_next": [
            (
                "Watch for updates on the highest-priority "
                "India, world, and business stories."
            ),
            (
                "Track regulatory and market reactions to major "
                "technology and AI developments."
            ),
        ],
    }

    html_content = generate_email_html(
        brief
    )

    json_content = json.dumps(
        brief,
        ensure_ascii=False,
    )

    existing_brief = (
        db.query(DailyBrief)
        .filter(
            DailyBrief.date == today
        )
        .first()
    )

    try:
        if existing_brief:
            existing_brief.html = (
                html_content
            )

            existing_brief.json = (
                json_content
            )

            existing_brief.articles_used = (
                len(articles)
            )

        else:
            daily_brief = DailyBrief(
                date=today,
                html=html_content,
                json=json_content,
                articles_used=len(articles),
            )

            db.add(daily_brief)

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": (
            "Daily brief generated successfully"
        ),
        "articles_used": len(articles),
        "brief": brief,
    }