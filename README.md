# CineMatch – movie recommendation website

HTML/CSS/JS frontend + Flask API + a content-based ML recommender that learns from what the
user **views, likes, dislikes, searches and which genres they tap**.

## Run it

```bash
pip install -r requirements.txt
cd backend
python app.py            # open http://127.0.0.1:5000
```
$env:TMDB_API_KEY="eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNGJjY2MwMjc5ZTcyODYzZGM2ZjQ5NGY3NzU3ODg3YSIsIm5iZiI6MTc5NTM2Mjg2NS4xMjgsInN1YiI6IjZiMDMxMDMxN2MyNTg1Y2ViZTNlMjFhNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.3gqip7rumQnDddfZvOIaIQ_3E-PPGAclpD1p6ukfLv0"; python app.py

**The Flask server must be running** for the page to show movies. You can open the site at
http://127.0.0.1:5000, or keep using VS Code Live Server (port 5500): the page finds the API on port 5000
automatically, so just start `python app.py` first.

It starts with a 50-movie **demo catalogue**. To use the real dataset, copy these two Kaggle files
into the `data/` folder and restart:

```
data/tmdb_5000_movies.csv
data/tmdb_5000_credits.csv
```

(Or set `MOVIE_DATA_DIR` to the folder that holds them.)

## Movie posters (optional, free)

Posters come from the TMDB API. Without a key the site still works and shows coloured placeholder cards.

1. Create a free account at themoviedb.org, then go to Settings → API and request a key (choose "Developer").
2. Start the server with the key in an environment variable:

   ```powershell
   # Windows PowerShell
   $env:TMDB_API_KEY="your_key_here"; python app.py
   ```
   ```bat
   :: Windows cmd
   set TMDB_API_KEY=your_key_here
   python app.py
   ```
   ```bash
   # macOS / Linux
   TMDB_API_KEY=your_key_here python app.py
   ```

How it works: the browser asks `/api/posters` for the ids on screen, the Flask server asks TMDB (so your key
is never sent to the browser) and remembers the answers in `data/poster_cache.json`, so each poster is looked
up only once. With the TMDB 5000 files it looks movies up by TMDB id; with the demo catalogue it searches by
title and year. If a poster is missing or fails to load, the placeholder stays. TMDB's terms ask for the
attribution line that appears in the footer when posters are on.

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
backend/posters.py    TMDB poster lookup + cache
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
| POST | `/api/posters` `{ids}` | poster image URLs (needs `TMDB_API_KEY`) |
| GET | `/api/info` | genres, catalogue size |

An event looks like `{"type": "view|like|dislike|search|genre", "movie_id": 1, "query": "...", "genre": "Horror", "ts": 1700000000000}`.

## Notes and next steps

- History is kept in the browser (localStorage); the server is stateless, so there is no login or database to set up.
  For accounts and cross-device history, store the events per user in a database and pass them to the same model.
- TMDB 5000 has no user ratings, so this is content-based. Posters need a TMDB API key (see above).
- `python tests/simulate.py` uses simulated users, so it checks that the profile logic works, not real-world accuracy.
- For deployment use a production server, e.g. `gunicorn -w 2 app:app` from `backend/`.
