# Did You Like This Movie?

**Did You Like This Movie?** is a simple movie rating app built around one question: *Did you like this movie, and would you recommend it?*

Instead of long reviews, the app focuses on quick and clear feedback. You can:
- Like a movie without recommending it
- Dislike a movie but still recommend it to others

## Features

- Users can create an account and log in  
- Users can add, delete, and browse movies  
- Users can assign genres and keywords to movies  
- Users can rate movies with a like/dislike system  
- Users can mark movies as recommended or not recommended  
- Users can write short reviews (e.g., up to 10 words)  
- Users can view reviews from other users  

## How to run

This project uses `uv` as package manager, but shouldn't necessarily be needed if ran through `Make` commands

**Create virtual environment:**
```bash
make venv
```

**Install dependencies:**
```bash
make install
```

**Setup database:**
```bash
make setup
```

**Install dependencies:**
```bash
make install
```

**Run app in dev mode:**
```bash
make dev
```

**Run app in prod mode:**
```bash
make prod
```
