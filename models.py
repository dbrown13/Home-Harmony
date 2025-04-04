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