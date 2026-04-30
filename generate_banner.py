#!/usr/bin/env python3
"""
generate_banner.py — Aundreka OS Profile Banner Generator

Usage:
  python3 generate_banner.py                        # generates banner-dark.svg + banner-light.svg
  python3 generate_banner.py --theme dark           # dark only  → banner-dark.svg
  python3 generate_banner.py --theme light          # light only → banner-light.svg
  python3 generate_banner.py --mode random          # random project pick
  python3 generate_banner.py --mode chronological   # latest pushed repo first
  python3 generate_banner.py --github --streak 7    # fetch real GitHub data
  python3 generate_banner.py --visits 1234          # set profile visit count manually
"""

import random
import datetime
import argparse
import json
import urllib.request
from pathlib import Path


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

GITHUB_USERNAME = "aundreka"   # ← change to your GitHub username

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
    "evil":     [" /\\_/\\ ", "=( >.< )=", "  > 😈<  "],
    "focused":  [" /\\_/\\ ", "=( o.o )=", "  > ~ <  "],
    "confused": [" /\\_/\\ ", "=( ?_? )=", "  > . <  "],
}

PET_MESSAGES = {
    "happy":    ["keep building!", "you got this!", "ship it!"],
    "sleepy":   ["zzz... still building...", "one more commit...", "*yawns* deploy later"],
    "excited":  ["LOOK AT THIS PROJECT!!", "WE'RE SHIPPING TODAY!!", "LFG!! 🔥"],
    "evil":     ["you WILL click my repo 😈", "resistance is futile.", "fork me. NOW."],
    "focused":  ["in the zone.", "deep work activated.", "no distractions."],
    "confused": ["why does this work?", "git blame says... me.", "stackoverflow tab #47"],
}

# 3 rotating terminal commands that appear ABOVE the guaranteed project line
ROTATING_COMMANDS = [
    ("git status",        "nothing to commit (yet)"),
    ("cat about.txt",     "developer · builder · dreamer"),
    ("git log --oneline -1", "feat: ship something great"),
    ("./launch.sh",       "build successful ✓"),
    ("whoami",            "aundreka"),
    ("run deploy.sh",     "deploying..."),
    ("git diff HEAD",     "3 files changed"),
    ("npm run build",     "compiled successfully"),
]

STATUSES  = ["coding", "debugging", "building", "deploying", "experimenting", "in grindset"]
DEV_MODES = ["grindset", "experimenting", "shipping", "debugging", "building", "vibing"]

RARITY_LABELS = {
    "common":   "",
    "uncommon": " ✦",
    "rare":     " 💎",
    "hidden":   " 👀 rare drop",
}

LABEL_COLORS_DARK = {
    "GAME":   ("#3B6D11", "#7ee787"),
    "AI":     ("#854F0B", "#ffa657"),
    "WEB":    ("#0C447C", "#58a6ff"),
    "MOBILE": ("#3C3489", "#a855f7"),
}
LABEL_COLORS_LIGHT = {
    "GAME":   ("#dcfce7", "#3B6D11"),
    "AI":     ("#fef3c7", "#854F0B"),
    "WEB":    ("#dbeafe", "#185FA5"),
    "MOBILE": ("#ede9fe", "#534AB7"),
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
    elif hour < 17:
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
        req = urllib.request.Request(url, headers={"User-Agent": "aundreka-banner"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            repos = json.loads(resp.read())
        projects = []
        for r in repos:
            if r.get("fork"):
                continue
            topics = r.get("topics", [])
            labels = []
            if any(t in topics for t in ["game", "games"]):   labels.append("GAME")
            if any(t in topics for t in ["ai", "ml"]):        labels.append("AI")
            if any(t in topics for t in ["web", "website"]):  labels.append("WEB")
            if any(t in topics for t in ["mobile","android"]): labels.append("MOBILE")
            projects.append({
                "name":        r["name"],
                "labels":      labels,
                "stars":       r.get("stargazers_count", 0),
                "description": (r.get("description") or "")[:55],
                "url":         r.get("html_url", ""),
                "weight":      max(1, r.get("stargazers_count", 0)),
                "rarity":      "common",
                "pushed_at":   (r.get("pushed_at") or "")[:10],
            })
        return projects or FALLBACK_PROJECTS
    except Exception as e:
        print(f"  [github] fetch failed: {e} — using fallback projects")
        return FALLBACK_PROJECTS


def fetch_github_visits(username: str) -> str:
    """
    GitHub doesn't expose profile view counts via the public API.
    Real implementations use a self-hosted counter (e.g. https://komarev.com/ghpvc/).
    We return a placeholder so the layout renders — replace with your real count.
    """
    return "—"


def pick_project(projects: list, mode: str, seed: int) -> dict:
    if not projects:
        return FALLBACK_PROJECTS[0]
    if mode == "chronological":
        return sorted(projects, key=lambda p: p.get("pushed_at", ""), reverse=True)[0]
    if mode == "weighted":
        rng = random.Random(seed)
        return rng.choices(projects, weights=[max(1, p.get("weight", 1)) for p in projects], k=1)[0]
    return random.Random(seed).choice(projects)


def pick_commands(seed: int) -> list:
    """Pick 2 rotating commands. The project recommendation is always appended as a 3rd line."""
    rng  = random.Random(seed + 3)
    pool = list(ROTATING_COMMANDS)
    rng.shuffle(pool)
    return pool[:2]


# ─────────────────────────────────────────────
#  SVG HELPERS
# ─────────────────────────────────────────────

def esc(s: str) -> str:
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def t(x, y, text, fill, size=12, anchor="start", weight="normal"):
    return (f'<text font-family="monospace" font-size="{size}" font-weight="{weight}" '
            f'x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}">{esc(text)}</text>')

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

def label_tags(x, y, labels, dark_mode):
    colors = LABEL_COLORS_DARK if dark_mode else LABEL_COLORS_LIGHT
    default = DEFAULT_DARK if dark_mode else DEFAULT_LIGHT
    parts = []
    cx = x
    for lbl in labels:
        bg, fg = colors.get(lbl, default)
        w = len(lbl) * 7 + 12
        op = 0.3 if dark_mode else 0.9
        parts.append(box(cx, y - 13, w, 17, 3, bg, op=op))
        parts.append(f'<text x="{cx + w//2}" y="{y}" text-anchor="middle" '
                     f'font-family="monospace" font-size="11" fill="{fg}">{esc(lbl)}</text>')
        cx += w + 5
    return "\n".join(parts)


# ─────────────────────────────────────────────
#  CARD BUILDER
# ─────────────────────────────────────────────

def build_card(dark_mode, project, mood, time_ctx, status, dev_mode,
               commands, visits, streak) -> str:

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
    L.append(box(0, 0, 680, 300, 16, f"url(#{pat})"))
    L.append(box(12, 12, 656, 276, 14, bg_card, border, 0.75))

    # Header bar
    L.append(box(12, 12, 656, 44, 14, bg_out, border, 0.5))
    L.append(box(12, 40, 656, 16, 0, bg_out))
    L.append(dot(38, 34, 5.5, "#FF5F57"))
    L.append(dot(58, 34, 5.5, "#FEBC2E"))
    L.append(dot(78, 34, 5.5, "#28C840"))
    L.append(t(340, 38, "aundreka_os — profile.sh", muted, anchor="middle"))
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

    # 2 rotating commands
    for cmd, output in commands:
        L.append(t(36, y, "$", muted))
        L.append(t(50, y, cmd, muted))
        y += 16
        L.append(t(50, y, output, pri))
        y += 18
        L.append(hline(36, y - 2, 400, border))
        y += 10

    # ── GUARANTEED PROJECT RECOMMENDATION ────
    L.append(t(36, y, "$", muted))
    L.append(t(50, y, "today --recommend", muted))
    y += 16

    rarity  = RARITY_LABELS.get(project.get("rarity", "common"), "")
    name    = project["name"]
    desc    = project.get("description", "")
    labels  = project.get("labels", [])

    # project name + rarity
    L.append(t(50, y, f"→ {name}{rarity}", pri))

    # label tags inline after the name
    tag_x = 50 + (len(f"→ {name}{rarity}") * 7) + 6
    if labels:
        L.append(label_tags(tag_x, y, labels, dark_mode))

    y += 16
    if desc:
        L.append(t(50, y, desc[:52], muted, size=11))
        y += 14

    # Blinking cursor
    L.append(
        f'<rect x="50" y="{y}" width="8" height="12" rx="1" fill="{muted}" opacity="0.7">'
        f'<animate attributeName="opacity" values="0.7;0;0.7" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
    )

    # ── RIGHT PANEL ──────────────────────────
    L.append(vline(416, 56, 276, border))

    ry = 74
    L.append(t(444, ry, "pet_ai.exe", muted))
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
    L.append(hline(12, 260, 668, border))
    L.append(box(36,  270, 80, 4, 2, s_green, op=0.7))
    L.append(box(124, 270, 55, 4, 2, s_blue,  op=0.7))
    L.append(box(187, 270, 95, 4, 2, s_purp,  op=0.7))
    L.append(box(290, 270, 65, 4, 2, s_pink,  op=0.7))
    L.append(t(644, 276, "v1.0", muted, anchor="end"))

    return "\n".join(L)


# ─────────────────────────────────────────────
#  SVG ASSEMBLER
# ─────────────────────────────────────────────

DEFS = """<defs>
  <pattern id="dots-dark" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#30363d"/>
  </pattern>
  <pattern id="dots-light" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#d0d7de"/>
  </pattern>
</defs>"""


def generate_svg(dark_mode: bool, project, mood, time_ctx, status,
                 dev_mode, commands, visits, streak, label: str) -> str:
    body = build_card(dark_mode, project, mood, time_ctx, status,
                      dev_mode, commands, visits, streak)
    return "\n".join([
        '<svg width="680" height="300" viewBox="0 0 680 300" '
        'role="img" xmlns="http://www.w3.org/2000/svg">',
        f'  <title>Aundreka OS — {label}</title>',
        DEFS,
        body,
        '</svg>',
    ])


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
    p.add_argument("--streak", type=int, default=1,
                   help="Coding streak in days")
    p.add_argument("--visits", default=None,
                   help="Profile visit count to display (overrides GitHub fetch)")
    args = p.parse_args()

    now  = datetime.datetime.now()
    seed = int(now.strftime("%Y%m%d"))

    time_ctx = get_time_context(now)
    mood     = pick_mood(time_ctx, seed)
    status   = random.Random(seed + 1).choice(STATUSES)
    dev_mode = random.Random(seed + 2).choice(DEV_MODES)
    commands = pick_commands(seed)

    print("Aundreka OS Banner Generator")
    print("─" * 36)
    print(f"  [time]    {now.strftime('%Y-%m-%d %H:%M')} · {time_ctx['period']}")
    print(f"  [mood]    {mood}")

    if args.github:
        print(f"  [github]  fetching @{GITHUB_USERNAME}...")
        projects = fetch_github_projects(GITHUB_USERNAME)
        visits   = args.visits or fetch_github_visits(GITHUB_USERNAME)
    else:
        projects = FALLBACK_PROJECTS
        visits   = args.visits or "—"

    project = pick_project(projects, args.mode, seed)
    print(f"  [project] {project['name']} ({args.mode})")
    print(f"  [status]  {status} · mode={dev_mode}")

    themes = []
    if args.theme in ("dark",  "both"): themes.append((True,  "banner-dark.svg"))
    if args.theme in ("light", "both"): themes.append((False, "banner-light.svg"))

    for dark_mode, filename in themes:
        svg = generate_svg(
            dark_mode=dark_mode, project=project, mood=mood,
            time_ctx=time_ctx, status=status, dev_mode=dev_mode,
            commands=commands, visits=visits, streak=args.streak,
            label=now.strftime("%b %d"),
        )
        Path(filename).write_text(svg, encoding="utf-8")
        print(f"  [output]  {filename} ({len(svg):,} bytes)")

    print("─" * 36)
    print("Done ✓")


if __name__ == "__main__":
    main()