# FastAPI Imports
import base64
from fastapi import FastAPI, Form, File, status, Depends, UploadFile, Cookie, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2 

# Other Imports
from typing import Annotated
from sqlite3 import Connection, Row
from database import get_user_rooms, get_room_by_id, create_user, get_user, delete_user, delete_room_by_id
from database import create_new_room, insertBLOB, readBlobData_by_id, update_room_by_id, delete_image_by_id
from models import UserRoomId, UserHashed, UserID, UserImage, Room 
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
import jwt as jwt
from pathlib import Path

# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# Set up DB Connection
connection = Connection('harmony.db', check_same_thread=False)
connection.row_factory = Row

# Configure Jinja2 Template Directory
templates = Jinja2Templates('./templates')

# JWT Configuration
# For prod save to environment variables
SECRET_KEY = "38271a4d89d6dd985ef820ef83aa2cd0a947f4f3622112ae456a04f5b6bbf65f"
ALGORITHM = "HS256"
EXPIRATION_TIME = 3600

def decrypt_access_token(access_token: str | None) -> dict[str, str | int] | None:
    if access_token is None:
        return None
    _, token = access_token.split()
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return data

class OAuthCookie(OAuth2):
    def __call__(self, request: Request) -> int | str | None:
        data = decrypt_access_token(request.cookies.get("access_token"))
        if data is None:
            return None
        return data["user_id"]       

oauth_cookie = OAuthCookie()
print(f"Cookie: {oauth_cookie}")
if oauth_cookie == '401':
    print("Unauthorized")
    RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/")
async def root(
    request: Request, access_token: Annotated[str |None, Cookie()] = None
)->HTMLResponse:
    context = {}
    print(f"Access Token: {access_token}")
    if access_token:
        context["login"] = True
    else:
        context["login"] = False
    print(context)
    return templates.TemplateResponse(request, "./index.html", context=context)

@app.get("/signup")
async def signup(
    request: Request, access_token: Annotated[str | None, Cookie()] = None
)->HTMLResponse:
    context = {"signup": True}
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./signup.html", context=context)


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
        
    response = RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", 
                        f"Bearer {token}",
                        samesite='lax',
                        expires=EXPIRATION_TIME
                        #set this to true for production
                        # httpOnly=True
                        #secure=True
                        )
    return response

@app.get("/logout")
async def logout(
    request: Request, 
    access_token: Annotated[str | None, Cookie()] = None):
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.delete("/delete_acct")
async def delete_acct(user: UserID):
    # delete all decor tables for user
    delete_user(connection, user.user_id)

@app.get("/home")
async def home(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
)->HTMLResponse:
    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
            print(f"user_id: {user_id} is viewing home")
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    context = get_user_rooms(connection, user_id).model_dump()
    #if len(context["rooms"]) == 0:
    #    return None
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./home.html", context=context)

@app.get("/rooms", response_model=None)
async def get_rooms(
        request: Request,
        access_token: Annotated[str | None, Cookie()] = None,
)->HTMLResponse | None:
    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    print(f"user_id: {user_id} is requesting rooms")
    context = get_user_rooms(connection, user_id).model_dump()
    print(context)
    #if len(context["rooms"]) == 0:
    #    return None
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./rooms.html", context=context)


@app.get("/add_room")
async def create_room(request: Request, user_id: int = Depends(oauth_cookie))->HTMLResponse:
    print(f"user_id: {user_id} is requesting to add a new room")
    return templates.TemplateResponse(request, "./add_room.html", context={})

@app.post("/add_room")
async def add_room(request: Request, room_name : Annotated[str, Form()], room_desc : Annotated[str, Form()], user_id : int  = Depends(oauth_cookie)):
    print("In edit POST")
    print(f"user_id: {user_id} is adding room with name: {room_name}, description: {room_desc}")
    room = UserRoomId(
        room_name = room_name,
        room_desc = room_desc,
        user_id = user_id
    )
    create_new_room(connection, room)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/edit_room/{room_id}")
async def edit_room(request: Request, room_id: int)->HTMLResponse:
    print("In edit GET")
    room = get_room_by_id(connection, room_id)
    print(room)
    images = readBlobData_by_id(connection, room_id)

    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')

    context = {"images": images, "room": room, "login": True}
    return templates.TemplateResponse(request, "./edit_room.html", context=context)

@app.post("/edit_room/{room_id}")
async def edit_room(
    request: Request,
    room_name : Annotated[str, Form()], 
    room_desc : Annotated[str, Form()],
    user_id : int  = Depends(oauth_cookie))-> HTMLResponse:
    room_id = request.path_params["room_id"]
    print(f"User is editing room with id: {room_id} and new name: {room_name}, description: {room_desc}")
    room = Room(
        room_id = room_id,
        room_name = room_name,
        room_desc = room_desc,
        user_id = user_id)
    print(room)
    update_room_by_id(connection, room)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

# Ask user for verification of delete before deleting a room
@app.get("/confirm_delete/{room_id}")
async def confirm_delete(request: Request, room_id: int)->HTMLResponse:
    print(f"Confirm delete of room with id: {room_id}")
    room = get_room_by_id(connection, room_id)
    print(room)
    return templates.TemplateResponse(request, "./confirm_delete.html", context={"request": request, "room_id": room_id, "room_name": room.room_name})

@app.get("/delete_room/{room_id}")
async def delete_room(request: Request, room_id: int)->HTMLResponse: 
    print(f"User is requesting to delete room with id: {room_id}")
    #room = get_room_by_id(connection, room_id)
    #print(room)
    delete_room_by_id(connection, room_id)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/delete_room/{room_id}")
async def delete_room(request: Request, room_id: int)->HTMLResponse:
    print(f"User is requesting to delete room with id: {room_id}")

    delete_room_by_id(connection, room_id)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/upload/{room_id}")
async def upload_image_form(
    request: Request, 
    room_id: int,
    access_token: Annotated[str | None, Cookie()] = None
)->HTMLResponse:
    print("In upload GET")
    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    context = {"request": request, "room_id": room_id, "access_token": access_token, "login": user_id is not None} 
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    print(f"User is requesting upload image form for room with id: {room_id}")
    return templates.TemplateResponse(request, "./upload_image.html", context=context)

@app.post("/upload/{room_id}")
async def upload(request: Request, 
           file: UploadFile = File(...),
           image_name: Annotated[str, Form()] = None,
           image_desc: Annotated[str, Form()] = None,
           access_token: Annotated[str | None, Cookie()] = None):
    print("In upload POST")
    filename = file.filename
    room_id = request.path_params["room_id"]

    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    print(f"User_id: {user_id}" )
    # save image to static/uploads/uploaded_filename
    try:
        contents = file.file.read()
        with open("./static/uploads/uploaded_" + file.filename, "wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()

    image_path = f"./static/uploads/uploaded_{filename}"
    file_ext = filename.split('.')[-1]

    image = UserImage(
        image_name = image_name,
        image_desc = image_desc,
        image_filename = image_path,
        image_type = file_ext,
        user_id = user_id,
        room_id = room_id
    )
    successful_insert = insertBLOB(connection, image)
    print(f"Image added: {successful_insert}")
    room = get_room_by_id(connection, room_id)    
    images = readBlobData_by_id(connection, room_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')

    context = {"images": images, "room": room, "login": True}
    return templates.TemplateResponse(request, "./edit_room.html", context=context)    

@app.get("/upload")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "./upload_image.html", context=context)

@app.get("/delete_image/{room_id}/{image_id}")
async def delete_image(request: Request, image_id: int)->HTMLResponse:
    room_id = request.path_params["room_id"]
    image_id = request.path_params["image_id"]
    print(f"User is requesting to delete image with id: {image_id}")
    room = get_room_by_id(connection, room_id)
    images = delete_image_by_id(connection, room_id, image_id)
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    print("Image deleted") 
    context = {"room": room, "images": images, "login": True}
    return templates.TemplateResponse(request, "./edit_room.html", context=context)