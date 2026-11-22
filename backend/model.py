"""Content-based, behaviour-aware movie recommender.

How it works
------------
1. Every movie becomes a vector: TF-IDF of its plot/keywords/cast/director, joined to a
   (weighted) multi-hot genre block.
2. Every user action (view, like, dislike, search, genre click) is turned into a vector
   in the same space and multiplied by a weight and a time-decay factor, so recent
   behaviour counts more. The sum is the user's taste profile.
3. Movies are scored by cosine similarity to the profile, blended with a quality prior
   (Bayesian weighted rating) and a small popularity prior.
4. The top candidates are re-ranked with MMR so the list is not 10 near-duplicates, and
   each pick gets a short human-readable reason ("Because you watched ...").

With no history the model falls back to popular, well-rated movies (cold start).
The user's history lives in their browser; the server stays stateless.
"""
import ast
import difflib
import os
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import normalize

from demo_data import DEMO

# ---- tunables ---------------------------------------------------------------------
EVENT_WEIGHTS = {"view": 1.0, "like": 3.0, "dislike": -2.5, "search": 0.8, "genre": 1.2}
HALF_LIFE_DAYS = 10.0          # an event loses half its influence every 10 days
W_TEXT, W_GENRE = 1.0, 0.8     # how much plot/people vs genre shapes a movie vector
SCORE_MIX = {"sim": 0.84, "quality": 0.11, "pop": 0.05}
MMR_LAMBDA = 0.85              # 1 = pure relevance, lower = more variety
MAX_EVENTS = 200

GENRE_ALIASES = {
    "sci-fi": "Science Fiction", "scifi": "Science Fiction", "sci fi": "Science Fiction",
    "animated": "Animation", "cartoon": "Animation", "cartoons": "Animation",
    "scary": "Horror", "funny": "Comedy", "romantic": "Romance", "kids": "Family",
    "docu": "Documentary", "mystery": "Mystery",
}


# ---- data loading -----------------------------------------------------------------
def _names(text, limit=None):
    try:
        items = ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError):
        return []
    names = [i["name"] for i in items if isinstance(i, dict) and "name" in i]
    return names[:limit] if limit else names


def _director(text):
    try:
        crew = ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError):
        return ""
    for member in crew:
        if member.get("job") == "Director":
            return member.get("name", "")
    return ""


def _load_tmdb(movies_path, credits_path):
    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)
    credits = credits.rename(columns={"movie_id": "id"}).drop(columns=["title"], errors="ignore")
    df = movies.merge(credits, on="id")
    out = pd.DataFrame(
        {
            "id": df["id"].astype(int),
            "title": df["title"].fillna("").astype(str),
            "year": pd.to_datetime(df["release_date"], errors="coerce").dt.year.fillna(0).astype(int),
            "genres": df["genres"].apply(_names),
            "overview": df["overview"].fillna("").astype(str),
            "keywords": df["keywords"].apply(_names),
            "cast": df["cast"].apply(lambda x: _names(x, 5)),
            "director": df["crew"].apply(_director),
            "vote_average": pd.to_numeric(df["vote_average"], errors="coerce").fillna(0.0),
            "vote_count": pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int),
        }
    )
    if "popularity" in df:
        out["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0.0)
    out = out[out["title"].str.strip() != ""].drop_duplicates("id")
    return out.reset_index(drop=True)


def load_catalog(data_dir=None):
    """Return (DataFrame, source_name). Uses real TMDB CSVs if present, else the demo list."""
    data_dir = Path(data_dir or os.environ.get("MOVIE_DATA_DIR") or Path(__file__).parent.parent / "data")
    movies_csv, credits_csv = data_dir / "tmdb_5000_movies.csv", data_dir / "tmdb_5000_credits.csv"
    if movies_csv.exists() and credits_csv.exists():
        return _load_tmdb(movies_csv, credits_csv), "tmdb_5000"
    return pd.DataFrame(DEMO), "demo"


# ---- model --------------------------------------------------------------------------
def _pct_rank(values):
    return pd.Series(values).rank(pct=True).to_numpy()


class Recommender:
    def __init__(self, df, source="custom"):
        self.source = source
        self.df = df.reset_index(drop=True)
        n = len(self.df)
        self.n = n
        self.ids = self.df["id"].to_numpy()
        self.id_to_idx = {int(i): k for k, i in enumerate(self.ids)}
        self.genre_names = sorted({g for gs in self.df["genres"] for g in gs})
        self._genre_lookup = {g.lower(): g for g in self.genre_names}

        # ---- text block (TF-IDF over plot + keywords + cast + director) ----
        def squash(items):
            return " ".join(s.replace(" ", "") for s in items)

        soup = (
            self.df["overview"]
            + " " + self.df["keywords"].apply(lambda k: " ".join(k) + " " + squash(k))
            + " " + self.df["cast"].apply(squash)
            + " " + self.df["director"].apply(lambda d: (d.replace(" ", "") + " ") * 2)
        )
        self.tfidf = TfidfVectorizer(
            stop_words="english", sublinear_tf=True, ngram_range=(1, 2), min_df=1 if n < 500 else 2,
            max_features=30000,
        )
        text = self.tfidf.fit_transform(soup)

        # ---- genre block ----
        self.gvec = CountVectorizer(analyzer=lambda gs: gs, binary=True)
        genres = normalize(self.gvec.fit_transform(self.df["genres"]).astype(float))
        self.n_text, self.n_genre = text.shape[1], genres.shape[1]
        self.X = normalize(hstack([text * W_TEXT, genres * W_GENRE]).tocsr())

        # ---- priors ----
        v, r = self.df["vote_count"].to_numpy(float), self.df["vote_average"].to_numpy(float)
        c, m = r[v > 0].mean() if (v > 0).any() else 0.0, np.percentile(v, 60)
        wr = v / (v + m + 1e-9) * r + m / (v + m + 1e-9) * c
        self.quality = _pct_rank(wr)
        pop = self.df["popularity"].to_numpy(float) if "popularity" in self.df else v
        self.popularity = _pct_rank(np.log1p(pop))

        # ---- lookup helpers for search ----
        self.title_lower = self.df["title"].str.lower().tolist()
        self.people_lower = (
            self.df["cast"].apply(lambda c_: " | ".join(c_)).str.lower()
            + " | " + self.df["director"].str.lower()
        ).tolist()

    # ------------------------------------------------------------------ card helpers
    def card(self, idx, reason=None, score=None):
        row = self.df.iloc[idx]
        out = {
            "id": int(row["id"]),
            "title": row["title"],
            "year": int(row["year"]) if row["year"] else None,
            "genres": list(row["genres"]),
            "rating": round(float(row["vote_average"]), 1),
            "votes": int(row["vote_count"]),
            "overview": row["overview"],
            "cast": list(row["cast"])[:4],
            "director": row["director"],
        }
        if reason:
            out["reason"] = reason
        if score is not None:
            out["score"] = round(float(score), 3)
        return out

    def get(self, movie_id):
        idx = self.id_to_idx.get(int(movie_id))
        return None if idx is None else self.card(idx)

    # ------------------------------------------------------------------ user profile
    def _genres_in_text(self, text):
        t = " " + re.sub(r"[^a-z0-9\- ]", " ", text.lower()) + " "
        found = {g for low, g in self._genre_lookup.items() if f" {low} " in t}
        for alias, g in GENRE_ALIASES.items():
            if g in self.genre_names and f" {alias} " in t:
                found.add(g)
        return found

    def _genre_block(self, genre_list):
        vec = np.zeros(self.n_genre)
        if genre_list:
            row = self.gvec.transform([list(genre_list)]).astype(float)
            vec = normalize(row).toarray().ravel() * W_GENRE
        return vec

    def _query_vec(self, query):
        text = normalize(self.tfidf.transform([query])).toarray().ravel() * W_TEXT
        genre = self._genre_block(self._genres_in_text(query))
        v = np.concatenate([text, genre])
        norm = np.linalg.norm(v)
        return v / norm if norm else v

    @staticmethod
    def clean_events(events, now_ms=None):
        now_ms = now_ms or time.time() * 1000
        cleaned = []
        if not isinstance(events, list):
            return cleaned
        for e in events[-MAX_EVENTS:]:
            if not isinstance(e, dict) or e.get("type") not in EVENT_WEIGHTS:
                continue
            try:
                ts = float(e.get("ts", now_ms))
                if not np.isfinite(ts):
                    ts = now_ms
            except (TypeError, ValueError, OverflowError):
                ts = now_ms
            try:
                movie_id = int(e.get("movie_id"))
            except (TypeError, ValueError, OverflowError):
                movie_id = None
            cleaned.append(
                {
                    "type": e["type"],
                    "movie_id": movie_id,
                    "query": str(e.get("query", ""))[:100],
                    "genre": str(e.get("genre", ""))[:40],
                    "ts": min(ts, now_ms),
                }
            )
        return cleaned

    def build_profile(self, events, now_ms=None):
        """Turn raw events into a taste vector + bookkeeping used for reasons and filtering."""
        now_ms = now_ms or time.time() * 1000
        events = self.clean_events(events, now_ms)
        profile = np.zeros(self.n_text + self.n_genre)
        genre_pref, anchors, seen, disliked = {}, {}, set(), set()
        used = 0

        for e in events:
            decay = 0.5 ** (max(0.0, now_ms - e["ts"]) / 86_400_000 / HALF_LIFE_DAYS)
            w = EVENT_WEIGHTS[e["type"]] * decay
            vec, genres = None, []
            if e["type"] in ("view", "like", "dislike"):
                idx = self.id_to_idx.get(e["movie_id"])
                if idx is None:
                    continue
                vec, genres = self.X[idx].toarray().ravel(), self.df.iloc[idx]["genres"]
                seen.add(idx)
                if e["type"] == "dislike":
                    disliked.add(idx)
                else:
                    anchors[idx] = anchors.get(idx, 0.0) + w
            elif e["type"] == "search":
                if not e["query"].strip():
                    continue
                vec, genres = self._query_vec(e["query"]), self._genres_in_text(e["query"])
            elif e["type"] == "genre":
                g = self._genre_lookup.get(e["genre"].lower())
                if not g:
                    continue
                vec = np.concatenate([np.zeros(self.n_text), self._genre_block([g])])
                genres = [g]
            profile += w * vec
            used += 1
            for g in genres:
                genre_pref[g] = genre_pref.get(g, 0.0) + w

        norm = np.linalg.norm(profile)
        return {
            "vec": profile / norm if norm > 1e-9 and used else None,
            "genre_pref": genre_pref,
            "anchors": anchors,
            "seen": seen,
            "disliked": disliked,
        }

    @staticmethod
    def top_genres(profile, k=5):
        pos = {g: s for g, s in profile["genre_pref"].items() if s > 0}
        total = sum(pos.values()) or 1.0
        return [{"genre": g, "share": round(s / total, 3)} for g, s in sorted(pos.items(), key=lambda x: -x[1])[:k]]

    # ------------------------------------------------------------------ ranking
    def _blend(self, sim, personalised):
        if personalised:
            s = sim / sim.max() if sim.max() > 0 else sim
            return SCORE_MIX["sim"] * s + SCORE_MIX["quality"] * self.quality + SCORE_MIX["pop"] * self.popularity
        return 0.65 * self.quality + 0.35 * self.popularity

    def _mmr(self, cand, scores, k, lam=MMR_LAMBDA):
        if len(cand) <= 1:
            return list(range(len(cand)))
        sims = (self.X[cand] @ self.X[cand].T).toarray()
        chosen, remaining = [int(np.argmax(scores[cand]))], set(range(len(cand)))
        remaining.discard(chosen[0])
        while remaining and len(chosen) < k:
            rem = np.array(sorted(remaining))
            mmr = lam * scores[cand][rem] - (1 - lam) * sims[np.ix_(rem, chosen)].max(axis=1)
            pick = int(rem[np.argmax(mmr)])
            chosen.append(pick)
            remaining.discard(pick)
        return chosen

    def _reason(self, idx, profile):
        anchors = profile["anchors"]
        if anchors:
            ids = list(anchors)
            sims = (self.X[idx] @ self.X[ids].T).toarray().ravel() * np.array([max(anchors[i], 1e-6) for i in ids]) ** 0.25
            best = int(np.argmax(sims))
            if sims[best] > 0.2:
                return f"Because you watched {self.df.iloc[ids[best]]['title']}"
        top = [g["genre"] for g in self.top_genres(profile, 3)]
        shared = [g for g in self.df.iloc[idx]["genres"] if g in top]
        if shared:
            return f"Matches your interest in {shared[0]}"
        return "Popular and highly rated" if profile["vec"] is not None else None

    def recommend(self, events=None, n=12, genre=None, exclude_ids=(), diversify=True):
        profile = self.build_profile(events)
        personalised = profile["vec"] is not None
        sim = self.X @ profile["vec"] if personalised else np.zeros(self.n)
        scores = self._blend(np.asarray(sim).ravel(), personalised)

        mask = np.ones(self.n, bool)
        for i in profile["seen"]:
            mask[i] = False
        for mid in exclude_ids:
            if int(mid) in self.id_to_idx:
                mask[self.id_to_idx[int(mid)]] = False
        if genre:
            g = self._genre_lookup.get(genre.lower())
            mask &= np.array([g in gs for gs in self.df["genres"]]) if g else False
        scores = np.where(mask, scores, -np.inf)

        pool = np.argsort(-scores)[: max(n * 5, 40)]
        pool = np.array([i for i in pool if np.isfinite(scores[i])])
        if len(pool) == 0:
            return [], profile
        order = self._mmr(pool, scores, n) if diversify else range(min(n, len(pool)))
        picks = [int(pool[i]) for i in order]
        return [self.card(i, self._reason(i, profile), scores[i]) for i in picks], profile

    def similar(self, movie_id, n=10):
        idx = self.id_to_idx.get(int(movie_id))
        if idx is None:
            return []
        sim = np.asarray((self.X @ self.X[idx].T).todense()).ravel()
        scores = 0.85 * sim + 0.10 * self.quality + 0.05 * self.popularity
        scores[idx] = -np.inf
        pool = np.argsort(-scores)[: n * 3]
        picks = [int(pool[i]) for i in self._mmr(pool, scores, n, lam=0.85)]
        return [self.card(i, f"Similar to {self.df.iloc[idx]['title']}", scores[i]) for i in picks]

    # ------------------------------------------------------------------ search
    def search(self, query, events=None, n=20):
        q = query.strip().lower()
        if not q:
            return []
        title = np.array([1.0 if t == q else 0.9 if t.startswith(q) else 0.7 if q in t else 0.0 for t in self.title_lower])
        if not title.any():  # typo tolerance only when nothing matches exactly
            for close in difflib.get_close_matches(q, self.title_lower, n=5, cutoff=0.6):
                title[self.title_lower.index(close)] = 0.6
        people = np.array([0.6 if q in p else 0.0 for p in self.people_lower])
        qv = self._query_vec(query)
        sem = np.asarray(self.X @ qv).ravel()
        sem = sem / sem.max() if sem.max() > 0 else sem
        genres = self._genres_in_text(query)
        gmatch = np.array([0.35 if genres and genres & set(gs) else 0.0 for gs in self.df["genres"]])

        score = title + people + 0.8 * sem + gmatch + 0.05 * self.quality
        profile = self.build_profile(events)
        if profile["vec"] is not None:  # nudge results toward what this user tends to like
            ps = np.asarray(self.X @ profile["vec"]).ravel()
            score = score + 0.15 * (ps / ps.max() if ps.max() > 0 else ps)

        keep = np.argsort(-score)[:n]
        out = []
        for i in keep:
            if score[i] < 0.12:
                continue
            if title[i] >= 0.6:
                why = "Title match"
            elif people[i] > 0:
                why = "Cast or director match"
            elif gmatch[i] > 0 and sem[i] < 0.25:
                why = "Genre match"
            else:
                why = "Plot match"
            out.append(self.card(int(i), why, score[i]))
        return out

    # ------------------------------------------------------------------ home page
    def home(self, events=None):
        recs, profile = self.recommend(events, n=12)
        rows = [{"key": "recommended", "title": "Recommended for you" if profile["vec"] is not None else "Popular right now", "movies": recs}]

        # "Because you watched X" rows for the two most recent distinct viewed / liked movies
        recent_ids, seen_ids = [], set()
        for e in reversed(self.clean_events(events)):
            if e["type"] in ("view", "like") and e["movie_id"] in self.id_to_idx:
                mid = e["movie_id"]
                if mid not in seen_ids:
                    seen_ids.add(mid)
                    recent_ids.append(mid)
        shown = {m["id"] for m in recs}
        for mid in recent_ids[:2]:
            sims = [m for m in self.similar(mid, 14) if m["id"] not in shown and self.id_to_idx[m["id"]] not in profile["seen"]][:10]
            if sims:
                rows.append({"key": f"because-{mid}", "title": f"Because you watched {self.get(mid)['title']}", "movies": sims})
                shown |= {m["id"] for m in sims}

        # top genres, ranked within the genre
        for g in [t["genre"] for t in self.top_genres(profile, 2)]:
            picks, _ = self.recommend(events, n=10, genre=g, exclude_ids=shown)
            if picks:
                rows.append({"key": f"genre-{g}", "title": f"Top picks in {g}", "movies": picks})
                shown |= {m["id"] for m in picks}

        recent = [self.get(mid) for mid in recent_ids[:12]]
        return {
            "rows": rows,
            "recent": [m for m in recent if m],
            "taste": self.top_genres(profile),
            "personalised": profile["vec"] is not None,
        }

    def browse_genre(self, genre, events=None, n=24):
        return self.recommend(events, n=n, genre=genre, diversify=False)[0]
