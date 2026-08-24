#!/usr/bin/env python3
"""CI rewrites this repository's public face from its own GitHub stats.

Daily (and on demand) we:
1. Snapshot stars/forks/watchers/issues/contributors
2. Append one point per UTC day to docs/pulse-history.json
3. Redraw docs/assets/pulse.svg (particle field + star-growth sparkline)
4. Patch README.md between <!-- pulse:start --> and <!-- pulse:end -->

No third-party APIs and no LLM: GitHub runners have neither Ollama nor a
paid model key, and letting a model rewrite the README is a supply-chain
footgun. The narrator is deterministic on the same numbers.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

REPO = os.environ.get("GITHUB_REPOSITORY", "jeremy-jaeger/loop-engineering-lite")
API = f"https://api.github.com/repos/{REPO}"
ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "docs" / "assets" / "pulse.svg"
MD_PATH = ROOT / "docs" / "pulse.md"
HISTORY_PATH = ROOT / "docs" / "pulse-history.json"
README_PATH = ROOT / "README.md"
MARKER_START = "<!-- pulse:start -->"
MARKER_END = "<!-- pulse:end -->"
MAX_HISTORY = 365


def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "loop-engineering-lite-pulse",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url: str):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch() -> dict:
    try:
        repo = _get(API)
        contributors = _get(API + "/contributors?per_page=30")
        commits = _get(API + "/commits?per_page=1")
        last_sha = ""
        if isinstance(commits, list) and commits:
            last_sha = commits[0].get("sha", "")[:7]
        logins = [
            c.get("login", "?")
            for c in contributors
            if isinstance(c, dict) and c.get("type") != "Bot"
        ]
        return {
            "stars": int(repo.get("stargazers_count") or 0),
            "forks": int(repo.get("forks_count") or 0),
            "watchers": int(repo.get("subscribers_count") or 0),
            "open_issues": int(repo.get("open_issues_count") or 0),
            "created": repo.get("created_at") or "",
            "description": repo.get("description") or "",
            "contributors": logins or ["jeremy-jaeger"],
            "last_sha": last_sha,
            "ok": True,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return {
            "stars": 0,
            "forks": 0,
            "watchers": 0,
            "open_issues": 0,
            "created": "",
            "description": "",
            "contributors": ["offline"],
            "last_sha": "",
            "ok": False,
            "error": str(exc),
        }


def load_history(path: Path = HISTORY_PATH) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def append_history(history: list, stats: dict, day: str) -> list:
    """One sample per UTC day; later runs the same day overwrite the point."""
    point = {
        "date": day,
        "stars": int(stats.get("stars") or 0),
        "forks": int(stats.get("forks") or 0),
        "watchers": int(stats.get("watchers") or 0),
        "open_issues": int(stats.get("open_issues") or 0),
        "contributors": len(stats.get("contributors") or []),
    }
    if history and history[-1].get("date") == day:
        history = history[:-1] + [point]
    else:
        history = history + [point]
    return history[-MAX_HISTORY:]


def star_delta(history: list) -> int:
    if len(history) < 2:
        return 0
    return int(history[-1]["stars"]) - int(history[-2]["stars"])


def narrate(stats: dict, history: list, generated_at: str) -> str:
    """Deterministic README blurb from live metrics (not an LLM)."""
    stars = stats["stars"]
    forks = stats["forks"]
    delta = star_delta(history)
    people = stats.get("contributors") or []
    n_people = len(people)
    days = max(1, len(history))
    if delta > 0:
        growth = f"Star count moved **+{delta}** since the previous sample."
    elif delta < 0:
        growth = f"Star count moved **{delta}** since the previous sample."
    elif days <= 1:
        growth = "History just started — this is sample zero of the sparkline."
    else:
        growth = "Star count is unchanged since the previous sample."
    who = ", ".join(f"`{p}`" for p in people[:6]) or "`unknown`"
    return (
        f"CI last redrew this README **{generated_at}**. "
        f"Live totals: **{stars}** stars, **{forks}** forks, "
        f"**{stats['watchers']}** watchers, **{stats['open_issues']}** open issues/PRs, "
        f"**{n_people}** listed contributors ({who}). {growth} "
        f"The particle field and sparkline are generated from those numbers "
        f"([how](scripts/generate_pulse.py))."
    )


def html_blurb(stats: dict, history: list, generated_at: str) -> str:
    text = narrate(stats, history, generated_at)
    text = text.replace("**", "")
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[how\]\(([^)]+)\)", r'<a href="\1">how</a>', text)
    return text


def readme_block(stats: dict, history: list, generated_at: str) -> str:
    blurb = html_blurb(stats, history, generated_at)
    return (
        f"{MARKER_START}\n"
        f"<p align=\"center\">\n"
        f"  <a href=\"docs/pulse.md\"><img src=\"docs/assets/pulse.svg\" "
        f"alt=\"Live repository pulse redrawn by CI from GitHub stars, forks, and contributors\" width=\"920\"></a>\n"
        f"</p>\n\n"
        f"<p align=\"center\"><sub>{blurb}</sub></p>\n"
        f"{MARKER_END}"
    )


def patch_readme(readme: str, block: str) -> str:
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if not pattern.search(readme):
        raise ValueError("README.md is missing pulse markers")
    return pattern.sub(block, readme)


def sparkline_path(history: list, x: float, y: float, w: float, h: float) -> str:
    if not history:
        return ""
    ys = [int(p.get("stars") or 0) for p in history]
    lo, hi = min(ys), max(ys)
    span = max(1, hi - lo)
    n = len(ys)
    pts = []
    for i, val in enumerate(ys):
        px = x if n == 1 else x + (w * i / (n - 1))
        py = y + h - ((val - lo) / span) * h
        pts.append(f"{px:.1f},{py:.1f}")
    return " ".join(pts)


def _rng(seed: bytes):
    n = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big")

    def nxt() -> float:
        nonlocal n
        n = (1103515245 * n + 12345) & 0x7FFFFFFF
        return n / 0x7FFFFFFF

    return nxt


def render_svg(stats: dict, generated_at: str, history: list | None = None) -> str:
    history = history or []
    stars = stats["stars"]
    forks = stats["forks"]
    watchers = stats["watchers"]
    issues = stats["open_issues"]
    people = stats["contributors"][:12]
    seed = f"{REPO}|{stars}|{forks}|{stats.get('last_sha')}|{generated_at[:10]}".encode()
    rnd = _rng(seed)

    w, h = 1100, 480
    dots = []
    n_dots = min(180, 24 + stars * 7 + forks * 5 + watchers * 3)
    for i in range(n_dots):
        ang = rnd() * math.tau
        rad = 40 + rnd() * 170
        cx = 320 + math.cos(ang) * rad * (0.7 + rnd() * 0.6)
        cy = 200 + math.sin(ang) * rad * (0.45 + rnd() * 0.4)
        r = 1.2 + rnd() * 3.2
        alpha = 0.25 + rnd() * 0.7
        hue = 160 + int(rnd() * 50) + (i % 7) * 3
        dots.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="hsla({hue},70%,65%,{alpha:.2f})" />'
        )

    rings = []
    for k in range(3 + min(6, forks)):
        rr = 50 + k * 22 + min(stars, 80)
        rings.append(
            f'<circle cx="320" cy="200" r="{rr}" fill="none" '
            f'stroke="rgba(20,184,166,{max(0.08, 0.35 - k * 0.04):.2f})" '
            f'stroke-width="{1.2 + k * 0.15:.1f}" />'
        )

    bars = []
    metrics = [
        ("stars", stars, "#5eead4"),
        ("forks", forks, "#fbbf24"),
        ("watch", watchers, "#7dd3fc"),
        ("issues", issues, "#fda4af"),
    ]
    max_v = max(1, max(m[1] for m in metrics))
    for i, (label, val, color) in enumerate(metrics):
        bh = 12 + (val / max_v) * 70
        x = 640 + i * 100
        bars.append(
            f'<rect x="{x}" y="{210 - bh:.1f}" width="54" height="{bh:.1f}" rx="8" fill="{color}" opacity="0.9"/>'
            f'<text x="{x + 27}" y="236" text-anchor="middle" fill="#e5e7eb" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" font-size="13" font-weight="700">{val}</text>'
            f'<text x="{x + 27}" y="256" text-anchor="middle" fill="#9ca3af" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" font-size="11">{label}</text>'
        )

    sp = sparkline_path(history, 640, 300, 380, 70)
    spark = ""
    if sp:
        spark = (
            f'<text x="640" y="292" fill="#9ca3af" font-family="ui-sans-serif,system-ui,sans-serif" '
            f'font-size="11">star growth ({len(history)} daily samples)</text>'
            f'<rect x="632" y="298" width="396" height="86" rx="10" fill="#0b1220" stroke="#1f2937"/>'
            f'<polyline fill="none" stroke="#5eead4" stroke-width="2" points="{sp}"/>'
        )

    names = " · ".join(people)
    status = "live GitHub API" if stats.get("ok") else f"fallback ({escape(str(stats.get('error', 'n/a')))[:80]})"
    delta = star_delta(history)
    delta_s = f"{delta:+d} stars vs prior sample" if len(history) > 1 else "sparkline waiting for day 2"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Live repository pulse">
  <title>Loop Engineering Lite — live pulse</title>
  <desc>Generative graphic redrawn by CI from stars, forks, watchers, issues, contributors, and a stored daily history.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#070b14"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="20" fill="url(#bg)"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="none" stroke="#1f2937"/>
  <text x="40" y="42" fill="#5eead4" font-family="ui-sans-serif,system-ui,sans-serif" font-size="12" letter-spacing="3">SELF-UPDATING / CI WRITES THIS README</text>
  <text x="40" y="74" fill="#f9fafb" font-family="ui-sans-serif,system-ui,sans-serif" font-size="26" font-weight="700">Repository pulse</text>
  <text x="40" y="100" fill="#9ca3af" font-family="ui-sans-serif,system-ui,sans-serif" font-size="13">{escape(REPO)} · {escape(generated_at)} · {escape(status)}</text>
  <g>{''.join(rings)}</g>
  <g>{''.join(dots)}</g>
  <circle cx="320" cy="200" r="18" fill="#14b8a6"/>
  <text x="320" y="205" text-anchor="middle" fill="#042f2e" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11" font-weight="700">VFS</text>
  {''.join(bars)}
  {spark}
  <text x="40" y="430" fill="#6b7280" font-family="ui-sans-serif,system-ui,sans-serif" font-size="12">contributors: {escape(names)}</text>
  <text x="40" y="452" fill="#4b5563" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11">{escape(delta_s)} · tip {escape(stats.get("last_sha") or "no-sha")}</text>
</svg>
'''


def render_md(stats: dict, generated_at: str, history: list) -> str:
    desc = stats.get("description") or "(no GitHub description set)"
    rows = "\n".join(
        f"| {p['date']} | {p['stars']} | {p['forks']} | {p['watchers']} | {p['open_issues']} |"
        for p in history[-14:]
    )
    return f"""# Pulse

GitHub Actions **rewrites** `docs/assets/pulse.svg`, this page, `docs/pulse-history.json`,
and the marked section of `README.md` from the public GitHub API.

We do **not** call an LLM to invent marketing copy. The runner has no model,
and a model that can rewrite the README is a gift to prompt injection.

Last draw: `{generated_at}` · source `{REPO}` · API `{'ok' if stats.get('ok') else 'fallback'}`

{narrate(stats, history, generated_at)}

| Metric | Value |
| --- | ---: |
| Stars | {stats['stars']} |
| Forks | {stats['forks']} |
| Watchers | {stats['watchers']} |
| Open issues + PRs | {stats['open_issues']} |
| Contributors (sample) | {', '.join(stats['contributors'][:12])} |
| Tip SHA | `{stats.get('last_sha') or '—'}` |
| History samples | {len(history)} |

GitHub description at draw time:

> {desc}

## Recent samples

| Date (UTC) | Stars | Forks | Watch | Issues |
| --- | ---: | ---: | ---: | ---: |
{rows}

![pulse](assets/pulse.svg)
"""


def main() -> int:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    day = now.strftime("%Y-%m-%d")
    stats = fetch()
    history = append_history(load_history(), stats, day)

    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(render_svg(stats, stamp, history), encoding="utf-8")
    MD_PATH.write_text(render_md(stats, stamp, history), encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")

    if README_PATH.exists():
        block = readme_block(stats, history, stamp)
        README_PATH.write_text(patch_readme(README_PATH.read_text(encoding="utf-8"), block), encoding="utf-8")

    print(f"Wrote pulse artifacts ({len(history)} history points)")
    print(json.dumps({k: stats[k] for k in stats if k != "description"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
