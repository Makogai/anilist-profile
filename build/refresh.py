"""Daily refresh, run by .github/workflows/refresh-stats.yml (also works locally).

Fetches the AniList stats; when a number changed (or with --force) it re-renders the three panels that
show them: stats.webp, genres.webp and milestones.webp. about.md serves every asset from GitHub Pages
(main), so AniList shows the new versions without re-pasting the About text.
"""
import subprocess
import sys

import animated
import fetch_stats
import panels
from common import ROOT, STATS


def stats_changed() -> bool:
    diff = subprocess.run(["git", "status", "--porcelain", "--", str(STATS)], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout
    return bool(diff.strip())


def main():
    fetch_stats.main()
    if not (stats_changed() or "--force" in sys.argv):
        print("nothing to render")
        return
    panels.stats()
    panels.genres()
    animated.milestones()


if __name__ == "__main__":
    main()
