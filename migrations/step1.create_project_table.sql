CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_title VARCHAR(50) NOT NULL,
    project_desc VARCHAR(500),
    user_id INTEGER
);