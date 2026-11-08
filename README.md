# Makogai — AniList profile

Rem-themed (Re:Zero) About section, banner and avatar for [anilist.co/user/Makogai](https://anilist.co/user/Makogai),
in midnight blue and violet with mint, pink and gold accents. Assets are served from this repo through jsDelivr.

## Put it on AniList

1. **About:** copy all of [`about.md`](about.md) into *Settings → About*. The asset URLs are pinned to a commit, so
   jsDelivr never serves a stale cached file.
2. **Banner:** upload [`profile/banner.jpg`](profile/banner.jpg) (1700×330) in *Settings → Banner*. AniList only
   takes static banners.
3. **Avatar:** upload [`profile/avatar.png`](profile/avatar.png) (Rem, blue ring) or
   [`profile/avatar-sunflower.png`](profile/avatar-sunflower.png) (Rem with her sunflower, gold ring) in
   *Settings → Avatar*. Both are transparent PNGs.
4. **Sound (optional):** AniList's `webm()` always plays muted, so the visualizer is silent on the page. For sound,
   put the song's YouTube video id in `YOUTUBE_ID` in `build/make_about.py` and regenerate `about.md`. That adds a
   click-to-play `youtube()` embed under the visualizer.

Open [`preview.html`](preview.html) locally to see the page in a mock of AniList's About column before posting.
[`old-profile.txt`](old-profile.txt) keeps the previous About text for reference.

## Live stats

[`.github/workflows/refresh-stats.yml`](.github/workflows/refresh-stats.yml) runs daily (and on demand from the
Actions tab, with an optional *force* re-render). It runs [`build/refresh.py`](build/refresh.py), which fetches the
AniList stats into [`data/stats.json`](data/stats.json). When a number changed, it re-renders the three panels that
show them and commits:

- `stats.webp`: counts, episodes, days watched, chapters, mean scores, top genres, "updated" date
- `genres.webp`: the current top 5 anime genres with their counts and ranks. Genres without their own emblem get
  the crest in the genre's colour.
- `milestones.webp`: the five cards always end at the next tier to reach (tiers go up to Mythic 15,000 and
  Legend 20,000), with the progress trail at the real episode count

`about.md` serves those three from `main` on raw.githubusercontent.com (5-minute cache), so the profile updates
without re-pasting. Everything else stays pinned to a commit on jsDelivr. The Action commits to `main`, so run
`git pull` before working locally.

## What's in it

| Section | File(s) | Notes |
|---|---|---|
| Hero | `hero.webp` | Animated: Rem's hair and ribbon sway and she blinks; snow, moon glow, light sweep over the name |
| Marquee tapes | `tapes.webp` | Animated crossing tapes ("WELCOME · ようこそ", "REM · レム · BEST GIRL") |
| About me + favorite kanji 向日葵 | `intro.webp` | Animated: Rem waves, blinks, hair sways; sunflower (himawari) seal |
| Statistics | `stats.webp` | Chamfered "tech" card; live, refreshed daily from the AniList API |
| Top 3 anime | `top3.webp` | Re:Zero, Shield Hero, Code Geass, official AniList covers |
| Firsts & favorites | `firsts.webp` | Scattered polaroids with washi tape |
| Waifu collection | `waifu.webp` | Fanned SSR cards with a holographic shine: Zero Two, Rem, Iroha Igarashi |
| Now playing | `nowplaying.webm` | ~11 s seamless loop from the chorus, bars driven by the real song spectrum |
| Episode milestones | `milestones.webp` | Crest cards on a rising trail up to the next tier; live |
| Genre mastery | `genres.webp` | Honeycomb of the top 5 genres by titles watched, each with its own emblem; live |
| Socials + footer | `social-*.webp`, `footer.webp` | |
| Separators | `sep-chain.webp` (animated), `sep-lace.webp`, `sep-sigil.webp` | |

Profile banner: a moonlit sunflower field with Rem holding a sunflower, fireflies, petals and a shooting star.
"MAKOGAI" sits in the night sky between the moon and Rem, with a colour-split glow, light streak and a gold rule
over マコガイ, and 向日葵 is in gold on the right. Rem sits right of centre and the lower-left stays calm, because
AniList crops banners per screen and puts the avatar and username there.

"Living" Rem: `build/live.py` animates the still art without redrawing it. Colour masks find her hair (blue),
ribbon (pink) and the sunflowers, and smooth displacement fields sway them. The waving hand rotates around the
wrist, and a Codex-made closed-eye twin of each artwork is blended over the eyes for the blink.

Design notes: AniList shows the About column about **514 px** wide on desktop (measured), and images are capped to
that width. Everything is drawn at 1440 px for sharp high-DPI screens, with text sized to stay readable at 0.36×.
Each panel is a self-contained dark card, so it also works in AniList's light theme. Sections deliberately vary
in shape (rounded, chamfered, honeycomb, tilted cards), alignment and colour so the page isn't one uniform stack.

## Rebuild

Needs Python 3 with the packages in `build/requirements.txt`, and ffmpeg (VP9) on PATH for the visualizer. Fonts: Windows' Bahnschrift, Segoe UI and Noto JP (or the OFL Noto JP files in `build/fonts/`).

```bash
cd build
python fetch_covers.py        # official cover art from the AniList API -> build/covers (git-ignored)
python fetch_stats.py         # AniList numbers -> data/stats.json (refresh.py = this + re-render the live panels)
python panels.py              # static panels, separators, socials, footer
python animated.py            # hero, about me, waifu fan, tapes, milestones, chain separator
python visualizer.py loop     # profile/nowplaying.webm (needs ../music.mp3, which is git-ignored)
python visualizer.py full     # optional: export/rem-visualizer-full.mp4, 1080p with audio for YouTube
python extras.py              # banner + avatars
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
