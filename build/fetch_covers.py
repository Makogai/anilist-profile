"""Download the official AniList cover art used by the Top 3 and Firsts panels into build/covers."""
import json
import urllib.request

from common import COVERS

QUERY = """query { Page { media(id_in: [21355, 99263, 1575, 5114, 106929, 100476]) {
  id coverImage { extraLarge } bannerImage } } }"""
NAMES = {21355: "rezero", 99263: "shield", 1575: "geass", 5114: "fmab", 106929: "eleceed", 100476: "redo"}
# AniList answers 403 to Python's default user agent
UA = {"User-Agent": "makogai-anilist-profile-build/1.0"}


def download(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        path.write_bytes(r.read())


def main():
    req = urllib.request.Request(
        "https://graphql.anilist.co", data=json.dumps({"query": QUERY}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json", **UA})
    media = json.load(urllib.request.urlopen(req))["data"]["Page"]["media"]
    COVERS.mkdir(parents=True, exist_ok=True)
    for m in media:
        name = NAMES[m["id"]]
        download(m["coverImage"]["extraLarge"], COVERS / f"{name}.jpg")
        if name == "rezero":
            download(m["bannerImage"], COVERS / "rezero_banner.jpg")
        print("fetched", name)


if __name__ == "__main__":
    main()
