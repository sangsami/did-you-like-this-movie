"""Authentication database queries."""

from app.db import get_db

def get_user_by_id(user_id):
    """Get user by ID."""
    db = get_db()
    return db.execute(
        "SELECT id, username, password_hash FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()


def get_user_by_username(username):
    """Get user by username."""
    db = get_db()
    return db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()


def create_user(username, password_hash):
    """Create user."""
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    db.commit()
