# Pylint-raportti

Pylint antaa seuraavan raportin sovelluksesta:

```
> make lint
venv/bin/uv run --active pylint app

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

pylint-ignoreen on laitettu seuraavat varoitukset:

```
app/__init__.py:18:4: C0415: Import outside toplevel (.db) (import-outside-toplevel)
app/__init__.py:21:4: C0415: Import outside toplevel (auth.bp) (import-outside-toplevel)
app/__init__.py:24:4: C0415: Import outside toplevel (movies.bp) (import-outside-toplevel)
```

Koodi on kirjoitettu samalla tavalla kuin Flask-dokumentaation suositusten mukaan, joten kyseiset varoitukset on tarkoituksella ohitettu. Pylint ei oletuksena tunnista Flaskin käyttämää arkkitehtuurimallia.
