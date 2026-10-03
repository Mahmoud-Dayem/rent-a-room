from fastapi import APIRouter, HTTPException, status
from pwdlib import PasswordHash
from sqlmodel import select

from app.dependicies.database import SessionDep
from app.models.booking import BookingModel, BookingPublic
from app.models.user import UserCreate, UserModel, UserPublic

router = APIRouter(prefix="/users", tags=["Users"])

password_hash = PasswordHash.recommended()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic,
)
async def create_user(
    user: UserCreate,
    session: SessionDep,
):
    # Check if username already exists
    username_result = await session.execute(
        select(UserModel).where(UserModel.username == user.username)
    )

    if username_result.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    email_result = await session.execute(
        select(UserModel).where(UserModel.email == user.email)
    )

    if email_result.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    # Hash password
    hashed_password = password_hash.hash(user.password)

    # Create database model
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )

    session.add(db_user)

    await session.commit()
    await session.refresh(db_user)

    return db_user


# fetch user based on id
@router.get(
    "/{user_id}",
    response_model=UserPublic,
)
async def get_user(
    user_id: int,
    session: SessionDep,
):
    user = await session.get(UserModel, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


##############################


@router.get(
    "/{user_id}/bookings",
    response_model=list[BookingModel],
)
async def get_user_bookings(
    user_id: int,
    session: SessionDep,
):

    user = await session.get(UserModel, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await session.execute(
        select(BookingModel).where(BookingModel.user_id == user_id)
    )

    bookings = result.scalars().all()

    return bookings
