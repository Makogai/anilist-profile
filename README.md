# Makogai — AniList profile

Rem-themed (Re:Zero) About section, banner and avatar for [anilist.co/user/Makogai](https://anilist.co/user/Makogai),
in midnight blue and violet with mint, pink and gold accents. Assets are served from this repo through jsDelivr.

## Put it on AniList

1. **About:** copy all of [`about.md`](about.md) into *Settings → About*. The asset URLs are pinned to a commit, so
   jsDelivr never serves a stale cached file.
2. **Banner:** upload [`profile/banner.gif`](profile/banner.gif) (animated, 1700×330) in *Settings → Banner*. If
   AniList rejects it or shows it frozen, use the static [`profile/banner.jpg`](profile/banner.jpg) instead.
3. **Avatar:** upload [`profile/avatar.png`](profile/avatar.png) (Rem, blue ring) or
   [`profile/avatar-sunflower.png`](profile/avatar-sunflower.png) (Rem with her sunflower, gold ring) in
   *Settings → Avatar*. Both are transparent PNGs.
4. **Sound (optional):** AniList's `webm()` always plays muted, so the visualizer is silent on the page. For sound,
   put the song's YouTube video id in `YOUTUBE_ID` in `build/make_about.py` and regenerate `about.md`. That adds a
   click-to-play `youtube()` embed under the visualizer.

Open [`preview.html`](preview.html) locally to see the page in a mock of AniList's About column before posting.

## What's in it

| Section | File(s) | Notes |
|---|---|---|
| Hero | `hero.webp` | Animated: Rem's hair and ribbon sway and she blinks; snow, moon glow, light sweep over the name |
| Marquee tapes | `tapes.webp` | Animated crossing tapes ("WELCOME · ようこそ", "REM · レム · BEST GIRL") |
| About me + favorite kanji 向日葵 | `intro.webp` | Animated: Rem waves, blinks, hair sways; sunflower (himawari) seal |
| Statistics | `stats.webp` | Chamfered "tech" card; snapshot from the AniList API, November 2026 |
| Top 3 anime | `top3.webp` | Re:Zero, Shield Hero, Code Geass, official AniList covers |
| Firsts & favorites | `firsts.webp` | Scattered polaroids with washi tape |
| Waifu collection | `waifu.webp` | Fanned SSR cards with a holographic shine: Zero Two, Rem, Iroha Igarashi |
| Now playing | `nowplaying.webm` | ~11 s seamless loop from the chorus, bars driven by the real song spectrum |
| Episode milestones | `milestones.webp` | Bronze → Diamond crests on a rising trail; 10,000 is locked at 9,607 (96%) |
| Genre mastery | `genres.webp` | Honeycomb of the top 5 genres by titles watched, each with its own emblem |
| Socials + footer | `social-*.webp`, `footer.webp` | |
| Separators | `sep-chain.webp` (animated), `sep-lace.webp`, `sep-sigil.webp` | |

Profile banner: a moonlit sunflower field with Rem holding a sunflower and 向日葵 in gold. Animated: wind through
the field, Rem's hair and ribbon, fireflies, falling petals, moon glow and a shooting star. Rem sits right of
centre and the lower-left stays calm, because AniList crops banners per screen and puts the avatar there.

"Living" Rem: `build/live.py` animates the still art without redrawing it. Colour masks find her hair (blue),
ribbon (pink) and the sunflowers, and smooth displacement fields sway them. The waving hand rotates around the
wrist, and a Codex-made closed-eye twin of each artwork is blended over the eyes for the blink.

Design notes: AniList shows the About column about **514 px** wide on desktop (measured), and images are capped to
that width. Everything is drawn at 1440 px for sharp high-DPI screens, with text sized to stay readable at 0.36×.
Each panel is a self-contained dark card, so it also works in AniList's light theme. Sections deliberately vary
in shape (rounded, chamfered, honeycomb, tilted cards), alignment and colour so the page isn't one uniform stack.

## Rebuild

Needs Python 3 with Pillow and numpy, and ffmpeg (VP9) on PATH. Fonts: Windows' Bahnschrift, Segoe UI and Noto JP.

```bash
cd build
python fetch_covers.py        # official cover art from the AniList API -> build/covers (git-ignored)
python panels.py              # static panels, separators, socials, footer
python animated.py            # hero, about me, waifu fan, tapes, milestones, chain separator
python visualizer.py loop     # profile/nowplaying.webm (needs ../music.mp3, which is git-ignored)
python visualizer.py full     # optional: export/rem-visualizer-full.mp4, 1080p with audio for YouTube
python extras.py              # banner (gif + jpg) + avatars
python make_about.py <commit-sha>
```

## Credits

- Character art, backgrounds, ornaments, the milestone crest and the genre emblems in `art/` were generated with
  OpenAI Codex image generation as fan art. Rem and Re:Zero belong to Tappei Nagatsuki / Kadokawa, Zero Two to
  Trigger / A-1 Pictures / CloverWorks, and Iroha Igarashi (3D Kanojo: Real Girl) to Mao Nanami / Kodansha.
- Cover art comes from AniList.
- Design spec: [`design/PLAN.md`](design/PLAN.md), written by Codex (the first version of the layout; the page has
  since moved to in-panel titles and more varied shapes).
- The song itself is not included in this repository.
