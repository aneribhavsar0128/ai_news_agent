from datetime import datetime, timedelta
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import SessionLocal
from app.models import NewsArticle
from app.services.agent_service import (
    run_processing_pipeline,
    send_daily_email_to_subscribers,
)
from app.services.news_service import fetch_rss_news

scheduler = BackgroundScheduler(
    timezone=settings.scheduler_timezone
)

PIPELINE_LOCK = Lock()


def get_recent_pending_article_ids(
    db,
    hours: int = 6,
    limit: int = 5,
) -> list[int]:
    """
    Return a limited number of recent unprocessed article IDs.

    Old historical backlog is intentionally ignored so one scheduler
    run cannot continue for a very long time.
    """

    cutoff = datetime.utcnow() - timedelta(
        hours=hours
    )

    rows = (
        db.query(NewsArticle.id)
        .filter(
            NewsArticle.importance_score == 0,
            NewsArticle.created_at >= cutoff,
        )
        .order_by(
            NewsArticle.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        row[0]
        for row in rows
    ]


def combine_article_ids(
    new_article_ids: list[int],
    pending_article_ids: list[int],
) -> list[int]:
    """
    Combine IDs while preserving order and removing duplicates.
    """

    return list(
        dict.fromkeys(
            new_article_ids
            + pending_article_ids
        )
    )


def process_selected_articles(
    db,
    article_ids: list[int],
) -> dict:
    """
    Process only one bounded batch in the current scheduler run.

    This function intentionally does not loop until the entire
    pending backlog is empty.
    """

    if not article_ids:
        print(
            "No new or recent pending articles to process.",
            flush=True,
        )

        return {
            "processed_count": 0,
            "skipped_count": 0,
            "remaining_articles": 0,
            "errors": [],
        }

    batch_size = max(
        1,
        settings.processing_batch_size,
    )

    selected_ids = article_ids[
        :batch_size
    ]

    print(
        f"Scheduler selected "
        f"{len(selected_ids)} article(s) "
        f"for this run.",
        flush=True,
    )

    result = run_processing_pipeline(
        db=db,
        batch_size=len(selected_ids),
        article_ids=selected_ids,
        max_workers=settings.processing_workers,
    )

    print(
        "Scheduler batch completed:",
        {
            "processed": result.get(
                "processed_count",
                0,
            ),
            "skipped": result.get(
                "skipped_count",
                0,
            ),
            "remaining_in_selected_batch": result.get(
                "remaining_articles",
                0,
            ),
            "errors": len(
                result.get(
                    "errors",
                    [],
                )
            ),
        },
        flush=True,
    )

    return result


def fetch_and_process_news(db) -> dict:
    """
    Fetch new RSS articles and process one small batch.

    Priority:
    1. Newly inserted articles.
    2. Recent pending articles from failed runs.
    """

    new_articles = fetch_rss_news(db)

    new_article_ids = [
        article.id
        for article in new_articles
        if article.id is not None
    ]

    pending_article_ids = (
        get_recent_pending_article_ids(
            db=db,
            hours=6,
            limit=settings.processing_batch_size,
        )
    )

    article_ids = combine_article_ids(
        new_article_ids,
        pending_article_ids,
    )

    print(
        f"New RSS articles inserted: "
        f"{len(new_article_ids)}",
        flush=True,
    )

    print(
        f"Recent pending articles found: "
        f"{len(pending_article_ids)}",
        flush=True,
    )

    print(
        f"Total candidate articles: "
        f"{len(article_ids)}",
        flush=True,
    )

    processing_result = (
        process_selected_articles(
            db=db,
            article_ids=article_ids,
        )
    )

    return {
        "new_articles": len(
            new_article_ids
        ),
        "recent_pending": len(
            pending_article_ids
        ),
        "candidate_articles": len(
            article_ids
        ),
        "selected_for_processing": min(
            len(article_ids),
            settings.processing_batch_size,
        ),
        "processed": processing_result.get(
            "processed_count",
            0,
        ),
        "skipped": processing_result.get(
            "skipped_count",
            0,
        ),
        "remaining_in_selected_batch": (
            processing_result.get(
                "remaining_articles",
                0,
            )
        ),
        "errors": processing_result.get(
            "errors",
            [],
        ),
    }


def refresh_news_job():
    """
    Fetch and process one small batch of fresh news.

    Runs:
    - shortly after server startup
    - every 30 minutes while the server is running

    This job does not generate or send emails.
    """

    if not PIPELINE_LOCK.acquire(
        blocking=False
    ):
        print(
            "News refresh skipped because another "
            "pipeline job is already running.",
            flush=True,
        )
        return

    db = SessionLocal()

    try:
        print("=" * 60)
        print(
            "Starting automatic news refresh",
            flush=True,
        )

        result = fetch_and_process_news(
            db
        )

        try:
            from app.services.brief_service import generate_daily_brief
            brief_result = generate_daily_brief(db)
            print("Automatic daily brief updated:", brief_result.get("message"), flush=True)
        except Exception as brief_error:
            print("Daily brief auto-generation note:", f"{type(brief_error).__name__}: {brief_error}", flush=True)

        print(
            "News refresh completed:",
            {
                "new_articles": result[
                    "new_articles"
                ],
                "recent_pending": result[
                    "recent_pending"
                ],
                "candidates": result[
                    "candidate_articles"
                ],
                "selected": result[
                    "selected_for_processing"
                ],
                "processed": result[
                    "processed"
                ],
                "skipped": result[
                    "skipped"
                ],
                "errors": len(
                    result["errors"]
                ),
            },
            flush=True,
        )

        print("=" * 60)

    except Exception as error:
        db.rollback()

        print(
            "Automatic news refresh failed:",
            f"{type(error).__name__}: {error}",
            flush=True,
        )

    finally:
        db.close()
        PIPELINE_LOCK.release()


def daily_email_job():
    """
    Complete daily subscriber workflow:

    1. Fetch latest RSS articles.
    2. Process one small article batch.
    3. Generate one daily brief.
    4. Send it separately to all active subscribers.

    The daily email does not wait for the complete backlog.
    It uses the recent articles that have already been processed.
    """

    if not PIPELINE_LOCK.acquire(
        blocking=False
    ):
        print(
            "Daily email job skipped because another "
            "pipeline job is already running.",
            flush=True,
        )
        return

    db = SessionLocal()

    try:
        print("=" * 60)
        print(
            "Starting daily subscriber email pipeline",
            flush=True,
        )

        processing_result = (
            fetch_and_process_news(db)
        )

        print(
            "Daily news processing completed:",
            {
                "new_articles": (
                    processing_result[
                        "new_articles"
                    ]
                ),
                "selected": (
                    processing_result[
                        "selected_for_processing"
                    ]
                ),
                "processed": (
                    processing_result[
                        "processed"
                    ]
                ),
                "skipped": (
                    processing_result[
                        "skipped"
                    ]
                ),
                "errors": len(
                    processing_result[
                        "errors"
                    ]
                ),
            },
            flush=True,
        )

        email_result = (
            send_daily_email_to_subscribers(
                db
            )
        )

        print(
            "Subscriber email result:",
            {
                "success": email_result.get(
                    "success",
                    False,
                ),
                "subscribers": email_result.get(
                    "subscriber_count",
                    0,
                ),
                "sent": email_result.get(
                    "sent",
                    0,
                ),
                "failed": email_result.get(
                    "failed",
                    0,
                ),
                "errors": len(
                    email_result.get(
                        "errors",
                        [],
                    )
                ),
            },
            flush=True,
        )

        print(
            "Daily subscriber email pipeline "
            "completed.",
            flush=True,
        )

        print("=" * 60)

    except Exception as error:
        db.rollback()

        print(
            "Daily subscriber email pipeline failed:",
            f"{type(error).__name__}: {error}",
            flush=True,
        )

    finally:
        db.close()
        PIPELINE_LOCK.release()


# Keep this alias because main.py imports daily_news_job.
daily_news_job = daily_email_job


def start_scheduler():
    """
    Start:
    - one delayed startup refresh
    - a refresh every 30 minutes
    - the daily subscriber email
    """

    if scheduler.running:
        print(
            "Scheduler is already running.",
            flush=True,
        )
        return

    scheduler.add_job(
        refresh_news_job,
        IntervalTrigger(
            minutes=30,
            timezone=(
                settings.scheduler_timezone
            ),
        ),
        id="periodic_news_refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=900,
    )

    scheduler.add_job(
        daily_email_job,
        CronTrigger(
            hour=settings.scheduler_hour,
            minute=settings.scheduler_minute,
            timezone=(
                settings.scheduler_timezone
            ),
        ),
        id="daily_subscriber_email",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=(
            settings.scheduler_misfire_grace_time
        ),
    )

    scheduler.start()

    print(
        "Scheduler started successfully.",
        flush=True,
    )

    print(
        "News refresh will run every 30 minutes.",
        flush=True,
    )

    print(
        "Each refresh will process at most "
        f"{settings.processing_batch_size} article(s).",
        flush=True,
    )

    print(
        "Daily subscriber email will run at "
        f"{settings.scheduler_hour:02d}:"
        f"{settings.scheduler_minute:02d} "
        f"{settings.scheduler_timezone}.",
        flush=True,
    )

    scheduler.add_job(
        refresh_news_job,
        trigger="date",
        run_date=(
            datetime.now()
            + timedelta(seconds=10)
        ),
        id="startup_news_refresh",
        replace_existing=True,
        misfire_grace_time=300,
    )

    print(
        "Startup news refresh scheduled "
        "for 10 seconds after startup.",
        flush=True,
    )