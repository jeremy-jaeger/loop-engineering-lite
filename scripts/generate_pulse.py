#!/usr/bin/env python3
"""Redraw docs/assets/pulse.svg from this repository's live GitHub stats.

Designed to run in GitHub Actions (GITHUB_TOKEN) or locally (unauthenticated
API, lower rate limit). Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
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


def _rng(seed: bytes):
    n = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big")

    def nxt() -> float:
        nonlocal n
        n = (1103515245 * n + 12345) & 0x7FFFFFFF
        return n / 0x7FFFFFFF

    return nxt


def render_svg(stats: dict, generated_at: str) -> str:
    stars = stats["stars"]
    forks = stats["forks"]
    watchers = stats["watchers"]
    issues = stats["open_issues"]
    people = stats["contributors"][:12]
    seed = f"{REPO}|{stars}|{forks}|{stats.get('last_sha')}|{generated_at[:10]}".encode()
    rnd = _rng(seed)

    w, h = 1100, 420
    dots = []
    n_dots = min(180, 24 + stars * 7 + forks * 5 + watchers * 3)
    for i in range(n_dots):
        ang = rnd() * math.tau
        rad = 40 + rnd() * 170
        cx = 320 + math.cos(ang) * rad * (0.7 + rnd() * 0.6)
        cy = 210 + math.sin(ang) * rad * (0.45 + rnd() * 0.4)
        r = 1.2 + rnd() * 3.2
        alpha = 0.25 + rnd() * 0.7
        hue = 160 + int(rnd() * 50) + (i % 7) * 3
        dots.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="hsla({hue},70%,65%,{alpha:.2f})" />'
        )

    rings = []
    for k in range(3 + min(6, forks)):
        rr = 50 + k * 22 + stars
        rings.append(
            f'<circle cx="320" cy="210" r="{rr}" fill="none" '
            f'stroke="rgba(20,184,166,{0.35 - k * 0.04:.2f})" '
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
        bh = 12 + (val / max_v) * 90
        x = 640 + i * 100
        bars.append(
            f'<rect x="{x}" y="{260 - bh:.1f}" width="54" height="{bh:.1f}" rx="8" fill="{color}" opacity="0.9"/>'
            f'<text x="{x + 27}" y="286" text-anchor="middle" fill="#e5e7eb" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" font-size="13" font-weight="700">{val}</text>'
            f'<text x="{x + 27}" y="306" text-anchor="middle" fill="#9ca3af" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" font-size="11">{label}</text>'
        )

    names = " · ".join(people)
    status = "live GitHub API" if stats.get("ok") else f"fallback ({escape(str(stats.get('error', 'n/a')))[:80]})"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Live repository pulse">
  <title>Loop Engineering Lite — live pulse</title>
  <desc>Generative graphic redrawn by CI from stars, forks, watchers, issues, and contributors.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#070b14"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="20" fill="url(#bg)"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="none" stroke="#1f2937"/>
  <text x="40" y="42" fill="#5eead4" font-family="ui-sans-serif,system-ui,sans-serif" font-size="12" letter-spacing="3">SELF-UPDATING / CI DRAWS THIS</text>
  <text x="40" y="74" fill="#f9fafb" font-family="ui-sans-serif,system-ui,sans-serif" font-size="26" font-weight="700">Repository pulse</text>
  <text x="40" y="100" fill="#9ca3af" font-family="ui-sans-serif,system-ui,sans-serif" font-size="13">{escape(REPO)} · {escape(generated_at)} · {escape(status)}</text>
  <g>{''.join(rings)}</g>
  <g>{''.join(dots)}</g>
  <circle cx="320" cy="210" r="18" fill="#14b8a6"/>
  <text x="320" y="215" text-anchor="middle" fill="#042f2e" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11" font-weight="700">VFS</text>
  {''.join(bars)}
  <text x="40" y="384" fill="#6b7280" font-family="ui-sans-serif,system-ui,sans-serif" font-size="12">contributors: {escape(names)}</text>
  <text x="40" y="404" fill="#4b5563" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11">seeded from stars/forks/SHA so the field mutates as the repo does · {escape(stats.get("last_sha") or "no-sha")}</text>
</svg>
'''


def render_md(stats: dict, generated_at: str) -> str:
    desc = stats.get("description") or "(no GitHub description set)"
    return f"""# Pulse

This page and `docs/assets/pulse.svg` are **rewritten by GitHub Actions**
(daily + manual dispatch) from the public GitHub API. The picture is generative:
star/fork/watcher counts change the particle field. No model, no designer.

Last draw: `{generated_at}` · source `{REPO}` · API `{'ok' if stats.get('ok') else 'fallback'}`

| Metric | Value |
| --- | ---: |
| Stars | {stats['stars']} |
| Forks | {stats['forks']} |
| Watchers | {stats['watchers']} |
| Open issues + PRs | {stats['open_issues']} |
| Contributors (sample) | {', '.join(stats['contributors'][:12])} |
| Tip SHA | `{stats.get('last_sha') or '—'}` |

GitHub description at draw time:

> {desc}

![pulse](assets/pulse.svg)
"""


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stats = fetch()
    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(render_svg(stats, now), encoding="utf-8")
    MD_PATH.write_text(render_md(stats, now), encoding="utf-8")
    print(f"Wrote {SVG_PATH.relative_to(ROOT)} and {MD_PATH.relative_to(ROOT)}")
    print(json.dumps({k: stats[k] for k in stats if k != "description"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
