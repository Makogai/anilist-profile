# Makogai — AniList profile

Rem-themed (Re:Zero) About section, banner and avatar for [anilist.co/user/Makogai](https://anilist.co/user/Makogai),
in midnight blue and violet. Assets are served from this repo through jsDelivr.

## Put it on AniList

1. **About:** copy all of [`about.md`](about.md) into *Settings → About*. The asset URLs are pinned to a commit, so
   jsDelivr never serves a stale cached file.
2. **Banner:** upload [`profile/banner.jpg`](profile/banner.jpg) (1700×330) in *Settings → Banner*.
3. **Avatar:** upload [`profile/avatar.png`](profile/avatar.png) in *Settings → Avatar*.
4. **Sound (optional):** AniList's `webm()` always plays muted, so the visualizer is silent on the page. For sound,
   put the song's YouTube video id in `YOUTUBE_ID` in `build/make_about.py` and regenerate `about.md`. That adds a
   click-to-play `youtube()` embed under the visualizer.

Open [`preview.html`](preview.html) locally to see the page in a mock of AniList's About column before posting.

## What's in it

| Section | File(s) | Notes |
|---|---|---|
| Hero | `hero.webp` | Animated: falling snow, moon glow, light sweep over the name |
| About me + favorite kanji 愛 | `intro.webp` | |
| Statistics | `stats.webp` | Snapshot from the AniList API, November 2026 |
| Top 3 anime | `top3.webp` | Re:Zero, Shield Hero, Code Geass, official AniList covers |
| Firsts & favorites | `firsts.webp` | |
| Waifu collection | `waifu-row.webp` (+ single `waifu-*.webp`) | SSR cards with a holographic shine: Rem, Zero Two, Shiro |
| Now playing | `nowplaying.webm` | ~11 s seamless loop from the chorus, bars driven by the real song spectrum |
| Milestones / genres | `head-*.webp` | Third-party cards by [Logia](https://anilist.co/user/Logia) under themed headers |
| Socials + footer | `social-*.webp`, `footer.webp` | |
| Separators | `sep-chain.webp` (animated), `sep-lace.webp`, `sep-sigil.webp` | |

Design notes: AniList shows the About column about **514 px** wide on desktop (measured), and images are capped to
that width. Everything is drawn at 1440 px for sharp high-DPI screens, with text sized to stay readable at 0.36×.
Each panel is a self-contained dark card, so it also works in AniList's light theme.

## Rebuild

Needs Python 3 with Pillow and numpy, and ffmpeg (VP9) on PATH. Fonts: Windows' Bahnschrift, Segoe UI and Noto JP.

```bash
cd build
python fetch_covers.py        # official cover art from the AniList API -> build/covers (git-ignored)
python panels.py              # static panels, headers, separators, socials, footer
python animated.py            # waifu cards + row, chain separator, hero
python visualizer.py loop     # profile/nowplaying.webm (needs ../music.mp3, which is git-ignored)
python visualizer.py full     # optional: export/rem-visualizer-full.mp4, 1080p with audio for YouTube
python extras.py              # banner + avatar
python make_about.py <commit-sha>
```

## Credits

- Character art, backgrounds and ornaments in `art/` were generated with OpenAI Codex image generation as fan art.
  Rem and Re:Zero belong to Tappei Nagatsuki / Kadokawa, Zero Two to Trigger / A-1 Pictures / CloverWorks, and
  Shiro to Yuu Kamiya.
- Cover art comes from AniList.
- Design spec: [`design/PLAN.md`](design/PLAN.md), written by Codex.
- The song itself is not included in this repository.
