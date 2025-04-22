from pydantic import BaseModel
from typing import List

class UserRoom(BaseModel):
    room_name: str
    room_desc: str
    room_num_walls: int
    room_wall_color1: str
    room_wall_color2: str
    room_ceiling_color: str
    room_floor_color: str
    room_trim_color: str
    room_other_details: str

class UserRoomId(UserRoom):
    user_id: int

class Room(UserRoomId):
    room_id: int

class Rooms(BaseModel):
    rooms: List[Room]

class Image(BaseModel):
    image_name: str
    image_desc: str
    image_filename: str
    image_type: str
    room_id: int

class UserImage(Image):
    user_id: int

class ImageId(UserImage):
    image_id: int

class ImageUpdate(BaseModel):
    image_id: int
    image_name: str
    image_desc: str

class ImageRetrieve(ImageUpdate):
    image_data: bytes
    image_type: str
    room_id: int
    user_id: int

class Images(BaseModel):
    images: List[ImageRetrieve]

class User(BaseModel):
    username: str
    password: str

class UserID(User):
    user_id: int

class UserHashed(BaseModel):
    username: str
    salt: str
    hash_password: str

class UserHashedIndex(UserHashed):
    user_id: int