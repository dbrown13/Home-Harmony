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
    room_num_walls INTEGER,
    room_wall_color1 TEXT,
    room_wall_color2 TEXT,
    room_ceiling_color TEXT,
    room_floor_color TEXT,
    room_trim_color TEXT,
    room_other_details VARCHAR(500),
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

CREATE TRIGGER IF NOT EXISTS delete_images_on_room_delete
AFTER DELETE ON rooms
FOR EACH ROW
BEGIN
    DELETE FROM images 
    WHERE room_id = OLD.room_id;
END;

CREATE TRIGGER IF NOT EXISTS delete_images_on_user_delete
AFTER DELETE ON users 
FOR EACH ROW
BEGIN
    DELETE FROM images 
    WHERE user_id = OLD.user_id;
END;

CREATE TRIGGER IF NOT EXISTS delete_rooms_on_user_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
    DELETE FROM rooms 
    WHERE user_id = OLD.user_id;
END;