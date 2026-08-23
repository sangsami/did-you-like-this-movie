# Did You Like This Movie?

**Did You Like This Movie?** is a simple movie review app built around one question: *Did you like this movie, and would you recommend it?*

Users can write short reviews, classify movies by genre, and react to each other's reviews.

## Features

- Create an account and log in
- Add, edit, and delete your own reviews
- Review movie as liked / disliked / no answer
- Review movie as recommended / not recommended / no answer
- Browse movies on Explore, sorted by most reviewed, most liked, title, or newest
- Search for movies by title
- See a movie's own page with its review statistics and every review
- Like or dislike other people's reviews
- Assign one or more genres to a movie (Action, Comedy, Drama, …)
- View any user's profile page for their reviews and review statistics

## How to run

**Create virtual environment and install dependencies:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
```

**Initialise and seed the database:**
```bash
flask init-db
flask seed-db
```

**Run in development mode:**
```bash
flask run --debug
```

**Run in production mode:**
```bash
SECRET_KEY=your-secret-key flask run
```

> For development the app falls back to the key `'dev'`. Set the `SECRET_KEY`
> environment variable (or add `SECRET_KEY = '…'` to a `config.py` in the
> project root) for any public deployment.

## Getting started

1. Open `http://localhost:5000` in your browser.
2. Register a new account at `/auth/register`.
3. Start adding reviews with **New Review**.
