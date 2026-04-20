from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.movies import queries

bp = Blueprint('movies', __name__)

@bp.route('/')
@login_required
def index():
    reviews = queries.get_reviews_by_user(g.user['id'])

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
            flash('Movie title is required.', 'error')
            return render_template('movies/create.html')

        liked = True if liked_raw == '1' else False if liked_raw == '0' else None
        recommend = True if recommend_raw == '1' else False if recommend_raw == '0' else None

        if not movie_id:
            movie_id = get_or_create_movie(title)

        
        exists = queries.review_exists(g.user['id'], movie_id)

        if exists:
            flash(f'You already reviewed "{title}".', 'error')
            return render_template('movies/create.html')

        queries.insert_review(user_id=g.user['id'], movie_id=movie_id, body=body, liked=liked, recommend=recommend)
        return redirect(url_for('movies.index'))

    return render_template('movies/create.html')


def get_or_create_movie(title):
    movie = queries.find_movie_by_title(title)

    if movie is None:
        movie_id = queries.create_movie(title=title.strip())
    else:
        movie_id = movie['id']

    return movie_id


@bp.route('/<int:review_id>/update', methods=('GET', 'POST'))
@login_required
def update(review_id):
    review = queries.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form.get('body', '').strip()
        liked = request.form.get('liked')
        recommend = request.form.get('recommend')

        if not title:
            flash('Movie title is required.', 'error')
            return render_template('movies/update.html', review=review)

        liked = True if liked == '1' else False if liked == '0' else None
        recommend = True if recommend == '1' else False if recommend == '0' else None

        movie_id = get_or_create_movie(title)

        queries.update_review(review_id=review_id, movie_id=movie_id, body=body, liked=liked, recommend=recommend)

        flash('Review updated successfully.')
        return redirect(url_for('movies.index'))

    return render_template('movies/update.html', review=review)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    review = queries.get_review(review_id=id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    queries.delete_review(id, g.user['id'])
    return redirect(url_for('movies.index'))


@bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '')

    movies = queries.search_movies(q)

    return {"movies": [dict(m) for m in movies]}
