# FastAPI Imports
from fastapi import FastAPI, Form, status, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2, OAuth2AuthorizationCodeBearer

# Other Imports
from typing import Annotated, Union, List
from sqlite3 import Connection, Row
from database import get_user_projects, get_project_by_id, create_user, get_user, delete_user
from models import Project, Projects, UserProjectId, User, UserHashed, UserID
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
import jwt as jwt
import os

# Initialize FastAPI
app = FastAPI()
# Set up DB Connection
connection = Connection('harmony.db')
connection.row_factory = Row

# Configure Jinja2 Template Directory
templates = Jinja2Templates('./templates')

# JWT Configuration
# For prod save to environment variables
SECRET_KEY = "38271a4d89d6dd985ef820ef83aa2cd0a947f4f3622112ae456a04f5b6bbf65f"
ALGORITHM = "HS256"
EXPIRATION_TIME = 3600

class OAuthCookie(OAuth2):
    def __call__(self, request: Request) -> int:
        _,token = request.cookies.get("access_token").split()
        if not token:
            return status.HTTP_401_UNAUTHORIZED
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data.get("user_id")
        
oauth_cookie = OAuthCookie()

"""
This function handles the signup route. It renders the signup.html template.

Parameters:
- request: A FastAPI Request object that contains information about the incoming request.

Returns:
- An HTMLResponse object containing the rendered signup.html template.
"""
@app.get("/signup")
async def signup(request: Request)->HTMLResponse:
    return templates.TemplateResponse(request, "./signup.html", context={})


@app.post("/signup")
async def add_user(request: Request, username : Annotated[str, Form()], password : Annotated[str, Form()]):   
    if get_user(connection, username) is not None:
        return templates.TemplateResponse(request, "./signup.html", context={'taken': True, 'username': username})
    # generate a salt for new user
    hex_int = 15
    salt = token_hex(hex_int)
    # hash users password
    hash_password = pbkdf2_sha256.hash(password + salt)
    # update database
    hashed_user = UserHashed(
        username = username,
        salt = salt,
        hash_password = hash_password
    )
    create_user(connection, hashed_user)
    # create decor table for user
    return RedirectResponse("./login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login")
async def login(request: Request)->HTMLResponse:
    return templates.TemplateResponse(request, "./login.html", context={})

@app.post("/login")
async def login_user(request: Request, username : Annotated[str, Form()], password : Annotated[str, Form()]):      
    user = get_user(connection, username)
    if user is None:
        return templates.TemplateResponse(request, "./login.html", context={'incorrect_username': True, 'username': username})
    correct_pwd = pbkdf2_sha256.verify(password + user.salt, user.hash_password)
    if not correct_pwd:
        return templates.TemplateResponse(request, "./login.html", context={'incorrect_password': True})
    
    token = jwt.encode(
        {
            "username": user.username,
            "user_id": user.user_id
        }, 
        SECRET_KEY, algorithm=ALGORITHM)
        
    response = RedirectResponse("/projects", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", 
                        f"Bearer {token}",
                        samesite='lax',
                        expires=EXPIRATION_TIME
                        #set this to true for production
                        # httpOnly=True
                        #secure=True
                        )
    return response

@app.delete("/delete_acct")
async def delete_acct(user: UserID):
    # delete all decor tables for user
    delete_user(connection, user.user_id)

@app.get("/")
async def home(request: Request)->HTMLResponse:
    return templates.TemplateResponse(request, "./index.html", context={})

@app.get("/projects")
async def get_projects(request: Request, user_id: int  = Depends(oauth_cookie))->HTMLResponse:
    print(f"user_id: {user_id} is requesting projects")
    print(type(user_id))
    projects = get_user_projects(connection, user_id)
    return templates.TemplateResponse(request, "./projects.html", context=projects.model_dump())

@app.get("/edit_project/{proj_id}")
async def edit_project(request: Request, proj_id: int)->HTMLResponse:
    projects = get_project_by_id(connection, proj_id)
    #project = {
    #    'project_title' : 'test project',
    #    'project_desc' : 'test description'
    #}
    return templates.TemplateResponse(request, "./edit_project.html", context=projects.model_dump())