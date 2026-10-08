import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.auth import create_access_token, decode_access_token
from app.config import settings
from app.dependicies.database import SessionDep, init_db
from app.errors import EMAIL_ALREADY_EXIST, USER_ALREADY_EXIST, USER_NOT_FOUND
from app.models.booking import BookingModel, BookingPublic
from app.models.user import UserCreate, UserModel, UserPublic
from app.routers import booking, general, rooms, users

# Create simple logger (you can use print or actual logging)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()

from app.config import settings

DUMMY_HASHED_PASSWORD = password_hash.hash("123456")


def verify_password(plain_passoword: str, hashed_password: str):
    return password_hash.verify(plain_passoword, hashed_password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def log_request(request: Request) -> None:
    """Simple dependency to log incoming request info"""
    # Get basic information from the request
    method = request.method
    path = request.url.path
    client_host = request.client.host if request.client else "unknown"

    # Print request details (for learning purposes)
    logger.info(f"{method} {path}")
    logger.info(f"Client: {client_host}")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan, title="Rent Room", dependencies=[Depends(log_request)])
app.include_router(general.router)
app.include_router(rooms.router)
app.include_router(booking.router)
app.include_router(users.router)


class UserAgent(BaseModel):
    user_agent: str | None = None


class RoomQuery(BaseModel):
    search: str | None = None
    max_price: float | None = Field(default=None, gt=10, le=10000)
    limit: int = Field(default=1, ge=1, le=10)


@app.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    result = await session.execute(
        select(UserModel).where(UserModel.email == form_data.username)
    )

    user = result.scalar_one_or_none()

    if not user:
        password_hash.verify(form_data.password, DUMMY_HASHED_PASSWORD)

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not password_hash.verify(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"www-Authenticate": "Beared"},
        )

    token = create_access_token({"email": user.email})
    return {"access_token": token, "token_type": "bearer", "token": token}


@app.get("/test-token")
def test_token(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
