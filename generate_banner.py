#!/usr/bin/env python3
"""
  python3 generate_banner.py                        # generates banner-dark.svg + banner-light.svg
  python3 generate_banner.py --theme dark           # dark only  → banner-dark.svg
  python3 generate_banner.py --theme light          # light only → banner-light.svg
  python3 generate_banner.py --mode random          # random project pick
  python3 generate_banner.py --mode chronological   # latest pushed repo first
"""

import random
import datetime
import argparse
import colorsys
import json
import os
import re
import subprocess
import urllib.request
from html import unescape
from pathlib import Path


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

GITHUB_USERNAME = "aundreka"  
PROFILE_VISITOR_PAGE_ID = f"{GITHUB_USERNAME}.{GITHUB_USERNAME}"
DISPLAY_TIMEZONE = datetime.timezone(datetime.timedelta(hours=8), name="Asia/Manila")
SVG_WIDTH = 680
SVG_HEIGHT = 340
TYPING_DURATION_SECONDS = 8
TYPING_PAUSE_SECONDS = 30
DEFAULT_DESCRIPTION_LINES = 2
RECOMMENDATION_DESCRIPTION_LINES = 4
RECOMMENDATION_DESCRIPTION_FETCH_LIMIT = 110
TOPIC_LABELS = {
    "game": "GAME",
    "games": "GAME",
    "ai": "AI",
    "ml": "AI",
    "web": "WEB",
    "website": "WEB",
    "mobile": "MOBILE",
    "android": "MOBILE",
    "app": "APP",
    "apps": "APP",
    "application": "APP",
    "edtech": "EDTECH",
    "education": "EDTECH",
    "fintech": "FINTECH",
    "finance": "FINTECH",
    "trading": "FINTECH",
    "marketing": "MARKETING",
    "python": "PYTHON",
    "horror": "HORROR",
    "vn": "VN",
    "visual-novel": "VN",
}
LABEL_INFERENCE_RULES = [
    ("GAME", ["game", "games", "rpg", "tower defense", "survival", "combat", "visual novel"]),
    ("AI", ["ai", "ml", "llm", "model", "models", "prediction", "predictive", "sentiment", "recommendation"]),
    ("WEB", ["web", "website", "dashboard", "site", "browser"]),
    ("MOBILE", ["mobile", "android", "ios", "flutter", "expo", "react native"]),
    ("APP", ["app", "application", "platform", "system", "tool"]),
    ("EDTECH", ["edtech", "education", "learning", "learn", "study", "quiz", "lesson", "academic", "school"]),
    ("FINTECH", ["fintech", "finance", "trading", "bitcoin", "crypto", "analytics", "backtesting"]),
    ("MARKETING", ["marketing", "creator", "creators", "sme", "smes", "content", "campaign"]),
    ("PYTHON", ["python"]),
    ("HORROR", ["horror", "curse", "survival horror"]),
    ("VN", ["visual novel", "vn", "branching story"]),
]


FALLBACK_PROJECTS = [
    {
        "name": "Academon",
        "labels": ["GAME", "AI", "APP"],
        "stars": 42,
        "description": "Gacha-powered learning RPG with PvP & PvE quiz combat",
        "url": f"https://github.com/{GITHUB_USERNAME}/academon",
        "weight": 5,
        "rarity": "legendary",
        "pushed_at": "2026-04-30",
    },
    {
        "name": "SchEDU Teach",
        "labels": ["APP", "AI", "EDTECH"],
        "stars": 36,
        "description": "AI academic planning system for lessons, quizzes, and schedules",
        "url": f"https://github.com/{GITHUB_USERNAME}/schedu-teach",
        "weight": 5,
        "rarity": "legendary",
        "pushed_at": "2026-03-26",
    },
    {
        "name": "Fishbowl Trading Analytics",
        "labels": ["WEB", "AI", "FINTECH"],
        "stars": 30,
        "description": "Trading strategy simulator and analytics dashboard",
        "url": f"https://github.com/{GITHUB_USERNAME}/fishbowl-trading-analytics",
        "weight": 4,
        "rarity": "rare",
        "pushed_at": "2026-04-15",
    },
    {
        "name": "PRISM",
        "labels": ["APP", "AI", "MARKETING"],
        "stars": 28,
        "description": "AI scheduling and recommendation tool for SMEs and creators",
        "url": f"https://github.com/{GITHUB_USERNAME}/prism",
        "weight": 4,
        "rarity": "rare",
        "pushed_at": "2025-10-15",
    },
    {
        "name": "Universentiment",
        "labels": ["AI", "WEB"],
        "stars": 24,
        "description": "Sentiment-analysis chatbot for Philippine university reviews",
        "url": f"https://github.com/{GITHUB_USERNAME}/universentiment",
        "weight": 4,
        "rarity": "rare",
        "pushed_at": "2026-02-21",
    },
    {
        "name": "SchEDU Learn",
        "labels": ["APP", "AI", "EDTECH"],
        "stars": 21,
        "description": "Adaptive study planner that turns deadlines into study schedules",
        "url": f"https://github.com/{GITHUB_USERNAME}/schedu-learn",
        "weight": 3,
        "rarity": "rare",
        "pushed_at": "2026-04-08",
    },
    {
        "name": "CS301 Tower Defense",
        "labels": ["GAME", "WEB"],
        "stars": 18,
        "description": "Flutter tower defense game with strategic waves and playable units",
        "url": f"https://github.com/{GITHUB_USERNAME}/cs301td-flutter",
        "weight": 3,
        "rarity": "uncommon",
        "pushed_at": "2025-12-01",
    },
    {
        "name": "Grimm Runner",
        "labels": ["GAME", "WEB"],
        "stars": 16,
        "description": "Survival game with movement, combat, and expanding maps",
        "url": f"https://github.com/{GITHUB_USERNAME}/appdev-finalproj",
        "weight": 3,
        "rarity": "uncommon",
        "pushed_at": "2025-11-19",
    },
    {
        "name": "BitMind",
        "labels": ["AI", "PYTHON", "FINTECH"],
        "stars": 14,
        "description": "Bitcoin auto-trading system with predictive modeling and backtesting",
        "url": f"https://github.com/{GITHUB_USERNAME}/bitmind",
        "weight": 2,
        "rarity": "uncommon",
        "pushed_at": "2025-03-09",
    },
    {
        "name": "TreeQuest",
        "labels": ["GAME", "WEB", "EDTECH"],
        "stars": 12,
        "description": "Educational game for learning tree traversal algorithms",
        "url": f"https://github.com/{GITHUB_USERNAME}/treequest",
        "weight": 2,
        "rarity": "uncommon",
        "pushed_at": "2024-08-06",
    },
    {
    "name": "Ju-On: Cursebreaker",
    "labels": ["GAME", "HORROR", "VN"],
    "stars": 15,
    "description": "Horror visual novel inspired by JU-ON with branching story and survival elements",
    "url": f"https://github.com/{GITHUB_USERNAME}/ju-on-cursebreaker",
    "weight": 3,
    "rarity": "rare",
    "pushed_at": "2025-07-14",
},
]

PET_FACES = {
    "happy":    [" /\\_/\\ ", "=( ^.^ )=", "  > ~ <  "],
    "sleepy":   [" /\\_/\\ ", "=( -.- )=", "  > z <  "],
    "excited":  [" /\\_/\\ ", "=( !! ) =", "  > ^ <  "],
    "evil":     [" /\\_/\\ ", "=( >.< )=", "  > * <  "],
    "focused":  [" /\\_/\\ ", "=( o.o )=", "  > ~ <  "],
    "confused": [" /\\_/\\ ", "=( ?_? )=", "  > . <  "],
}

PET_MESSAGES = {
    "happy":    [""],
    "sleepy":   ["zzz...",],
    "excited":  [""],
    "evil":     [""],
    "focused":  ["locked in rn."],
    "confused": ["git blame says... me."],
}

# 2 rotating terminal commands that appear ABOVE the guaranteed project line.
# The third slot is always "currently working on" → most recently pushed project.
ROTATING_COMMANDS = [
    ("reach me at",           "c.aundrekaperez@gmail.com"),
    ("run deploy.sh",        "deploying..."),
    ("git diff HEAD",        "3 files changed"),
    ("npm run build",        "compiled successfully"),
]

STATUSES  = ["coding", "debugging", "building", "deploying", "experimenting", "in grindset"]
DEV_MODES = ["grindset", "experimenting", "shipping", "debugging", "building", "vibing"]

LABEL_COLORS_DARK = {
    "GAME":   ("#3B6D11", "#7ee787"),
    "AI":     ("#854F0B", "#ffa657"),
    "WEB":    ("#0C447C", "#58a6ff"),
    "MOBILE": ("#3C3489", "#a855f7"),
    "APP":    ("#6B4F2A", "#f6d365"),
    "EDTECH": ("#0F766E", "#99f6e4"),
    "FINTECH": ("#14532D", "#86efac"),
    "MARKETING": ("#831843", "#f9a8d4"),
    "PYTHON": ("#1E3A8A", "#93c5fd"),
    "HORROR": ("#4C1D95", "#c4b5fd"),
    "VN": ("#9D174D", "#fbcfe8"),
}
LABEL_COLORS_LIGHT = {
    "GAME":   ("#dcfce7", "#3B6D11"),
    "AI":     ("#fef3c7", "#854F0B"),
    "WEB":    ("#dbeafe", "#185FA5"),
    "MOBILE": ("#ede9fe", "#534AB7"),
    "APP":    ("#fef3c7", "#92400e"),
    "EDTECH": ("#ccfbf1", "#0f766e"),
    "FINTECH": ("#dcfce7", "#166534"),
    "MARKETING": ("#fce7f3", "#9d174d"),
    "PYTHON": ("#dbeafe", "#1d4ed8"),
    "HORROR": ("#ede9fe", "#6d28d9"),
    "VN": ("#fce7f3", "#be185d"),
}
DEFAULT_DARK  = ("#444441", "#B4B2A9")
DEFAULT_LIGHT = ("#F1EFE8", "#5F5E5A")


# ─────────────────────────────────────────────
#  TIME & MOOD
# ─────────────────────────────────────────────

def get_time_context(now: datetime.datetime) -> dict:
    hour     = now.hour
    weekday  = now.weekday()
    is_wkend = weekday >= 5

    if hour < 6:
        period, greeting = "night",     "late night grind detected."
    elif hour < 12:
        period, greeting = "morning",   "good morning, dev."
    elif hour < 18:
        period, greeting = "afternoon", "good afternoon, dev."
    elif hour < 21:
        period, greeting = "evening",   "good evening, dev."
    else:
        period, greeting = "night",     "burning the midnight oil."

    if weekday == 4 and hour >= 17:
        event = "friday_chill"
    elif is_wkend:
        event = "weekend_chaos"
    else:
        event = None

    return {"period": period, "greeting": greeting, "event": event}


def pick_mood(time_ctx: dict, seed: int) -> str:
    rng = random.Random(seed)
    ev  = time_ctx["event"]
    p   = time_ctx["period"]
    if ev == "friday_chill":   return rng.choice(["happy", "sleepy"])
    if ev == "weekend_chaos":  return rng.choice(["excited", "evil", "confused"])
    if p  == "night":          return rng.choice(["sleepy", "focused", "evil"])
    if p  == "morning":        return rng.choice(["happy", "focused"])
    return rng.choice(list(PET_FACES.keys()))


# ─────────────────────────────────────────────
#  PROJECT ENGINE
# ─────────────────────────────────────────────

def fetch_github_projects(username: str) -> list:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "aundreka-banner",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            repos = json.loads(resp.read())
        projects = []
        for r in repos:
            if r.get("fork"):
                continue
            topics = [str(topic).lower() for topic in r.get("topics", [])]
            if not topics:
                topics = fetch_github_topics(username, r["name"])
            labels = normalize_topics(topics)
            projects.append({
                "name":        r["name"],
                "labels":      labels,
                "stars":       r.get("stargazers_count", 0),
                "description": truncate_text(
                    r.get("description") or "",
                    RECOMMENDATION_DESCRIPTION_FETCH_LIMIT,
                ),
                "url":         r.get("html_url", ""),
                "weight":      max(1, r.get("stargazers_count", 0)),
                "rarity":      "common",
                "pushed_at":   (r.get("pushed_at") or "")[:10],
            })
        return projects or FALLBACK_PROJECTS
    except Exception as e:
        print(f"  [github] fetch failed: {e} — using fallback projects")
        return FALLBACK_PROJECTS


def fetch_github_topics(username: str, repo_name: str) -> list[str]:
    url = f"https://api.github.com/repos/{username}/{repo_name}/topics"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "aundreka-banner",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read())
        return [str(topic).lower() for topic in payload.get("names", [])]
    except Exception:
        return []


def normalize_topics(topics: list[str], max_labels: int = 3) -> list[str]:
    labels = []
    for topic in topics:
        cleaned = str(topic).strip().upper()
        if not cleaned or cleaned in labels:
            continue
        labels.append(cleaned)
        if len(labels) >= max_labels:
            break
    return labels


def topic_labels(
    topics: list[str],
    max_labels: int = 3,
    name: str = "",
    description: str = "",
    language: str = "",
) -> list[str]:
    labels = []
    for topic in topics:
        label = TOPIC_LABELS.get(topic)
        if not label or label in labels:
            continue
        labels.append(label)
        if len(labels) >= max_labels:
            break

    haystack = " ".join([name, description, language]).lower()
    for label, keywords in LABEL_INFERENCE_RULES:
        if label in labels:
            continue
        if any(keyword in haystack for keyword in keywords):
            labels.append(label)
        if len(labels) >= max_labels:
            break

    return labels


def fetch_github_visits(username: str) -> str:
    """
    Read the profile view count from a public badge counter.
    If the fetch fails, fall back to the last rendered banner count.
    """
    url = (
        "https://visitor-badge.laobi.icu/badge"
        f"?page_id={PROFILE_VISITOR_PAGE_ID}"
        "&left_color=gray&right_color=blue&left_text=Profile%20visitors"
        f"&_ts={int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "aundreka-banner"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            svg = resp.read().decode("utf-8", errors="replace")
        visit_count = parse_visit_count(svg)
        if visit_count:
            return visit_count
    except Exception as e:
        print(f"  [visits]  live badge fetch failed: {e} - trying cached banner value")

    cached = read_cached_visit_count()
    if cached == "0":
        return "—"
    return cached or "—"


def parse_visit_count(svg_text: str) -> str | None:
    text_matches = re.findall(r">([^<]+)<", svg_text)
    number_pattern = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?[KMBT]?)", re.IGNORECASE)

    for text in text_matches:
        if "views" not in text.lower():
            continue
        match = number_pattern.search(text)
        if match:
            return match.group(1)

    for text in text_matches:
        stripped = text.strip()
        match = number_pattern.fullmatch(stripped)
        if match:
            return match.group(1)
    return None


def read_cached_visit_count() -> str | None:
    pattern = re.compile(r"profile visits:\s*([0-9][0-9,]*)", re.IGNORECASE)
    for filename in ("banner-dark.svg", "banner-light.svg"):
        path = Path(filename)
        if not path.exists():
            continue
        match = pattern.search(path.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return match.group(1)
    return None


def github_api_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": "aundreka-banner",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def compute_streak_from_dates(active_dates: set[datetime.date], today: datetime.date) -> int:
    if not active_dates:
        return 0

    if today in active_dates:
        current = today
    elif today - datetime.timedelta(days=1) in active_dates:
        current = today - datetime.timedelta(days=1)
    else:
        return 0

    streak = 0
    while current in active_dates:
        streak += 1
        current -= datetime.timedelta(days=1)
    return streak


def fetch_github_contribution_streak(username: str, now: datetime.datetime, token: str) -> int | None:
    since = (now.date() - datetime.timedelta(days=365)).isoformat()
    until = now.date().isoformat()
    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps(
        {
            "query": query,
            "variables": {
                "username": username,
                "from": f"{since}T00:00:00Z",
                "to": f"{until}T23:59:59Z",
            },
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=payload,
            headers={**github_api_headers(token), "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
    except Exception as e:
        print(f"  [streak]  GitHub contributions fetch failed: {e} - trying public events")
        return None

    if body.get("errors"):
        print("  [streak]  GitHub contributions returned errors - trying public events")
        return None

    user = (body.get("data") or {}).get("user") or {}
    collection = user.get("contributionsCollection") or {}
    weeks = ((collection.get("contributionCalendar") or {}).get("weeks") or [])
    active_dates = set()
    for week in weeks:
        for day in week.get("contributionDays", []):
            if (day.get("contributionCount") or 0) > 0:
                try:
                    active_dates.add(datetime.date.fromisoformat(day["date"]))
                except Exception:
                    continue

    return compute_streak_from_dates(active_dates, now.date())


def fetch_github_public_events_streak(username: str, now: datetime.datetime) -> int | None:
    active_dates = set()
    for page in range(1, 4):
        url = f"https://api.github.com/users/{username}/events/public?per_page=100&page={page}"
        try:
            req = urllib.request.Request(url, headers=github_api_headers())
            with urllib.request.urlopen(req, timeout=10) as resp:
                events = json.loads(resp.read())
        except Exception as e:
            print(f"  [streak]  GitHub public events fetch failed: {e} - trying local git")
            return None

        if not events:
            break

        for event in events:
            created_at = event.get("created_at")
            if not created_at:
                continue
            try:
                dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                active_dates.add(dt.astimezone(DISPLAY_TIMEZONE).date())
            except ValueError:
                continue

    return compute_streak_from_dates(active_dates, now.date())


def fetch_real_activity_streak(now: datetime.datetime, username: str = GITHUB_USERNAME) -> int:
    token = os.getenv("GITHUB_TOKEN")
    if token:
        streak = fetch_github_contribution_streak(username, now, token)
        if streak is not None:
            return streak

    streak = fetch_github_public_events_streak(username, now)
    if streak is not None:
        return streak

    return fetch_git_streak(now)


def fetch_git_streak(now: datetime.datetime) -> int:
    """
    Compute the current commit streak from local git history.
    A streak is considered active if the latest commit was today or yesterday.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--date=short", "--pretty=format:%ad"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        print(f"  [streak]  git history unavailable: {e} — using fallback")
        return 1

    unique_dates = []
    seen = set()
    for line in result.stdout.splitlines():
        date_str = line.strip()
        if not date_str or date_str in seen:
            continue
        seen.add(date_str)
        try:
            unique_dates.append(datetime.date.fromisoformat(date_str))
        except ValueError:
            continue

    if not unique_dates:
        return 1

    today = now.date()
    latest = unique_dates[0]
    if latest < today - datetime.timedelta(days=1):
        return 0

    streak = 1
    previous = latest
    for current in unique_dates[1:]:
        if previous - current == datetime.timedelta(days=1):
            streak += 1
            previous = current
            continue
        break
    return streak


def pick_project(projects: list, mode: str, seed: int, exclude_name: str | None = None) -> dict:
    if not projects:
        return FALLBACK_PROJECTS[0]

    candidates = [p for p in projects if p.get("name") != exclude_name]
    if not candidates:
        candidates = projects

    if mode == "chronological":
        return sorted(candidates, key=lambda p: p.get("pushed_at", ""), reverse=True)[0]
    if mode == "weighted":
        rng = random.Random(seed)
        return rng.choices(candidates, weights=[max(1, p.get("weight", 1)) for p in candidates], k=1)[0]
    return random.Random(seed).choice(candidates)


def pick_commands(seed: int) -> list:
    """Pick 2 rotating commands. The project recommendation is always appended as a 3rd line."""
    rng  = random.Random(seed + 3)
    pool = list(ROTATING_COMMANDS)
    rng.shuffle(pool)
    return pool[:2]


def get_current_project(projects: list) -> dict:
    """Return the most recently pushed project — what you're actively working on."""
    if not projects:
        return FALLBACK_PROJECTS[0]
    return sorted(projects, key=lambda p: p.get("pushed_at", ""), reverse=True)[0]


# ─────────────────────────────────────────────
#  SVG HELPERS
# ─────────────────────────────────────────────

def esc(s: str) -> str:
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def t(x, y, text, fill, size=12, anchor="start", weight="normal"):
    return (f'<text font-family="monospace" font-size="{size}" font-weight="{weight}" '
            f'x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" xml:space="preserve">{esc(text)}</text>')

def hline(x1, y, x2, stroke, sw=0.5):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{stroke}" stroke-width="{sw}"/>'

def vline(x, y1, y2, stroke, sw=0.75):
    return f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'

def box(x, y, w, h, rx, fill, stroke=None, sw=0.75, op=1.0):
    s  = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    o  = f' opacity="{op}"' if op != 1.0 else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{s}{o}/>'

def dot(cx, cy, r, fill, op=1.0):
    o = f' opacity="{op}"' if op != 1.0 else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{o}/>'

def topic_pastel_colors(label: str, dark_mode: bool) -> tuple[str, str]:
    seed = sum((index + 1) * ord(ch) for index, ch in enumerate(label))
    hue = (seed % 360) / 360.0
    if dark_mode:
        bg_rgb = colorsys.hls_to_rgb(hue, 0.26, 0.55)
        fg_rgb = colorsys.hls_to_rgb(hue, 0.78, 0.75)
    else:
        bg_rgb = colorsys.hls_to_rgb(hue, 0.88, 0.65)
        fg_rgb = colorsys.hls_to_rgb(hue, 0.34, 0.65)

    def to_hex(rgb: tuple[float, float, float]) -> str:
        return "#" + "".join(f"{round(channel * 255):02x}" for channel in rgb)

    return to_hex(bg_rgb), to_hex(fg_rgb)


def label_width(label: str) -> int:
    return len(label) * 7 + 12


def fit_labels(labels: list[str], start_x: int, max_x: int, gap: int = 5) -> list[str]:
    fitted = list(labels)
    while fitted:
        total_width = sum(label_width(label) for label in fitted) + gap * (len(fitted) - 1)
        if start_x + total_width <= max_x:
            return fitted
        longest = max(fitted, key=lambda label: (len(label), label))
        fitted.remove(longest)
    return fitted


def label_tags(x, y, labels, dark_mode):
    parts = []
    cx = x
    for lbl in labels:
        bg, fg = topic_pastel_colors(lbl, dark_mode)
        w = label_width(lbl)
        op = 0.3 if dark_mode else 0.9
        parts.append(
            f'<rect x="{cx}" y="{y - 8}" width="{w}" height="17" rx="3" fill="{bg}" '
            f'opacity="0" data-typing-bg="1" data-final-opacity="{op}"/>'
        )
        parts.append(f'<text x="{cx + w//2}" y="{y}" text-anchor="middle" '
                     f'font-family="monospace" font-size="11" fill="{fg}" dominant-baseline="middle">{esc(lbl)}</text>')
        cx += w + 5
    return "\n".join(parts)


def wrap_text(text: str, max_chars: int, max_lines: int = DEFAULT_DESCRIPTION_LINES) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if len(trial) <= max_chars:
            current = trial
            continue
        lines.append(current)
        current = word
        if len(lines) == max_lines - 1:
            break

    remaining_words = words[len(" ".join(lines + [current]).split()):]
    if remaining_words:
        current = f"{current} {' '.join(remaining_words)}".strip()

    if len(current) > max_chars:
        current = current[: max_chars - 3].rstrip() + "..."
    lines.append(current)
    return lines[:max_lines]


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def tokenize_svg_text(text: str) -> list[str]:
    return re.findall(r"&[^;]+;|.", text, flags=re.DOTALL)


def render_svg_token(token: str) -> str:
    if token == " ":
        return "&#160;"
    return token


def build_cursor_animation(start_seconds: float, cycle_seconds: float, blink_period: float = 1.1) -> str:
    key_times = [0.0]
    values = ["0"]

    start_seconds = min(max(start_seconds, 0.0), cycle_seconds)
    start_frac = start_seconds / cycle_seconds if cycle_seconds else 0.0
    key_times.append(start_frac)
    values.append("0")

    current = start_seconds
    visible = True
    while current < cycle_seconds:
        frac = min(current / cycle_seconds, 1.0)
        key_times.append(frac)
        values.append("0.7" if visible else "0")
        current += blink_period / 2
        visible = not visible

    if key_times[-1] != 1.0:
        key_times.append(1.0)
        values.append(values[-1])

    key_times_text = ";".join(f"{value:.6f}" for value in key_times)
    values_text = ";".join(values)
    return (
        f'<animate attributeName="opacity" values="{values_text}" '
        f'keyTimes="{key_times_text}" dur="{cycle_seconds}s" repeatCount="indefinite"/>'
    )


def animate_svg_lines(body_lines: list[str]) -> str:
    pattern = re.compile(r"^(?P<indent>\s*)<text(?P<attrs>[^>]*)>(?P<content>.*?)</text>$")
    rect_pattern = re.compile(
        r'^(?P<indent>\s*)<rect(?P<attrs>[^>]*)data-typing-bg="1"(?P<tail>[^>]*)data-final-opacity="(?P<final>[^"]+)"(?P<end>[^>]*)/>$'
    )
    cursor_pattern = re.compile(
        r'^(?P<indent>\s*)<rect(?P<attrs>[^>]*) opacity="0\.7">.*attributeName="opacity".*</rect>$'
    )
    parsed = []
    total_chars = 0

    for line in body_lines:
        if rect_pattern.match(line) or cursor_pattern.match(line):
            parsed.append((None, line))
            continue
        match = pattern.match(line)
        if not match:
            parsed.append((None, line))
            continue
        attrs = match.group("attrs")
        content = match.group("content")
        tokens = tokenize_svg_text(content)
        visible_chars = sum(1 for token in tokens if unescape(token))
        total_chars += visible_chars
        parsed.append((match, tokens))

    total_chars = max(total_chars, 1)
    step_seconds = TYPING_DURATION_SECONDS / total_chars
    cycle_seconds = TYPING_DURATION_SECONDS + TYPING_PAUSE_SECONDS
    char_index = 0
    animated_lines = []
    pending_rects = []

    for item in parsed:
        match, payload = item
        if match is None:
            rect_match = rect_pattern.match(payload)
            if rect_match:
                pending_rects.append(rect_match)
                continue

            cursor_match = cursor_pattern.match(payload)
            if cursor_match:
                indent = cursor_match.group("indent")
                attrs = cursor_match.group("attrs")
                animated_lines.append(
                    f'{indent}<rect{attrs} opacity="0">{build_cursor_animation(TYPING_DURATION_SECONDS, cycle_seconds)}</rect>'
                )
                continue

            animated_lines.append(payload)
            continue

        attrs = match.group("attrs")
        indent = match.group("indent")
        tokens = payload
        line_start_seconds = char_index * step_seconds
        line_start_frac = line_start_seconds / cycle_seconds

        while pending_rects:
            rect = pending_rects.pop(0)
            rect_indent = rect.group("indent")
            rect_attrs = rect.group("attrs")
            rect_tail = rect.group("tail")
            rect_end = rect.group("end")
            final_opacity = rect.group("final")
            rect_markup = f"{rect_attrs}{rect_tail}{rect_end}"
            rect_markup = re.sub(r'\sdata-typing-bg="1"', "", rect_markup)
            rect_markup = re.sub(r'\sdata-final-opacity="[^"]+"', "", rect_markup)
            rect_markup = re.sub(r'\sopacity="[^"]+"', "", rect_markup)
            animated_lines.append(
                f'{rect_indent}<rect{rect_markup} opacity="0">'
                f'<animate attributeName="opacity" values="0;0;{final_opacity};{final_opacity}" '
                f'keyTimes="0;{line_start_frac:.6f};{line_start_frac:.6f};1" '
                f'dur="{cycle_seconds}s" repeatCount="indefinite"/></rect>'
            )

        parts = [f'{indent}<text{attrs}>']
        for token in tokens:
            if not unescape(token):
                parts.append(token)
                continue
            rendered_token = render_svg_token(token)
            start = char_index * step_seconds
            frac = start / cycle_seconds
            parts.append(
                f'<tspan opacity="0">{rendered_token}'
                f'<animate attributeName="opacity" values="0;0;1;1" '
                f'keyTimes="0;{frac:.6f};{frac:.6f};1" '
                f'dur="{cycle_seconds}s" repeatCount="indefinite"/></tspan>'
            )
            char_index += 1
        parts.append("</text>")
        animated_lines.append("".join(parts))

    return "\n".join(animated_lines)


# ─────────────────────────────────────────────
#  CARD BUILDER
# ─────────────────────────────────────────────

def build_card(dark_mode, project, mood, time_ctx, status, dev_mode,
               commands, visits, streak, current_project) -> str:

    if dark_mode:
        bg_out  = "#0d1117"; bg_card = "#161b22"; border = "#30363d"
        pri     = "#f0f6fc"; muted   = "#8b949e"; accent = "#58a6ff"
        s_green = "#28C840"; s_blue  = "#58a6ff"; s_purp = "#a855f7"; s_pink = "#f472b6"
        pat     = "dots-dark"
    else:
        bg_out  = "#f6f8fa"; bg_card = "#ffffff"; border = "#d0d7de"
        pri     = "#24292f"; muted   = "#57606a"; accent = "#185FA5"
        s_green = "#28C840"; s_blue  = "#185FA5"; s_purp = "#534AB7"; s_pink = "#D4537E"
        pat     = "dots-light"

    L = []   # SVG lines

    # Background dot texture + card shell
    L.append(box(0, 0, SVG_WIDTH, SVG_HEIGHT, 16, f"url(#{pat})"))
    L.append(box(12, 12, 656, 316, 14, bg_card, border, 0.75))

    # Header bar
    L.append(box(12, 12, 656, 44, 14, bg_out, border, 0.5))
    L.append(box(12, 40, 656, 16, 0, bg_out))
    L.append(dot(38, 34, 5.5, "#FF5F57"))
    L.append(dot(58, 34, 5.5, "#FEBC2E"))
    L.append(dot(78, 34, 5.5, "#28C840"))
    L.append(t(340, 38, "profile.sh", muted, anchor="middle"))
    L.append(dot(602, 34, 4, "#28C840", 0.9))
    L.append(t(612, 38, "online", muted))
    L.append(hline(12, 56, 668, border, 0.75))

    # ── LEFT PANEL ───────────────────────────
    y = 76
    L.append(t(36, y, time_ctx["greeting"], muted, size=11))
    y += 15
    L.append(t(36, y, f"streak: {streak} days coding", accent, size=11))
    y += 16
    L.append(hline(36, y, 400, border))
    y += 14

    # 1 rotating command
    for cmd, output in commands[:1]:
        L.append(t(36, y, "$", muted))
        L.append(t(50, y, cmd, muted))
        y += 16
        L.append(t(50, y, output, pri))
        y += 18
        L.append(hline(36, y - 2, 400, border))
        y += 10

    # ── CURRENTLY WORKING ON ─────────────────
    cur_name   = current_project["name"]
    cur_labels = fit_labels(current_project.get("labels", []), start_x=248, max_x=400)
    cur_desc   = current_project.get("description", "")
    L.append(t(36, y, "$", muted))
    L.append(t(50, y, "currently working on:", muted))
    if cur_labels:
        L.append(label_tags(248, y, cur_labels, dark_mode))
    y += 16
    L.append(t(50, y, f"→ {cur_name}", pri))
    y += 16
    if cur_desc:
        for line in wrap_text(cur_desc, max_chars=46):
            L.append(t(50, y, line, muted, size=11))
            y += 12

    L.append(hline(36, y - 2, 400, border))
    y += 10

    # ── GUARANTEED PROJECT RECOMMENDATION ────
    L.append(t(36, y, "$", muted))
    L.append(t(50, y, "daily repo reco:", muted))

    name    = project["name"]
    desc    = project.get("description", "")
    labels  = fit_labels(project.get("labels", []), start_x=248, max_x=400)

    if labels:
        L.append(label_tags(248, y, labels, dark_mode))
    y += 16
    L.append(t(50, y, f"→ {name}", pri))
    y += 16
    last_recommendation_line = f"→ {name}"
    last_recommendation_y = y
    if desc:
        wrapped_desc = wrap_text(
            desc,
            max_chars=46,
            max_lines=RECOMMENDATION_DESCRIPTION_LINES,
        )
        for line in wrapped_desc:
            L.append(t(50, y, line, muted, size=11))
            last_recommendation_line = line
            last_recommendation_y = y
            y += 12
    else:
        last_recommendation_y = y - 16

    # Blinking cursor
    cursor_x = 50 + len(last_recommendation_line) * 7 + 6
    cursor_y = last_recommendation_y - 10
    L.append(
        f'<rect x="{cursor_x}" y="{cursor_y}" width="8" height="12" rx="1" fill="{muted}" opacity="0.7">'
        f'<animate attributeName="opacity" values="0.7;0;0.7" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
    )

    # ── RIGHT PANEL ──────────────────────────
    L.append(vline(416, 56, 328, border))

    ry = 74
    L.append(t(444, ry, "aundreka.exe", muted))
    ry += 10
    L.append(hline(444, ry, 644, border))
    ry += 20

    face = PET_FACES.get(mood, PET_FACES["happy"])
    for row in face:
        L.append(t(530, ry, row, muted, anchor="middle"))
        ry += 18
    ry += 4

    L.append(t(530, ry, f"mood: {mood}", muted, size=11, anchor="middle"))
    ry += 15

    msg = random.Random().choice(PET_MESSAGES.get(mood, ["keep building."]))
    L.append(t(530, ry, msg, pri, anchor="middle"))
    ry += 20

    L.append(hline(444, ry, 644, border))
    ry += 14

    L.append(t(444, ry, f"status: {status}", accent, size=11))
    ry += 14
    L.append(t(444, ry, f"mode:   {dev_mode}", muted, size=11))
    ry += 20

    L.append(hline(444, ry, 644, border))
    ry += 14

    L.append(t(444, ry, f"profile visits: {visits}", muted, size=11))

    # ── BOTTOM STRIP ─────────────────────────
    L.append(hline(12, 302, 668, border))
    L.append(box(36,  312, 80, 4, 2, s_green, op=0.7))
    L.append(box(124, 312, 55, 4, 2, s_blue,  op=0.7))
    L.append(box(187, 312, 95, 4, 2, s_purp,  op=0.7))
    L.append(box(290, 312, 65, 4, 2, s_pink,  op=0.7))
    L.append(t(644, 318, "v1.0", muted, anchor="end"))

    return "\n".join(L)


# ─────────────────────────────────────────────
#  SVG ASSEMBLER
# ─────────────────────────────────────────────

DEFS = f"""<defs>
  <pattern id="dots-dark" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#30363d"/>
  </pattern>
  <pattern id="dots-light" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#d0d7de"/>
  </pattern>
</defs>"""


def generate_svg(dark_mode: bool, project, mood, time_ctx, status,
                 dev_mode, commands, visits, streak, current_project, label: str) -> str:
    body = build_card(dark_mode, project, mood, time_ctx, status,
                      dev_mode, commands, visits, streak, current_project)
    body_lines = body.splitlines()
    static_lines = []
    animated_candidates = []
    for line in body_lines:
        stripped = line.lstrip()
        if stripped.startswith("<text") or 'data-typing-bg="1"' in stripped or 'attributeName="opacity"' in stripped:
            animated_candidates.append(line)
        else:
            static_lines.append(line)
    animated_text = animate_svg_lines(animated_candidates)
    return "\n".join([
        f'<svg width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        'role="img" xmlns="http://www.w3.org/2000/svg">',
        f'  <title>Aundreka OS: {label}</title>',
        DEFS,
        "\n".join(static_lines),
        animated_text,
        '</svg>',
    ])


def resolve_banner_context(
    mode: str = "weighted",
    github: bool = False,
    streak_override: int | None = None,
    visits_override: str | None = None,
    now: datetime.datetime | None = None,
) -> dict:
    now = now or datetime.datetime.now(DISPLAY_TIMEZONE)
    seed = int(now.strftime("%Y%m%d"))

    time_ctx = get_time_context(now)
    mood = pick_mood(time_ctx, seed)
    status = random.Random(seed + 1).choice(STATUSES)
    dev_mode = random.Random(seed + 2).choice(DEV_MODES)
    commands = pick_commands(seed)
    streak = streak_override if streak_override is not None else fetch_real_activity_streak(now)
    visits = visits_override or fetch_github_visits(GITHUB_USERNAME)

    if github:
        projects = fetch_github_projects(GITHUB_USERNAME)
    else:
        projects = FALLBACK_PROJECTS

    current_project = get_current_project(projects)
    project = pick_project(
        projects,
        mode,
        seed,
        exclude_name=current_project.get("name"),
    )

    return {
        "commands": commands,
        "current_project": current_project,
        "dev_mode": dev_mode,
        "mood": mood,
        "now": now,
        "project": project,
        "projects": projects,
        "status": status,
        "streak": streak,
        "time_ctx": time_ctx,
        "visits": visits,
    }


def render_banner(
    theme: str = "dark",
    mode: str = "weighted",
    github: bool = False,
    streak_override: int | None = None,
    visits_override: str | None = None,
    now: datetime.datetime | None = None,
) -> str:
    dark_mode = theme == "dark"
    context = resolve_banner_context(
        mode=mode,
        github=github,
        streak_override=streak_override,
        visits_override=visits_override,
        now=now,
    )
    return generate_svg(
        dark_mode=dark_mode,
        project=context["project"],
        mood=context["mood"],
        time_ctx=context["time_ctx"],
        status=context["status"],
        dev_mode=context["dev_mode"],
        commands=context["commands"],
        visits=context["visits"],
        streak=context["streak"],
        current_project=context["current_project"],
        label=context["now"].strftime("%b %d"),
    )


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Aundreka OS Banner Generator")
    p.add_argument("--mode",   choices=["random","weighted","chronological"],
                   default="weighted",
                   help="Project selection: random | weighted | chronological")
    p.add_argument("--theme",  choices=["dark","light","both"], default="both",
                   help="Output theme (default: both — two separate files)")
    p.add_argument("--github", action="store_true",
                   help="Fetch real repos + visits from GitHub")
    p.add_argument("--streak", type=int, default=None,
                   help="Coding streak in days (defaults to git-derived value)")
    p.add_argument("--visits", default=None,
                   help="Profile visit count to display (overrides GitHub fetch)")
    args = p.parse_args()

    print("Aundreka OS Banner Generator")
    print("-" * 36)
    if args.github:
        print(f"  [github]  fetching @{GITHUB_USERNAME}...")
    context = resolve_banner_context(
        mode=args.mode,
        github=args.github,
        streak_override=args.streak,
        visits_override=args.visits,
    )
    now = context["now"]
    time_ctx = context["time_ctx"]
    mood = context["mood"]
    status = context["status"]
    dev_mode = context["dev_mode"]
    streak = context["streak"]
    visits = context["visits"]
    project = context["project"]
    current_project = context["current_project"]

    print(f"  [time]    {now.strftime('%Y-%m-%d %H:%M')} · {time_ctx['period']}")
    print(f"  [mood]    {mood}")
    print(f"  [project] {project['name']} ({args.mode})")
    print(f"  [working] {current_project['name']} (most recent push: {current_project.get('pushed_at','?')[:10]})")
    print(f"  [status]  {status} · mode={dev_mode}")
    print(f"  [streak]  {streak} day(s)")
    print(f"  [visits]  {visits}")

    themes = []
    if args.theme in ("dark",  "both"): themes.append((True,  "banner-dark.svg"))
    if args.theme in ("light", "both"): themes.append((False, "banner-light.svg"))

    for dark_mode, filename in themes:
        svg = render_banner(
            theme="dark" if dark_mode else "light",
            mode=args.mode,
            github=args.github,
            streak_override=args.streak,
            visits_override=args.visits,
            now=now,
        )
        Path(filename).write_text(svg, encoding="utf-8")
        print(f"  [output]  {filename} ({len(svg):,} bytes)")

    print("-" * 36)
    print("Done")


if __name__ == "__main__":
    main()
