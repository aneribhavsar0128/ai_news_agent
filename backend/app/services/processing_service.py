import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from typing import Any, Optional

from app.agent.graph import news_graph
from app.database import SessionLocal
from app.models import NewsArticle
from app.services.chroma_service import (
    search_similar_articles,
    store_article_embedding,
)

WRITE_LOCK = Lock()

def get_related_context(
    article: NewsArticle,
    max_distance: float = 1.8,
) -> str:
    """
    Retrieve a small amount of related historical context
    from ChromaDB.
    """

    query_text = (
        f"{article.title}\n"
        f"{article.summary or ''}"
    )

    results = search_similar_articles(
        query_text=query_text,
        n_results=5,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    timeline_points = []

    result_count = min(
        len(documents),
        len(metadatas),
        len(distances),
    )

    for index in range(result_count):
        distance = distances[index]

        if distance is None:
            continue

        try:
            distance_value = float(distance)
        except (TypeError, ValueError):
            continue

        if distance_value > max_distance:
            continue

        metadata = metadatas[index] or {}
        document = documents[index] or ""

        # Keep context compact to reduce Groq token usage.
        short_content = document[:220]

        timeline_points.append(
            "\n".join(
                [
                    f"- Title: {metadata.get('title', '')}",
                    f"  Source: {metadata.get('source', '')}",
                    f"  Published: {metadata.get('published_at', '')}",
                    f"  Context: {short_content}",
                ]
            )
        )

    if not timeline_points:
        return "No relevant historical context found."

    return (
        "Related historical news:\n\n"
        + "\n\n".join(timeline_points)
    )


def safe_integer(
    value: Any,
    default: int = 5,
    minimum: int = 1,
    maximum: int = 10,
) -> int:
    """
    Convert the LLM importance score safely.
    """

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        parsed_value = default

    return max(
        minimum,
        min(maximum, parsed_value),
    )


def safe_boolean(value: Any) -> bool:
    """
    Convert common string values returned by the LLM
    into a proper boolean.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "yes",
            "1",
            "y",
        }

    return bool(value)


def extract_retry_wait(
    error_message: str,
) -> Optional[float]:
    """
    Extract Groq's suggested retry time from an error such as:

    Please try again in 14.16s
    """

    match = re.search(
        r"try again in\s+([\d.]+)s",
        error_message,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def invoke_news_graph_with_retry(
    payload: dict,
    max_attempts: int = 3,
) -> dict:
    """
    Retry temporary Groq errors and rate limits.
    """

    last_error: Optional[Exception] = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            return news_graph.invoke(payload)

        except Exception as error:
            last_error = error
            error_text = str(error).lower()

            retryable = any(
                marker in error_text
                for marker in [
                    "429",
                    "rate limit",
                    "rate_limit",
                    "timeout",
                    "timed out",
                    "temporarily unavailable",
                    "connection",
                    "502",
                    "503",
                    "504",
                ]
            )

            final_attempt = (
                attempt >= max_attempts
            )

            if not retryable or final_attempt:
                raise

            suggested_wait = extract_retry_wait(
                str(error)
            )

            if suggested_wait is not None:
                wait_seconds = suggested_wait + 1
            else:
                wait_seconds = 10 * attempt

            print(
                f"Temporary LLM error. "
                f"Retrying in {wait_seconds:.1f} seconds "
                f"(attempt {attempt}/{max_attempts})...",
                flush=True,
            )

            time.sleep(wait_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "LLM processing failed unexpectedly."
    )


def update_article_from_result(
    article: NewsArticle,
    data: dict,
) -> None:
    """
    Save the LangGraph result into the NewsArticle model.
    """

    article.category = (
        data.get("category")
        or "Other"
    )

    article.summary = (
        data.get("summary")
        or article.summary
        or ""
    )

    article.importance_score = safe_integer(
        data.get("importance_score"),
        default=5,
    )

    article.why_it_matters = (
        data.get("why_it_matters")
        or ""
    )

    article.who_is_affected = (
        data.get("who_is_affected")
        or ""
    )

    article.future_impact = (
        data.get("future_impact")
        or ""
    )

    historical_context = data.get(
        "historical_context",
        [],
    )

    if isinstance(historical_context, list):
        article.historical_context = json.dumps(
            historical_context,
            ensure_ascii=False,
        )
    else:
        article.historical_context = str(
            historical_context or ""
        )

    article.trend_analysis = (
        data.get("trend_analysis")
        or ""
    )

    article.email_reason = (
        data.get("email_reason")
        or ""
    )

    tags = data.get("tags", [])

    if isinstance(tags, list):
        article.tags = ",".join(
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        )
    else:
        article.tags = str(tags or "")

    article.estimated_read_time = (
        data.get("estimated_read_time")
        or "45 sec"
    )

    article.should_email = safe_boolean(
        data.get("should_email", False)
    )

    article.processed_at = datetime.utcnow()


def process_single_article(
    article_id: int,
) -> dict:
    """
    Process one article using its own SQLAlchemy session.

    SQLAlchemy sessions must not be shared between threads.
    """

    worker_db = SessionLocal()
    article: Optional[NewsArticle] = None

    try:
        article = (
            worker_db.query(NewsArticle)
            .filter(
                NewsArticle.id == article_id
            )
            .first()
        )

        if article is None:
            return {
                "success": False,
                "article_id": article_id,
                "title": "",
                "error": "Article not found.",
            }

        # Skip articles that another run has already processed.
        if article.importance_score != 0:
            return {
                "success": True,
                "skipped": True,
                "article_id": article.id,
                "title": article.title,
            }

        print(
            f"Processing article {article.id}: "
            f"{article.title}",
            flush=True,
        )

        related_context = get_related_context(
            article
        )

        print(
            f"Article {article.id}: "
            f"related context retrieved",
            flush=True,
        )

        # IMPORTANT:
        # Your LangGraph node expects state["query"].
        payload = {
                "query": (
                    "Analyze the following news article and "
                    "return the required structured result."
                ),
                "title": article.title,
                "source": article.source,
                "summary": article.summary or "",
                "related_context": related_context,
                "result": {},
        }

        result = invoke_news_graph_with_retry(
            payload=payload,
            max_attempts=3,
        )

        print(
            f"Article {article.id}: LLM completed",
            flush=True,
        )

        data = result.get("result", {})

        if not isinstance(data, dict):
            raise ValueError(
                "LangGraph result must contain a dictionary "
                "under the 'result' key."
            )

        update_article_from_result(
            article=article,
            data=data,
        )

        # LLM calls can run concurrently, but database and
        # ChromaDB writes are kept one at a time.
        with WRITE_LOCK:
            embedding_id = (
                store_article_embedding(article)
            )

            article.embedding_id = embedding_id

            worker_db.commit()

        print(
            f"Article {article.id}: stored in SQL "
            f"and ChromaDB",
            flush=True,
        )

        return {
            "success": True,
            "skipped": False,
            "article_id": article.id,
            "title": article.title,
        }

    except Exception as error:
        worker_db.rollback()

        title = (
            article.title
            if article is not None
            else ""
        )

        print(
            f"Article {article_id} failed: "
            f"{type(error).__name__}: {error}",
            flush=True,
        )

        return {
            "success": False,
            "article_id": article_id,
            "title": title,
            "error": (
                f"{type(error).__name__}: "
                f"{str(error)}"
            ),
        }

    finally:
        worker_db.close()


def get_pipeline_counts(
    db,
) -> dict:
    """
    Return common processing statistics.
    """

    high_priority_articles = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.importance_score >= 7
        )
        .count()
    )

    emails_to_send = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.should_email.is_(True),
            NewsArticle.sent_email.is_(False),
        )
        .count()
    )

    return {
        "high_priority_articles": (
            high_priority_articles
        ),
        "emails_to_send": emails_to_send,
    }


def process_news_batch(
    db,
    batch_size: int = 10,
    article_ids: Optional[list[int]] = None,
    max_workers: int = 1,
) -> dict:
    """
    Process articles concurrently.

    When article_ids is supplied, process only those newly
    fetched articles.

    max_workers defaults to 1 because the current Groq account
    has a low tokens-per-minute limit. Increase it only after
    confirming that rate limits are not being reached.
    """

    safe_batch_size = max(
        1,
        min(batch_size, 50),
    )

    safe_workers = max(
        1,
        min(max_workers, 2),
    )

    query = db.query(NewsArticle).filter(
        NewsArticle.importance_score == 0
    )

    if article_ids is not None:
        if not article_ids:
            counts = get_pipeline_counts(db)

            return {
                "message": "No new articles to process",
                "processed_count": 0,
                "skipped_count": 0,
                "remaining_articles": 0,
                "high_priority_articles": counts[
                    "high_priority_articles"
                ],
                "emails_to_send": counts[
                    "emails_to_send"
                ],
                "errors": [],
            }

        query = query.filter(
            NewsArticle.id.in_(article_ids)
        )

    selected_ids = [
        row[0]
        for row in (
            query.with_entities(NewsArticle.id)
            .order_by(
                NewsArticle.created_at.desc()
            )
            .limit(safe_batch_size)
            .all()
        )
    ]

    if not selected_ids:
        counts = get_pipeline_counts(db)

        return {
            "message": "No pending articles to process",
            "processed_count": 0,
            "skipped_count": 0,
            "remaining_articles": 0,
            "high_priority_articles": counts[
                "high_priority_articles"
            ],
            "emails_to_send": counts[
                "emails_to_send"
            ],
            "errors": [],
        }

    print(
        f"Starting article processing: "
        f"{len(selected_ids)} articles, "
        f"{safe_workers} worker(s)",
        flush=True,
    )

    processed_count = 0
    skipped_count = 0
    errors = []

    with ThreadPoolExecutor(
        max_workers=safe_workers,
        thread_name_prefix="news-worker",
    ) as executor:
        future_to_article_id = {
            executor.submit(
                process_single_article,
                article_id,
            ): article_id
            for article_id in selected_ids
        }

        for future in as_completed(
            future_to_article_id
        ):
            article_id = (
                future_to_article_id[future]
            )

            try:
                result = future.result()

            except Exception as error:
                errors.append(
                    {
                        "article_id": article_id,
                        "title": "",
                        "error": (
                            f"{type(error).__name__}: "
                            f"{str(error)}"
                        ),
                    }
                )
                continue

            if result.get("success"):
                if result.get("skipped"):
                    skipped_count += 1
                else:
                    processed_count += 1
            else:
                errors.append(
                    {
                        "article_id": result.get(
                            "article_id",
                            article_id,
                        ),
                        "title": result.get(
                            "title",
                            "",
                        ),
                        "error": result.get(
                            "error",
                            "Unknown processing error.",
                        ),
                    }
                )

    # Refresh parent session state after worker commits.
    db.expire_all()

    remaining_query = db.query(
        NewsArticle
    ).filter(
        NewsArticle.importance_score == 0
    )

    if article_ids is not None:
        remaining_query = (
            remaining_query.filter(
                NewsArticle.id.in_(article_ids)
            )
        )

    remaining_articles = (
        remaining_query.count()
    )

    counts = get_pipeline_counts(db)

    return {
        "message": "News processing completed",
        "processed_count": processed_count,
        "skipped_count": skipped_count,
        "workers_used": safe_workers,
        "remaining_articles": remaining_articles,
        "high_priority_articles": counts[
            "high_priority_articles"
        ],
        "emails_to_send": counts[
            "emails_to_send"
        ],
        "errors": errors,
    }