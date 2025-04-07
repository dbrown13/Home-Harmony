CREATE TABLE decor (
    decor_id INTEGER PRIMARY KEY,
    decor_name VARCHAR(50),
    decor_type VARCHAR(50),
    decor_desc VARCHAR(500),
    decor_img_url TEXT,
    decor_blob BLOB,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL
);