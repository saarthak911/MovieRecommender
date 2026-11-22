
import os
import re
from pathlib import Path

from flask import Flask, jsonify, request

from model import Recommender, load_catalog
from posters import PosterService

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024  # histories are small; reject anything huge

_df, _source = load_catalog()
model = Recommender(_df, _source)
print(f"[movie-site] catalogue: {_source}, {model.n} movies, {len(model.genre_names)} genres")

_data_dir = Path(os.environ.get("MOVIE_DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
posters = PosterService(_data_dir / "poster_cache.json", by_id=(_source == "tmdb_5000"))
print(f"[movie-site] posters: {'on' if posters.enabled else 'off (set TMDB_API_KEY to enable)'}")


@app.after_request
def allow_local_frontends(resp):
    """Let a page served from another local port (e.g. VS Code Live Server) call this API."""
    origin = request.headers.get("Origin", "")
    if re.fullmatch(r"http://(localhost|127\.0\.0\.1)(:\d+)?", origin):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Vary"] = "Origin"
    return resp


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/info")
def info():
    return jsonify({"source": model.source, "count": model.n, "genres": model.genre_names, "posters": posters.enabled})


@app.post("/api/posters")
def poster_urls():
    """Body: {"ids": [movie ids]}  ->  {"posters": {"<id>": url or null}}"""
    if not posters.enabled:
        return jsonify({"enabled": False, "posters": {}})
    ids = _body().get("ids")
    items = []
    for raw in (ids if isinstance(ids, list) else [])[:60]:
        try:
            idx = model.id_to_idx.get(int(raw))
        except (TypeError, ValueError, OverflowError):
            continue
        if idx is not None:
            row = model.df.iloc[idx]
            items.append({"id": int(row["id"]), "title": row["title"], "year": int(row["year"]) or None})
    return jsonify({"enabled": True, "posters": {str(k): v for k, v in posters.get_many(items).items()}})


@app.post("/api/home")
def home():
    return jsonify(model.home(_body().get("events")))


@app.post("/api/search")
def search():
    body = _body()
    query = str(body.get("q", ""))[:100]
    return jsonify({"query": query, "results": model.search(query, body.get("events"))})


@app.post("/api/genre/<name>")
def genre(name):
    if name.lower() not in {g.lower() for g in model.genre_names}:
        return jsonify({"error": "unknown genre"}), 404
    return jsonify({"genre": name, "results": model.browse_genre(name, _body().get("events"))})


@app.get("/api/movie/<int:movie_id>")
def movie(movie_id):
    found = model.get(movie_id)
    if not found:
        return jsonify({"error": "movie not found"}), 404
    return jsonify({"movie": found, "similar": model.similar(movie_id, 10)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
