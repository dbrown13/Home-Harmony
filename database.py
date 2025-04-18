import sqlite3
from sqlite3 import Connection
from typing import List, Union
from pydantic import ValidationError
from models import Room, Rooms, UserRoom, UserRoomId, UserHashed, UserHashedIndex, UserImage, ImageRetrieve, Images
import os

def create_user(connection: Connection,
                user: UserHashed)->bool:
    with connection: 
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
def get_user(connection: Connection,
             username: str)->Union[UserHashedIndex, None]:
    with connection: 
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
    
def delete_user(connection: Connection,
                user_id: int)->bool:
    with connection: 
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
                

def create_new_room(connection: Connection, 
                   room: UserRoomId):
    with connection:
        print(f"Creating new room: {room}")
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO rooms (room_name, room_desc, user_id)
            VALUES
            ( :room_name, :room_desc, :user_id)
            """,
            room.model_dump()
        )
        connection.commit()

def get_rooms(connection: Connection)->Rooms:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT room_name, room_desc, user_id, room_id
            FROM rooms;
            """
        )
        return Rooms(rooms = [Room.model_validate(dict(room)) for room in cur])

def get_user_rooms(connection: Connection, user_id: int)->Rooms:
    print(f"Getting rooms for user_id: {user_id}")
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT room_id, room_name, room_desc, user_id
            FROM rooms
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return Rooms(rooms = [Room.model_validate(dict(room)) for room in cur])
        #return cur.fetchall()

def get_room_by_id(connection: Connection, room_id: int)->Room:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT room_name, room_desc, user_id, room_id
            FROM rooms
            WHERE room_id = ?
            LIMIT 1
            """,
            (room_id,),
        )
        #return cur.fetchone()
        return Room.model_validate(dict(cur.fetchone()))

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

def readBlobData_by_id(connection: Connection, room_id : int)->None:
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

        images = readBlobData_by_id(connection=connection, room_id=room_id)
        return images
    
if __name__ == "__main__":
    connection = sqlite3.connect('harmony.db')
    connection.row_factory = sqlite3.Row

    #insert_room(connection=connection, room=test_room)
    #rooms = get_rooms(connection=connection)
    #print(get_rooms(connection=connection))
    #for room in get_rooms(connection=connection):
    #    print(room)
    #rooms = get_user_rooms(connection=connection, user_id=4)
    #for room in rooms:
    #    print(dict(room))
    #room = get_room_by_id(connection=connection, room_id=2)
    #print(room.model_dump())
    #user = get_user(connection, 'dibrown2')
    #print(user)
    #decor = Decor(decor_name='test decor', decor_type='wall', decor_desc='test decor description', user_id=1, room_id=1)
    #print(add_decor(connection=connection, decor=decor))