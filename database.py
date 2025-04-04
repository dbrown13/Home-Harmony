import sqlite3
from sqlite3 import Connection
from models import Project, Projects, UserProject, UserProjectId

def insert_project(connection: Connection, 
                   project: UserProjectId):
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            INSERT INTO projects (project_title, project_desc, user_id)
            VALUES
            ( :project_title, :project_desc, :user_id)
            """,
            project.model_dump()
        )

def get_projects(connection: Connection)->UserProjectId:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT project_title, project_desc, user_id
            FROM projects;
            """
        )
        return Projects(projects = [Project.model_validate(dict(project)) for project in cur])
    
def get_user_projects(connection: Connection, user_id: int)->UserProjectId:
    with connection:
        cur = connection.cursor()
        cur.execute(
            """
            SELECT project_title, project_desc, user_id
            FROM projects
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return UserProjectId(projects = [UserProjectId.model_validate(dict(project)) for project in cur])
        
if __name__ == "__main__":
    connection = sqlite3.connect('harmony.db')
    connection.row_factory = sqlite3.Row

    test_project = UserProjectId(
        project_title="Test project 3", 
        project_desc="Description for test project 3",
        user_id = 3
    )

    #insert_project(connection=connection, project=test_project)
    #projects = get_projects(connection=connection)
    #print(get_projects(connection=connection))
    #print(get_user_projects(connection=connection, user_id=2))