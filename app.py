# FastAPI Imports
from fastapi import FastAPI, Form, File, status, Depends, UploadFile, Cookie, HTTPException
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
from database import readBlobData_inner_join 
from database import update_image_by_id, update_user
from models import UserRoomId, UserHashed, UserID, UserImage, Room, ImageUpdate
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
import jwt as jwt
from pathlib import Path
import os
import base64

# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up database connection
connection = Connection('harmony.db')
connection.row_factory = Row

# Configure Jinja2 Template Directory
templates = Jinja2Templates('./templates')

# JWT Configuration
# For prod save to environment variables
SECRET_KEY = "38271a4d89d6dd985ef820ef83aa2cd0a947f4f3622112ae456a04f5b6bbf65f"
ALGORITHM = "HS256"
EXPIRATION_TIME = 3600

# Directory for image uploads
UPLOAD_DIR = Path("./static/uploads")

#####################################################################################################
# Authorization and Authentication                                                                  #
#####################################################################################################
"""
    Function to decrypt JWT access token
        Input: JWT access token
        Output: Decoded data if valid, None otherwise
"""
def decrypt_access_token(
        access_token: str | None
) -> dict[str, str | int] | None:
    if access_token is None:
        return None
    _, token = access_token.split()
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return data

"""
    OAuthCookie Class and instanciation of oauth_cookie
"""
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

#####################################################################################################
# Root (login), sign up, logout endpoints                                                           #
#####################################################################################################
"""
    Root endpoint for user login 
        Input: access token (should not exist)
        Output: Redirects to login page

"""
@app.get("/")
async def root(
    request: Request, 
    access_token: Annotated[str | None, Cookie()] = None
)->HTMLResponse:
    context = {}
    if access_token:
        context["login"] = True
    else:
        context["login"] = False
    return templates.TemplateResponse(request, "./index.html", context=context)

"""
    Endpoint called when user submits login form
        Input: username and password
        Output: Redirects to home page or displays error message if username or password is incorrect
"""
@app.post("/login")
async def login_user(
    request: Request, 
    username : Annotated[str, Form()], 
    password : Annotated[str, Form()]):      

    # See if user exists in the database
    user = get_user(connection, username.strip())
    # 
    if user is None:
        return templates.TemplateResponse(request, "./index.html", context={'incorrect_username': True, 'username': username})
    correct_pwd = pbkdf2_sha256.verify(password.strip() + user.salt, user.hash_password)
    # If password is incorrect, return error message
    if not correct_pwd:
        return templates.TemplateResponse(request, "./index.html", context={'incorrect_password': True})
    
    # If login is successful, generate JWT token and set cookie
    token = jwt.encode(
        {
            "username": user.username,
            "user_id": user.user_id
        }, 
        SECRET_KEY, algorithm=ALGORITHM)
    
    if user is not None:
        print(f"User {user.username} logged in")
        context = {"login": True}

    # Set cookie and redirect to home page
    response = templates.TemplateResponse(request, "./home.html", context=context)    
    response.set_cookie("access_token", 
                        f"Bearer {token}",
                        samesite='lax',
                        expires=EXPIRATION_TIME
                        #set this to true for production
                        # httpOnly=True
                        #secure=True
                        )
    return response

"""
    Endpoint for user signup  
        Input: None
        Output: Redirects to signup page  
"""
@app.get("/signup")
async def signup(
    request: Request, 
) -> HTMLResponse:
    context = {}
    return templates.TemplateResponse(request, "./signup.html", context=context)

"""
    Endpoint called from signup form (signup.html)
        Input: username, password
        Output: Redirect to home page if successful signup, else stay on signup page with error message
"""
@app.post("/signup")
async def add_user(
    request: Request, 
    username : Annotated[str, Form()], 
    password : Annotated[str, Form()]
):   
    # Check if username already exists in database
    if get_user(connection, username) is not None:
        return templates.TemplateResponse(request, "./signup.html", context={'taken': True, 'username': username})
    # If username does not exist, create new user in database
    # Generate a salt for new user
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
    # create new user in database
    create_user(connection, hashed_user)
    return RedirectResponse("./login", status_code=status.HTTP_303_SEE_OTHER)

"""
    Endpoint for user logout (clicked on nav bar)
        Input: None
        Output: Redirects to home page and logs out user (removes JWT token and cookie)
"""
@app.get("/logout")
async def logout(
    request: Request, 
    access_token: Annotated[str | None, Cookie()] = None):
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    os.environ['LOGIN_STATUS'] = 'False'
    #delete_uploaded_images()
    return response

#####################################################################################################
# Account management endpoints                                                                      #
#####################################################################################################
"""
    Endpoint to display account page for logged in user
        Input: user id (should be in JWT token)
        Output: Account page with user information
"""
@app.get("/get_account")
async def serve_user_form(
    request: Request,
    user_id: Annotated[int, Path()] = Depends(oauth_cookie)
)-> HTMLResponse:
    # Verify user in database
    user = get_user_by_id(connection, user_id)
    return templates.TemplateResponse(request, "./get_account.html", context={"user": user, "login": True})

"""
    Endpoint to verify current user information before allowing account update
        Input: user id (should be in JWT token), username, password
        Output: Redirects to account page to allow update
"""
@app.post("/get_account")
async def get_user_info(
    request: Request,
    username: Annotated[str, Form()] = None,
    password : Annotated[str, Form()] = None,
    user_id : Annotated[int, Path()] = Depends(oauth_cookie),
    )->HTMLResponse:
    #Verify account info
    user = get_user_by_id(connection, user_id)
    # Verify user exists  
    if user is None:
        print("User not found")
        context = {"user": user, "incorrect_username": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)
    # Verify entered password matches current password
    if not pbkdf2_sha256.verify(password + user.salt, user.hash_password):
        print("Incorrect password")
        context = {"user": user, "incorrect_password": True}
        return templates.TemplateResponse(request, "./get_account.html", context=context)

    context = {"user": user, "login": True}
    return templates.TemplateResponse(request, "./account.html", context=context)

"""
    Endpoint to update user information
        Input: user id (should be in JWT token), new username and/or new password
        Output: Redirects to account page with success message
"""
@app.post("/account")
async def get_user_info(
    request: Request,
    user_id : Annotated[int, Path()] = Depends(oauth_cookie),
    username : Annotated[str, Form()] = None,
    password : Annotated[str, Form()] = None,
)->HTMLResponse:
    print(f"user_id: {user_id} is requesting account update")
    user = get_user_by_id(connection, user_id)
    if user is None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    # See if username changed
    # Remove leading and trailing whitespace from username
    user.username = user.username.strip()
    username = username.strip()
    if user.username != username:
        # Check if new username already exists
        existing_user = get_user(connection, username)
        if existing_user is not None:
            return templates.TemplateResponse(request, "./account.html", context={'taken': True, 'user': user})
        # update username in user model
        user.username = username
    if password:
        # update password in user model
        user.hash_password = pbkdf2_sha256.hash(password + user.salt)
    # update user in database   
    update_user(connection, user) 
    return templates.TemplateResponse(request, "./account.html", context={'success': True, 'user': user})

"""
    Endpoint to update username
        Input: user id (should be in JWT token), new username
        Output: Redirects to account page with success message or error message if username is taken
"""
@app.post("/update_username")
async def update_username(
    request: Request,
    user: UserID,
    new_username : Annotated[str, Form()]
)->HTMLResponse:
    print(f"User {user.username} is updating username to {new_username}")
    # check if current user exists
    user = get_user_by_id(connection, user.user_id)
    # if not, redirect to login page  
    if user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    # check if new username already exists
    existing_user = get_user(connection, new_username)
    # if username is taken, return error message  
    if existing_user is not None:
        return templates.TemplateResponse(request, "./account.html", context={'username_taken': True})
    # update username in database
    user.username = new_username
    update_user(connection, user)
    return RedirectResponse("/account", status_code=status.HTTP_303_SEE_OTHER)

"""
    Endpoint to delete user account
        Input: user id (should be in JWT token)
        Output: Redirects to root (login) page and logs out user (removes JWT token and cookie)
"""
@app.get("/delete_account")
async def delete_account(
    request: Request,
    userID: UserID = Depends(oauth_cookie),
)->HTMLResponse:
    print(f"User {userID} is deleting account")
    delete_user(connection, userID)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

#####################################################################################################
# Home Page and Room Management endpoints                                                           #
#####################################################################################################

"""
    Endpoint to display user's home page
        Input: user id (should be in JWT token)
        Output: Home page 
"""
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

"""
    Endpoint to display user's room page
        Input: user id (should be in JWT token), room id
        Output: Room page
"""
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
    # Datbase query to get rooms for user
    context = get_user_rooms(connection, user_id).model_dump()

    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./rooms.html", context=context)

"""
    Endpoint to display add room form
        Input: user id (should be in JWT token)
        Output: Add room form
"""
@app.get("/add_room")
async def create_room(request: Request, user_id: int = Depends(oauth_cookie))->HTMLResponse:
    print(f"user_id: {user_id} is requesting to add a new room")
    context = {'login': True}
    return templates.TemplateResponse(request, "./add_room.html", context=context)

"""
    Endpoint to handle adding a new room to the database
        Input: user id (should be in JWT token), room details
        Output: Redirects to rooms page with success message
"""
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
    # Create new room in database
    create_new_room(connection, room)
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

"""
    Endpoint to display edit room form
        Input: user id (should be in JWT token), room id
        Output: Edit room form with room details and images
"""
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

"""
    Endpoint to handle editing a room in the database
        Input: user id (should be in JWT token), room id, updated room details
        Output: Redirects to rooms page with success message        
"""
@app.post("/edit_room/{room_id}")
async def edit_room(
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
)-> HTMLResponse:
    room_id = request.path_params["room_id"]
    print(f"User is editing room with id: {room_id} and new name: {room_name}, description: {room_desc}")
    # Update room in database
    room = Room(
        room_id = room_id,
        room_name = room_name,
        room_desc = room_desc,
        room_num_walls = room_num_walls,
        room_wall_color1 = room_wall_color1,
        room_wall_color2 = room_wall_color2,
        room_ceiling_color = room_ceiling_color,
        room_floor_color = room_floor_color,
        room_trim_color = room_trim_color,
        room_other_details = room_other_details,
        user_id = user_id)
    update_room_by_id(connection, room)
    print("after database update")
    return RedirectResponse("/rooms", status_code=status.HTTP_303_SEE_OTHER)

""" 
@app.get("/confirm_delete/{room_id}")
async def confirm_delete(request: Request, room_id: int)->HTMLResponse:
    print(f"Confirm delete of room with id: {room_id}")
    room = get_room_by_id(connection, room_id)
    return templates.TemplateResponse(request, "./confirm_delete.html", context={"request": request, "room_id": room_id, "room_name": room.room_name})
 """
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

##################################################################################################### 
#  Image Management Endpoints                                                                       #
#####################################################################################################
"""
    Endpoint to display room images
        Input: user id (should be in JWT token), room id
        Output: Room images page with images and delete option if user is owner
"""
@app.get("/room_images/{room_id}")
async def room_images(request: Request, room_id: int)->HTMLResponse:
    room_id = request.path_params["room_id"]
    print(f"room_image: User is requesting images for room with id: {room_id}")
    # Retrieve room information from database
    room = get_room_by_id(connection, room_id)
    # Retrieve images for the room from database and convert binary data to base64 for display in HTML
    images = readBlobData_by_room_id(connection, room_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"images": images, "room": room, "login": True, "image_msg": None}
    return templates.TemplateResponse(request, "./room_images.html", context=context)

"""
    Endpoint to handle display of all user images by room
        Input: user id (should be in JWT token)
        Output: All user images page with images
"""
@app.get("/all_images")
async def all_images(
    request: Request,
    user_id : int  = Depends(oauth_cookie)
)->HTMLResponse:
    print(f"User {{user_id}} is requesting all images")
    images = readBlobData_inner_join(connection, user_id)
    context = get_user_rooms(connection, user_id).model_dump()
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context["images"] = images
    context["login"] = True
    return templates.TemplateResponse(request, "./all_images.html", context=context)

"""
    Endpoint to display image upload form
        Input: room_id (from url), user id (should be in JWT token), room name and description (optional)
        Output: Redirects to room images upload form
"""
@app.post("/upload_image_form/{room_id}")
async def upload_image_form(
    request: Request,
    user_id: int = Depends(oauth_cookie),
    room_name : Annotated[str, Form()] = None, 
    room_desc : Annotated[str, Form()] = None
)->HTMLResponse:
    room_id = request.path_params["room_id"]
    context = {"request": request, "room_id": room_id, "user_id": user_id, "login": user_id is not None, "image_msg": None} 
    assert isinstance(user_id, int) or user_id is None, "Invalid access token"
    print(f"Upload_image_form: User is requesting upload image form for room with id: {room_id}")
    return templates.TemplateResponse(request, "./upload_image.html", context=context)

"""
    Endpoint to handle image upload
      Input: room_id (from url), user id (should be in JWT token), image name, image description, and uploaded image file
      Output: Redirects to room images page with success message
"""
@app.post("/upload_image/{room_id}")
async def upload(
    request: Request,
    image_name: Annotated[str, Form()],
    image_desc: Annotated[str, Form()],
    file: UploadFile = File(...),
    user_id: int = Depends(oauth_cookie),
)->HTMLResponse:
    # get filename from file info
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

    # set upload path and get file extension from file info
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
    # insert image into database 
    successful_insert = insertBLOB(connection, image)
    if successful_insert:
        image_msg = "Image uploaded successfully"
    else:
        image_msg = "Image upload failed"

    # Get room information and images from database for display in HTML
    room = get_room_by_id(connection, room_id)    
    # Get images for the room from database and convert binary data to base64 for display in HTML
    images = readBlobData_by_room_id(connection, room_id)
    # Convert binary data to base64 for display in HTML
    for item in images["images"]:
        item.image_data = base64.b64encode(item.image_data).decode('utf-8')
    context = {"room": room, "images": images, "image_msg": image_msg, "login": True}
    return templates.TemplateResponse(request, "./room_images.html", context=context)

"""
    Endpoint to display edit image form
        Input: room_id (from url)
        Output: Redirects to edit image form
"""
@app.get("/upload")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "./upload_image.html", context=context)
""" 
@app.get("/upload_success")
async def upload_success(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "./upload_success.html", context={}) """

"""
    Endpoint to display edit image form
        Input: room_id (from url), image_id (from url)
        Output: Redirects to edit image form
"""
@app.get("/edit_image/{room_id}/{image_id}")
async def edit_image(
    request: Request, 
)->HTMLResponse:
    room_id = request.path_params["room_id"]
    image_id = request.path_params["image_id"]
    print(f"User is requesting to edit image with id: {image_id}")
    # Retrieve room information and image information from database for display in HTML
    room = get_room_by_id(connection, room_id)
    image = readBlobData_by_id(connection, image_id)
    # Convert binary data to base64 for display in HTML
    image.image_data = base64.b64encode(image.image_data).decode('utf-8')
    context = {"room": room, "image": image, "login": True}
    return templates.TemplateResponse(request, "./edit_image.html", context=context)

""" 
    Endpoint to handle image edit
    Input: room_id (from url), image_id (from url), new image name and description (optional)
    Output: Redirects to room images page with success message
"""
@app.post("/edit_image/{room_id}/{image_id}")
async def edit_image(
    request: Request, 
    room_id: int, 
    image_id: int, 
    image_name: Annotated[str, Form()] = None, 
    image_desc: Annotated[str, Form()] = None
)->HTMLResponse:
    print(f"User is editing image with id: {image_id} and new name: {image_name}, description: {image_desc}")
    image = ImageUpdate(
        image_id = image_id,
        image_name = image_name,
        image_desc = image_desc
    )
    successful = update_image_by_id(connection, image)
    return RedirectResponse(f"/room_images/{room_id}", status_code=status.HTTP_303_SEE_OTHER)

"""
    Endpoint to handle image deletion   
        Input: room_id (from url), image_id (from url)
        Output: Redirects to room images page with success message
"""
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

#####################################################################################################
# Contact Form Endpoints                                                                            #
#####################################################################################################
"""
    Endpoint to display contact form
        Input: 
        Output: Redirects to contact form
"""
@app.get("/contact")
async def contact(
    request: Request
)->HTMLResponse:
    context = {"login": True}
    user_id = None
    access_token = request.cookies.get("access_token")
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    context["user_id"] = user_id
    return templates.TemplateResponse(request, "./contact.html", context=context)

"""
    Endpoint to handle contact form submission
        Input: email and message
        Output: Redirects to contact form with success message
"""
@app.post("/contact")
async def contact(
    request: Request, 
    email: Annotated[str, Form()],
    message: Annotated[str, Form()]
)->HTMLResponse:
       context = {'submitted': True, 'email': email,'message': message}
       return templates.TemplateResponse(request, "./contact.html", context=context)