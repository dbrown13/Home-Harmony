import sqlite3
from sqlite3 import Connection
from typing import Union
from models import Room, Rooms, UserRoomId, UserHashed, UserHashedIndex, UserImage, ImageRetrieve, ImageUpdate, Images, UserRoomName, RoomNames
from models import ImageJoin
import os
import shutil

#####################################################################################################
# User functions (CRUD)                                                                             # 
#####################################################################################################
"""
    This function creates a new user in the database.
    Parameters: 
        connection (Connection): The database connection to use.
        user (UserHashed): The user to create.
    Returns:
        bool: True if the user was created successfully, False otherwise.
"""
def create_user(connection: Connection,
                user: UserHashed)->bool:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO users (username, salt, hash_password)
            VALUES
            ( :username, :salt, :hash_password)
            """,
            user.model_dump()
        )
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        print("Database: User already exists")
        return False


"""
    This function retrieves a user from the database by their username.
    Parameters: 
        connection (Connection): The database connection to use.
        username (str): The username of the user to retrieve.
    Returns:
        Union[UserHashedIndex, None]: The user if found, None otherwise.
"""
# Get User from database by username
def get_user(
        connection: Connection,
        username: str
)->Union[UserHashedIndex, None]:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT user_id, username, salt, hash_password
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        user = cur.fetchone()
        if user is None:
            return None
        return UserHashedIndex(**dict(user))
    except sqlite3.Error as e:
        print(f"Database: Error getting user: {e}")
        return None

"""
    This function retrieves a user from the database by their user_id.
    Parameters: 
        connection (Connection): The database connection to use.
        user_id (int): The id of the user to retrieve.
    Returns:
        Union[UserHashedIndex, None]: The user if found, None otherwise.
"""
def get_user_by_id(connection: Connection,
                   user_id: int)->Union[UserHashedIndex, None]:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT user_id, username, salt, hash_password
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        user = cur.fetchone()
        if user is None:
            return None
        # Return the user as a UserHashedIndex object - unpacked 
        return UserHashedIndex(**dict(user))
    except sqlite3.Error as e:
        print(f"Database: Error getting user by id: {e}")
        return None

"""
    This function updates a user in the database.
    Parameters: 
        connection (Connection): The database connection to use.
"""
def update_user(connection: Connection,
                   user: UserHashed)->bool:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            UPDATE users
            SET username = ?, salt = ?, hash_password = ?
            WHERE user_id = ?
            """,
            (user.username, user.salt, user.hash_password, user.user_id)
        )
        connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database: Error updating user: {e}")
        return False

"""
    This function deletes a user from the database.
    Parameters: 
        connection (Connection): The database connection to use.
        user_id (int): The id of the user to delete.
    Returns:
        bool: True if the user was deleted successfully, False otherwise.
"""
def delete_user(connection: Connection,
                user_id: int)->bool:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            DELETE FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database: Error deleting user: {e}")
        return False
#####################################################################################################
# Room functions (CRUD)                                                                             # 
#####################################################################################################
"""
    This function creates a new room in the database.
    Parameters:
        connection (Connection): The database connection to use.
        room (UserRoomId): The room to create.
    Returns:
        bool: True if the room was created successfully, False otherwise.
"""
def create_new_room(connection: Connection, 
                   room: UserRoomId):
    try:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO rooms (room_name, room_desc, room_num_walls, room_wall_color1, room_wall_color2, room_ceiling_color, room_floor_color, room_trim_color, room_other_details, user_id)
            VALUES
            ( :room_name, :room_desc, :room_num_walls, :room_wall_color1, :room_wall_color2, :room_ceiling_color, :room_floor_color, :room_trim_color, :room_other_details, :user_id)
            """,
            room.model_dump()
        )
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        print("Database: Room already exists")
        return False

"""
    This function retrieves a room from the database by their room_id.
    Parameters:
        connection (Connection): The database connection to use.
        room_id (int): The id of the room to retrieve.
    Returns:
        Union[Room, None]: The room if found, None otherwise.
"""
def get_rooms(connection: Connection)->Rooms:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT *
            FROM rooms;
            """
        )
        return Rooms(rooms = [Room.model_validate(dict(room)) for room in cur])
    except sqlite3.Error as e:
        print(f"Database: Error getting rooms: {e}")
        return None

"""
    This function retrieves all rooms from the database for a user_id.
    Parameters:
        connection (Connection): The database connection to use.
        user_id (int): user_id of the user whose rooms to retrieve.
    Returns:
        Rooms: List of rooms if found, None otherwise.
"""
def get_user_rooms(connection: Connection, user_id: int)->Rooms:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT room_id, room_name, room_desc, room_num_walls, room_wall_color1, room_wall_color2, room_ceiling_color, room_floor_color, room_trim_color, room_other_details, user_id
            FROM rooms
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return Rooms(rooms = [Room.model_validate(dict(room)) for room in cur])
    except sqlite3.Error as e:
        print(f"Database: Error getting user rooms: {e}")
        return None

"""
    This function retrieves a room by room_id.
    Parameters:
        connection (Connection): The database connection to use.
        room_id (int): The id of the room to retrieve.
    Returns:
        Room: The room if found, None otherwise.
"""
def get_room_by_id(connection: Connection, room_id: int)->Room:
    try:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT room_name, room_desc, room_num_walls, room_wall_color1, room_wall_color2, room_ceiling_color, room_floor_color, room_trim_color, room_other_details, user_id, room_id
            FROM rooms
            WHERE room_id = ?
            LIMIT 1
            """,
            (room_id,),
        )
        return Room.model_validate(dict(cur.fetchone()))
    except sqlite3.Error as e:
        print(f"Database: Error getting room by id: {e}")
        return None

def update_room_by_id(
        connection: Connection, 
        room: Room)->bool:
    
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            UPDATE rooms
            SET room_name =?, room_desc =?
            WHERE room_id =?
            """,
            (room.room_name, room.room_desc, room.room_id)
        )
        connection.commit()
        return True
    
def delete_room_by_id(connection: Connection, room_id: int)->bool:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            DELETE FROM rooms
            WHERE room_id = ?
            """,
            (room_id,),
        )
        connection.commit()
        #return Rooms(rooms = [Room.model_validate(dict(room)) for room in cur])
        return True
    
def add_image(connection: Connection, image: UserImage)->bool:

    # Insert the image into the database
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO images (image_name, image_desc, image_data, user_id, room_id)
            VALUES
            ( :image_name, :image_desc, :image_data, :user_id, :room_id)
            """,
            image.model_dump()
        )
    connection.commit()
    return True

def get_images_by_room_id(connection: Connection, room_id: int)->Images:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT image_name, image_desc, image_data, user_id, room_id
            FROM images
            WHERE room_id =?
            """,
            (room_id,),
        )
        return Images(images = [UserImage.model_validate(dict(image)) for image in cur])

def get_image_by_id(connection: Connection, image_id: int)->ImageRetrieve:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT image_id, image_name, image_desc, image_data, user_id, room_id
            FROM images
            WHERE image_id =?
            """,
            (image_id,),
        )
        return ImageRetrieve.model_validate(dict(cur.fetchone()))
    

def update_image_by_id(
        connection: Connection,
        image: ImageUpdate)->bool:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            UPDATE images
            SET image_name =?, image_desc =?
            WHERE image_id =?
            """,
            (image.image_name, image.image_desc, image.image_id)
        )
        connection.commit()
        return True
    
def convertToBinaryData(filename):
    # Convert digital data to binary format
    print("Convert to binary format")
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

#def insertBLOB(empID, name, photo, resumeFile):
def insertBLOB(connection: Connection, image: UserImage)->bool:
    with connection:
        cur = connection.cursor()
        sqlite_insert_blob_query = """ INSERT 
            INTO images (image_name, image_desc, image_data, image_type, user_id, room_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        image_data = convertToBinaryData(image.image_filename)
        # Convert data into typle format
        data_tuple = (image.image_name, image.image_desc, image_data, image.image_type, image.user_id, image.room_id)
        # Insert the BLOB data into the database
        cur.execute(sqlite_insert_blob_query, data_tuple)    
        connection.commit()
        print("Image and file inserted successfully as a BLOB into a table")
    return True



def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)
        print("Stored blob data into ", filename, "\n")

def readBlobData_by_room_id(connection: Connection, room_id : int)->None:
    print("Fetching BLOB data from room_id: ", room_id)
    with connection:
        cur = connection.cursor()

        sql_fetch_blob_query = """SELECT * 
        FROM images WHERE room_id =?"""
        cur.execute(sql_fetch_blob_query, (room_id,))
        image_list = []
        rows = cur.fetchall()
        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_desc = row[2]
            image_data = row[3]
            image_type = row[4]
            user_id = row[5]
            room_id = row[6]
            image = {"image_id": image_id,
                     "image_name": image_name,
                     "image_desc": image_desc,
                     "image_data": image_data,
                     "image_type": image_type,
                     "room_id": room_id,
                     "user_id": user_id}
            image_list.append(ImageRetrieve.model_validate(image))
        images = dict(images=image_list)   
        return images

def readBlobData_by_id(connection: Connection, image_id : int)->None:
    print("Fetching BLOB data by image id: ", image_id)
    with connection:
        cur = connection.cursor()

        sql_fetch_blob_query = """SELECT * 
        FROM images WHERE image_id =? LIMIT 1"""
        cur.execute(sql_fetch_blob_query, (image_id,))
        image_list = []
        row = cur.fetchone()

        image_id = row[0]
        image_name = row[1]
        image_desc = row[2]
        image_data = row[3]
        image_type = row[4]
        user_id = row[5]
        room_id = row[6]
        image = {"image_id": image_id,
                    "image_name": image_name,
                    "image_desc": image_desc,
                    "image_data": image_data,
                    "image_type": image_type,
                    "room_id": room_id,
                    "user_id": user_id} 
        return ImageRetrieve.model_validate(image)
        
def readBlobData_by_user_id(connection: Connection, userid : int)->None:
    print("Fetching BLOB data by user id: ", userid)
    with connection:
        cur = connection.cursor()

        sql_fetch_blob_query = """SELECT * 
        FROM images WHERE user_id =?"""
        cur.execute(sql_fetch_blob_query, (userid,))
        image_list = []
        rows = cur.fetchall()
        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_desc = row[2]
            image_data = row[3]
            image_type = row[4]
            user_id = row[5]
            room_id = row[6]
            image = {"image_id": image_id,
                     "image_name": image_name,
                     "image_desc": image_desc,
                     "image_data": image_data,
                     "image_type": image_type,
                     "room_id": room_id,
                     "user_id": user_id}
            image_list.append(ImageRetrieve.model_validate(image))
        images = dict(images=image_list)   
        return images

def readBlobData_inner_join(connection: Connection, user_id: int)->None:
    print("Fetching BLOB inner join data")    
    with connection:
        cur = connection.cursor()
        sql_fetch_blob_query = """SELECT images.*, rooms.room_name 
                                FROM images 
                                INNER JOIN rooms ON rooms.room_id = images.room_id 
                                WHERE images.user_id =?
                                ORDER BY images.room_id"""
        cur.execute(sql_fetch_blob_query, (user_id,))
        image_list = []
        rows = cur.fetchall()
        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_desc = row[2]
            image_data = row[3]
            image_type = row[4]
            user_id = row[5]
            room_id = row[6]
            room_name = row[7]
            image = {"image_id": image_id,
                     "image_name": image_name,
                     "image_desc": image_desc,
                     "image_data": image_data,
                     "image_type": image_type,
                     "room_id": room_id,
                     "user_id": user_id,
                     "room_name": room_name}
            image_list.append(ImageJoin.model_validate(image))
            
        images = dict(images=image_list)   
        return images

def delete_image_by_id(connection: Connection, room_id: int, image_id: int)->bool:
    print("Deleting image_id: ", image_id, " from room_id: ", room_id)
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            DELETE FROM images
            WHERE image_id = ?
            """,
            (image_id,),
        )
        connection.commit()

        images = readBlobData_by_room_id(connection=connection, room_id=room_id)
        return images
    
def delete_uploaded_images() -> None:
    dir_path = "c:/Users/diver/Development/Home-Harmony-Deryn-Apr22/Home-Harmony/static/uploads"
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
    
if __name__ == "__main__":
    connection = sqlite3.connect('harmony.db')
    connection.row_factory = sqlite3.Row
    
    current_directory = os.getcwd()
    #dir_path = os.path.join(current_directory, "/Home-Harmony/static/uploads")
    #dir_path = "c:/Users/diver/Development/Home-Harmony-Deryn-Apr22/Home-Harmony/static/uploads"

    delete_uploaded_images()
