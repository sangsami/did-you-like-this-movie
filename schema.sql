DROP TABLE IF EXISTS review_reactions;
DROP TABLE IF EXISTS review_genres;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS users;


CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT UNIQUE NOT NULL
);

CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    body TEXT,
    liked BOOLEAN,
    recommend BOOLEAN,
    FOREIGN KEY (author_id) REFERENCES users (id),
    FOREIGN KEY (movie_id) REFERENCES movies (id),
    UNIQUE(author_id, movie_id)
);

CREATE TABLE review_genres (
    review_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (review_id, genre_id),
    FOREIGN KEY (review_id) REFERENCES reviews (id),
    FOREIGN KEY (genre_id) REFERENCES genres (id)
);

CREATE TABLE review_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    review_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    UNIQUE(user_id, review_id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (review_id) REFERENCES reviews (id)
);

CREATE INDEX idx_reviews_author_created ON reviews (author_id, created DESC);
CREATE INDEX idx_reactions_review ON review_reactions (review_id);

INSERT INTO genres (name) VALUES
    ('Action'),
    ('Animation'),
    ('Comedy'),
    ('Documentary'),
    ('Drama'),
    ('Horror'),
    ('Romance'),
    ('Sci-Fi'),
    ('Thriller');
