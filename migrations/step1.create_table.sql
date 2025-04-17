
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS images;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    salt TEXT NOT NULL,
    hash_password TEXT NOT NULL
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_title VARCHAR(50) NOT NULL,
    project_desc VARCHAR(500),
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE images (
    image_id INTEGER PRIMARY KEY,
    image_title VARCHAR(50) NOT NULL,
    image_desc VARCHAR(500),
    image_data blob NOT NULL,
    image_type text not null,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);