"""Write about.md (paste into AniList -> Settings -> About) and preview.html (local look-alike), plus
waifus.md / preview-waifus.html for the side waifu collection (not part of the main About page).

  python build/make_about.py

Every asset is served by GitHub Pages from main (10-minute cache), so pushing a changed image updates the
profile by itself; the About text only needs re-pasting when sections are added, removed or reordered.
"""
import html
import re

from common import ROOT
from waifus import PYRAMID, RANKS, SUB, WAIFUS

PAGES = "https://makogai.github.io/anilist-profile/profile/"
FULL_VIDEO = PAGES + "rem-visualizer-full.mp4"  # full song with sound; AniList's webm() always starts muted
YOUTUBE_ID = ""  # set to the song's YouTube video id to add a play-with-sound embed under the visualizer

STEAM = "https://steamcommunity.com/id/mrharold0011"
YOUTUBE = "https://www.youtube.com/c/MareGraphics"
DISCORD_WIDGET = "https://discord.c99.nl/widget/theme-4/141206144264699904.png"


def blocks(a):
    """a(name) -> URL of a profile asset. Each inner list is one centred ~~~ block; images inside a block
    sit tight, between blocks AniList adds paragraph spacing, so grouping varies the page rhythm."""
    yt = [f"youtube({YOUTUBE_ID})"] if YOUTUBE_ID else []

    def img(name):
        return f"img720({a(name)})"

    return [
        [img("hero.webp"), img("tapes.webp")],
        [img("intro.webp"), img("sep-lace.webp"), img("stats.webp")],
        [img("top3.webp"), img("sep-sigil.webp"), img("firsts.webp")],
        [img("sep-chain.webp"), img("waifu.webp"), f"webm({a('nowplaying.webm')})", *yt,
         f"[ img420({a('play-sound.webp')}) ]({FULL_VIDEO})"],
        [img("sep-lace.webp"), img("milestones.webp"), img("genres.webp")],
        [img("tapes.webp")],
        # the spaces inside [ ... ] matter: AniList's img rule is greedy up to the last ")" before
        # whitespace, so "[img250(url)](link)" swallows "](link" into the image URL (see ANILIST_IMG)
        [f"[ img250({a('social-steam.webp')}) ]({STEAM}) [ img250({a('social-youtube.webp')}) ]({YOUTUBE})"],
        [f"img420({DISCORD_WIDGET})"],
        [img("footer.webp")],
    ]


def waifu_blocks(a):
    """Side collection: header plus the card pyramid, one line per row (AniList keeps line breaks), card
    width set by the row's rank."""
    rank_of = {w[0]: w[4] for w in WAIFUS}
    rows = [" ".join(f"img{RANKS[rank_of[k]]['out'] // 2}({a(f'{SUB}card-{k}.webp')})" for k in row)
            for row in PYRAMID]
    return [[f"img720({a(SUB + 'waifu-head.webp')})", *rows]]


def to_markdown(bl):
    return "\n".join("~~~\n" + "\n".join(lines) + "\n~~~" for lines in bl) + "\n"


# AniList's own image rule, copied from anilist.co's markdownHtml(); the preview uses it so parsing
# quirks show up locally instead of on the live profile
ANILIST_IMG = re.compile(r"img\s?(\d+%?)?\s?\((.[\S]+)\)", re.I)


def to_html(bl, title="Makogai profile preview"):
    def line(s):
        s = html.escape(s, quote=False)
        s = ANILIST_IMG.sub(r'<img width="\1" src="\2">', s)
        s = re.sub(r"\[\s*(<img [^>]+>)\s*\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"webm\(([^)]+)\)", r'<video src="\1" muted autoplay loop controls></video>', s)
        s = re.sub(r"youtube\(([^)]+)\)", r'<iframe width="480" height="270" src="https://www.youtube.com/embed/\1"></iframe>', s)
        s = re.sub(r"__\[([^\]]+)\]\(([^)]+)\)__", r'<b><a href="\2">\1</a></b>', s)
        return s
    body = "\n".join('<div class="c">' + "<br>".join(line(x) for x in lines) + "</div>" for lines in bl)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
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
    def url(name):
        return PAGES + name

    (ROOT / "about.md").write_text(to_markdown(blocks(url)), encoding="utf-8")
    (ROOT / "preview.html").write_text(to_html(blocks(lambda n: "profile/" + n)), encoding="utf-8")
    (ROOT / "waifus.md").write_text(to_markdown(waifu_blocks(url)), encoding="utf-8")
    (ROOT / "preview-waifus.html").write_text(to_html(waifu_blocks(lambda n: "profile/" + n), "Waifu collection"),
                                              encoding="utf-8")
    print("about.md + waifus.md (assets on GitHub Pages), preview.html + preview-waifus.html written")


if __name__ == "__main__":
    main()
