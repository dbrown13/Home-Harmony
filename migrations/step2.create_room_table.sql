CREATE TABLE rooms (
    room_id INTEGER PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    room_desc VARCHAR(500),
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);