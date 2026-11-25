import json
import re
import time
from typing import Any, TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from app.agent.prompts import NEWS_AGENT_PROMPT
from app.config import settings


load_dotenv()

llm = ChatGroq(
    model=settings.groq_model,
    temperature=0,
    max_tokens=2500,
    model_kwargs={
        "response_format": {
            "type": "json_object"
        }
    },
)

class NewsState(TypedDict, total=False):
    query: str
    title: str
    source: str
    summary: str
    related_context: str
    result: dict[str, Any]

def extract_retry_seconds(
    error_message: str,
) -> float | None:
    """
    Extract Groq's recommended retry time from a 429 error.
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


def invoke_llm_with_retry(
    prompt: str,
    max_attempts: int = 3,
):
    """
    Retry temporary Groq rate-limit and connection errors.
    """
    last_error = None

    for attempt in range(
        1,
        max_attempts + 1,
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
                    "timed out",
                    "temporarily unavailable",
                    "connection",
                    "502",
                    "503",
                    "504",
                ]
            )

            if (
                not retryable
                or attempt >= max_attempts
            ):
                raise

            suggested_wait = extract_retry_seconds(
                str(error)
            )

            if suggested_wait is not None:
                wait_seconds = suggested_wait + 1
            else:
                wait_seconds = 10 * attempt

            print(
                f"Graph LLM temporarily unavailable. "
                f"Retrying in {wait_seconds:.1f} seconds "
                f"(attempt {attempt}/{max_attempts})...",
                flush=True,
            )

            time.sleep(wait_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "News analysis LLM failed unexpectedly."
    )


def extract_json_object(
    response_text: str,
) -> dict[str, Any]:
    """
    Parse JSON even when the model wraps it in markdown fences.
    """

    cleaned_text = response_text.strip()

    cleaned_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned_text,
        flags=re.IGNORECASE,
    )

    cleaned_text = re.sub(
        r"\s*```$",
        "",
        cleaned_text,
    )

    try:
        parsed = json.loads(cleaned_text)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # Attempt to extract the first complete-looking JSON object.
    start_index = cleaned_text.find("{")
    end_index = cleaned_text.rfind("}")

    if (
        start_index != -1
        and end_index != -1
        and end_index > start_index
    ):
        candidate = cleaned_text[
            start_index : end_index + 1
        ]

        parsed = json.loads(candidate)

        if isinstance(parsed, dict):
            return parsed

    raise ValueError(
        "The LLM response did not contain valid JSON."
    )


def get_fallback_result(
    state: NewsState,
) -> dict[str, Any]:
    """
    Return a safe fallback result when parsing fails.
    """

    summary = state.get("summary", "")

    return {
        "category": "Other",
        "summary": summary[:500],
        "historical_context": [],
        "trend_analysis": (
            "Trend analysis could not be completed."
        ),
        "importance_score": 5,
        "why_it_matters": (
            "The significance of this article "
            "could not be analyzed reliably."
        ),
        "who_is_affected": "General readers",
        "future_impact": "Unknown",
        "tags": [],
        "estimated_read_time": "45 sec",
        "should_email": False,
        "email_reason": (
            "The article was processed with low confidence."
        ),
    }


def analyze_news(
    state: NewsState,
) -> dict[str, Any]:
    """
    Analyze one news article and return structured JSON.
    """

    title = state.get("title", "")
    source = state.get("source", "")
    summary = state.get("summary", "")
    related_context = state.get(
        "related_context",
        "No relevant historical context found.",
    )

    query = state.get(
        "query",
        (
            "Analyze this news article, classify it, "
            "score its importance, and explain its impact."
        ),
    )

    prompt = NEWS_AGENT_PROMPT.format(
    query=query,
    title=title,
    source=source,
    summary=summary,
    context=related_context,
    related_context=related_context,
)
    try:
        response = invoke_llm_with_retry(
            prompt=prompt,
            max_attempts=3,
        )

        result = extract_json_object(
            response.content
        )

    except Exception as error:
        print(
            f"News graph analysis failed for "
            f"'{title}': {type(error).__name__}: {error}",
            flush=True,
        )

        result = get_fallback_result(state)

    return {
        "result": result
    }


graph_builder = StateGraph(NewsState)

graph_builder.add_node(
    "analyze_news",
    analyze_news,
)

graph_builder.set_entry_point(
    "analyze_news"
)

graph_builder.add_edge(
    "analyze_news",
    END,
)

news_graph = graph_builder.compile()