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


def set_reaction(user_id, review_id, value):
    db = get_db()
    db.execute("""
        INSERT INTO review_reactions (user_id, review_id, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, review_id)
        DO UPDATE SET value=excluded.value
    """, (user_id, review_id, value))
    db.commit()


def get_reaction_counts(review_id):
    db = get_db()
    return db.execute("""
        SELECT
            SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END) AS likes,
            SUM(CASE WHEN value = -1 THEN 1 ELSE 0 END) AS dislikes
        FROM review_reactions
        WHERE review_id = ?
    """, (review_id,)).fetchone()


def get_user_reaction(user_id, review_id):
    db = get_db()
    row = db.execute("""
        SELECT value
        FROM review_reactions
        WHERE user_id=? AND review_id=?
    """, (user_id, review_id)).fetchone()

    return row["value"] if row else None


def get_all_reviews_except_user(user_id):
    db = get_db()
    return db.execute("""
        SELECT 
            r.id, r.body, r.liked, r.recommend,
            r.author_id, m.title, u.username,

            COALESCE(SUM(CASE WHEN rr.value = 1 THEN 1 END), 0) AS likes_count,
            COALESCE(SUM(CASE WHEN rr.value = -1 THEN 1 END), 0) AS dislikes_count

        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        JOIN users u ON r.author_id = u.id
        LEFT JOIN review_reactions rr ON rr.review_id = r.id

        WHERE r.author_id != ?

        GROUP BY r.id
        ORDER BY r.created DESC
    """, (user_id,)).fetchall()
