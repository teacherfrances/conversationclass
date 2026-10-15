"""Builds activities.json for the Friday Conversation Class homepage.

Lists every public repo on the teacherfrances account whose name starts with
"fridayclass" and has GitHub Pages switched on, reads each page's <title>,
and sorts it into a homepage section by keyword.

To change what happens, edit the three settings below.
"""
import json, os, re, urllib.request, html
from datetime import datetime, timezone

OWNER = "teacherfrances"
PREFIX = "fridayclass"

# Repos that must never appear on the homepage (removed on purpose).
EXCLUDE = {
    "fridayclass",               # a homepage repo, not an activity
    "fridayclass_moonfestival",  # Special days section was removed
}

# Keyword in the repo name -> (section title on the homepage, section emoji, put new section at top?)
# The first keyword that matches wins. Add a line here for each new lesson.
SECTIONS = [
    ("lastlap",            "The last lap",           "🏁", True),
    ("nothingsetinstone",  "Nothing set in stone",   "🪨", False),
    ("nothingissetinstone","Nothing set in stone",   "🪨", False),
    ("findingyourfeet",    "Finding your feet",      "👣", False),
    ("excursion",          "Excursions",             "📸", False),
    ("escape",             "Games and escape rooms", "🎲", False),
]
OTHER = ("More activities", "🌟", False)

# Keyword in the repo name -> card emoji and short line for the card.
CARD = [
    ("jeopardy", "🏆", "A team quiz game."),
    ("phone",    "📱", "Unlock the phone."),
    ("hunt",     "🧭", "A scavenger hunt."),
    ("escape",   "🔐", "An escape room game."),
    ("deck",     "🎬", "The lesson introduction."),
    ("intro",    "🎬", "The lesson introduction."),
    ("quiz",     "❓", "A quiz."),
    ("bingo",    "🎱", "Talk to your classmates."),
    ("revision", "🔁", "Revise the expressions."),
    ("game",     "🎲", "A class game."),
]

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get(url, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "fridayclass-homepage"})
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def list_repos():
    repos, page = [], 1
    while True:
        batch = json.loads(get(f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}&type=owner"))
        if not batch:
            return repos
        repos += batch
        page += 1


def page_title(name):
    try:
        text = get(f"https://{OWNER}.github.io/{name}/", accept="text/html").decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    if not m:
        return None
    t = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return t or None


def main():
    items = []
    for r in list_repos():
        name = r["name"]
        low = name.lower()
        if not low.startswith(PREFIX) or low in EXCLUDE or r.get("fork") or r.get("archived") or r.get("private"):
            continue
        if not r.get("has_pages"):
            continue
        section, s_emoji, s_top = OTHER
        for key, title, emoji, top in SECTIONS:
            if key in low:
                section, s_emoji, s_top = title, emoji, top
                break
        emoji, desc = "✨", "A class activity."
        for key, e, d in CARD:
            if key in low:
                emoji, desc = e, d
                break
        if r.get("description"):
            desc = r["description"].strip()
        title = page_title(name) or name
        items.append({
            "repo": name,
            "title": title,
            "desc": desc,
            "emoji": emoji,
            "date": r["created_at"][:10],
            "section": section,
            "sectionEmoji": s_emoji,
            "sectionTop": s_top,
        })
    # oldest first, so the page (which adds each to the top of its section) shows newest first
    items.sort(key=lambda x: x["date"])
    out = {"items": items}
    old = None
    if os.path.exists("activities.json"):
        with open("activities.json", encoding="utf-8") as f:
            old = json.load(f)
    if old and old.get("items") == items:
        print("No change")
        return
    out["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open("activities.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(items)} activities")


if __name__ == "__main__":
    main()
