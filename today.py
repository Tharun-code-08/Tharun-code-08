"""Render the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Static fields live in PROFILE below; GitHub stats are fetched live with the
token in GH_TOKEN. Run by .github/workflows/build.yaml every day.
"""
import calendar
import datetime as dt
import json
import os
import time
import urllib.request
from html import escape
from pathlib import Path

USER = "Tharun-code-08"
LEETCODE_USER = "Tharun-code-08"
UPTIME_SINCE = dt.date(2025, 6, 5)  # GitHub join date; swap for a birthday to show age
WIDTH = 64  # characters in the right-hand column
ROOT = Path(__file__).parent

# Each row: ("title", text) | ("kv", key, value) | ("blank",) | ("stats", ...)
PROFILE = [
    ("title", "tharun@adhithya"),
    ("kv", "OS", "Windows 11"),
    ("kv", "Uptime", "{uptime}"),
    ("kv", "Host", "Sathyabama Institute of Science and Technology"),
    ("kv", "Kernel", "CSE Student · Full-Stack Developer"),
    ("kv", "IDE", "VS Code, Claude Code"),
    ("blank",),
    ("kv", "Languages.Programming", "TypeScript, JavaScript, Java, Python"),
    ("kv", "Languages.Computer", "HTML, CSS, SQL, JSON, YAML"),
    ("kv", "Languages.Real", "English, Tamil"),
    ("blank",),
    ("kv", "Stack.Frontend", "React, Next.js, Three.js, Astro"),
    ("kv", "Stack.Backend", "Node.js, NestJS, PostgreSQL, Prisma, Redis"),
    ("kv", "Focus", "SaaS products, Dev tools, AI integrations"),
    ("kv", "Motto", "Code first, ask questions later"),
    ("gap",),
    ("section", "Contact"),
    ("kv", "Website", "softdigitconsulting.com"),
    ("kv", "GitHub", "Tharun-code-08"),
    ("kv", "Location", "Chennai, India"),
    ("gap",),
    ("section", "GitHub Stats"),
    ("repos",),
    ("commits",),
    ("loc",),
    ("gap",),
    ("section", "LeetCode Stats"),
    ("leetcode",),
]

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 add="#3fb950", dele="#f85149", cc="#616e7f"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  add="#1a7f37", dele="#cf222e", cc="#c2cfde"),
}


# ---------------------------------------------------------------- GitHub data
def _req(url, body=None):
    headers = {"Authorization": f"bearer {os.environ['GH_TOKEN']}",
               "User-Agent": USER, "Accept": "application/vnd.github+json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req) as r:
        return r.status, (json.loads(r.read() or "null"))


def graphql(query, **variables):
    _, res = _req("https://api.github.com/graphql", {"query": query, "variables": variables})
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return res["data"]


def fetch_stats():
    data = graphql("""
      query($login: String!) {
        user(login: $login) {
          createdAt
          followers { totalCount }
          repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
          repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
            totalCount
            nodes { name isFork stargazerCount }
          }
        }
      }""", login=USER)["user"]
    repos = data["repositories"]["nodes"]

    commits = 0
    year = dt.datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")).year
    while year <= dt.date.today().year:
        c = graphql("""
          query($login: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $login) {
              contributionsCollection(from: $from, to: $to) {
                totalCommitContributions restrictedContributionsCount
              }
            }
          }""", login=USER, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        cc = c["user"]["contributionsCollection"]
        commits += cc["totalCommitContributions"]
        year += 1

    added = deleted = 0
    for repo in repos:
        if repo["isFork"]:
            continue
        url = f"https://api.github.com/repos/{USER}/{repo['name']}/stats/contributors"
        for _ in range(8):  # GitHub answers 202 while it computes the stats
            status, body = _req(url)
            if status == 200:
                break
            time.sleep(3)
        for author in body or []:
            if (author.get("author") or {}).get("login", "").lower() == USER.lower():
                added += sum(w["a"] for w in author["weeks"])
                deleted += sum(w["d"] for w in author["weeks"])

    return {
        "repos": data["repositories"]["totalCount"],
        "contributed": data["repositoriesContributedTo"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": data["followers"]["totalCount"],
        "commits": commits,
        "added": added,
        "deleted": deleted,
    }


def fetch_leetcode_stats():
    """Fetch accepted-problem counts from LeetCode's public GraphQL API."""
    query = """
      query userProfile($username: String!) {
        matchedUser(username: $username) {
          profile { ranking }
          submitStatsGlobal {
            acSubmissionNum { difficulty count }
          }
        }
      }
    """
    payload = json.dumps({"query": query, "variables": {"username": LEETCODE_USER}}).encode()
    request = urllib.request.Request(
        "https://leetcode.com/graphql/",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read())

    user = result.get("data", {}).get("matchedUser")
    if not user:
        raise RuntimeError(f"LeetCode profile not found: {LEETCODE_USER}")

    counts = {item["difficulty"]: item["count"] for item in user["submitStatsGlobal"]["acSubmissionNum"]}
    return {
        "all": counts.get("All", 0),
        "easy": counts.get("Easy", 0),
        "medium": counts.get("Medium", 0),
        "hard": counts.get("Hard", 0),
        "ranking": user["profile"].get("ranking"),
    }


def uptime(since, today):
    total = (today.year - since.year) * 12 + today.month - since.month - (today.day < since.day)
    years, months = divmod(total, 12)
    ay, am = divmod(since.month - 1 + total, 12)
    ay += since.year
    anchor = dt.date(ay, am + 1, min(since.day, calendar.monthrange(ay, am + 1)[1]))
    days = (today - anchor).days
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


# ---------------------------------------------------------------- rendering
# A row is a list of (text, css_class) segments; dots pad keys to values.
def kv(key, value, width):
    parts = key.split(".")
    keyseg = []
    for i, p in enumerate(parts):
        keyseg.append((p, "key"))
        if i < len(parts) - 1:
            keyseg.append((".", None))
    head = [(". ", "cc")] + keyseg + [(":", None), (" ", None)]
    used = sum(len(t) for t, _ in head) + len(value) + 1
    dots = "." * max(1, width - used)
    return head + [(dots, "cc"), (" ", None), (value, "value")]


def rule(label, width, lead):
    text = f"{lead}{label} "
    return [(text, None), ("—" * (width - len(text) - 3), None), ("-—-", None)]


def build_rows(stats, leetcode):
    n = lambda v: f"{v:,}"
    rows = []
    for row in PROFILE:
        kind = row[0]
        if kind == "title":
            rows.append(rule(row[1], WIDTH, ""))
        elif kind == "section":
            rows.append(rule(row[1], WIDTH, "- "))
        elif kind == "kv":
            value = row[2].format(uptime=uptime(UPTIME_SINCE, dt.date.today()))
            rows.append(kv(row[1], value, WIDTH))
        elif kind == "blank":
            rows.append([(". ", "cc")])
        elif kind == "gap":
            rows.append([])
        elif kind == "repos":
            left = kv("Repos", f"{n(stats['repos'])} {{Contributed: {n(stats['contributed'])}}}", 36)
            right = kv("Stars", n(stats["stars"]), WIDTH - 37)[1:]
            rows.append(left + [(" | ", None)] + right)
        elif kind == "commits":
            left = kv("Commits", n(stats["commits"]), 36)
            right = kv("Followers", n(stats["followers"]), WIDTH - 37)[1:]
            rows.append(left + [(" | ", None)] + right)
        elif kind == "loc":
            net, add, dele = n(stats["added"] - stats["deleted"]), n(stats["added"]), n(stats["deleted"])
            # pad with the full plain-text value, then recolour its parts
            row_ = kv("Lines of Code on GitHub", f"{net} ( {add}++, {dele}-- )", WIDTH)[:-1]
            rows.append(row_ + [(net, "value"), (" ( ", None), (f"{add}++", "add"),
                                (", ", None), (f"{dele}--", "del"), (" )", None)])
        elif kind == "leetcode":
            rank = f" · Rank #{n(leetcode['ranking'])}" if leetcode["ranking"] else ""
            rows.append(kv("Solved", f"{n(leetcode['all'])}{rank}", WIDTH))
            rows.append(kv("Easy", n(leetcode["easy"]), WIDTH))
            rows.append(kv("Medium", n(leetcode["medium"]), WIDTH))
            rows.append(kv("Hard", n(leetcode["hard"]), WIDTH))
    return rows


def svg(theme, art, rows):
    c = THEMES[theme]
    lh, top, pad, ch = 20, 30, 30, 9.6  # ch: glyph width of 16px Courier / size-adjusted Consolas
    art_x = pad
    text_x = round(art_x + max(map(len, art)) * ch + 30)
    width = round(text_x + (WIDTH + 1) * ch + pad)
    height = top + max(len(art), len(rows)) * lh + 10
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'Courier New\',monospace" '
        f'width="{width}px" height="{height}px" font-size="16px">',
        "<style>",
        "@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';"
        "font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}",
        f".key{{fill:{c['key']};}} .value{{fill:{c['value']};}} .add{{fill:{c['add']};}} "
        f".del{{fill:{c['dele']};}} .cc{{fill:{c['cc']};}}",
        "text,tspan{white-space:pre;}",
        "</style>",
        f'<rect width="{width}px" height="{height}px" fill="{c["bg"]}" rx="15"/>',
        f'<text x="{art_x}" y="{top}" fill="{c["text"]}" class="ascii">',
    ]
    for i, line in enumerate(art):
        out.append(f'<tspan x="{art_x}" y="{top + i * lh}">{escape(line)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="{text_x}" y="{top}" fill="{c["text"]}">')
    for i, row in enumerate(rows):
        segs = "".join(
            f'<tspan class="{cls}">{escape(t)}</tspan>' if cls else escape(t) for t, cls in row
        )
        out.append(f'<tspan x="{text_x}" y="{top + i * lh}">{segs}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    art = (ROOT / "ascii-art.txt").read_text(encoding="utf-8").splitlines()
    rows = build_rows(fetch_stats(), fetch_leetcode_stats())
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, art, rows), encoding="utf-8")


if __name__ == "__main__":
    main()
