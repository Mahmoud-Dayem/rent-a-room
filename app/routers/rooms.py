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
from sqlmodel import col, select

from app.dependicies.database import SessionDep, get_session, init_db
from app.errors import ROOM_NOT_FOUND, SERVICE_UNDER_MAINTENANCE
from app.models.room import RoomCreate, RoomUpdate
from app.models.room import RoomModel as RoomModel

RoomID = Annotated[int, Path(ge=1)]
maintenance_mode = True


def check_maintenance_mode():
    if maintenance_mode is False:
        raise SERVICE_UNDER_MAINTENANCE

    return True


async def room_available_or_404(session: SessionDep, room_id: RoomID):
    room = await session.get(RoomModel, room_id)
    if not room:
        raise ROOM_NOT_FOUND
    return room


router = APIRouter(prefix="/rooms")


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[RoomModel],
    dependencies=[Depends(check_maintenance_mode)],
)
async def root(session: SessionDep):

    result = await session.execute(select(RoomModel))
    return result.scalars().all()


@router.get("/faq")
async def get_rooms_faq():
    return {
        "check_in": "Check-in starts at 3 PM.",
        "check_out": "Check-out is before 11 AM.",
        "pets_allowed": False,
        "wifi_available": True,
    }


@router.get("/{room_id}")
async def get_room(
    session: SessionDep,
    room: Annotated[RoomModel, Depends(room_available_or_404)],
    room_id: int = RoomID,
):
    return room


@router.patch("/{room_id}")
async def update_room(
    session: SessionDep,
    pay_load: RoomUpdate,
    room: Annotated[RoomModel, Depends(room_available_or_404)],
    room_id: int = RoomID,
    response_model=RoomUpdate,
):
    pay_load_model_dump = pay_load.model_dump(exclude_unset=True)

    room.sqlmodel_update(pay_load)
    session.add(room)
    await session.commit()
    await session.refresh(room)

    return room


@router.delete("/{room_id}")
async def delete_room(
    session: SessionDep,
    room: Annotated[RoomModel, Depends(room_available_or_404)],
    room_id: int = RoomID,
):
    await session.delete(room)
    await session.commit()

    deleted_room = await session.get(RoomModel, room_id)

    if deleted_room:
        return {
            "message": "Room was NOT deleted",
            "id": room_id,
        }

    return {
        "message": "Room deleted successfully",
        "id": room_id,
    }


max_price_query = Query(gt=10, le=10000)
annotated_max_price = Annotated[float | None, max_price_query]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RoomModel)
async def create_room(room: RoomCreate, session: SessionDep):
    validated_room = RoomModel.model_validate(room)
    session.add(validated_room)
    await session.commit()
    await session.refresh(validated_room)
    return validated_room
