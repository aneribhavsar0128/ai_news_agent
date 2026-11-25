from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import DailyBrief, NewsArticle
from app.services.agent_service import (
    preview_daily_email,
    run_daily_brief,
    run_fetch_pipeline,
    run_full_pipeline,
    run_processing_pipeline,
    run_rag_query,
    send_daily_email_to_subscribers,
)
from app.services.chroma_service import (
    get_collection_count,
    search_similar_articles,
)
from app.services.scheduler_service import (
    daily_news_job,
    refresh_news_job,
    scheduler,
    start_scheduler,
)
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberResponse,
    UnsubscribeRequest,
)

from app.services.subscriber_service import (
    get_active_subscribers,
    subscribe_user,
    unsubscribe_user,
)

from fastapi.security import OAuth2PasswordRequestForm

from app.models import User
from app.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)


# Create missing database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start the scheduler when FastAPI starts and stop it
    when FastAPI shuts down.
    """

    print("Starting AI News Agent scheduler...")

    start_scheduler()

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler stopped successfully.")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Automated AI news system with RSS ingestion, "
        "LangGraph processing, ChromaDB RAG, daily briefs "
        "and email delivery."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health")
def health():
    jobs = []

    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat()
                        if job.next_run_time
                        else None
                    ),
                }
            )

    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "scheduled_jobs": jobs,
    }


@app.post("/fetch-news")
def fetch_news(
    db: Session = Depends(get_db),
):         
    return run_fetch_pipeline(db)


@app.post("/process-news")
def process_news(
    batch_size: int | None = None,
    max_workers: int | None = None,
    db: Session = Depends(get_db),
):
    return run_processing_pipeline(
        db=db,
        batch_size=(
            batch_size
            or settings.processing_batch_size
        ),
        max_workers=(
            max_workers
            or settings.processing_workers
        ),
    )


@app.post("/run-pipeline")
def run_pipeline(
    batch_size: int | None = None,
    db: Session = Depends(get_db),
):
    return run_full_pipeline(
        db=db,
        batch_size=(
            batch_size
            or settings.processing_batch_size
        ),
    )


@app.post("/refresh-news")
def refresh_news():
    """
    Fetch and process only newly inserted RSS articles.
    """

    print("Manual news refresh requested.")

    refresh_news_job()

    return {
        "message": (
            "News refresh executed. "
            "Check the server terminal for details."
        )
    }


@app.post("/run-daily-job")
def run_daily_job():
    """
    Run the complete workflow manually:

    fetch -> process -> generate brief -> send email
    """

    print("Manual daily pipeline requested.")

    daily_news_job()

    return {
        "message": (
            "Daily pipeline executed. "
            "Check the server terminal for details."
        )
    }

@app.get("/ask")
def ask(
    query: str,
    n_results: int = 5,
    max_distance: float = 1.8,
):
    cleaned_query = query.strip()

    if not cleaned_query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    return run_rag_query(
        query=cleaned_query,
        n_results=n_results,
        max_distance=max_distance,
    )


@app.get("/rag-search")
def rag_search(
    query: str,
    n_results: int = 10,
    max_distance: float = 1.8,
):
    cleaned_query = query.strip()

    if not cleaned_query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    results = search_similar_articles(
        query_text=cleaned_query,
        n_results=n_results,
    )

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
        distance = distances[index]

        if distance is None:
            continue

        if distance > max_distance:
            continue

        metadata = metadatas[index] or {}

        cleaned_results.append(
            {
                "id": ids[index],
                "title": metadata.get("title"),
                "source": metadata.get("source"),
                "category": metadata.get("category"),
                "url": metadata.get("url"),
                "importance_score": metadata.get(
                    "importance_score"
                ),
                "tags": metadata.get("tags"),
                "published_at": metadata.get(
                    "published_at"
                ),
                "distance": distance,
                "document": documents[index],
            }
        )

    return {
        "query": cleaned_query,
        "requested_results": n_results,
        "returned_results": len(cleaned_results),
        "max_distance": max_distance,
        "results": cleaned_results,
    }


@app.get("/chroma-count")
def chroma_count():
    return {
        "documents": get_collection_count()
    }

@app.get("/news")
def get_news(
    db: Session = Depends(get_db),
):
    return (
        db.query(NewsArticle)
        .order_by(
            NewsArticle.created_at.desc()
        )
        .all()
    )


@app.get("/news/{article_id}")
def get_single_news(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.id == article_id
        )
        .first()
    )

    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found.",
        )

    return article

@app.post("/generate-daily-brief")
def generate_brief(
    db: Session = Depends(get_db),
):
    return run_daily_brief(db)


@app.get("/daily-briefs")
def get_daily_briefs(
    limit: int = 30,
    db: Session = Depends(get_db),
):
    safe_limit = max(
        1,
        min(limit, 365),
    )

    return (
        db.query(DailyBrief)
        .order_by(
            DailyBrief.created_at.desc()
        )
        .limit(safe_limit)
        .all()
    )


@app.get(
    "/preview-email",
    response_class=HTMLResponse,
)
def preview_email(
    db: Session = Depends(get_db),
):
    email_html = preview_daily_email(db)

    if email_html is None:
        return HTMLResponse(
            content="<h2>No Daily Brief Available.</h2>",
            status_code=404,
        )

    return HTMLResponse(
        content=email_html,
        status_code=200,
    )

@app.post(
    "/subscribe",
    response_model=SubscriberResponse,
)
def subscribe(
    payload: SubscriberCreate,
    db: Session = Depends(get_db),
):
    subscriber, created_new = subscribe_user(
        db=db,
        email=str(payload.email),
        name=payload.name,
    )
    if created_new:
        print(
            f"New subscriber created: "
            f"{subscriber.email}"
        )
    else:
        print(
            f"Subscriber already existed or "
            f"was reactivated: {subscriber.email}"
        )
    return subscriber


@app.post("/unsubscribe")
def unsubscribe(
    payload: UnsubscribeRequest,
    db: Session = Depends(get_db),
):
    subscriber = unsubscribe_user(
        db=db,
        email=str(payload.email),
    )

    if subscriber is None:
        raise HTTPException(
            status_code=404,
            detail="Subscriber not found.",
        )

    return {
        "message": (
            "You have been unsubscribed successfully."
        ),
        "email": subscriber.email,
    }


@app.get(
    "/subscribers",
    response_model=list[SubscriberResponse],
)
def list_subscribers(
    db: Session = Depends(get_db),
):
    return get_active_subscribers(db)


@app.post("/send-to-subscribers")
def send_to_subscribers(
    db: Session = Depends(get_db),
):
    return send_daily_email_to_subscribers(db)

# =========================================================
# AUTHENTICATION
# =========================================================


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    return register_user(
        db=db,
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
        subscribe_to_newsletter=(
            payload.subscribe_to_newsletter
        ),
    )


@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=str(payload.email),
        password=payload.password,
    )

    token, expires_in = (
        create_access_token(user)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user,
    }


@app.post(
    "/auth/token",
    response_model=TokenResponse,
)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    token, expires_in = (
        create_access_token(user)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user,
    }


@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user