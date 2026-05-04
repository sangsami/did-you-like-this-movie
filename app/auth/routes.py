import functools
import secrets
import sqlite3

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import queries
from app.auth.security import check_csrf


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.before_app_request
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = queries.get_user_by_id(user_id=user_id)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        check_csrf()

        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']

        error = None

        if not username:
            error = 'Username is required.'
        elif len(username) > 50:
            error = 'Username must be 50 characters or fewer.'
        elif not password1 or not password2:
            error = 'Password is required.'
        elif len(password1) > 200:
            error = 'Password must be 200 characters or fewer.'
        elif password1 != password2:
            error = "Passwords did not match"

        if error is None:
            try:
                queries.create_user(
                    username,
                    generate_password_hash(password1)
                )
            except sqlite3.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error, 'error')

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        check_csrf()

        username = request.form['username']
        password = request.form['password']
        error = None

        user = queries.get_user_by_username(username=username)

        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['csrf_token'] = secrets.token_hex(16)
            return redirect(url_for('movies.index'))

        flash(error, 'error')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('movies.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
