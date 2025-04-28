# FastAPI Imports
import base64
import shutil
from fastapi import FastAPI, Form, File, status, Depends, UploadFile, Cookie, HTTPException
from fastapi import requests
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2 

# Other Imports
from typing import Annotated
from sqlite3 import Connection, Row
from database import get_user_rooms, get_room_by_id, create_user, get_user, get_user_by_id, delete_user, delete_room_by_id
from database import create_new_room, insertBLOB, readBlobData_by_room_id, readBlobData_by_id, update_room_by_id, delete_image_by_id
from database import update_image_by_id, readBlobData_by_user_id, delete_uploaded_images, update_user
from models import UserRoomId, UserHashed, UserID, UserImage, Room, ImageUpdate
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
import jwt as jwt
from pathlib import Path
import os
import requests


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

UPLOAD_DIR = Path("./static/uploads")


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
if oauth_cookie == '401':
    print("Unauthorized")
    RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/")
async def root(
    request: Request, access_token: Annotated[str |None, Cookie()] = None
)->HTMLResponse:
    context = {}
    if access_token:
        context["login"] = True
    else:
        context["login"] = False
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
    hash_password = pbkdf2_sha256.hash(password.strip() + salt)
    # update database
    hashed_user = UserHashed(
        username = username.strip(),
        salt = salt,
        hash_password = hash_password
    )
    create_user(connection, hashed_user)
    # create decor table for user
    return RedirectResponse("./login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/get_account")
async def serve_user_form(
    request: Request,
    user_id: Annotated[int, Path()] = Depends(oauth_cookie)
)-> HTMLResponse:
    user = get_user_by_id(connection, user_id)
    return templates.TemplateResponse(request, "./get_account.html", context={"user": user, "login": True})

@app.post("/get_account")
async def get_user_info(
    request: Request,
    username: Annotated[str, Form()] = None,
    password : Annotated[str, Form()] = None,
    user_id : Annotated[int, Path()] = Depends(oauth_cookie),
    )->HTMLResponse:
    print(f"APP - /get_account")
    #Verify account info
    user = get_user_by_id(connection, user_id)
    print(f"username: {user.username}")
    if user is None:
        print("User not found")
        context = {"user": user, "incorrect_username": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)
    if not pbkdf2_sha256.verify(password + user.salt, user.hash_password):
        print("Incorrect password")
        context = {"user": user, "incorrect_password": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)

    print("User found")
    context = {"user": user, "login": True}
    return templates.TemplateResponse(request, "./account.html", context=context)

""" @app.get("/account")
async def get_update_page(
    request: Request,
    user_id : Annotated[int, Path()] = Depends(oauth_cookie),
    username: Annotated[str, Form()] = None,
    password : Annotated[str, Form()] = None
)->HTMLResponse:
    print(f"APP - /account  GET")
    print(f"username: {username}")
    #Verify login info
    user = get_user_by_id(connection, user_id)
    print(f"username: {user.username}")
    if user is None:
        print("User not found")
        context = {"incorrect_username": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)
    if not pbkdf2_sha256.verify(password + user.salt, user.hash_password):
        print("Incorrect password")
        context = {"incorrect_password": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)

    print("User found")
    context = {"user": user, "login": True}
    
    return templates.TemplateResponse(request, "./account.html", context=context)
 """
@app.post("/account")
async def get_user_info(
    request: Request,
    user_id : Annotated[int, Path()] = Depends(oauth_cookie),
    username : Annotated[str, Form()] = None,
    password : Annotated[str, Form()] = None,
)->HTMLResponse:
    print(f"user_id: {user_id} is requesting account update")
    print(f"username: {username}")
    print(f"password: {password}")
    user = get_user_by_id(connection, user_id)
    if user is None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    # See if username changed
    print("user is not None")
    print(f"username: {username}")
    print(f"user.username: {user.username}")
    # Remove leading and trailing whitespace from username
    user.username = user.username.strip()
    username = username.strip()
    if user.username != username:
        # Check if new username already exists
        existing_user = get_user(connection, username)
        print(f"existing_user: {existing_user}")
        if existing_user is not None:
            return templates.TemplateResponse(request, "./account.html", context={'taken': True, 'user': user})
        # update username in user model
        user.username = username
    if password:
        # update password in user model
        print(f"update password")
        user.hash_password = pbkdf2_sha256.hash(password + user.salt)
    # update user in database   
    update_user(connection, user) 
    return templates.TemplateResponse(request, "./account.html", context={'success': True, 'user': user})

@app.get("/login")
async def login(request: Request)->HTMLResponse:
    return templates.TemplateResponse(request, "./index.html", context={})


@app.post("/login")
async def login_user(request: Request, username : Annotated[str, Form()], password : Annotated[str, Form()]):      
    print(f"APP - /login")
    user = get_user(connection, username.strip())
    if user is None:
        return templates.TemplateResponse(request, "./index.html", context={'incorrect_username': True, 'username': username})
    correct_pwd = pbkdf2_sha256.verify(password.strip() + user.salt, user.hash_password)
    if not correct_pwd:
        return templates.TemplateResponse(request, "./index.html", context={'incorrect_password': True})
    
    token = jwt.encode(
        {
            "username": user.username,
            "user_id": user.user_id
        }, 
        SECRET_KEY, algorithm=ALGORITHM)
    
    if user is not None:
        print(f"User {user.username} logged in")
        os.environ['LOGIN_STATUS'] = 'True'
        context = {"login": True}

    response = templates.TemplateResponse(request, "./home.html", context=context)    
    #response = RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
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
    os.environ['LOGIN_STATUS'] = 'False'
    #delete_uploaded_images()
    return response

@app.post("/update_username")
async def update_username(
    request: Request,
    user: UserID,
    new_username : Annotated[str, Form()]
)->HTMLResponse:
    print(f"User {user.username} is updating username to {new_username}")
    # check if user exists
    user = get_user_by_id(connection, user.user_id)
    if user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    # check if new username already exists
    existing_user = get_user(connection, new_username)
    if existing_user is not None:
        return templates.TemplateResponse(request, "./account.html", context={'username_taken': True})
    # update username in database
    user.username = new_username
    update_user(connection, user)
    return RedirectResponse("/account", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/delete_acct")
async def delete_acct(
    request: Request,
    user: UserID = Depends(oauth_cookie),
)->HTMLResponse:
    delete_user(connection, user.user_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

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

    #if len(context["rooms"]) == 0:
    #    return None
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./rooms.html", context=context)


@app.get("/add_room")
async def create_room(request: Request, user_id: int = Depends(oauth_cookie))->HTMLResponse:
    print(f"user_id: {user_id} is requesting to add a new room")
    context = {}
    context["login"] = True
    return templates.TemplateResponse(request, "./add_room.html", context=context)

@app.post("/add_room")
async def add_room(
    request: Request, 
    room_name : Annotated[str, Form()], 
    room_desc : Annotated[str, Form()], 
    room_num_walls : Annotated[int, Form()],
    room_wall_color1 : Annotated[str, Form()],
    room_wall_color2 : Annotated[str, Form()],
    room_ceiling_color : Annotated[str, Form()],
    room_floor_color : Annotated[str, Form()],
    room_trim_color : Annotated[str, Form()],
    room_other_details : Annotated[str, Form()],
    user_id : int  = Depends(oauth_cookie)
):
    print(f"user_id: {user_id} is adding room with name: {room_name}, description: {room_desc}")
    room = UserRoomId(
        room_name = room_name,
        room_desc = room_desc,
        room_num_walls = room_num_walls,
        room_wall_color1 = room_wall_color1,
        room_wall_color2 = room_wall_color2,
        room_ceiling_color = room_ceiling_color,
        room_floor_color = room_floor_color,
        room_trim_color = room_trim_color,
        room_other_details = room_other_details,
        user_id = user_id
    )
    create_new_room(connection, room)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/edit_room/{room_id}")
async def edit_room(request: Request, room_id: int)->HTMLResponse:
    room = get_room_by_id(connection, room_id)
    images = readBlobData_by_room_id(connection, room_id)
    print(f"User is requesting to edit room with id: {room_id}")
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
    update_room_by_id(connection, room)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/room_images/{room_id}")
async def room_images(request: Request, room_id: int)->HTMLResponse:
    room_id = request.path_params["room_id"]
    print(f"room_image: User is requesting images for room with id: {room_id}")
    room = get_room_by_id(connection, room_id)
    images = readBlobData_by_room_id(connection, room_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"images": images, "room": room, "login": True, "image_msg": None}
    return templates.TemplateResponse(request, "./room_images.html", context=context)

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
    delete_room_by_id(connection, room_id)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/delete_room/{room_id}")
async def delete_room(request: Request, room_id: int)->HTMLResponse:
    print(f"User is requesting to delete room with id: {room_id}")

    delete_room_by_id(connection, room_id)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/all_images")
async def all_images(
    request: Request,
    user_id : int  = Depends(oauth_cookie))->HTMLResponse:
    print(f"User is requesting all images")
    images = readBlobData_by_user_id(connection, user_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"images": images, "login": True}
    return templates.TemplateResponse(request, "./all_images.html", context=context)

@app.post("/upload_image_form/{room_id}")
async def upload_image_form(
    request: Request,
    room_id: int = None,
    user_id: int = Depends(oauth_cookie),
    room_name : Annotated[str, Form()] = None, 
    room_desc : Annotated[str, Form()] = None
)->HTMLResponse:
    room_id = request.path_params["room_id"]
    context = {"request": request, "room_id": room_id, "user_id": user_id, "login": user_id is not None, "image_msg": None} 
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    print(f"Upload_image_form: User is requesting upload image form for room with id: {room_id}")
    print(f"Context: {context}")
    return templates.TemplateResponse(request, "./upload_image.html", context=context)

@app.post("/newupload_image/{room_id}")
async def upload_image(
    request: Request,
    image_name: Annotated[str, Form()],
    image_desc: Annotated[str, Form()],
    image_msg: Annotated[str, Form()],
    file: UploadFile = File(...),
    user_id: int = Depends(oauth_cookie),
)->HTMLResponse:
    room_id = request.path_params["room_id"]
    print(f"filename: {file.filename}")


    # Create the uploads directory if it doesn't exist
    # and save the file to that directory
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = UPLOAD_DIR + file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_path = f"./static/uploads/uploaded_{file.filename}"
        file_ext = file.filename.split('.')[-1]

        image = UserImage(
            image_name = image_name,
            image_desc = image_desc,
            image_filename = image_path,
            image_type = file_ext,
            user_id = user_id,
            room_id = room_id
        )
        print(f"Image: {image}")
        insertBLOB(connection, image)
            
        print(f"File {file.filename} uploaded successfully to {file_path}")
    except Exception as e:
        print(f"Error while uploading: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@app.post("/upload_image/{room_id}")
async def upload(
    request: Request,
    image_name: Annotated[str, Form()],
    image_desc: Annotated[str, Form()],
    file: UploadFile = File(...),
    user_id: int = Depends(oauth_cookie),
    )->HTMLResponse:
    print(f"filename: {file.filename}")

    filename = file.filename
    room_id = request.path_params["room_id"]

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
    if successful_insert:
        image_msg = "Image uploaded successfully"
    else:
        image_msg = "Image upload failed"

    room = get_room_by_id(connection, room_id)    
    images = readBlobData_by_room_id(connection, room_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"room": room, "images": images, "image_msg": image_msg, "login": True}
    #return templates.TemplateResponse(request, "./upload_success.html", context=context)
    return templates.TemplateResponse(request, "./room_images.html", context=context)

@app.get("/upload")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "./upload_image.html", context=context)

@app.get("/upload_success")
async def upload_success(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "./upload_success.html", context={})

@app.get("/edit_image/{room_id}/{image_id}")
async def edit_image(request: Request, room_id: int, image_id: int)->HTMLResponse:
    print(f"User is requesting to edit image with id: {image_id}")
    room = get_room_by_id(connection, room_id)
    image = readBlobData_by_id(connection, image_id)
    # Convert binary data to base64 for display in HTML
    image.image_data = base64.b64encode(image.image_data).decode('utf-8')
    context = {"room": room, "image": image, "login": True}
    return templates.TemplateResponse(request, "./edit_image.html", context=context)

@app.post("/edit_image/{room_id}/{image_id}")
async def edit_image(request: Request, room_id: int, image_id: int, image_name: Annotated[str, Form()] = None, image_desc: Annotated[str, Form()] = None)->HTMLResponse:
    print(f"User is editing image with id: {image_id} and new name: {image_name}, description: {image_desc}")
    image = ImageUpdate(
        image_id = image_id,
        image_name = image_name,
        image_desc = image_desc
    )
    successful = update_image_by_id(connection, image)
    return RedirectResponse(f"/room_images/{room_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/delete_image/{room_id}/{image_id}")
async def delete_image(request: Request, image_id: int)->HTMLResponse:
    room_id = request.path_params["room_id"]
    image_id = request.path_params["image_id"]
    print(f"User is requesting to delete image with id: {image_id}")
    room = get_room_by_id(connection, room_id)
    images = delete_image_by_id(connection, room_id, image_id)
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"room": room, "images": images, "login": True}
    return templates.TemplateResponse(request, "./room_images.html", context=context)

@app.get("/contact")
async def contact(request: Request)->HTMLResponse:
    context = {}
    user_id = None
    access_token = request.cookies.get("access_token")
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    context["user_id"] = user_id
    return templates.TemplateResponse(request, "./contact.html", context=context)