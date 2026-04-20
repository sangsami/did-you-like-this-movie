from app.db import get_db


def get_reviews_by_user(user_id):
    db = get_db()
    return db.execute("""
        SELECT r.id, r.body, r.author_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.author_id = ?
        ORDER BY r.created DESC
    """, (user_id,)).fetchall()


def find_movie_by_title(title):
    db = get_db()
    return db.execute(
        'SELECT id FROM movies WHERE LOWER(title) = LOWER(?)',
        (title.strip(),)
    ).fetchone()


def create_movie(title):
    db = get_db()
    cursor = db.execute(
        'INSERT INTO movies (title) VALUES (?)',
        (title.strip(),)
    )
    db.commit()
    return cursor.lastrowid


def get_or_create_movie(title):
    movie = find_movie_by_title(title)
    return movie['id'] if movie else create_movie(title)


def review_exists(user_id, movie_id):
    db = get_db()
    return db.execute(
        'SELECT id FROM reviews WHERE author_id=? AND movie_id=?',
        (user_id, movie_id)
    ).fetchone()


def insert_review(user_id, movie_id, body, liked, recommend):
    db = get_db()
    db.execute(
        '''
        INSERT INTO reviews (author_id, movie_id, body, liked, recommend) 
        VALUES (?, ?, ?, ?, ?)
        ''',
        (user_id, movie_id, body, liked, recommend)
    )
    db.commit()


def get_review(review_id, user_id):
    db = get_db()
    return db.execute(
        '''
        SELECT r.id, r.body, r.movie_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.id=? AND r.author_id=?
        ''',
        (review_id, user_id)
    ).fetchone()


def update_review(review_id, movie_id, body, liked, recommend):
    db = get_db()
    db.execute(
        '''
        UPDATE reviews
        SET movie_id=?, body=?, liked=?, recommend=?
        WHERE id=?
        ''',
        (movie_id, body, liked, recommend, review_id)
    )
    db.commit()


def delete_review(review_id, user_id):
    db = get_db()
    db.execute(
        'DELETE FROM reviews WHERE id=? AND author_id=?',
        (review_id, user_id)
    )
    db.commit()


def search_movies(q):
    db = get_db()
    return db.execute(
        'SELECT id, title FROM movies WHERE title LIKE ? LIMIT 10',
        (f'%{q}%',)
    ).fetchall()
