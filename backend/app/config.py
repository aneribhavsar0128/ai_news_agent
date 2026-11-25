import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default

def get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./news_agent.db",
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


RSS_FEEDS = list(
    dict.fromkeys(
        [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
            "https://www.reuters.com/world/rss",
            "https://www.reuters.com/technology/rss",
            "https://www.theverge.com/rss/index.xml",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://indianexpress.com/section/india/feed/",
            "https://www.livemint.com/rss/news",
            "https://feeds.feedburner.com/ndtvnews-top-stories",
            "https://www.news18.com/rss/india.xml",
            "https://techcrunch.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.wired.com/feed/rss",
            "https://www.zdnet.com/news/rss.xml",
            "https://www.infoq.com/feed/",
            "https://venturebeat.com/feed/",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.marketwatch.com/rss/topstories",
            "https://www.ft.com/world?format=rss",
            "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
            "https://www.who.int/rss-feeds/news-english.xml",
            "https://www.medicalnewstoday.com/rss",
            "https://www.nih.gov/news-events/news-releases/feed",
        ]
    )
)

@dataclass(frozen=True)
class Settings:
    # Application
    app_name: str = os.getenv(
        "APP_NAME",
        "AI Daily News Agent",
    )

    app_version: str = os.getenv(
        "APP_VERSION",
        "1.0.0",
    )

    environment: str = os.getenv(
        "ENVIRONMENT",
        "development",
    )

    # LLM
    groq_model: str = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    )

    llm_temperature: float = get_float_env(
        "LLM_TEMPERATURE",
        0.0,
    )

    llm_max_retries: int = get_int_env(
        "LLM_MAX_RETRIES",
        3,
    )

    llm_retry_delay: int = get_int_env(
        "LLM_RETRY_DELAY",
        10,
    )

    # Processing
    processing_batch_size: int = get_int_env(
        "PROCESSING_BATCH_SIZE",
        10,
    )

    processing_workers: int = get_int_env(
        "PROCESSING_WORKERS",
        2,
    )

    related_articles_limit: int = get_int_env(
        "RELATED_ARTICLES_LIMIT",
        5,
    )

    related_context_distance: float = get_float_env(
        "RELATED_CONTEXT_DISTANCE",
        1.8,
    )

    related_context_char_limit: int = get_int_env(
        "RELATED_CONTEXT_CHAR_LIMIT",
        300,
    )

    # Scheduler
    scheduler_timezone: str = os.getenv(
        "SCHEDULER_TIMEZONE",
        "Asia/Kolkata",
    )

    scheduler_hour: int = get_int_env(
        "SCHEDULER_HOUR",
        15,
    )

    scheduler_minute: int = get_int_env(
        "SCHEDULER_MINUTE",
        15,
    )

    scheduler_misfire_grace_time: int = get_int_env(
        "SCHEDULER_MISFIRE_GRACE_TIME",
        3600,
    )

    # Daily brief
    brief_article_limit: int = get_int_env(
        "BRIEF_ARTICLE_LIMIT",
        40,
    )

    brief_min_importance: int = get_int_env(
        "BRIEF_MIN_IMPORTANCE",
        6,
    )
    # Ask AI / RAG
    rag_results_limit: int = get_int_env(
        "RAG_RESULTS_LIMIT",
        10,
    )

    rag_context_char_limit: int = get_int_env(
    "RAG_CONTEXT_CHAR_LIMIT",
    220,
    )

    rag_max_tokens: int = get_int_env(
        "RAG_MAX_TOKENS",
        600,
    )

    rag_retry_attempts: int = get_int_env(
        "RAG_RETRY_ATTEMPTS",
        3,
    )

    rag_retry_delay: int = get_int_env(
        "RAG_RETRY_DELAY",
        15,
    )

    # Email
    email_sender: str = os.getenv(
        "EMAIL_SENDER",
        "",
    )

    email_password: str = os.getenv(
        "EMAIL_PASSWORD",
        "",
    )

    email_recipient: str = os.getenv(
        "EMAIL_RECIPIENT",
        "",
    )

    smtp_server: str = os.getenv(
        "SMTP_SERVER",
        "smtp.gmail.com",
    )

    smtp_port: int = get_int_env(
        "SMTP_PORT",
        587,
    )

    # Logging
    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )

    log_file: str = os.getenv(
        "LOG_FILE",
        "logs/news_agent.log",
    )

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "",
)

    jwt_algorithm: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    jwt_access_token_minutes: int = get_int_env(
        "JWT_ACCESS_TOKEN_MINUTES",
        60,
    )


settings = Settings()