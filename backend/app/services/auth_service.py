from datetime import (datetime,timedelta,timezone,)
import jwt
from fastapi import (Depends,HTTPException,status,)
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import Subscriber, User

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)

def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    stored_hash: str,
) -> bool:
    try:
        return password_hash.verify(
            plain_password,
            stored_hash,
        )
    except Exception:
        return False


def create_access_token(
    user: User,
) -> tuple[str, int]:
    if not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is missing in .env"
        )

    expires_minutes = (
        settings.jwt_access_token_minutes
    )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=expires_minutes
        )
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return token, expires_minutes * 60


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    subscribe_to_newsletter: bool = True,
) -> User:
    normalized_email = normalize_email(
        email
    )

    existing_user = (
        db.query(User)
        .filter(
            User.email == normalized_email
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(
            password
        ),
        is_active=True,
        is_admin=False,
    )

    db.add(user)

    if subscribe_to_newsletter:
        subscriber = (
            db.query(Subscriber)
            .filter(
                Subscriber.email
                == normalized_email
            )
            .first()
        )

        if subscriber:
            subscriber.is_active = True

            if not subscriber.name:
                subscriber.name = (
                    name.strip()
                )
        else:
            subscriber = Subscriber(
                name=name.strip(),
                email=normalized_email,
                is_active=True,
            )

            db.add(subscriber)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    normalized_email = normalize_email(
        email
    )

    user = (
        db.query(User)
        .filter(
            User.email == normalized_email
        )
        .first()
    )

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    if user is None:
        raise invalid_credentials

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise invalid_credentials

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    return user


def get_db_session():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(
        get_db_session
    ),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Could not validate credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_error

        user_id = int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise credentials_error

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    return user

def require_admin(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user