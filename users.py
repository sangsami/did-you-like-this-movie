"""Authentication database queries."""

import db


def get_user_by_id(user_id):
    """Get user by ID."""
    return db.query_one("SELECT id, username, password_hash FROM users WHERE id = ?", (user_id,))


def get_user_by_username(username):
    """Get user by username."""
    return db.query_one(
        "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
    )


def create_user(username, password_hash):
    """Create user."""
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
