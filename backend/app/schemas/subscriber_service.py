from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Subscriber

def normalize_email(email: str) -> str:
    return email.strip().lower()

def subscribe_user(
    db: Session,
    email: str,
    name: str | None = None,
) -> tuple[Subscriber, bool]:
    """
    Returns:
        subscriber
        created_new
    """

    normalized_email = normalize_email(email)
    cleaned_name = name.strip() if name else None

    existing = (
        db.query(Subscriber)
        .filter(
            Subscriber.email == normalized_email
        )
        .first()
    )

    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.unsubscribed_at = None

        if cleaned_name:
            existing.name = cleaned_name

        db.commit()
        db.refresh(existing)

        return existing, False

    subscriber = Subscriber(
        email=normalized_email,
        name=cleaned_name,
        is_active=True,
    )

    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)

    return subscriber, True


def get_active_subscribers(
    db: Session,
) -> list[Subscriber]:
    return (
        db.query(Subscriber)
        .filter(
            Subscriber.is_active.is_(True)
        )
        .order_by(
            Subscriber.created_at.asc()
        )
        .all()
    )


def unsubscribe_user(
    db: Session,
    email: str,
) -> Subscriber | None:
    normalized_email = normalize_email(email)

    subscriber = (
        db.query(Subscriber)
        .filter(
            Subscriber.email == normalized_email
        )
        .first()
    )

    if subscriber is None:
        return None

    subscriber.is_active = False
    subscriber.unsubscribed_at = datetime.utcnow()

    db.commit()
    db.refresh(subscriber)

    return subscriber