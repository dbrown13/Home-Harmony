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

class Decor(BaseModel):
    decor_name: str
    decor_type: str
    decor_desc: str
    user_id: int
    project_id: int

class DecorImages(Decor):
    decor_img_url: str
    decor_blob: bytes

class DecorID(DecorImages):
    decor_id: int

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