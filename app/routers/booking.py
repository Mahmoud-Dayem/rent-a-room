from contextlib import asynccontextmanager
from typing import Annotated, Literal, Optional

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from app.dependicies.database import SessionDep, get_session, init_db
from app.errors import (
    BOOKING_NOT_FOUND,
    ROOM_NOT_FOUND,
    SERVICE_UNDER_MAINTENANCE,
    USER_NOT_FOUND,
)
from app.models.booking import BookingBase, BookingModel, BookingPublic, BookingStatus
from app.models.room import RoomModel as RoomModel
from app.models.user import UserModel
from app.routers.rooms import room_available_or_404
from app.schemas.responses import BookingWithDetails

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingPublic,
)
async def create_booking(
    booking: BookingBase,
    session: SessionDep,
):
    room = await session.get(RoomModel, booking.room_id)
    user = await session.get(UserModel, booking.user_id)

    if not user:
        raise USER_NOT_FOUND
    if not room:
        raise ROOM_NOT_FOUND

    nights = (booking.check_out - booking.check_in).days

    if nights <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out must be after check-in",
        )

    total_price = nights * room.price_per_night

    validated_booking = BookingModel.model_validate(
        booking,
        update={"total_price": total_price},
    )

    session.add(validated_booking)

    await session.commit()
    await session.refresh(validated_booking)

    return {
        **validated_booking.model_dump(),
    }


BookingID = Annotated[int, Path(ge=1)]


async def booking_available_or_404(session: SessionDep, booking_id: BookingID):
    print("**************************")
    print(booking_id)
    booking = await session.get(BookingModel, booking_id)
    if not booking:
        raise BOOKING_NOT_FOUND
    return booking


@router.get(
    "/{booking_id}",
    status_code=status.HTTP_200_OK,
    response_model=BookingWithDetails,
    tags=["booking"],
)
async def get_booking(
    session: SessionDep,
    # booking: Annotated[BookingModel, Depends(booking_available_or_404)],
    booking_id: int = BookingID,
):
    booking = await session.get(
        BookingModel,
        booking_id,
        options=[joinedload(BookingModel.room), joinedload(BookingModel.user)],
    )
    if not booking:
        raise BOOKING_NOT_FOUND
    return booking
