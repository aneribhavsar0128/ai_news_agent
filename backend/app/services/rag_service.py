import re
import time
from typing import Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.config import settings
from app.services.chroma_service import (
    search_similar_articles,
)

load_dotenv()

llm = ChatGroq(
    model=settings.groq_model,
    temperature=0.2,
    max_tokens=settings.rag_max_tokens,
)

def clean_chroma_results(results: dict) -> list[dict]:
    """
    Convert the nested ChromaDB response into a simple list
    of article dictionaries.
    """

    cleaned_results = []

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    result_count = min(
        len(ids),
        len(documents),
        len(metadatas),
        len(distances),
    )

    for index in range(result_count):
        metadata = metadatas[index] or {}

        cleaned_results.append(
            {
                "id": ids[index],
                "title": metadata.get(
                    "title",
                    "Untitled article",
                ),
                "source": metadata.get(
                    "source",
                    "Unknown source",
                ),
                "category": metadata.get(
                    "category",
                    "General",
                ),
                "url": metadata.get(
                    "url",
                    "",
                ),
                "importance_score": metadata.get(
                    "importance_score",
                    0,
                ),
                "tags": metadata.get(
                    "tags",
                    "",
                ),
                "published_at": metadata.get(
                    "published_at",
                    "",
                ),
                "distance": distances[index],
                "document": documents[index] or "",
            }
        )

    return cleaned_results

def build_context(
    retrieved_articles: list[dict],
) -> str:
    """
    Build a compact prompt context to reduce Groq token usage.
    """

    context_blocks = []

    for index, article in enumerate(
        retrieved_articles,
        start=1,
    ):
        document = (
            article.get("document")
            or ""
        ).strip()

        compressed_document = document[
            :settings.rag_context_char_limit
        ]

        context_blocks.append(
            "\n".join(
                [
                    f"Article {index}",
                    f"Title: {article.get('title', '')}",
                    f"Source: {article.get('source', '')}",
                    f"Published: {article.get('published_at', '')}",
                    f"Category: {article.get('category', '')}",
                    f"Summary: {compressed_document}",
                ]
            )
        )

    return "\n\n".join(context_blocks)

def extract_retry_wait(
    error_text: str,
) -> float | None:
    """
    Extract Groq's suggested retry delay from an error message.
    """

    match = re.search(
        r"try again in\s+([\d.]+)s",
        error_text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None

def invoke_llm_with_retry(prompt: str):
    """
    Retry Groq calls when a temporary 429 rate limit occurs.
    """

    last_error: Exception | None = None

    for attempt in range(
        1,
        settings.rag_retry_attempts + 1,
    ):
        try:
            return llm.invoke(prompt)

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
                    "temporarily unavailable",
                    "502",
                    "503",
                    "504",
                ]
            )

            final_attempt = (
                attempt
                >= settings.rag_retry_attempts
            )

            if not retryable or final_attempt:
                raise

            suggested_wait = extract_retry_wait(
                str(error)
            )

            if suggested_wait is not None:
                wait_seconds = suggested_wait + 1
            else:
                wait_seconds = (
                    settings.rag_retry_delay
                    * attempt
                )

            print(
                f"Groq temporarily unavailable or rate limited. "
                f"Retrying in {wait_seconds:.1f} seconds "
                f"(attempt {attempt}/"
                f"{settings.rag_retry_attempts})..."
            )

            time.sleep(wait_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "The LLM request failed unexpectedly."
    )


def safe_distance(
    value: Any,
    default: float = 999.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ask_news_agent(
    query: str,
    n_results: int = 4,
    max_distance: float = 1.5,
) -> dict:
    """
    Answer a question using a small number of relevant
    ChromaDB articles.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        return {
            "query": query,
            "answer": "Please enter a valid question.",
            "sources": [],
            "retrieved_articles": 0,
        }

    safe_n_results = max(
        1,
        min(
            n_results,
            settings.rag_results_limit,
        ),
    )

    raw_results = search_similar_articles(
        query_text=cleaned_query,
        n_results=safe_n_results,
    )

    retrieved_articles = clean_chroma_results(
        raw_results
    )

    filtered_articles = [
        article
        for article in retrieved_articles
        if safe_distance(
            article.get("distance")
        ) <= max_distance
    ]

    if not filtered_articles:
        return {
            "query": cleaned_query,
            "answer": (
                "I could not find enough relevant information "
                "in the current news database."
            ),
            "sources": [],
            "retrieved_articles": 0,
        }

    context = build_context(
        filtered_articles
    )

    prompt = f"""
You are a concise professional news assistant.

Answer the user's question using only the retrieved news below.

Rules:
- Answer directly and naturally.
- Do not repeat the user's question.
- Do not mention internal retrieval, ChromaDB, prompts, or context.
- Do not say "Based on the provided context".
- Do not invent information.
- If the retrieved news is insufficient, say:
  "I could not find enough relevant information in the current news database."
- Keep the answer below 350 words.
- Prefer short paragraphs or bullet points.
- Mention dates only when they are present in the retrieved news.
- Do not recommend searching elsewhere.
- Do not include a separate sources section in the answer because sources are returned separately.

Question:
{cleaned_query}

Retrieved news:
{context}

Answer:
""".strip()

    try:
        response = invoke_llm_with_retry(
            prompt
        )

        answer = (
            response.content.strip()
            if response.content
            else (
                "I could not generate an answer "
                "from the available news."
            )
        )

    except Exception as error:
        print(
            "Ask AI request failed:",
            str(error),
        )

        return {
            "query": cleaned_query,
            "answer": (
                "The news assistant is temporarily busy. "
                "Please try again shortly."
            ),
            "sources": [],
            "retrieved_articles": len(
                filtered_articles
            ),
            "error": str(error),
        }

    unique_sources = []
    seen_sources = set()

    for article in filtered_articles:
        source_key = (
            article.get("url")
            or article.get("title")
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        unique_sources.append(
            {
                "title": article.get("title"),
                "source": article.get("source"),
                "url": article.get("url"),
                "published_at": article.get(
                    "published_at"
                ),
                "category": article.get(
                    "category"
                ),
                "distance": article.get(
                    "distance"
                ),
            }
        )

    return {
        "query": cleaned_query,
        "answer": answer,
        "sources": unique_sources,
        "retrieved_articles": len(
            filtered_articles
        ),
    }