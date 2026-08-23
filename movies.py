"""Movies database queries."""

import db
from db import get_db

PER_PAGE = 10


def get_review_stats(user_id):
    """GET reviews statistics."""
    row = db.query_one("""
        SELECT
            COUNT(*) AS total,
            SUM(liked = 1) AS liked,
            SUM(liked = 0) AS unliked,
            SUM(liked IS NULL) AS no_answer
        FROM reviews
        WHERE author_id = ?
    """, (user_id,))

    return {
        'total': row['total'] or 0,
        'liked': row['liked'] or 0,
        'unliked': row['unliked'] or 0,
        'no_answer': row['no_answer'] or 0,
    }


def get_reviews_by_user(user_id, page=1, filter_type='all'):
    """GET reviews by user."""
    offset = (page - 1) * PER_PAGE

    query = """
        SELECT
            r.id, r.body, r.author_id, r.movie_id, r.liked, r.recommend,
            m.title,
            COALESCE(SUM(rr.value = 1), 0) AS likes_count,
            COALESCE(SUM(rr.value = -1), 0) AS dislikes_count
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        LEFT JOIN review_reactions rr ON rr.review_id = r.id
        WHERE r.author_id = ?
    """

    params = [user_id]

    if filter_type == 'liked':
        query += " AND r.liked = ?"
        params.append(1)
    elif filter_type == 'unliked':
        query += " AND r.liked = ?"
        params.append(0)
    elif filter_type == 'no_answer':
        query += " AND r.liked IS NULL"

    query += """
        GROUP BY r.id
        ORDER BY r.created DESC
        LIMIT ? OFFSET ?
    """

    params.extend([PER_PAGE, offset])

    return db.query(query, params)


def get_movie_by_id(movie_id):
    """Get movie by movie ID."""
    return db.query_one(
        'SELECT id, title FROM movies WHERE id = ?',
        (movie_id,)
    )


def get_review_by_movie(user_id, movie_id):
    """Get a user's existing review for a movie, or None."""
    return db.query_one(
        'SELECT id FROM reviews WHERE author_id = ? AND movie_id = ?',
        (user_id, movie_id)
    )


def insert_review(user_id, movie_id, body, liked, recommend):
    """INSERT review."""
    return db.execute(
        'INSERT INTO reviews (author_id, movie_id, body, liked, recommend) VALUES (?, ?, ?, ?, ?)',
        (user_id, movie_id, body, liked, recommend)
    )


def get_review(review_id, user_id):
    """Get review by review ID and user ID."""
    return db.query_one(
        """
        SELECT r.id, r.body, r.movie_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.id = ? AND r.author_id = ?
        """,
        (review_id, user_id)
    )


def update_review(review_id, body, liked, recommend):
    """UPDATE review."""
    db.execute(
        'UPDATE reviews SET body = ?, liked = ?, recommend = ? WHERE id = ?',
        (body, liked, recommend, review_id)
    )


def delete_review(review_id, user_id):
    """DELETE review and its reactions."""
    con = get_db()
    con.execute(
        'DELETE FROM review_reactions WHERE review_id = ?',
        (review_id,)
    )
    con.execute(
        'DELETE FROM reviews WHERE id = ? AND author_id = ?',
        (review_id, user_id)
    )
    con.commit()


def search_movies(q):
    """Search movie titles that contain given parameter."""
    return db.query(
        'SELECT id, title FROM movies WHERE title LIKE ? LIMIT 10',
        (f'%{q}%',)
    )


def insert_movie(title):
    """Insert a new movie and return its id."""
    return db.execute(
        'INSERT INTO movies (title) VALUES (?)',
        (title,)
    )


def get_movie_by_title(title):
    """Get a movie by exact title (case-insensitive)."""
    return db.query_one(
        'SELECT id, title FROM movies WHERE title = ? COLLATE NOCASE LIMIT 1',
        (title,)
    )


def set_reaction(user_id, review_id, value):
    """Set user reaction for review, or remove it if it already has the same value."""
    con = get_db()
    cursor = con.execute(
        'DELETE FROM review_reactions WHERE user_id = ? AND review_id = ? AND value = ?',
        (user_id, review_id, value)
    )
    if cursor.rowcount == 0:
        con.execute(
            """
            INSERT INTO review_reactions (user_id, review_id, value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, review_id)
            DO UPDATE SET value = excluded.value
            """,
            (user_id, review_id, value)
        )
    con.commit()


def get_user_reactions(user_id):
    """GET user reactions."""
    rows = db.query(
        'SELECT review_id, value FROM review_reactions WHERE user_id = ?',
        (user_id,)
    )
    return {row['review_id']: row['value'] for row in rows}


def count_all_reviews(q='', search_by='movie'):
    """Count all reviews."""
    if q and search_by == 'user':
        return db.query_one(
            """SELECT COUNT(*) FROM reviews r
               JOIN users u ON r.author_id = u.id
               WHERE u.username LIKE ?""",
            (f'%{q}%',)
        )[0]
    if q and search_by == 'movie':
        return db.query_one(
            """SELECT COUNT(*) FROM reviews r
               JOIN movies m ON r.movie_id = m.id
               WHERE m.title LIKE ?""",
            (f'%{q}%',)
        )[0]
    return db.query_one('SELECT COUNT(*) FROM reviews')[0]


def get_all_reviews(page=1, q='', search_by='movie'):
    """GET all reviews by movie title or user."""
    offset = (page - 1) * PER_PAGE

    where = ""
    params = []

    if q:
        if search_by == 'user':
            where = "WHERE u.username LIKE ?"
        else:
            where = "WHERE m.title LIKE ?"
        params.append(f'%{q}%')

    query = f"""
        SELECT
            r.id, r.body, r.liked, r.recommend,
            r.author_id, r.movie_id, m.title, u.username,
            SUM(rr.value = 1) AS likes_count,
            SUM(rr.value = -1) AS dislikes_count
        FROM (
            SELECT r.id
            FROM reviews r
            JOIN movies m ON r.movie_id = m.id
            JOIN users u ON r.author_id = u.id
            {where}
            ORDER BY r.created DESC
            LIMIT ? OFFSET ?
        ) page
        JOIN reviews r ON r.id = page.id
        JOIN movies m ON r.movie_id = m.id
        JOIN users u ON r.author_id = u.id
        LEFT JOIN review_reactions rr ON rr.review_id = r.id
        GROUP BY r.id
        ORDER BY r.created DESC
    """

    params.extend([PER_PAGE, offset])

    return db.query(query, params)


def get_all_genres():
    """GET all genres."""
    return db.query('SELECT id, name FROM genres ORDER BY name')


def get_movie_genres(movie_id):
    """GET genres for single movie."""
    return db.query(
        """
        SELECT g.id, g.name FROM genres g
        JOIN movie_genres mg ON g.id = mg.genre_id
        WHERE mg.movie_id = ?
        ORDER BY g.name
        """,
        (movie_id,)
    )


def get_genres_for_movies(movie_ids):
    """GET all genres for all movies."""
    if not movie_ids:
        return {}
    placeholders = ','.join('?' * len(movie_ids))
    rows = db.query(
        f"""
        SELECT mg.movie_id, g.name FROM movie_genres mg
        JOIN genres g ON g.id = mg.genre_id
        WHERE mg.movie_id IN ({placeholders})
        ORDER BY g.name
        """,
        tuple(movie_ids)
    )
    result = {}
    for row in rows:
        result.setdefault(row['movie_id'], []).append(row['name'])
    return result


def set_movie_genres(movie_id, genre_ids):
    """SET genres for movie ID."""
    con = get_db()
    con.execute('DELETE FROM movie_genres WHERE movie_id = ?', (movie_id,))
    if genre_ids:
        con.executemany(
            'INSERT INTO movie_genres (movie_id, genre_id) VALUES (?, ?)',
            [(movie_id, int(gid)) for gid in genre_ids]
        )
    con.commit()
