# FastAPI Imports
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2, OAuth2AuthorizationCodeBearer

# Other Imports
from typing import Annotated, Union
from sqlite3 import Connection, Row
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
from database import get_projects
from models import Projects, UserProjectId

# Initialize FastAPI
app = FastAPI()

# Configure Jinja2 Template Directory
templates = Jinja2Templates('./templates')

# Set up DB Connection
connection = Connection('harmony.db')
connection.row_factory = Row

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "./index.html", context={})

@app.get("/projects")
async def get_projects()->UserProjectId:
    return get_projects(connection)
