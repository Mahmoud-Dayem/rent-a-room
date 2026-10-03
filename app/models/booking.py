from datetime import date, datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.room import RoomModel
    from app.models.user import UserModel


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingModel(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", index=True)
    room_id: int = Field(foreign_key="rooms.id", index=True)
    room: "RoomModel" = Relationship(back_populates="bookings")
    user: "UserModel" = Relationship(back_populates="bookings")
    check_in: date
    check_out: date

    total_price: float = Field(ge=0)

    status: BookingStatus = Field(default=BookingStatus.pending)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BookingBase(SQLModel):
    room_id: int
    check_in: date
    check_out: date
    user_id: int


class BookingPublic(BookingBase):
    id: int
    total_price: float
