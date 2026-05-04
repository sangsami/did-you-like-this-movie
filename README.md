# Did You Like This Movie?

**Did You Like This Movie?** is a simple movie review app built around one question: *Did you like this movie, and would you recommend it?*

Users can write short reviews, classify movies by genre, and react to each other's reviews.

## Features

- Create an account and log in
- Add, edit, and delete your own reviews
- Mark a review as liked / disliked / no answer
- Mark a review as recommended / not recommended / no answer
- Assign one or more genres to a review (Action, Comedy, Drama, …)
- Browse all reviews on the Explore feed and like or dislike them
- Search for movies by title
- View your own review statistics and reaction counts on your profile page

## How to run

This project uses `uv` as the package manager.

If you are running the program from scratch, just run this command from the root of this project (where Makefile is)

```bash
make clean venv install setup dev
```

**Create virtual environment and install dependencies:**
```bash
make venv
make install
```

**Initialise and seed the database:**
```bash
make setup
```

**Run in development mode:**
```bash
make dev
```

**Run in production mode:**
```bash
SECRET_KEY=your-secret-key make prod
```

> For development the app falls back to the key `'dev'`. Set the `SECRET_KEY`
> environment variable (or add `SECRET_KEY = '…'` to `instance/config.py`) for
> any public deployment.

## Getting started

1. Open `http://localhost:5000` in your browser.
2. Register a new account at `/auth/register`.
3. Start adding reviews with **New Review**.
