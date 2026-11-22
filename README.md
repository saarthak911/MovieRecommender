# CineMatch – movie recommendation website

HTML/CSS/JS frontend + Flask API + a content-based ML recommender that learns from what the
user **views, likes, dislikes, searches and which genres they tap**.

## Run it

```bash
pip install -r requirements.txt
cd backend
python app.py            # open http://127.0.0.1:5000
```

It starts with a 50-movie **demo catalogue**. To use the real dataset, copy these two Kaggle files
into the `data/` folder and restart:

```
data/tmdb_5000_movies.csv
data/tmdb_5000_credits.csv
```

(Or set `MOVIE_DATA_DIR` to the folder that holds them.)

## How the ML works (`backend/model.py`)

1. **Movie vectors**: TF-IDF over plot, keywords, cast and director, joined to a weighted genre block.
2. **User profile**: each event becomes a vector (movie, search query, or genre) times a weight
   (like 3, view 1, genre tap 1.2, search 0.8, dislike -2.5) times a **time decay** (half-life 10 days),
   then everything is summed.
3. **Scoring**: cosine similarity to the profile + a Bayesian weighted-rating prior + a popularity prior.
4. **Diversity**: MMR re-ranking so results are not near-duplicates.
5. **Explanations**: "Because you watched X" or "Matches your interest in Y" on every pick.
6. **Cold start**: new users see popular, well-rated movies until they interact.
7. **Search**: title match (with typo tolerance), cast/director match, plot similarity and genre words
   ("scary", "sci-fi"), nudged toward the user's taste.

## Layout

```
backend/app.py        Flask API + serves the frontend
backend/model.py      the recommender
backend/demo_data.py  demo catalogue
frontend/             index.html, style.css, app.js (no build step)
tests/simulate.py     simulated-user sanity check
```

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/home` `{events}` | personalised rows + taste profile |
| POST | `/api/search` `{q, events}` | search |
| POST | `/api/genre/<name>` `{events}` | genre browse, ranked for the user |
| GET | `/api/movie/<id>` | details + similar movies |
| GET | `/api/info` | genres, catalogue size |

An event looks like `{"type": "view|like|dislike|search|genre", "movie_id": 1, "query": "...", "genre": "Horror", "ts": 1700000000000}`.

## Notes and next steps

- History is kept in the browser (localStorage); the server is stateless, so there is no login or database to set up.
  For accounts and cross-device history, store the events per user in a database and pass them to the same model.
- TMDB 5000 has no user ratings or poster paths, so this is content-based. Cards use genre-coloured
  placeholders; add a free TMDB API key to fetch posters by movie id.
- `python tests/simulate.py` uses simulated users, so it checks that the profile logic works, not real-world accuracy.
- For deployment use a production server, e.g. `gunicorn -w 2 app:app` from `backend/`.
