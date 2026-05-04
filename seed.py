import random
import sqlite3

from werkzeug.security import generate_password_hash

db = sqlite3.connect("instance/app.sqlite")
db.execute("PRAGMA foreign_keys = OFF")

db.execute("DELETE FROM review_reactions")
db.execute("DELETE FROM reviews")
db.execute("DELETE FROM movies")
db.execute("DELETE FROM users")

user_count = 1_000
movie_count = 10_000
review_count = 100_000
reaction_count = 500_000

password_hash = generate_password_hash("password")
for i in range(1, user_count + 1):
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
               [f"user{i}", password_hash])

for i in range(1, movie_count + 1):
    db.execute("INSERT INTO movies (title) VALUES (?)", [f"Movie {i}"])

seen = set()
review_ids = []
while len(seen) < review_count:
    user_id = random.randint(1, user_count)
    movie_id = random.randint(1, movie_count)
    if (user_id, movie_id) in seen:
        continue
    seen.add((user_id, movie_id))
    cursor = db.execute(
        "INSERT INTO reviews (author_id, movie_id, body, liked, recommend) VALUES (?, ?, ?, ?, ?)",
        [user_id, movie_id, f"Review {len(seen)}", random.choice([1, 0, None]), random.choice([1, 0, None])]
    )
    review_ids.append(cursor.lastrowid)
    if len(seen) % 10_000 == 0:
        print(f"  reviews {len(seen)}/{review_count}")

seen = set()
while len(seen) < reaction_count:
    user_id = random.randint(1, user_count)
    review_id = random.randint(0, len(review_ids) - 1)
    if (user_id, review_id) in seen:
        continue
    seen.add((user_id, review_id))
    db.execute("INSERT INTO review_reactions (user_id, review_id, value) VALUES (?, ?, ?)",
               [user_id, review_ids[review_id], random.choice([1, -1])])
    if len(seen) % 50_000 == 0:
        print(f"  reactions {len(seen)}/{reaction_count}")

db.execute("PRAGMA foreign_keys = ON")
db.commit()
db.close()
