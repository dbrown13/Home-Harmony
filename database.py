import sqlite3
from sqlite3 import Connection
from typing import List, Union
from pydantic import ValidationError
from models import Project, Projects, UserProject, UserProjectId, UserHashed, UserHashedIndex, Decor


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

def add_decor(connection: Connection, decor: Decor)->bool:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO decor (decor_name, decor_type, decor_desc, user_id, project_id)
            VALUES
            ( :decor_name, :decor_type, :decor_desc, :user_id, :project_id)
            """,
            decor.model_dump()
        )
    connection.commit()
    return True

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
    project = get_project_by_id(connection=connection, proj_id=2)
    print(project.model_dump())
    #user = get_user(connection, 'dibrown2')
    #print(user)
    #decor = Decor(decor_name='test decor', decor_type='wall', decor_desc='test decor description', user_id=1, project_id=1)
    #print(add_decor(connection=connection, decor=decor))