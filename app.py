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
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

import db
import movies
import users

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
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


@app.before_request
def before_request():
    """Start timer before app request."""
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Stop timer after request."""
    start_time = getattr(g, 'start_time', None)
    if start_time is not None:
        elapsed = round(time.time() - start_time, 2)
        print(f"elapsed time: {elapsed} s")
    return response


@app.before_request
def load_logged_in_user():
    """Load logged user before request."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = users.get_user_by_id(user_id=user_id)


@app.route('/auth/register', methods=('GET', 'POST'))
def register():
    """Register route."""
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

    return render_template('auth/register.html')


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

        existing = movies.get_movie_by_title(title)
        if existing:
            flash('Movie already exists, opening review form for that title.', 'info')
            return redirect(url_for('create_review', movie_id=existing['id']))

        movie_id = movies.insert_movie(title)
        movies.set_movie_genres(movie_id, request.form.getlist('genres'))
        flash('Movie added successfully.')
        return redirect(url_for('create_review', movie_id=movie_id))

    return render_template('movies/add.html', all_genres=all_genres)


@app.route('/create/<int:movie_id>', methods=('GET', 'POST'))
@login_required
def create_review(movie_id):
    """Create review page. Login required."""
    movie = movies.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    movie_genres = movies.get_movie_genres(movie_id)

    if request.method == 'POST':
        check_csrf()
        body = request.form.get('body', '').strip()
        liked_raw = request.form.get('liked')
        recommend_raw = request.form.get('recommend')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/create_review.html', movie=movie,
                                   movie_genres=movie_genres)

        if movies.review_exists(g.user['id'], movie_id):
            flash('You already reviewed this movie.', 'error')
            return redirect(url_for('index'))

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

    return render_template('movies/create_review.html', movie=movie, movie_genres=movie_genres)


@app.route('/<int:review_id>/update', methods=('GET', 'POST'))
@login_required
def update(review_id):
    """Update review. Login required."""
    review = movies.get_review(review_id=review_id, user_id=g.user['id'])

    if review is None:
        abort(404, "Review not found or you don't have permission.")

    if request.method == 'POST':
        check_csrf()
        body = request.form.get('body', '').strip()
        liked = request.form.get('liked')
        recommend = request.form.get('recommend')

        if len(body) > 2000:
            flash('Review must be 2000 characters or fewer.', 'error')
            return render_template('movies/update.html', review=review)

        liked = _parse_bool(liked)
        recommend = _parse_bool(recommend)

        movies.update_review(review_id=review_id, body=body, liked=liked, recommend=recommend)

        flash('Review updated successfully.')
        return redirect(url_for('index'))

    return render_template('movies/update.html', review=review)


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


@app.route('/search')
@login_required
def search():
    "Search movie."
    q = request.args.get('q', '').strip()
    found_movies = movies.search_movies(q) if q else []
    return render_template('movies/search.html', movies=found_movies, q=q)


@app.route('/feed')
@app.route('/feed/<int:page>')
@login_required
def feed(page=1):
    """Review feed page."""
    q = request.args.get('q', '').strip()
    search_by = request.args.get('search_by', 'movie')
    if search_by not in ('movie', 'user'):
        search_by = 'movie'

    total = movies.count_all_reviews(q=q, search_by=search_by)
    total_pages = max(1, math.ceil(total / movies.PER_PAGE))

    if page < 1:
        return redirect(url_for('feed', page=1, q=q, search_by=search_by))
    if page > total_pages:
        return redirect(url_for('feed', page=total_pages, q=q, search_by=search_by))

    reviews = movies.get_all_reviews(page=page, q=q, search_by=search_by)
    liked_map = movies.get_user_reactions(g.user['id'])
    genres_map = movies.get_genres_for_movies([r['movie_id'] for r in reviews])

    return render_template(
        'movies/feed.html',
        reviews=reviews,
        liked_map=liked_map,
        genres_map=genres_map,
        current_user_id=g.user['id'],
        page=page,
        total_pages=total_pages,
        q=q,
        search_by=search_by
    )


@app.route('/<int:review_id>/like', methods=['POST'])
@login_required
def like(review_id):
    """Increase reaction value."""
    check_csrf()
    movies.set_reaction(g.user['id'], review_id, 1)
    return redirect(request.referrer or url_for('feed'))


@app.route('/<int:review_id>/dislike', methods=['POST'])
@login_required
def dislike(review_id):
    """Decrease reaction value."""
    check_csrf()
    movies.set_reaction(g.user['id'], review_id, -1)
    return redirect(request.referrer or url_for('feed'))
