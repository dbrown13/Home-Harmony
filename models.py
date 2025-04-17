from pydantic import BaseModel
from typing import List

class UserProject(BaseModel):
    project_title: str
    project_desc: str

class UserProjectId(UserProject):
    user_id: int

class Project(UserProjectId):
    project_id: int

class Projects(BaseModel):
    projects: List[Project]

class Image(BaseModel):
    image_title: str
    image_desc: str
    image_filename: str
    image_type: str
    project_id: int

class UserImage(Image):
    user_id: int

class ImageId(UserImage):
    image_id: int

class ImageRetrieve(BaseModel):
    image_id: int
    image_title: str
    image_desc: str
    image_data: bytes
    image_type: str
    project_id: int
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