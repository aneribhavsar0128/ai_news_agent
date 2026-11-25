from pydantic import BaseModel, EmailStr, Field


class SubscriberCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(
        default=None,
        max_length=100,
    )


class SubscriberResponse(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class UnsubscribeRequest(BaseModel):
    email: EmailStr