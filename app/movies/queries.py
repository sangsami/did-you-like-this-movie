"""Movies database queries."""

from app.db import get_db

PER_PAGE = 10


def get_review_stats(user_id):
    """GET reviews statistics."""
    db = get_db()
    row = db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN liked = 1 THEN 1 ELSE 0 END) AS liked,
            SUM(CASE WHEN liked = 0 THEN 1 ELSE 0 END) AS unliked,
            SUM(CASE WHEN liked IS NULL THEN 1 ELSE 0 END) AS no_answer
        FROM reviews WHERE author_id = ?
    """, (user_id,)).fetchone()
    return {
        'total': row['total'],
        'liked': row['liked'] or 0,
        'unliked': row['unliked'] or 0,
        'no_answer': row['no_answer'] or 0,
    }


def get_reviews_by_user(user_id, page=1, filter_type='all'):
    """GET reviews by user."""
    db = get_db()
    offset = (page - 1) * PER_PAGE
    if filter_type == 'liked':
        extra = 'AND r.liked = 1'
    elif filter_type == 'unliked':
        extra = 'AND r.liked = 0'
    else:
        extra = ''
    return db.execute(f"""
        SELECT r.id, r.body, r.author_id, r.liked, r.recommend, m.title,
            COALESCE(SUM(CASE WHEN rr.value = 1 THEN 1 END), 0) AS likes_count,
            COALESCE(SUM(CASE WHEN rr.value = -1 THEN 1 END), 0) AS dislikes_count
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        LEFT JOIN review_reactions rr ON rr.review_id = r.id
        WHERE r.author_id = ? {extra}
        GROUP BY r.id
        ORDER BY r.created DESC
        LIMIT ? OFFSET ?
    """, (user_id, PER_PAGE, offset)).fetchall()



def get_movie_by_id(movie_id):
    """Get movie by movie ID."""
    db = get_db()
    return db.execute(
        'SELECT id, title FROM movies WHERE id = ?',
        (movie_id,)
    ).fetchone()


def review_exists(user_id, movie_id):
    """Check review exists in database."""
    db = get_db()
    return db.execute(
        'SELECT id FROM reviews WHERE author_id = ? AND movie_id = ?',
        (user_id, movie_id)
    ).fetchone()


def insert_review(user_id, movie_id, body, liked, recommend):
    """INSERT review."""
    db = get_db()
    cursor = db.execute(
        'INSERT INTO reviews (author_id, movie_id, body, liked, recommend) VALUES (?, ?, ?, ?, ?)',
        (user_id, movie_id, body, liked, recommend)
    )
    db.commit()
    return cursor.lastrowid


def get_review(review_id, user_id):
    """Get review by review ID and user ID."""
    db = get_db()
    return db.execute(
        """
        SELECT r.id, r.body, r.movie_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.id = ? AND r.author_id = ?
        """,
        (review_id, user_id)
    ).fetchone()


def update_review(review_id, body, liked, recommend):
    """UPDATE review."""
    db = get_db()
    db.execute(
        'UPDATE reviews SET body = ?, liked = ?, recommend = ? WHERE id = ?',
        (body, liked, recommend, review_id)
    )
    db.commit()


def delete_review(review_id, user_id):
    """DELETE review."""
    db = get_db()
    db.execute(
        'DELETE FROM reviews WHERE id = ? AND author_id = ?',
        (review_id, user_id)
    )
    db.commit()


def search_movies(q):
    """Search movie titles that contain given parameter."""
    db = get_db()
    return db.execute(
        'SELECT id, title FROM movies WHERE title LIKE ? LIMIT 10',
        (f'%{q}%',)
    ).fetchall()


def set_reaction(user_id, review_id, value):
    """Set user reaction for review."""
    db = get_db()
    existing = db.execute(
        'SELECT value FROM review_reactions WHERE user_id = ? AND review_id = ?',
        (user_id, review_id)
    ).fetchone()
    if existing and existing['value'] == value:
        db.execute(
            'DELETE FROM review_reactions WHERE user_id = ? AND review_id = ?',
            (user_id, review_id)
        )
    else:
        db.execute(
            """
            INSERT INTO review_reactions (user_id, review_id, value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, review_id)
            DO UPDATE SET value = excluded.value
            """,
            (user_id, review_id, value)
        )
    db.commit()


def get_user_reactions(user_id):
    """GET user reactions."""
    db = get_db()
    rows = db.execute(
        'SELECT review_id, value FROM review_reactions WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return {row['review_id']: row['value'] for row in rows}


def count_all_reviews(q='', search_by='movie'):
    """Count all reviews."""
    db = get_db()
    if q and search_by == 'user':
        return db.execute(
            """SELECT COUNT(*) FROM reviews r
               JOIN users u ON r.author_id = u.id
               WHERE u.username LIKE ?""",
            (f'%{q}%',)
        ).fetchone()[0]
    if q and search_by == 'movie':
        return db.execute(
            """SELECT COUNT(*) FROM reviews r
               JOIN movies m ON r.movie_id = m.id
               WHERE m.title LIKE ?""",
            (f'%{q}%',)
        ).fetchone()[0]
    return db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]


def get_all_reviews(page=1, q='', search_by='movie'):
    """GET all reviews by movie title or user."""
    db = get_db()
    offset = (page - 1) * PER_PAGE
    if q and search_by == 'user':
        where = 'WHERE u.username LIKE ?'
        params = (f'%{q}%', PER_PAGE, offset)
    elif q and search_by == 'movie':
        where = 'WHERE m.title LIKE ?'
        params = (f'%{q}%', PER_PAGE, offset)
    else:
        where = ''
        params = (PER_PAGE, offset)
    return db.execute(f"""
        SELECT
            r.id, r.body, r.liked, r.recommend,
            r.author_id, m.title, u.username,
            COALESCE(SUM(CASE WHEN rr.value = 1 THEN 1 END), 0) AS likes_count,
            COALESCE(SUM(CASE WHEN rr.value = -1 THEN 1 END), 0) AS dislikes_count
        FROM (
            SELECT r.id FROM reviews r
            JOIN movies m ON r.movie_id = m.id
            JOIN users u ON r.author_id = u.id
            {where}
            ORDER BY r.created DESC
            LIMIT ? OFFSET ?
        ) AS page
        JOIN reviews r ON r.id = page.id
        JOIN movies m ON r.movie_id = m.id
        JOIN users u ON r.author_id = u.id
        LEFT JOIN review_reactions rr ON rr.review_id = r.id
        GROUP BY r.id
        ORDER BY r.created DESC
    """, params).fetchall()


def get_all_genres():
    """GET all genres."""
    db = get_db()
    return db.execute('SELECT id, name FROM genres ORDER BY name').fetchall()


def get_review_genres(review_id):
    """GET genres for single review."""
    db = get_db()
    return db.execute(
        """
        SELECT g.id, g.name FROM genres g
        JOIN review_genres rg ON g.id = rg.genre_id
        WHERE rg.review_id = ?
        ORDER BY g.name
        """,
        (review_id,)
    ).fetchall()


def get_genres_for_reviews(review_ids):
    """GET all genres for all reviews."""
    if not review_ids:
        return {}
    placeholders = ','.join('?' * len(review_ids))
    db = get_db()
    rows = db.execute(
        f"""
        SELECT rg.review_id, g.name FROM review_genres rg
        JOIN genres g ON g.id = rg.genre_id
        WHERE rg.review_id IN ({placeholders})
        ORDER BY g.name
        """,
        tuple(review_ids)
    ).fetchall()
    result = {}
    for row in rows:
        result.setdefault(row['review_id'], []).append(row['name'])
    return result


def set_review_genres(review_id, genre_ids):
    """SET genres for review ID."""
    db = get_db()
    db.execute('DELETE FROM review_genres WHERE review_id = ?', (review_id,))
    if genre_ids:
        db.executemany(
            'INSERT INTO review_genres (review_id, genre_id) VALUES (?, ?)',
            [(review_id, int(gid)) for gid in genre_ids]
        )
    db.commit()
