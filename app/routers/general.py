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
from app.models.room import RoomCreate, RoomUpdate
from app.models.room import RoomModel as RoomModel

router = APIRouter(prefix="")


class PreferenceCookies(BaseModel):
    theme: Literal["dark", "light"] = "light"
    lang: Literal["eng", "fr", "italy"] = "eng"


@router.get("/")
def main_route():
    return {"message": "Welcome"}


@router.get("/preference")
def set_preferences(response: Response):

    cookies_reference = PreferenceCookies()

    response.set_cookie(key="theme", value=cookies_reference.theme, max_age=86400)
    response.set_cookie(key="lang", value=cookies_reference.lang, max_age=86400)
    return {"message": "Cookies have been set"}
