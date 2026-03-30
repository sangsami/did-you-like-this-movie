from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('movies', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()

    reviews = db.execute("""
        SELECT r.id, r.body, r.author_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.author_id = ?
        ORDER BY r.created DESC
    """, (g.user['id'],)).fetchall()

    return render_template('movies/index.html', reviews=reviews)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        liked_raw = request.form.get('liked')
        recommend_raw = request.form.get('recommend')
        movie_id = request.form.get('movie_id')

        if not title:
            flash('Movie title is required.')
            return render_template('movies/create.html')

        liked = True if liked_raw == '1' else False if liked_raw == '0' else None
        recommend = True if recommend_raw == '1' else False if recommend_raw == '0' else None

        if not movie_id:
            movie_id = get_or_create_movie(title)

        db = get_db()
        
        exists = db.execute(
            'SELECT id FROM reviews WHERE author_id=? AND movie_id=?',
            (g.user['id'], movie_id)
        ).fetchone()

        if exists:
            flash(f'You already reviewed "{title}".')
            return render_template('movies/create.html')

        db.execute(
            '''
            INSERT INTO reviews (author_id, movie_id, body, liked, recommend) 
            VALUES (?, ?, ?, ?, ?)
            ''',
            (g.user['id'], movie_id, body, liked, recommend)
        )
        db.commit()
        return redirect(url_for('movies.index'))

    return render_template('movies/create.html')


def get_or_create_movie(title):
    db = get_db()
    movie = db.execute(
        'SELECT id FROM movies WHERE LOWER(title) = LOWER(?)',
        (title.strip(),)
    ).fetchone()

    if movie is None:
        cursor = db.execute('INSERT INTO movies (title) VALUES (?)', (title.strip(),))
        db.commit()
        movie_id = cursor.lastrowid
    else:
        movie_id = movie['id']

    return movie_id


@bp.route('/<int:review_id>/update', methods=('GET', 'POST'))
@login_required
def update(review_id):
    db = get_db()
    
    review = db.execute(
        '''
        SELECT r.id, r.body, r.movie_id, r.liked, r.recommend, m.title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.id=? AND r.author_id=?
        ''',
        (review_id, g.user['id'])
    ).fetchone()

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form.get('body', '').strip()
        liked = request.form.get('liked')
        recommend = request.form.get('recommend')

        if not title:
            flash('Movie title is required.')
            return render_template('movies/update.html', review=review)

        liked = True if liked == '1' else False if liked == '0' else None
        recommend = True if recommend == '1' else False if recommend == '0' else None

        movie_id = get_or_create_movie(title)

        db.execute(
            '''
            UPDATE reviews
            SET movie_id=?, body=?, liked=?, recommend=?
            WHERE id=?
            ''',
            (movie_id, body, liked, recommend, review_id)
        )
        db.commit()
        flash('Review updated successfully.')
        return redirect(url_for('movies.index'))

    return render_template('movies/update.html', review=review)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    review = db.execute(
        'SELECT id FROM reviews WHERE id=? AND author_id=?',
        (id, g.user['id'])
    ).fetchone()

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    db.execute('DELETE FROM reviews WHERE id=?', (id,))
    db.commit()
    return redirect(url_for('movies.index'))


@bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '')
    db = get_db()

    movies = db.execute(
        'SELECT id, title FROM movies WHERE title LIKE ? LIMIT 10',
        (f'%{q}%',)
    ).fetchall()

    return {"movies": [dict(m) for m in movies]}
