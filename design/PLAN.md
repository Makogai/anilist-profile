# Makogai AniList Profile — Design Specification

## 1. Concept

**“Oni Moon: Rem’s Midnight Archive”** is a cinematic, neon-lit profile built as a sequence of self-contained dark cards. It replaces the old black-and-cyan collage style with deep indigo environments, layered glass panels, violet magic, icy blue highlights, and restrained pink accents inspired by Rem’s ribbon and oni horn. Maid-lace edges, chains, blue flowers, snow crystals, and a morning-star motif connect the sections without overwhelming the content. Every asset is authored at 1440 px wide and displayed at 720 px, giving typography and fine ornamentation crisp 2× rendering on both AniList themes.

## 2. Palette

| Name | Hex | Role |
|---|---:|---|
| Midnight Void | `#090B18` | Primary card background and deep vignette |
| Night Indigo | `#151A3D` | Raised panels, gradients, secondary backgrounds |
| Rem Blue | `#32B8F2` | Primary headings, borders, charts, key highlights |
| Ice Cyan | `#8EEBFF` | Crystal edges, particles, luminous text details |
| Arcane Violet | `#8257FF` | Secondary glow, gradients, manga statistics |
| Oni Magenta | `#F05AA6` | Ribbon crosses, horn glow, important accents |
| Lace White | `#F5F4FF` | Main text and maid-lace ornament |
| Moon Silver | `#AAB6D5` | Body text, dividers, inactive details |
| Black Satin | `#11131D` | Dress-inspired framing and text backplates |
| Aurora Lilac | `#C6A7FF` | Shiro accents and soft transition glow |

Use glows sparingly: Rem Blue at 35–55% opacity, Arcane Violet at 25–45%, and Oni Magenta at no more than 20% of any composition. All essential text must remain legible without relying on glow.

## 3. Typography

Use **Bahnschrift** throughout the Latin text for a cohesive technical-editorial look. The profile name uses Bahnschrift Bold, 112 px, slightly condensed if needed, with a blue-to-violet fill and a subtle 4 px cyan outer glow. Section titles use Bahnschrift SemiBold, 60–68 px, uppercase with 5 px tracking. Subtitles and card labels use Bahnschrift SemiCondensed SemiBold, 34–40 px. Body copy uses Segoe UI Regular, 34 px with 48 px line spacing; emphasized phrases use Segoe UI Bold in Ice Cyan.

Large rankings and statistics use Bahnschrift Condensed Bold, 104–132 px. Supporting numerical labels use Bahnschrift SemiCondensed, 30–36 px. Japanese accents use Noto Serif JP Bold: 72 px for decorative `レム` and 128 px for `愛`; small readings use Noto Sans JP Medium at 26–30 px. Keep all text at least 70 px from outer card edges and render Lace White body text over backgrounds no lighter than `#20284A`.

## 4. Page Order

1. **Hero identity banner**  
   Purpose: establish Makogai and the Rem theme immediately. Asset: WebM, 1440×460. A panoramic night-sky card shows Makogai’s name left of center, the line **“Male • Software Engineer”** beneath it, and `レム` vertically near the right edge. Rem occupies the right 42%, facing inward; a chain arcs behind the name toward a morning-star silhouette. The lower edge carries white maid-lace geometry and blue flowers. Snow particles drift diagonally, the chain catches traveling highlights, and an oni-horn glow softly breathes every 3 seconds. Use an 8-second seamless loop at 24 fps.

2. **Introduction and favourite kanji**  
   Purpose: introduce the user while preserving the most personal old content. Asset: PNG, 1440×900. Split the card 56/44: copy and kanji on the left, a waist-up Rem illustration on the right, extending slightly across the divider. Text: **“ABOUT MAKOGAI”**, then **“Hey there, you amazing person reading this! My name is Makogai, and I’m in love with anime. My dream is to visit Japan and buy all sorts of anime merch.”** Below, place `愛` inside a 220×220 silver-and-cyan seal with the reading `あい • ai`. Caption: **“My favourite kanji is 愛. It is read as ‘ai’, meaning ‘Love’. I like it because love drives us—and the kanji itself looks amazing.”** Static ice flecks and ribbon-X corners create energy without animation.

3. **Live statistics dashboard**  
   Purpose: make viewing activity feel substantial and current. Asset: PNG, 1440×650. Header: **“ANILIST ARCHIVE / LIVE STATISTICS”**. Divide the card into two 620×380 glass panels: Anime in blue and Manga in violet. Anime shows **457 ANIME**, **9,607 EPISODES**, **228,749 MINUTES**, **≈158.9 DAYS**, and **84.7 MEAN SCORE**. Manga shows **359 MANGA**, **23,094 CHAPTERS**, and **93.8 MEAN SCORE**. Use large numbers, slim progress arcs, tick marks, and faint radar rings; do not imply percentage completion. A central flail chain separates the panels.

4. **Top three anime podium**  
   Purpose: present the fixed ranking as the page’s main showcase. Asset: PNG, 1440×980. Title: **“TOP 3 ANIME / 三選”**. Place #1 Re:Zero in a raised 480×650 center frame, with #2 The Rising of the Shield Hero in a 390×570 frame left and #3 Code Geass in a matching frame right. Each frame contains art, a huge translucent rank numeral, English title, and a 26 px Japanese/romanized micro-label where appropriate. The center frame receives an oni-magenta crown glow; #2 uses shield-like ice corners, while #3 uses angular violet chess motifs. Maintain consistent bottom alignment.

5. **Firsts & favourites**  
   Purpose: preserve the four legacy milestones in a cleaner editorial grid. Asset: PNG, 1440×720. Header: **“ORIGIN POINTS & FAVOURITES”**. Use four equal 300×450 poster cells with 28 px gaps. Labels and values are: **FIRST ANIME — FMA: Brotherhood**, **FIRST MANGA — Redo of Healer**, **FAVOURITE ANIME — Re:Zero**, and **FAVOURITE MANGA — Solo Leveling**. Each cell has a dark gradient caption plate, one oversized two-letter marker such as `01` or `FAV`, and a thin blue-to-violet top rule.

6. **Waifu collection**  
   Purpose: add a new collectible-card centerpiece. Assets: three PNGs, each 460×680, displayed on one line at approximately 230 px wide each. A separate static header PNG, 1440×170, reads **“WAIFU ARCHIVE / CHARACTER FILES”** and shows a chain threaded through three glowing diamond sockets. Cards appear in this order: **Rem**, **Zero Two**, **Shiro**. Their shared construction is specified below.

7. **Music visualizer**  
   Purpose: turn the favourite song into the page’s primary animated spectacle. Asset: WebM, 1440×620, followed directly by the YouTube embed supplying real sound. Header inside the video: **“NOW PLAYING / FAVOURITE SONG”**; include the exact song title and artist supplied by the audio metadata or project brief, never invent them. The muted animation is a seamless 12-second loop at 24 fps. Visual details are specified in Section 7.

8. **Episodes watched achievements**  
   Purpose: frame the retained third-party achievement cards as part of the redesign. Asset: PNG header, 1440×180, followed by the existing 120 px-wide external cards in centered rows of 4–7. Header text: **“EPISODE MILESTONES / 視聴記録”**. Use seven empty chain links along the lower edge so the varied card rows feel intentionally attached to the header. No animation.

9. **Genre mastery**  
   Purpose: showcase the retained genre-mastery cards. Asset: PNG header, 1440×180, followed by existing third-party cards in centered rows of 4–7. Header text: **“GENRE MASTERY / 属性記録”**. Use a constellation map of small genre-node symbols, blue on the left and violet on the right. No labels inside the constellation beyond the heading.

10. **Social links footer**  
    Purpose: provide a strong visual close and three clear link targets. Asset: PNG, 1440×250. Three equal linked plates read **STEAM**, **YOUTUBE**, and **DISCORD**, with simple monochrome platform icons inside cyan-violet hexagons. Centered above them: **“FIND ME BEYOND THE ARCHIVE”**. A morning-star rests at the bottom center, its chain becoming the footer rule. Keep links visually distinct even if AniList adds no hover state.

## 5. Separator System

1. **Chain Pulse** — WebM, 1440×72, 4-second loop. A fine silver chain spans the width; a cyan light travels left-to-right and becomes violet after crossing a pink ribbon-X. Use after the hero, statistics, and music visualizer.

2. **Frozen Lace** — PNG, 1440×64. White maid-headdress lace fades into symmetrical ice crystals, with a small blue flower at center. Use between the introduction and statistics, and between Top 3 and Firsts & Favourites.

3. **Oni Eclipse** — WebM, 1440×92, 6-second loop. A central crescent/horn symbol brightens from violet to magenta while eight snowflake particles orbit once and dissolve. Use before Top 3 and before the Waifu Archive.

4. **Archive Sigil** — PNG, 1440×58. Thin blueprint lines, diamond nodes, and a centered `愛` seal at low opacity. Use between Waifu Archive and music, between the two achievement sections, and above the social footer.

Animated separators should use transparency only if WebM alpha remains efficient; otherwise place them on Midnight Void so their edges disappear against adjacent cards.

## 6. Waifu Card Template

Each card is **460×680 px**, with a 12 px outer gradient frame, 6 px Black Satin inset, and 3 px Ice Cyan keyline. The portrait occupies x=24–436 and y=24–500. A dark indigo gradient rises over the bottom 150 px of the portrait for legibility. Place the franchise in a vertical rail at x=402–436, y=52–300, using 22 px condensed capitals. Place the character name at x=34, y=505: 50 px given name above a 76 px surname or signature line where applicable. A 56×56 diamond emblem sits at x=34, y=602; three decorative stat ticks sit at x=108–330, y=628.

Rem uses blue flowers, a lace emblem, cyan ice shards, and one small pink ribbon-X. Zero Two uses restrained coral `#FF5B79`, paired horn shapes, and a faint red cockpit-grid accent. Shiro uses Aurora Lilac, a tiny gold crown, chessboard diamonds, and a narrow rainbow-prismatic edge limited to the frame’s upper right. Character art may break over the inner portrait border but never over the outer card boundary.

## 7. Music Visualizer

Use a dark moonlit Rem portrait centered at x=720, y=305, cropped to a 270 px circular medallion. Surround it with a 420 px-diameter circular spectrum of 96 bars: cyan on the left, violet on the right, with occasional magenta peak bars. Add mirrored horizontal waveforms across the lower third, stopping 80 px before each edge. Behind them, slow parallax snow, blue flower petals, and translucent ice prisms move at three depths. Spectrum movement must be derived from the supplied audio, then eased so it remains readable rather than frantic.

Select a musically recognizable 12-second segment containing a stable beat, melodic hook, and no abrupt cut—prefer the first complete chorus phrase. Cut on matching downbeats and crossfade the final 12 frames into the opening 12 frames. The portrait’s horn glow should peak only on the strongest two or three beats per cycle. Keep title and artist in a fixed 480×88 glass label at the upper left so motion never compromises text.

## 8. Generated Art List

1. **Hero Rem panorama** — 16:5. Rem on the right, moonlit hair, inward gaze, open night-sky space on left; avoid text, logos, chains, cropped hands, and excessive bloom.
2. **Intro Rem cutout** — 4:5. Waist-up maid pose facing left, clean silhouette, soft blue rim light; avoid background text and cut-off headdress.
3. **Re:Zero ensemble** — 3:4. Dynamic central composition with Subaru and key cast, Rem visually prominent; avoid typography and poster logos.
4. **Shield Hero ensemble** — 3:4. Naofumi foreground with shield, Raphtalia and Filo behind; avoid title marks and tiny faces.
5. **Code Geass ensemble** — 3:4. Lelouch foreground with C.C. and mecha silhouettes; avoid title text and overly busy lower edge.
6. **Milestone four-way montage** — 16:7. Four independently crop-safe vertical zones representing the specified titles; avoid embedded labels and blending characters across zone boundaries.
7. **Rem card portrait** — 2:3. Gentle frontal maid portrait with flowers and lace; avoid text and oversized hands.
8. **Zero Two card portrait** — 2:3. Confident three-quarter pose with horns and restrained red lighting; avoid logos and explicit imagery.
9. **Shiro card portrait** — 2:3. Calm seated pose with crown and chess pieces, lilac atmosphere; avoid text, distorted chessboards, and saturated rainbow backgrounds.

## 9. Performance Budget

| File or group | Format | Target size |
|---|---:|---:|
| Hero identity banner | WebM | 1.65 MB |
| Introduction panel | PNG | 0.85 MB |
| Statistics dashboard | PNG | 0.45 MB |
| Top three anime | PNG | 1.20 MB |
| Firsts & favourites | PNG | 0.90 MB |
| Waifu header | PNG | 0.12 MB |
| Three waifu cards | PNG | 1.35 MB total |
| Music visualizer | WebM | 2.35 MB |
| Two animated separator files | WebM | 0.55 MB total |
| Static separators | PNG | 0.16 MB total |
| Achievement and genre headers | PNG | 0.24 MB total |
| Social footer | PNG | 0.18 MB |
| **Designed asset total** |  | **10.00 MB** |

Third-party achievement and genre cards should be recompressed only if permitted, targeting no more than 1.5 MB collectively. Encode WebM with no audio track, 24 fps, and restrained particle density. Keep every individual file below 2.5 MB, leaving safety margin beneath AniList’s 3 MB limit and the overall 12 MB goal.
