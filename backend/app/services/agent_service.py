from app.services.news_service import fetch_rss_news
from app.services.processing_service import process_news_batch
from app.services.rag_service import ask_news_agent
from app.services.chroma_service import get_collection_count
from app.services.brief_service import generate_daily_brief
from app.services.email_template_service import generate_email_html
from app.services.email_service import EmailService
from app.services.subscriber_service import get_active_subscribers


def run_fetch_pipeline(db):
    articles = fetch_rss_news(db)

    return {
        "message": "News fetched successfully",
        "new_articles_count": len(articles),
    }

def run_processing_pipeline(
    db,
    batch_size=5,
    article_ids=None,
    max_workers=2,
):
    return process_news_batch(
        db=db,
        batch_size=batch_size,
        article_ids=article_ids,
        max_workers=max_workers,
    )

def run_full_pipeline(
    db,
    batch_size=5,
):
    fetched_articles = fetch_rss_news(db)

    article_ids = [
        article.id
        for article in fetched_articles
        if article.id is not None
    ]

    processing_result = process_news_batch(
        db=db,
        batch_size=batch_size,
        article_ids=article_ids,
        max_workers=1,
    )

    return {
        "message": "Full pipeline completed",
        "fetched_articles": len(fetched_articles),
        "processing": processing_result,
        "chroma_documents": get_collection_count(),
    }


def run_rag_query(
    query: str,
    n_results: int = 4,
    max_distance: float = 1.5,
):
    return ask_news_agent(
        query=query,
        n_results=n_results,
        max_distance=max_distance,
    )

def run_daily_brief(db):
    return generate_daily_brief(db)


def preview_daily_email(db):
    """
    Generate today's briefing and convert it into HTML.
    """

    brief_result = generate_daily_brief(db)

    brief = brief_result.get("brief")

    if not brief:
        return None

    return generate_email_html(brief)


def send_daily_email(db):
    """
    Send the current daily brief to the single recipient
    configured in the environment.

    Keep this only if you still use the old test endpoint.
    """

    import os

    recipient = os.getenv("RECIPIENT_EMAIL")

    if not recipient:
        return {
            "success": False,
            "message": "RECIPIENT_EMAIL is missing in .env",
        }

    brief_result = generate_daily_brief(db)
    brief = brief_result.get("brief")

    if not brief:
        return {
            "success": False,
            "message": "No daily brief available.",
        }

    html_content = generate_email_html(brief)

    subject = (
        f"Daily News Brief — "
        f"{brief.get('date', '')}"
    )

    service = EmailService()

    return service.send_html_email(
        recipient=recipient,
        subject=subject,
        html_content=html_content,
    )


def send_daily_email_to_subscribers(db):
    brief_result = generate_daily_brief(db)
    brief = brief_result.get("brief")

    if not brief:
        return {
            "success": False,
            "message": "No daily brief available.",
            "subscriber_count": 0,
            "sent": 0,
            "failed": 0,
            "sent_to": [],
            "errors": [],
        }

    subscribers = get_active_subscribers(db)

    if not subscribers:
        return {
            "success": False,
            "message": "No active subscribers found.",
            "subscriber_count": 0,
            "sent": 0,
            "failed": 0,
            "sent_to": [],
            "errors": [],
        }

    html_content = generate_email_html(brief)

    subject = (
        f"Daily News Brief — "
        f"{brief.get('date', '')}"
    )

    email_service = EmailService()

    sent_to = []
    errors = []

    for subscriber in subscribers:
        try:
            result = email_service.send_html_email(
                recipient=subscriber.email,
                subject=subject,
                html_content=html_content,
            )

            if result.get("success"):
                sent_to.append(subscriber.email)

                print(
                    f"Email sent successfully to "
                    f"{subscriber.email}",
                    flush=True,
                )
            else:
                errors.append(
                    {
                        "subscriber_id": subscriber.id,
                        "email": subscriber.email,
                        "error": result.get(
                            "message",
                            "Unknown SMTP error.",
                        ),
                    }
                )

                print(
                    f"Email failed for "
                    f"{subscriber.email}: "
                    f"{result.get('message')}",
                    flush=True,
                )

        except Exception as error:
            errors.append(
                {
                    "subscriber_id": subscriber.id,
                    "email": subscriber.email,
                    "error": str(error),
                }
            )

            print(
                f"Email exception for "
                f"{subscriber.email}: {error}",
                flush=True,
            )

    return {
        "success": len(sent_to) > 0,
        "message": "Subscriber email delivery completed.",
        "subscriber_count": len(subscribers),
        "sent": len(sent_to),
        "failed": len(errors),
        "sent_to": sent_to,
        "errors": errors,
    }