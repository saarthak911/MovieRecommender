"""Flask API + static file server for the movie recommender site.

Run:  python app.py      then open http://127.0.0.1:5000
"""
import os
from pathlib import Path

from flask import Flask, jsonify, request

from model import Recommender, load_catalog

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024  # histories are small; reject anything huge

_df, _source = load_catalog()
model = Recommender(_df, _source)
print(f"[movie-site] catalogue: {_source}, {model.n} movies, {len(model.genre_names)} genres")


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/info")
def info():
    return jsonify({"source": model.source, "count": model.n, "genres": model.genre_names})


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
