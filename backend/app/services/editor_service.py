import re
from datetime import datetime
from typing import Iterable

from app.models import NewsArticle


SECTION_LIMITS = {
    "top_stories": 8,
    "india": 8,
    "world": 8,
    "technology_ai": 6,
    "business": 6,
    "health_science": 4,
}

TOTAL_BRIEF_LIMIT = sum(
    SECTION_LIMITS.values()
)


def normalize_text(
    value,
) -> str:
    """
    Normalize any value for keyword matching.
    """

    return re.sub(
        r"\s+",
        " ",
        str(value or "").lower(),
    ).strip()


def serialize_date_value(
    value,
) -> str | None:
    """
    Convert datetime, date, string, or any other date-like
    value into a frontend-safe string.
    """

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)


def date_sort_value(
    value,
) -> float:
    """
    Convert datetime or string date values into a sortable
    timestamp.

    Invalid or missing values receive the lowest priority.
    """

    if value is None:
        return 0.0

    if isinstance(value, datetime):
        return value.timestamp()

    if hasattr(value, "timestamp"):
        try:
            return float(value.timestamp())
        except Exception:
            pass

    value_text = str(value).strip()

    if not value_text:
        return 0.0

    # Handle ISO timestamps ending in Z.
    normalized_value = value_text.replace(
        "Z",
        "+00:00",
    )

    try:
        return datetime.fromisoformat(
            normalized_value
        ).timestamp()
    except (ValueError, TypeError):
        pass

    common_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
    ]

    for date_format in common_formats:
        try:
            return datetime.strptime(
                value_text,
                date_format,
            ).timestamp()
        except (ValueError, TypeError):
            continue

    return 0.0


def article_to_card(
    article: NewsArticle,
) -> dict:
    """
    Convert a NewsArticle row into the structure required
    by the frontend and email template.
    """

    published_at = serialize_date_value(
        getattr(
            article,
            "published_at",
            None,
        )
    )

    processed_at = serialize_date_value(
        getattr(
            article,
            "processed_at",
            None,
        )
    )

    created_at = serialize_date_value(
        getattr(
            article,
            "created_at",
            None,
        )
    )

    return {
        "id": article.id,
        "headline": article.title,
        "title": article.title,
        "source": article.source,
        "category": article.category,
        "importance_score": (
            article.importance_score or 0
        ),
        "summary": (
            article.summary or ""
        )[:350],
        "why_it_matters": (
            article.why_it_matters or ""
        ),
        "who_is_affected": (
            article.who_is_affected or ""
        ),
        "future_impact": (
            article.future_impact or ""
        ),
        "tags": article.tags or "",
        "published_at": published_at,
        "processed_at": processed_at,
        "created_at": created_at,
        "estimated_read_time": (
            article.estimated_read_time
            or "45 sec"
        ),
        "url": article.url,
    }


def has_word(
    text: str,
    words: Iterable[str],
) -> bool:
    """
    Match complete words and phrases.

    Multi-word phrases use substring matching.
    Single words use word boundaries.
    """

    normalized_text = normalize_text(text)

    for word in words:
        normalized_word = normalize_text(
            word
        )

        if not normalized_word:
            continue

        if " " in normalized_word:
            if normalized_word in normalized_text:
                return True

        elif re.search(
            rf"\b{re.escape(normalized_word)}\b",
            normalized_text,
        ):
            return True

    return False


def normalize_category(
    category,
) -> str | None:
    """
    Convert AI-generated categories into one of the
    frontend brief sections.
    """

    value = normalize_text(category)

    if not value:
        return None

    mapping = {
        "technology_ai": "technology_ai",
        "technology ai": "technology_ai",
        "technology & ai": "technology_ai",
        "ai & technology": "technology_ai",
        "ai and technology": "technology_ai",
        "artificial intelligence": "technology_ai",
        "technology": "technology_ai",
        "tech": "technology_ai",
        "ai": "technology_ai",

        "business": "business",
        "finance": "business",
        "financial": "business",
        "markets": "business",
        "market": "business",
        "economy": "business",
        "economic": "business",

        "india": "india",
        "national": "india",
        "indian": "india",

        "world": "world",
        "international": "world",
        "global": "world",
        "politics": "world",
        "sports": "world",
        "entertainment": "world",
        "other": "world",

        "health_science": "health_science",
        "health science": "health_science",
        "health & science": "health_science",
        "health and science": "health_science",
        "health": "health_science",
        "science": "health_science",
        "climate": "health_science",
        "environment": "health_science",
    }

    if value in mapping:
        return mapping[value]

    for category_name, section in mapping.items():
        if category_name in value:
            return section

    return None


def detect_section(
    article: NewsArticle,
) -> str:
    """
    Detect the best editorial section.

    Priority:
    1. AI-generated category
    2. Article content keywords
    3. Specialist source hints
    4. Default to world
    """

    normalized_section = normalize_category(
        article.category
    )

    if normalized_section:
        return normalized_section

    source = normalize_text(
        article.source
    )

    text = " ".join(
        [
            normalize_text(article.category),
            normalize_text(article.tags),
            normalize_text(article.title),
            normalize_text(article.summary),
        ]
    )

    # Health and science
    if has_word(
        text,
        [
            "health",
            "healthcare",
            "medical",
            "medicine",
            "hospital",
            "disease",
            "virus",
            "vaccine",
            "science",
            "scientific",
            "climate",
            "heatwave",
            "weather",
            "temperature",
            "environment",
            "pollution",
            "space",
            "astronomy",
            "nasa",
            "isro",
            "who",
            "nih",
            "research",
            "researchers",
            "biology",
            "energy security",
            "biogas",
        ],
    ):
        return "health_science"

    # AI and technology
    if has_word(
        text,
        [
            "ai",
            "artificial intelligence",
            "generative ai",
            "openai",
            "anthropic",
            "chatgpt",
            "claude",
            "gemini",
            "llm",
            "large language model",
            "machine learning",
            "deep learning",
            "nvidia",
            "robot",
            "robotics",
            "cybersecurity",
            "cyber security",
            "software",
            "cloud computing",
            "semiconductor",
            "microchip",
            "chipmaker",
            "technology",
            "tech company",
            "startup",
            "data center",
            "digital platform",
            "smartphone",
            "computer",
            "internet",
            "app",
            "automation",
            "electric vehicle",
            "autonomous vehicle",
            "robotaxi",
            "social media platform",
        ],
    ):
        return "technology_ai"

    # Business and markets
    if has_word(
        text,
        [
            "business",
            "finance",
            "financial",
            "market",
            "markets",
            "stock",
            "stocks",
            "share",
            "shares",
            "sensex",
            "nifty",
            "economy",
            "economic",
            "bank",
            "banking",
            "inflation",
            "investment",
            "investor",
            "trade",
            "gdp",
            "growth",
            "revenue",
            "profit",
            "earnings",
            "ipo",
            "merger",
            "acquisition",
            "deal",
            "funding",
            "rupee",
            "gold price",
            "oil price",
            "interest rate",
            "rbi",
            "company",
            "pricing",
        ],
    ):
        return "business"

    # India
    if has_word(
        text,
        [
            "india",
            "indian",
            "new delhi",
            "delhi",
            "mumbai",
            "bengaluru",
            "bangalore",
            "kolkata",
            "chennai",
            "hyderabad",
            "gujarat",
            "maharashtra",
            "karnataka",
            "kerala",
            "telangana",
            "uttar pradesh",
            "west bengal",
            "jammu",
            "kashmir",
            "modi",
            "supreme court",
            "high court",
            "lok sabha",
            "rajya sabha",
            "parliament",
            "union government",
            "centre",
            "cbse",
        ],
    ):
        return "india"

    # Specialist technology sources
    if any(
        source_name in source
        for source_name in [
            "techcrunch",
            "the verge",
            "wired",
            "ars technica",
            "zdnet",
            "infoq",
            "venturebeat",
        ]
    ):
        return "technology_ai"

    # Specialist business sources
    if any(
        source_name in source
        for source_name in [
            "economic times",
            "cnbc",
            "marketwatch",
            "financial times",
            "livemint",
            "mint",
        ]
    ):
        return "business"

    return "world"


def article_recency_value(
    article: NewsArticle,
) -> float:
    """
    Return the best available timestamp for sorting.
    """

    for field_name in [
        "published_at",
        "processed_at",
        "created_at",
    ]:
        field_value = getattr(
            article,
            field_name,
            None,
        )

        sortable_value = date_sort_value(
            field_value
        )

        if sortable_value > 0:
            return sortable_value

    return 0.0


def sort_articles(
    articles: list[NewsArticle],
) -> list[NewsArticle]:
    """
    Sort articles by importance and recency.
    """

    return sorted(
        articles,
        key=lambda article: (
            int(
                article.importance_score
                or 0
            ),
            article_recency_value(
                article
            ),
            int(article.id or 0),
        ),
        reverse=True,
    )


def fill_section(
    brief: dict,
    section: str,
    articles: list[NewsArticle],
    used_ids: set[int],
) -> None:
    """
    Fill one category section without duplicates.
    """

    section_limit = SECTION_LIMITS[
        section
    ]

    for article in articles:
        if len(brief[section]) >= section_limit:
            break

        if article.id in used_ids:
            continue

        if detect_section(article) != section:
            continue

        brief[section].append(
            article_to_card(article)
        )

        used_ids.add(article.id)


def backfill_sections(
    brief: dict,
    articles: list[NewsArticle],
    used_ids: set[int],
) -> None:
    """
    Fill unused category capacity with remaining articles.

    This allows the brief to reach 40 unique articles when
    some categories do not contain enough content.
    """

    section_order = [
        "india",
        "world",
        "technology_ai",
        "business",
        "health_science",
    ]

    remaining_articles = [
        article
        for article in articles
        if article.id not in used_ids
    ]

    for article in remaining_articles:
        available_sections = [
            section
            for section in section_order
            if len(brief[section])
            < SECTION_LIMITS[section]
        ]

        if not available_sections:
            break

        preferred_section = detect_section(
            article
        )

        if preferred_section in available_sections:
            selected_section = preferred_section
        else:
            selected_section = max(
                available_sections,
                key=lambda section: (
                    SECTION_LIMITS[section]
                    - len(brief[section])
                ),
            )

        brief[selected_section].append(
            article_to_card(article)
        )

        used_ids.add(article.id)


def build_editor_brief(
    articles: list[NewsArticle],
) -> dict:
    """
    Build a balanced brief containing up to 40 unique stories.

    A 40-story brief is possible only when at least 40 unique
    article rows are provided by brief_service.py.
    """

    brief = {
        "top_stories": [],
        "india": [],
        "world": [],
        "technology_ai": [],
        "business": [],
        "health_science": [],
    }

    if not articles:
        brief["total_stories"] = 0
        brief["requested_stories"] = (
            TOTAL_BRIEF_LIMIT
        )
        brief["available_candidates"] = 0

        return brief

    sorted_articles = sort_articles(
        articles
    )

    candidate_articles = sorted_articles[
        :TOTAL_BRIEF_LIMIT
    ]

    used_ids: set[int] = set()

    # Select eight highest-ranked top stories.
    for article in candidate_articles:
        if (
            len(brief["top_stories"])
            >= SECTION_LIMITS["top_stories"]
        ):
            break

        brief["top_stories"].append(
            article_to_card(article)
        )

        used_ids.add(article.id)

    # Fill category sections.
    for section in [
        "india",
        "world",
        "technology_ai",
        "business",
        "health_science",
    ]:
        fill_section(
            brief=brief,
            section=section,
            articles=candidate_articles,
            used_ids=used_ids,
        )

    # Fill any remaining category capacity.
    backfill_sections(
        brief=brief,
        articles=candidate_articles,
        used_ids=used_ids,
    )

    total_stories = sum(
        len(brief[section])
        for section in [
            "top_stories",
            "india",
            "world",
            "technology_ai",
            "business",
            "health_science",
        ]
    )

    brief["total_stories"] = (
        total_stories
    )

    brief["requested_stories"] = (
        TOTAL_BRIEF_LIMIT
    )

    brief["available_candidates"] = len(
        candidate_articles
    )

    return brief