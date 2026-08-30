Suurien tietomäärien käsittelyn testausta varten luotiin `seed.py` tiedosto, joka loi 10 000 elokuvaa ja 100 000 arvostelua. Kaikkia sivuja testattiin sivutuksen kanssa, joka rajaa näytetyt arvostelut 10 kappaleeseen per sivu.

Seedillä alustetulla ohjelmaa voidaan testata käyttäjällä `user1` (tai millä vain tunnuksella välillä `user1` ja `user1000`) ja salasanalla `password`.

Projektissa käytettiin schemassa alla olevia indeksejä, ja niitä testattiin lataamalla tiettyjä sivuja indeksien kanssa ilman. Indeksien vaikutukset sivuihin on koottu yhteen alla olevaan taulukkoon.

```sql
CREATE INDEX idx_reviews_author_created ON reviews (author_id, created DESC);
CREATE INDEX idx_reviews_movie_created ON reviews (movie_id, created DESC);
CREATE INDEX idx_reactions_review ON review_reactions (review_id);
```

| Sivu                                  | Indeksien kanssa | Ilman indeksejä | Nopeutuskerroin |
|---------------------------------------|------------------|-----------------|-----------------|
| `/` - My reviews                      | 0.010 s          | 1.221 s         | 122.1x          |
| `/user/1` - profiilisivu              | 0.108 s          | 1.304 s         | 12.1x           |
| `/movie/500` - leffasivu              | 0.065 s          | 0.436 s         | 6.7x            |
| `/explore?q=Movie+1234` - haku        | 0.027 s          | 0.129 s         | 4.8x            |
| `/?filter=liked` - tykätyt arvostelut | 0.047 s          | 0.518 s         | 11.0x           |
| `/explore` - oletusjärjestys          | 0.086 s          | 0.108 s         | 1.3x            |

Yllä olevasta taulukosta huomataan, että indeksien lisäys nopeuttaa tietokantahakuja merkittävästi, parhaimmillaan nopeutus on 122x kertainen sivulla `/`, joka sisältää raskaita hakuja. Taulukosta nähdään, myös että sivulla `/explore` indeksien vaikutus on lähes olematon. `explore`-sivun tietokantahaut käyttävät `ORDER BY count(...)` queryä, joihin indeksit eivät voi vaikuttaa. Sivu pysyy silti melko nopeana indekseistä huolimatta, koska se on rajoitettu `GROUP BY` queryllä ja sivutuksella.

Indeksien vaikuttavuutta testattiin myös kokeilemalla tiputtamalla vuorotellen yksi indeksi, säilyttäen muut. Tulokset on koottu alla olevaan taulukkoon, josta nähdään, että merkittävin indeksi on `CREATE INDEX idx_reactions_review ON review_reactions (review_id);`, kun taas indeksi `CREATE INDEX idx_reviews_author_created ON reviews (author_id, created DESC);` on melko merkitsemätön. Tämä voisi olla, koska jokin query (`UNIQUE(author_id, movie_id)`?) saa SQLiten internaalisesti optimoimaan haun automaattisesti.

| Sivu         | Kaikki indeksit | -author | -movies | -reactions |
|--------------|-----------------|---------|---------|------------|
| `/`          | 0.015 s         | 0.077 s | 0.015 s | 1.337 s    |
| `/user/1`    | 0.106 s         | 0.104 s | 0.120 s | 1.476 s    |
| `/movie/500` | 0.065 s         | 0.068 s | 0.145 s | 0.431 s    |
