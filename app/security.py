"""App security helper functions."""

from flask import request, session, abort

def check_csrf():
    """Check for CSRF token, throw 403 if not found or mismatch."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        session_token = session.get("csrf_token")
        if not token or not session_token or token != session_token:
            abort(403)
