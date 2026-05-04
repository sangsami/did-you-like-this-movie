"""Movies routes."""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.auth.security import check_csrf
from app.movies import queries

bp = Blueprint('movies', __name__)


def _parse_bool(value):
    """Helper function for converting SQLite boolean values (1/0) to true booleans
    or None if doesn't exist."""
    return True if value == '1' else False if value == '0' else None


@bp.route('/')
@login_required
def index():
    """Index page."""
    filter_type = request.args.get('filter', 'all')

    all_reviews = queries.get_reviews_by_user(g.user['id'])

    stats = {
        "total": len(all_reviews),
        "liked": sum(1 for r in all_reviews if r['liked'] is True),
        "unliked": sum(1 for r in all_reviews if r['liked'] is False),
        "no_answer": sum(1 for r in all_reviews if r['liked'] is None),
    }

    if filter_type == 'liked':
        reviews = [r for r in all_reviews if r['liked'] is True]
    elif filter_type == 'unliked':
        reviews = [r for r in all_reviews if r['liked'] is False]
    else:
        reviews = all_reviews

    genres_map = queries.get_genres_for_reviews([r['id'] for r in reviews])

    return render_template(
        'movies/index.html',
        reviews=reviews,
        stats=stats,
        active_filter=filter_type,
        genres_map=genres_map
    )


@bp.route('/create')
@login_required
def create():
    """Create movie page."""
    q = request.args.get('q', '').strip()
    movies = queries.search_movies(q) if q else []
    return render_template('movies/create.html', movies=movies, q=q)


@bp.route('/create/<int:movie_id>', methods=('GET', 'POST'))
@login_required
def create_review(movie_id):
    """Create review page. Login required."""
    movie = queries.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    all_genres = queries.get_all_genres()

    if request.method == 'POST':
        check_csrf()
        body = request.form.get('body', '').strip()
        liked_raw = request.form.get('liked')
        recommend_raw = request.form.get('recommend')
        genre_ids = request.form.getlist('genres')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/create_review.html', movie=movie, all_genres=all_genres)

        if queries.review_exists(g.user['id'], movie_id):
            flash('You already reviewed this movie.', 'error')
            return redirect(url_for('movies.index'))

        liked = _parse_bool(liked_raw)
        recommend = _parse_bool(recommend_raw)

        review_id = queries.insert_review(
            user_id=g.user['id'],
            movie_id=movie_id,
            body=body,
            liked=liked,
            recommend=recommend
        )
        queries.set_review_genres(review_id, genre_ids)
        return redirect(url_for('movies.index'))

    return render_template('movies/create_review.html', movie=movie, all_genres=all_genres)


@bp.route('/<int:review_id>/update', methods=('GET', 'POST'))
@login_required
def update(review_id):
    """Update review. Login required."""
    review = queries.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    all_genres = queries.get_all_genres()
    current_genre_ids = {g['id'] for g in queries.get_review_genres(review_id)}

    if request.method == 'POST':
        check_csrf()
        body = request.form.get('body', '').strip()
        liked = request.form.get('liked')
        recommend = request.form.get('recommend')
        genre_ids = request.form.getlist('genres')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/update.html', review=review, all_genres=all_genres,
                                   current_genre_ids=current_genre_ids)

        liked = _parse_bool(liked)
        recommend = _parse_bool(recommend)

        queries.update_review(review_id=review_id, body=body, liked=liked, recommend=recommend)
        queries.set_review_genres(review_id, genre_ids)

        flash('Review updated successfully.')
        return redirect(url_for('movies.index'))

    return render_template(
        'movies/update.html',
        review=review,
        all_genres=all_genres,
        current_genre_ids=current_genre_ids
    )


@bp.route('/<int:review_id>/delete', methods=('POST',))
@login_required
def delete(review_id):
    """DELETE review. Login required."""
    check_csrf()
    review = queries.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    queries.delete_review(review_id, g.user['id'])
    return redirect(url_for('movies.index'))


@bp.route('/search')
@login_required
def search():
    "Search movie."
    q = request.args.get('q', '').strip()
    movies = queries.search_movies(q) if q else []
    return render_template('movies/search.html', movies=movies, q=q)


@bp.route('/feed')
@login_required
def feed():
    """Review feed page."""
    reviews = queries.get_all_reviews()
    liked_map = queries.get_user_reactions(g.user['id'])
    genres_map = queries.get_genres_for_reviews([r['id'] for r in reviews])

    return render_template(
        'movies/feed.html',
        reviews=reviews,
        liked_map=liked_map,
        genres_map=genres_map,
        current_user_id=g.user['id']
    )


@bp.route('/<int:review_id>/like', methods=['POST'])
@login_required
def like(review_id):
    """Increase reaction value."""
    check_csrf()
    queries.set_reaction(g.user['id'], review_id, 1)
    return redirect(url_for('movies.feed'))


@bp.route('/<int:review_id>/dislike', methods=['POST'])
@login_required
def dislike(review_id):
    """Decrease reaction value."""
    check_csrf()
    queries.set_reaction(g.user['id'], review_id, -1)
    return redirect(url_for('movies.feed'))
