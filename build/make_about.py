"""Write about.md (paste into AniList -> Settings -> About) and preview.html (local look-alike).

  python build/make_about.py <git-ref>

Assets are served by jsDelivr from this repo. Pin <git-ref> to a commit SHA so jsDelivr's cache
never serves a stale file after an update.
"""
import html
import re
import sys

from common import ROOT

CDN = "https://cdn.jsdelivr.net/gh/Makogai/anilist-profile@{ref}/profile/"
YOUTUBE_ID = ""  # set to the song's YouTube video id to add a play-with-sound embed under the visualizer

LOGIA_EPISODES = [
    "https://i.postimg.cc/rshDSd5k/1000_Episodes_Watched_ReVamp.png",
    "https://i.postimg.cc/7YWCh2x1/2000_Episodes_Watched_ReVamp.png",
    "https://i.postimg.cc/Gh1228SV/3000_Episodes_Watched_ReVamp.png",
    "https://i.postimg.cc/vZ2bWc3Q/4000_Episodes_Watched_ReVamp.png",
    "https://i.postimg.cc/m265jCf6/5000_Episodes_Watched_ReVampp.png",
    "https://i.postimg.cc/gjtNMF56/6000_Episodes_Watched_ReVamp.png",
    "https://i.postimg.cc/cHgbVJRB/7000_Episodes_Watched_ReVamp.png",
]
GENRE_CARDS = [
    "https://i.postimg.cc/ZRZbdWJd/Action-Mastery-Bronze.png",
    "https://i.postimg.cc/FH3XVhWg/Fantasy-Mastery-Gold.png",
    "https://i.postimg.cc/T3DfNVwb/Comedy-Mastery-Gold.png",
    "https://i.postimg.cc/1Rvm8R28/Adventure-Mastery-Silver.png",
]
STEAM = "https://steamcommunity.com/id/mrharold0011"
YOUTUBE = "https://www.youtube.com/c/MareGraphics"
DISCORD_WIDGET = "https://discord.c99.nl/widget/theme-4/141206144264699904.png"


def blocks(a):
    """a(name) -> URL of a profile asset. Each inner list is one centred ~~~ block."""
    yt = [f"youtube({YOUTUBE_ID})"] if YOUTUBE_ID else []
    return [
        [f"img720({a('hero.webp')})", f"img720({a('sep-chain.webp')})"],
        [f"img720({a('intro.webp')})", f"img720({a('sep-lace.webp')})"],
        [f"img720({a('stats.webp')})", f"img720({a('sep-sigil.webp')})"],
        [f"img720({a('top3.webp')})", f"img720({a('sep-lace.webp')})"],
        [f"img720({a('firsts.webp')})", f"img720({a('sep-chain.webp')})"],
        [f"img720({a('head-waifu.webp')})", f"img720({a('waifu-row.webp')})", f"img720({a('sep-sigil.webp')})"],
        [f"img720({a('head-music.webp')})", f"webm({a('nowplaying.webm')})", *yt, f"img720({a('sep-lace.webp')})"],
        [f"img720({a('head-milestones.webp')})"],
        ["Episode milestone cards by __[Logia](https://anilist.co/user/Logia)__"],
        [" ".join(f"img120({u})" for u in LOGIA_EPISODES)],
        [f"img720({a('sep-sigil.webp')})", f"img720({a('head-genres.webp')})"],
        [" ".join(f"img120({u})" for u in GENRE_CARDS)],
        [f"img720({a('sep-chain.webp')})", f"img720({a('head-socials.webp')})"],
        [f"[img250({a('social-steam.webp')})]({STEAM}) [img250({a('social-youtube.webp')})]({YOUTUBE})"],
        [f"img420({DISCORD_WIDGET})"],
        [f"img720({a('footer.webp')})"],
    ]


def to_markdown(bl):
    return "\n".join("~~~\n" + "\n".join(lines) + "\n~~~" for lines in bl) + "\n"


def to_html(bl):
    def line(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"\[img(\d+)\(([^)]+)\)\]\(([^)]+)\)", r'<a href="\3"><img width="\1" src="\2"></a>', s)
        s = re.sub(r"img(\d+)\(([^)]+)\)", r'<img width="\1" src="\2">', s)
        s = re.sub(r"webm\(([^)]+)\)", r'<video src="\1" muted autoplay loop controls></video>', s)
        s = re.sub(r"youtube\(([^)]+)\)", r'<iframe width="480" height="270" src="https://www.youtube.com/embed/\1"></iframe>', s)
        s = re.sub(r"__\[([^\]]+)\]\(([^)]+)\)__", r'<b><a href="\2">\1</a></b>', s)
        return s
    body = "\n".join('<div class="c">' + "<br>".join(line(x) for x in lines) + "</div>" for lines in bl)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Makogai profile preview</title>
<style>
  /* mimics AniList's profile About box: ~514 px column, dark theme */
  body {{ margin: 0; background: #0b1622; font: 14px/1.5 Overpass, "Segoe UI", sans-serif; color: #9fadbd; }}
  .about {{ width: 514px; max-width: calc(100vw - 32px); margin: 32px auto; padding: 18px;
           background: #151f2e; border-radius: 4px; }}
  .light .about {{ background: #fafafa; }} .light {{ background: #edf1f5; color: #5c728a; }}
  .c {{ text-align: center; margin: 0 0 10px; }}
  img, video, iframe {{ max-width: 100%; vertical-align: middle; }}
  video {{ width: auto; }}
  a {{ color: #3db4f2; }}
  button {{ position: fixed; top: 10px; right: 10px; }}
</style></head>
<body><button onclick="document.body.classList.toggle('light')">toggle light theme</button>
<div class="about">
{body}
</div></body></html>
"""


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else "main"
    (ROOT / "about.md").write_text(to_markdown(blocks(lambda n: CDN.format(ref=ref) + n)), encoding="utf-8")
    (ROOT / "preview.html").write_text(to_html(blocks(lambda n: "profile/" + n)), encoding="utf-8")
    print(f"about.md (assets @ {ref}) and preview.html written")


if __name__ == "__main__":
    main()
