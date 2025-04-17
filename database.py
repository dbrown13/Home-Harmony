import sqlite3
from sqlite3 import Connection
from typing import List, Union
from pydantic import ValidationError
from models import Project, Projects, UserProject, UserProjectId, UserHashed, UserHashedIndex, UserImage, ImageRetrieve, Images
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
                

def create_new_project(connection: Connection, 
                   project: UserProjectId):
    with connection:
        print(f"Creating new project: {project}")
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO projects (project_title, project_desc, user_id)
            VALUES
            ( :project_title, :project_desc, :user_id)
            """,
            project.model_dump()
        )
        connection.commit()

def get_projects(connection: Connection)->Projects:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT project_title, project_desc, user_id, project_id
            FROM projects;
            """
        )
        return Projects(projects = [Project.model_validate(dict(project)) for project in cur])

def get_user_projects(connection: Connection, user_id: int)->Projects:
    print(f"Getting projects for user_id: {user_id}")
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT project_id, project_title, project_desc, user_id
            FROM projects
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return Projects(projects = [Project.model_validate(dict(project)) for project in cur])
        #return cur.fetchall()

def get_project_by_id(connection: Connection, proj_id: int)->Project:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT project_title, project_desc, user_id, project_id
            FROM projects
            WHERE project_id = ?
            LIMIT 1
            """,
            (proj_id,),
        )
        #return cur.fetchone()
        return Project.model_validate(dict(cur.fetchone()))

def update_project_by_id(
        connection: Connection, 
        project: Project)->bool:
    
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            UPDATE projects
            SET project_title =?, project_desc =?
            WHERE project_id =?
            """,
            (project.project_title, project.project_desc, project.project_id)
        )
        connection.commit()
        return True
    
def delete_project_by_id(connection: Connection, proj_id: int)->bool:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            DELETE FROM projects
            WHERE project_id = ?
            """,
            (proj_id,),
        )
        connection.commit()
        #return Projects(projects = [Project.model_validate(dict(project)) for project in cur])
        return True
    
def add_image(connection: Connection, image: UserImage)->bool:

    # Insert the image into the database
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO images (image_title, image_desc, image_data, user_id, project_id)
            VALUES
            ( :image_title, :image_desc, :image_data, :user_id, :project_id)
            """,
            image.model_dump()
        )
    connection.commit()
    return True

def get_images_by_project_id(connection: Connection, project_id: int)->Images:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT image_title, image_desc, image_data, user_id, project_id
            FROM images
            WHERE project_id =?
            """,
            (project_id,),
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
            INTO images (image_title, image_desc, image_data, image_type, user_id, project_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        image_data = convertToBinaryData(image.image_filename)
        # Convert data into typle format
        data_tuple = (image.image_title, image.image_desc, image_data, image.image_type, image.user_id, image.project_id)
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

def readBlobData_by_id(connection: Connection, proj_id : int)->None:
    with connection:
        cur = connection.cursor()

        sql_fetch_blob_query = """SELECT * 
        FROM images WHERE project_id =?"""
        cur.execute(sql_fetch_blob_query, (proj_id,))
        image_list = []
        rows = cur.fetchall()
        for row in rows:
            image_id = row[0]
            image_title = row[1]
            image_desc = row[2]
            image_data = row[3]
            image_type = row[4]
            user_id = row[5]
            project_id = row[6]
            image = {"image_id": image_id,
                     "image_title": image_title,
                     "image_desc": image_desc,
                     "image_data": image_data,
                     "image_type": image_type,
                     "project_id": project_id,
                     "user_id": user_id}
            image_list.append(ImageRetrieve.model_validate(image))
        images = dict(images=image_list)   
        return images
    
if __name__ == "__main__":
    connection = sqlite3.connect('harmony.db')
    connection.row_factory = sqlite3.Row

    #insert_project(connection=connection, project=test_project)
    #projects = get_projects(connection=connection)
    #print(get_projects(connection=connection))
    #for project in get_projects(connection=connection):
    #    print(project)
    #projects = get_user_projects(connection=connection, user_id=4)
    #for project in projects:
    #    print(dict(project))
    #project = get_project_by_id(connection=connection, proj_id=2)
    #print(project.model_dump())
    #user = get_user(connection, 'dibrown2')
    #print(user)
    #decor = Decor(decor_name='test decor', decor_type='wall', decor_desc='test decor description', user_id=1, project_id=1)
    #print(add_decor(connection=connection, decor=decor))