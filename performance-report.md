Suurien tietomäärien käsittelyn testausta varten luotii `seed.py` tiedosto, joka loi 10 000 elokuvaa ja 100 000 arvostelua. Ennen indeksien lisäystä `feed` sivun lataus vei keskimäärin ~0.85 sekuntia. Sivulla on myös sivutus, joka rajaa näytetyt arvostelut 10 kappaleeseen per sivu.

```bash
elapsed time: 0.83 s
127.0.0.1 - - [04/May/2026 10:48:21] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:48:21] "GET /static/style.css HTTP/1.1" 304 -
elapsed time: 0.84 s
127.0.0.1 - - [04/May/2026 10:48:23] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:48:23] "GET /static/style.css HTTP/1.1" 304 -
elapsed time: 0.84 s
127.0.0.1 - - [04/May/2026 10:48:25] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:48:25] "GET /static/style.css HTTP/1.1" 304 -
elapsed time: 0.89 s
127.0.0.1 - - [04/May/2026 10:48:29] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:48:29] "GET /static/style.css HTTP/1.1" 304 -
```

Indeksien luonnin jälkeen sivu latautuu keskimäärin ~0.10 sekunnissa, eli indeksien luonti nopeutti arvosteluiden kyselyä huomattavasti.

```sql
CREATE INDEX idx_reviews_author_created ON reviews (author_id, created DESC);
CREATE INDEX idx_reactions_review ON review_reactions (review_id);
```

```bash
elapsed time: 0.09 s
127.0.0.1 - - [04/May/2026 10:50:22] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:50:22] "GET /static/style.css HTTP/1.1" 304 -
elapsed time: 0.1 s
127.0.0.1 - - [04/May/2026 10:50:23] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:50:23] "GET /static/style.css HTTP/1.1" 304 -
elapsed time: 0.1 s
127.0.0.1 - - [04/May/2026 10:50:24] "GET /feed HTTP/1.1" 200 -
elapsed time: 0.0 s
127.0.0.1 - - [04/May/2026 10:50:24] "GET /static/style.css HTTP/1.1" 304 -
```
