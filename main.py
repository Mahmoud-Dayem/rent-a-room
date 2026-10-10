import logging
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import select

import test
from app.auth import (
    INVALID_TOKEN,
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    oauth2_scheme,
)
from app.config import settings
from app.dependicies.database import SessionDep, init_db
from app.errors import EMAIL_ALREADY_EXIST, USER_ALREADY_EXIST, USER_NOT_FOUND
from app.models.booking import BookingModel, BookingPublic
from app.models.user import (
    PassswordResetRequest,
    PasswordResetToken,
    UserCreate,
    UserModel,
    UserPublic,
    UserUpdate,
)
from app.routers import booking, general, rooms, users

# Create simple logger (you can use print or actual logging)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()

from app.config import settings

DUMMY_HASHED_PASSWORD = password_hash.hash("123456")


def verify_password(plain_passoword: str, hashed_password: str):
    return password_hash.verify(plain_passoword, hashed_password)


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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


# INVALID_TOKEN = HTTPException(
#     detail="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED
# )


# async def get_current_user(
#     session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
# ):

#     payload = decode_token(token, token_type="access_token")

#     if not payload:
#         raise INVALID_TOKEN

#     if payload.get("type") != "access_token":
#         raise INVALID_TOKEN
#     email = payload.get("sub")
#     if not email:
#         raise INVALID_TOKEN
#     result = await session.execute(select(UserModel).where(UserModel.email == email))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise INVALID_TOKEN
#     return user


# CurrentUser = Annotated[UserModel, Depends(get_current_user)]

user_router = APIRouter(
    prefix="/protected",
    tags=["Protected"],
    dependencies=[Depends(get_current_user)],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan, title="Rent Room", dependencies=[Depends(log_request)])
app.include_router(general.router)
app.include_router(rooms.router)
app.include_router(booking.router)
app.include_router(users.router)
app.include_router(user_router)


class UserAgent(BaseModel):
    user_agent: str | None = None


class RoomQuery(BaseModel):
    search: str | None = None
    max_price: float | None = Field(default=None, gt=10, le=10000)
    limit: int = Field(default=1, ge=1, le=10)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@app.post("/login", response_model=Token)
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

    access_token = create_access_token({"sub": user.email, "type": "access_token"})

    refresh_token = create_refresh_token({"sub": user.email, "type": "refresh_token"})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    # return {"access_token": token, "token_type": "bearer", "token": token}


@app.get("/test-token")
def test_token(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


@user_router.get("/me", response_model=UserPublic)
def get_me(user: CurrentUser):

    return user


@app.patch("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def updata_me(
    session: SessionDep, user: CurrentUser, updated_payload: UserUpdate
):

    if not updated_payload.email:
        return user

    # Check whether the email is already used by another user

    statement = select(UserModel).where(
        UserModel.email == updated_payload.email, UserModel.id != user.id
    )
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already taken"
        )
        # Update the authenticated user's email

    user.email = updated_payload.email
    session.add(user)

    try:
        await session.commit()

    except IntegrityError:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    await session.refresh(user)

    return user


@user_router.get("/dashboard")
def user_dashboard():
    return {"profit": 1_000_000}


@app.post("/token/refresh")
async def refresh_token(
    session: SessionDep, refresh_token: Annotated[str, Body(embed=True)]
):

    print("*******-------------*************")
    print(refresh_token)
    payload = decode_token(refresh_token, token_type="refresh")

    if not payload:
        raise INVALID_TOKEN

    email = payload.get("sub")
    if not email:
        raise INVALID_TOKEN

    query = await session.execute(select(UserModel).where(UserModel.email == email))
    user = query.scalar_one_or_none()
    if not user:
        raise INVALID_TOKEN

    new_access_token = create_access_token({"sub": user.email, "type": "access_token"})

    return {"access_token": new_access_token, "token_type": "bearer"}


@app.post("/password-reset-request")
async def password_reset(session: SessionDep, payload: PassswordResetRequest):

    message = {
        "message": "if asn account exists with this email ,a reset link has been sent"
    }

    INVALID_USER = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    query = await session.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    user = query.scalar_one_or_none()
    if not user:
        raise INVALID_USER
    token = secrets.token_urlsafe(32)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        used=False,
    )
    session.add(reset_token)
    await session.commit()
    await session.refresh(user)

    return user
