"""Fetch Makogai's AniList statistics into data/stats.json.

The file is only rewritten when a number changed, so `git diff` tells the GitHub Action whether the
stats panels need re-rendering. "updated" is the date the numbers last changed.
"""
import datetime
import json
import urllib.request

from common import STATS

USER = "Makogai"
QUERY = """query ($name: String) { User(name: $name) { statistics {
  anime { count episodesWatched minutesWatched meanScore genres(limit: 12, sort: COUNT_DESC) { genre count } }
  manga { count chaptersRead meanScore genres(limit: 6, sort: COUNT_DESC) { genre count } } } } }"""
# AniList answers 403 to Python's default user agent
HEADERS = {"Content-Type": "application/json", "Accept": "application/json",
           "User-Agent": "makogai-anilist-profile-build/1.0"}


def fetch() -> dict:
    req = urllib.request.Request("https://graphql.anilist.co", headers=HEADERS,
                                 data=json.dumps({"query": QUERY, "variables": {"name": USER}}).encode())
    with urllib.request.urlopen(req, timeout=30) as r:
        s = json.load(r)["data"]["User"]["statistics"]
    a, m = s["anime"], s["manga"]
    return {
        "anime": {"count": a["count"], "episodes": a["episodesWatched"], "minutes": a["minutesWatched"],
                  "mean": a["meanScore"], "genres": a["genres"]},
        "manga": {"count": m["count"], "chapters": m["chaptersRead"], "mean": m["meanScore"],
                  "genres": m["genres"]},
    }


def main():
    new = fetch()
    old = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    if {k: old.get(k) for k in new} == new:
        print("stats unchanged")
        return
    new["updated"] = datetime.date.today().isoformat()
    STATS.parent.mkdir(exist_ok=True)
    STATS.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"stats updated: {new['anime']['count']} anime, {new['anime']['episodes']} episodes, "
          f"{new['manga']['count']} manga, {new['manga']['chapters']} chapters")


if __name__ == "__main__":
    main()
