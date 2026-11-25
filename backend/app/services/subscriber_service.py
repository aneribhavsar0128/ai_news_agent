from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Subscriber


def normalize_email(email: str) -> str:
    return email.strip().lower()


def subscribe_user(
    db: Session,
    email: str,
    name: Optional[str] = None,
):
    """
    Create a subscriber or reactivate an existing subscriber.

    Returns:
        subscriber
        created_new
    """

    normalized_email = normalize_email(email)

    cleaned_name = (
        name.strip()
        if name and name.strip()
        else None
    )

    existing_subscriber = (
        db.query(Subscriber)
        .filter(
            Subscriber.email == normalized_email
        )
        .first()
    )

    if existing_subscriber:
        if not existing_subscriber.is_active:
            existing_subscriber.is_active = True
            existing_subscriber.unsubscribed_at = None

        if cleaned_name:
            existing_subscriber.name = cleaned_name

        db.commit()
        db.refresh(existing_subscriber)

        return existing_subscriber, False

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
):
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
):
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