import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field

from app.dependicies.database import init_db
from app.routers import booking, general, rooms, users

# Create simple logger (you can use print or actual logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
