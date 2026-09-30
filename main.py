from contextlib import asynccontextmanager
from typing import Annotated, Literal, Optional

from fastapi import (
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

from database import SessionDep, get_session, init_db
from model import Room as RoomModel
from model import RoomCreate, RoomUpdate

RoomID = Annotated[int, Path(ge=1)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, title="Rent Room")


class PreferenceCookies(BaseModel):
    theme: Literal["dark", "light"] = "light"
    lang: Literal["eng", "fr", "italy"] = "eng"


class UserAgent(BaseModel):
    user_agent: str | None = None


def room_available_or_404(session: SessionDep, room_id: RoomID):
    room = session.get(RoomModel, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    return room


@app.get("/", status_code=status.HTTP_200_OK, response_model=list[RoomModel])
def root(session: SessionDep):
    return session.exec(select(RoomModel)).all()


@app.get("/rooms/faq")
async def get_rooms_faq():
    return {
        "check_in": "Check-in starts at 3 PM.",
        "check_out": "Check-out is before 11 AM.",
        "pets_allowed": False,
        "wifi_available": True,
    }


@app.get("/rooms/{room_id}")
async def get_room(
    session: SessionDep,
    room: Annotated[RoomModel, Depends(room_available_or_404)],
    room_id: int = RoomID,
):
    return room


@app.patch("/rooms/{room_id}")
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
    session.commit()
    session.refresh(room)

    return room


@app.delete("/rooms/{room_id}")
async def delete_room(
    session: SessionDep,
    room: Annotated[RoomModel, Depends(room_available_or_404)],
    room_id: int = RoomID,
):

    session.delete(room)
    session.commit()

    return {"message": "Room deleted successfully", "id": room_id}


max_price_query = Query(gt=10, le=10000)
annotated_max_price = Annotated[float | None, max_price_query]


@app.post("/rooms", status_code=status.HTTP_201_CREATED, response_model=RoomModel)
def create_room(room: RoomCreate, session: SessionDep):
    validated_room = RoomModel.model_validate(room)
    session.add(validated_room)
    session.commit()
    session.refresh(validated_room)
    return validated_room


class RoomQuery(BaseModel):
    search: str | None = None
    max_price: float | None = Field(default=None, gt=10, le=10000)
    limit: int = Field(default=1, ge=1, le=10)


# app.mount("/assets", StaticFiles(directory="assets"), name="assets")
@app.get("/rooms", status_code=status.HTTP_200_OK)
async def get_rooms(query: Annotated[RoomQuery, Query()], session: SessionDep):

    statement = select(RoomModel)

    rooms = session.exec(statement).all()
    if query.max_price is not None:
        # if query.search and query.max_price is not None:
        statement = statement.where(query.max_price > RoomModel.price_per_night)

    if query.search is not None:
        statement = statement.where(col(RoomModel.name).ilike(f"%{query.search}%"))
    statement = statement.limit(query.limit)
    fitered_rooms = session.exec(statement).all()

    # return filtered_rooms

    return fitered_rooms


@app.get("/preference")
def set_preferences(response: Response):

    cookies_reference = PreferenceCookies()

    response.set_cookie(key="theme", value=cookies_reference.theme, max_age=86400)
    response.set_cookie(key="lang", value=cookies_reference.lang, max_age=86400)
    return {"message": "Cookies have been set"}
