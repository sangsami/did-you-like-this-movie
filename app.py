"""App entrypoint."""

import functools
import math
import os
import secrets
import sqlite3
import time

from flask import (
    Flask, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.exceptions import HTTPException, abort
from werkzeug.security import check_password_hash, generate_password_hash

import db
import movies
import users

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    REQUEST_TIMING=os.environ.get('REQUEST_TIMING') == '1',
)
app.config.from_pyfile('config.py', silent=True)

os.makedirs(app.instance_path, exist_ok=True)

db.init_app(app)


def check_csrf():
    """Check for CSRF token, throw 403 if not found or mismatch."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        session_token = session.get("csrf_token")
        if not token or not session_token or token != session_token:
            abort(403)


def login_required(view):
    """Helper decorator for login-required routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view


def validate_registration(username, password1, password2):
    """Validate registration form values, return a list of error messages."""
    errors = []

    if not username:
        errors.append('Username is required.')
    elif len(username) < 3:
        errors.append('Username must be at least 3 characters.')
    elif len(username) > 50:
        errors.append('Username must be 50 characters or fewer.')

    if not password1 or not password2:
        errors.append('Password is required.')
    elif len(password1) > 200:
        errors.append('Password must be 200 characters or fewer.')
    elif password1 != password2:
        errors.append("Passwords did not match")

    return errors


def _parse_bool(value):
    """Helper function for converting SQLite boolean values (1/0) to true booleans
    or None if doesn't exist."""
    return True if value == '1' else False if value == '0' else None


@app.before_request
def ensure_csrf_token():
    """Create CSRF token if doesn't exist."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


def timing_enabled():
    """Check if in debug mode or request timing flag is on."""
    return app.debug or app.config['REQUEST_TIMING']


@app.before_request
def start_request_timer():
    """Start the request timer, when timing is enabled."""
    if timing_enabled():
        g.start_time = time.perf_counter()


@app.after_request
def log_request_time(response):
    """Log how long the request took, when timing is enabled."""
    start_time = g.pop('start_time', None)
    if start_time is not None:
        elapsed = time.perf_counter() - start_time
        app.logger.info('%s %s %.3f s', request.method, request.path, elapsed)
    return response


@app.before_request
def load_logged_in_user():
    """Load logged user before request."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = users.get_user_by_id(user_id=user_id)


@app.errorhandler(HTTPException)
def handle_http_error(error):
    """Render any HTTP error (404, 403, 405, 500, ...) with the site layout."""
    return render_template('error.html', error=error), error.code


@app.route('/auth/register', methods=('GET', 'POST'))
def register():
    """Register route."""
    username = ''
    if request.method == 'POST':
        check_csrf()

        username = request.form['username'].strip()
        password1 = request.form['password1']
        password2 = request.form['password2']

        errors = validate_registration(username, password1, password2)

        if not errors:
            try:
                users.create_user(
                    username,
                    generate_password_hash(password1)
                )
            except sqlite3.IntegrityError:
                errors.append(f"User {username} is already registered.")
            else:
                return redirect(url_for("login"))

        for error in errors:
            flash(error, 'error')

    return render_template('auth/register.html', username=username)


@app.route('/auth/login', methods=('GET', 'POST'))
def login():
    """Login route."""
    if request.method == 'POST':
        check_csrf()

        username = request.form['username']
        password = request.form['password']
        error = None

        user = users.get_user_by_username(username=username)

        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['csrf_token'] = secrets.token_hex(16)
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('auth/login.html')


@app.route('/auth/logout', methods=('POST',))
def logout():
    """Logout route."""
    check_csrf()
    session.clear()
    return redirect(url_for('index'))


@app.route('/')
@app.route('/<int:page>')
@login_required
def index(page=1):
    """Index page."""
    filter_type = request.args.get('filter', 'all')

    stats = movies.get_review_stats(g.user['id'])

    if filter_type == 'liked':
        filtered_total = stats['liked']
    elif filter_type == 'unliked':
        filtered_total = stats['unliked']
    elif filter_type == 'no_answer':
        filtered_total = stats['no_answer']
    else:
        filtered_total = stats['total']

    total_pages = max(1, math.ceil(filtered_total / movies.PER_PAGE))

    if page < 1:
        return redirect(url_for('index', page=1, filter=filter_type))
    if page > total_pages:
        return redirect(url_for('index', page=total_pages, filter=filter_type))

    reviews = movies.get_reviews_by_user(g.user['id'], page=page, filter_type=filter_type)
    genres_map = movies.get_genres_for_movies([r['movie_id'] for r in reviews])

    return render_template(
        'movies/index.html',
        reviews=reviews,
        stats=stats,
        active_filter=filter_type,
        genres_map=genres_map,
        page=page,
        total_pages=total_pages
    )


@app.route('/create')
@login_required
def create():
    """Create movie page."""
    q = request.args.get('q', '').strip()
    found_movies = movies.search_movies(q) if q else []
    return render_template('movies/create.html', movies=found_movies, q=q)


@app.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    """Add a new movie entry. After adding, redirect to create review page."""
    all_genres = movies.get_all_genres()

    if request.method == 'POST':
        check_csrf()
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('movies/add.html', title=title, all_genres=all_genres)

        genre_ids = movies.validate_genre_ids(request.form.getlist('genres'))
        if genre_ids is None:
            flash('Invalid genre selection.', 'error')
            return render_template('movies/add.html', title=title, all_genres=all_genres)

        existing = movies.get_movie_by_title(title)
        if existing:
            flash('Movie already exists, opening review form for that title.', 'info')
            return redirect(url_for('create_review', movie_id=existing['id']))

        movie_id = movies.create_movie(title, genre_ids)
        flash('Movie added successfully.')
        return redirect(url_for('create_review', movie_id=movie_id))

    return render_template('movies/add.html', all_genres=all_genres)


@app.route('/movie/<int:movie_id>')
@app.route('/movie/<int:movie_id>/<int:page>')
@login_required
def movie(movie_id, page=1):
    """Movie page. Shows review statistics and every review for one movie."""
    found_movie = movies.get_movie_by_id(movie_id)
    if found_movie is None:
        abort(404, 'Movie not found.')

    stats = movies.get_movie_stats(movie_id)
    total_pages = max(1, math.ceil(stats['total'] / movies.PER_PAGE))

    if page < 1:
        return redirect(url_for('movie', movie_id=movie_id, page=1))
    if page > total_pages:
        return redirect(url_for('movie', movie_id=movie_id, page=total_pages))

    return render_template(
        'movies/movie.html',
        movie=found_movie,
        stats=stats,
        movie_genres=movies.get_movie_genres(movie_id),
        reviews=movies.get_reviews_by_movie(movie_id, page=page),
        own_review=movies.get_review_by_movie(g.user['id'], movie_id),
        reactions_map=movies.get_user_reactions(g.user['id']),
        current_user_id=g.user['id'],
        page=page,
        total_pages=total_pages
    )


@app.route('/create/<int:movie_id>', methods=('GET', 'POST'))
@login_required
def create_review(movie_id):
    """Create review page. Login required.

    Redirects to the update page if the user already reviewed this movie."""
    movie = movies.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    if request.method == 'POST':
        check_csrf()

    existing = movies.get_review_by_movie(g.user['id'], movie_id)
    if existing:
        flash('You already reviewed this movie. You can edit your review here.', 'info')
        return redirect(url_for('update', review_id=existing['id']))

    movie_genres = movies.get_movie_genres(movie_id)

    if request.method == 'POST':
        body = request.form.get('body', '').replace('\r\n', '\n').strip()
        liked_raw = request.form.get('liked')
        recommend_raw = request.form.get('recommend')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/create_review.html', movie=movie,
                                   movie_genres=movie_genres, body=body)

        liked = _parse_bool(liked_raw)
        recommend = _parse_bool(recommend_raw)

        movies.insert_review(
            user_id=g.user['id'],
            movie_id=movie_id,
            body=body,
            liked=liked,
            recommend=recommend
        )
        return redirect(url_for('index'))

    return render_template('movies/create_review.html', movie=movie, movie_genres=movie_genres, body='')


@app.route('/<int:review_id>/update', methods=('GET', 'POST'))
@login_required
def update(review_id):
    """Update review. Login required."""
    review = movies.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    if request.method == 'POST':
        check_csrf()
        body = request.form.get('body', '').replace('\r\n', '\n').strip()
        liked = request.form.get('liked')
        recommend = request.form.get('recommend')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/update.html', review=review, body=body)

        liked = _parse_bool(liked)
        recommend = _parse_bool(recommend)

        movies.update_review(review_id=review_id, body=body, liked=liked, recommend=recommend)

        flash('Review updated successfully.')
        return redirect(url_for('index'))

    return render_template('movies/update.html', review=review, body=review['body'])


@app.route('/<int:review_id>/delete', methods=('POST',))
@login_required
def delete(review_id):
    """DELETE review. Login required."""
    check_csrf()
    review = movies.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    movies.delete_review(review_id, g.user['id'])
    return redirect(url_for('index'))


@app.route('/explore')
@app.route('/explore/<int:page>')
@login_required
def explore(page=1):
    """Explore page. Browse and search movies with their review stats."""
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', movies.DEFAULT_MOVIE_SORT)
    if sort not in movies.MOVIE_SORT_WHITELIST:
        sort = movies.DEFAULT_MOVIE_SORT

    total = movies.count_movies(q=q)
    total_pages = max(1, math.ceil(total / movies.PER_PAGE))

    if page < 1:
        return redirect(url_for('explore', page=1, q=q, sort=sort))
    if page > total_pages:
        return redirect(url_for('explore', page=total_pages, q=q, sort=sort))

    found_movies = movies.get_movies_with_stats(page=page, q=q, sort=sort)
    genres_map = movies.get_genres_for_movies([m['id'] for m in found_movies])

    return render_template(
        'movies/explore.html',
        movies=found_movies,
        genres_map=genres_map,
        total=total,
        page=page,
        total_pages=total_pages,
        q=q,
    )


@app.route('/user/<int:user_id>')
@app.route('/user/<int:user_id>/<int:page>')
@login_required
def profile(user_id, page=1):
    """Profile page. Shows user's reviews and statistics."""
    user = users.get_user_by_id(user_id)
    if user is None:
        abort(404, 'User not found.')

    stats = movies.get_review_stats(user_id)
    total_pages = max(1, math.ceil(stats['total'] / movies.PER_PAGE))

    if page < 1:
        return redirect(url_for('profile', user_id=user_id, page=1))
    if page > total_pages:
        return redirect(url_for('profile', user_id=user_id, page=total_pages))

    reviews = movies.get_reviews_by_user(user_id, page=page)

    return render_template(
        'movies/profile.html',
        user=user,
        stats=stats,
        reviews=reviews,
        genres_map=movies.get_genres_for_movies([r['movie_id'] for r in reviews]),
        reactions_map=movies.get_user_reactions(g.user['id']),
        current_user_id=g.user['id'],
        page=page,
        total_pages=total_pages
    )


def react_to_review(review_id, value):
    """Set a reaction, checks review exists and can't react own review.
    """
    review = movies.get_review_by_id(review_id)

    if review is None:
        abort(404, 'Review not found.')
    if review['author_id'] == g.user['id']:
        abort(403, "You can't react to your own review.")

    movies.set_reaction(g.user['id'], review_id, value)


@app.route('/<int:review_id>/like', methods=['POST'])
@login_required
def like(review_id):
    """Increase reaction value."""
    check_csrf()
    react_to_review(review_id, 1)
    return redirect(request.referrer or url_for('explore'))


@app.route('/<int:review_id>/dislike', methods=['POST'])
@login_required
def dislike(review_id):
    """Decrease reaction value."""
    check_csrf()
    react_to_review(review_id, -1)
    return redirect(request.referrer or url_for('explore'))
