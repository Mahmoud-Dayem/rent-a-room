from app.models.booking import BookingModel, BookingPublic
from app.models.room import RoomModel
from app.models.user import UserPublic


class BookingWithDetails(BookingPublic):
    room: RoomModel
    user: UserPublic
