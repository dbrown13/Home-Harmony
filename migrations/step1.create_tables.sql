DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS images;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    salt TEXT NOT NULL,
    hash_password TEXT NOT NULL
);

CREATE TABLE rooms (
    room_id INTEGER PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    room_desc VARCHAR(500),
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE images (
    image_id INTEGER PRIMARY KEY,
    image_name VARCHAR(50) NOT NULL,
    image_desc VARCHAR(500),
    image_data blob NOT NULL,
    image_type text not null,
    user_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);