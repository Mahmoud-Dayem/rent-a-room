from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import BookingModel


# What client sends
class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


# Database table
class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True, max_length=50)
    email: EmailStr = Field(index=True, unique=True, max_length=255)

    hashed_password: str

    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    bookings: list["BookingModel"] = Relationship(back_populates="user")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# What client receives
class UserPublic(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
