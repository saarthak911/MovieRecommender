"""Poster lookup through the TMDB API, with a disk cache.

Set TMDB_API_KEY (a v3 API key or a v4 "read access token") to turn posters on.
The key stays on the server; the browser only receives finished image URLs.

* TMDB 5000 catalogue  -> look up by TMDB id (exact).
* Demo catalogue       -> its ids are not TMDB ids, so look up by title + year instead.
"""
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class PosterService:
    def __init__(self, cache_path, by_id, api_key=None, api_base=None, image_base=None):
        self.key = (api_key if api_key is not None else os.environ.get("TMDB_API_KEY", "")).strip()
        self.api_base = (api_base or os.environ.get("TMDB_API_BASE") or "https://api.themoviedb.org/3").rstrip("/")
        self.image_base = (image_base or os.environ.get("TMDB_IMAGE_BASE") or "https://image.tmdb.org/t/p/w342").rstrip("/")
        self.by_id = by_id
        self.cache_path = Path(cache_path)
        self._lock = threading.Lock()
        self._cache = self._load()
        self._warned = False

    @property
    def enabled(self):
        return bool(self.key)

    # ---- cache -------------------------------------------------------------------
    def _load(self):
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._cache), encoding="utf-8")
            tmp.replace(self.cache_path)
        except OSError:
            pass  # a read-only folder just means no persistent cache

    @staticmethod
    def _key(item, by_id):
        return f"id:{item['id']}" if by_id else f"s:{item['title'].lower()}|{item.get('year') or ''}"

    # ---- TMDB --------------------------------------------------------------------
    def _get_json(self, path, params=None):
        params = dict(params or {})
        headers = {"Accept": "application/json"}
        if self.key.startswith("eyJ"):  # v4 read-access token
            headers["Authorization"] = f"Bearer {self.key}"
        else:
            params["api_key"] = self.key
        url = f"{self.api_base}{path}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=6) as resp:
            return json.load(resp)

    def _lookup(self, item):
        """Return a poster path, None if TMDB has none. Raises on temporary failures."""
        try:
            if self.by_id:
                return self._get_json(f"/movie/{item['id']}").get("poster_path")
            params = {"query": item["title"]}
            if item.get("year"):
                params["year"] = item["year"]
            for hit in self._get_json("/search/movie", params).get("results", []):
                if hit.get("poster_path"):
                    return hit["poster_path"]
            return None
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            raise

    def _fetch_one(self, item):
        try:
            return self._key(item, self.by_id), self._lookup(item), True
        except Exception as err:  # network down, bad key, rate limit: don't cache, try again later
            if not self._warned:
                self._warned = True
                print(f"[posters] lookup failed ({type(err).__name__}: {getattr(err, 'code', err)}). Check TMDB_API_KEY and network.")
            return self._key(item, self.by_id), None, False

    # ---- public ------------------------------------------------------------------
    def get_many(self, items):
        """items: [{'id', 'title', 'year'}] -> {id: url or None}"""
        if not self.enabled:
            return {i["id"]: None for i in items}
        missing = [i for i in items if self._key(i, self.by_id) not in self._cache]
        if missing:
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(self._fetch_one, missing))
            with self._lock:
                changed = False
                for key, path, ok in results:
                    if ok:
                        self._cache[key] = path
                        changed = True
                if changed:
                    self._save()
        out = {}
        for i in items:
            path = self._cache.get(self._key(i, self.by_id))
            out[i["id"]] = f"{self.image_base}{path}" if path else None
        return out
