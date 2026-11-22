"""Offline sanity check with SIMULATED users (TMDB has no real user histories).

Each fake user has two favourite genres. They "view" 4 random movies from those genres, then we
check how many of the top-10 recommendations are in a favourite genre, compared with a
popularity-only baseline. It proves the profile works; it is not a measure of real-world accuracy.

Run from the project root:  python tests/simulate.py
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from model import Recommender, load_catalog  # noqa: E402

df, source = load_catalog()
model = Recommender(df, source)
rng = random.Random(7)
now = time.time() * 1000

genres = [g for g in model.genre_names if sum(g in gs for gs in df["genres"]) >= 8]
hits_model = hits_pop = trials = 0
for _ in range(100):
    favs = rng.sample(genres, 2)
    pool = [i for i, gs in enumerate(df["genres"]) if any(g in gs for g in favs)]
    seeds = rng.sample(pool, 4)
    events = [{"type": "view", "movie_id": int(df.iloc[i]["id"]), "ts": now - k * 3600e3} for k, i in enumerate(seeds)]
    recs, _ = model.recommend(events, n=10)
    base, _ = model.recommend([], n=10, exclude_ids=[int(df.iloc[i]["id"]) for i in seeds])
    fav = lambda ms: sum(any(g in favs for g in m["genres"]) for m in ms)  # noqa: E731
    hits_model += fav(recs)
    hits_pop += fav(base)
    trials += 10

print(f"catalogue: {source} ({model.n} movies)")
print(f"top-10 in a favourite genre: model {hits_model / trials:.0%} vs popularity baseline {hits_pop / trials:.0%}")
sys.exit(0 if hits_model > hits_pop else 1)
