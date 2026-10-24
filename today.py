"""Render the light and dark profile cards shown in README.md.

The card keeps the profile concise: current work on the left, and measured
GitHub and LeetCode activity on the right. It runs daily through the workflow.
"""

import datetime as dt
import json
import os
import urllib.request
from html import escape
from pathlib import Path


USER = "Tharun-code-08"
LEETCODE_USER = "Tharun-code-08"
ROOT = Path(__file__).parent

THEMES = {
    "dark": {
        "background": "#0d1117",
        "surface": "#161b22",
        "text": "#f0f6fc",
        "muted": "#8b949e",
        "rule": "#30363d",
        "accent": "#58a6ff",
    },
    "light": {
        "background": "#ffffff",
        "surface": "#f6f8fa",
        "text": "#1f2328",
        "muted": "#57606a",
        "rule": "#d0d7de",
        "accent": "#0969da",
    },
}


def request_json(url, body=None, headers=None):
    """Make a JSON request, authenticating only when GitHub needs it."""
    request_headers = {
        "Accept": "application/json",
        "User-Agent": f"{USER}-profile-card",
        **(headers or {}),
    }
    if url.startswith("https://api.github.com"):
        request_headers["Authorization"] = f"bearer {os.environ['GH_TOKEN']}"

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers=request_headers,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read())


def github_graphql(query, **variables):
    response = request_json(
        "https://api.github.com/graphql",
        {"query": query, "variables": variables},
    )
    if response.get("errors"):
        raise RuntimeError(response["errors"])
    return response["data"]


def fetch_github_stats():
    user = github_graphql(
        """
        query($login: String!) {
          user(login: $login) {
            createdAt
            repositoryCount: repositories(ownerAffiliations: OWNER, privacy: PUBLIC) {
              totalCount
            }
            publicRepositories: repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
              nodes { isFork stargazerCount }
            }
          }
        }
        """,
        login=USER,
    )["user"]

    contributions = 0
    joined_year = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).year
    today = dt.date.today()
    for year in range(joined_year, today.year + 1):
        collection = github_graphql(
            """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                  totalCommitContributions
                }
              }
            }
            """,
            login=USER,
            **{
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )["user"]["contributionsCollection"]
        contributions += collection["totalCommitContributions"]

    return {
        "repositories": user["repositoryCount"]["totalCount"],
        "stars": sum(repo["stargazerCount"] for repo in user["publicRepositories"]["nodes"] if not repo["isFork"]),
        "commits": contributions,
    }


def fetch_leetcode_stats():
    response = request_json(
        "https://leetcode.com/graphql/",
        {
            "query": """
              query userProfile($username: String!) {
                matchedUser(username: $username) {
                  submitStatsGlobal {
                    acSubmissionNum { difficulty count }
                  }
                }
              }
            """,
            "variables": {"username": LEETCODE_USER},
        },
        {"Content-Type": "application/json"},
    )
    user = response.get("data", {}).get("matchedUser")
    if not user:
        raise RuntimeError(f"LeetCode profile not found: {LEETCODE_USER}")

    counts = {item["difficulty"]: item["count"] for item in user["submitStatsGlobal"]["acSubmissionNum"]}
    return {
        "total": counts.get("All", 0),
        "easy": counts.get("Easy", 0),
        "medium": counts.get("Medium", 0),
        "hard": counts.get("Hard", 0),
    }


def text(x, y, value, css_class):
    return f'<text x="{x}" y="{y}" class="{css_class}">{escape(value)}</text>'


def svg(theme, github, leetcode):
    color = THEMES[theme]
    number = lambda value: f"{value:,}"
    work = [
        ("SoftdigitIMS", "retail operations platform"),
        ("Captik Clipper", "short-form video editor"),
        ("THARUN OS", "interactive portfolio"),
    ]

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="440" viewBox="0 0 840 440" role="img" aria-labelledby="title desc">',
        '<title id="title">Tharun Adhithya — full-stack developer</title>',
        '<desc id="desc">A profile card showing current projects and live GitHub and LeetCode activity.</desc>',
        "<style>",
        f".panel{{fill:{color['surface']};stroke:{color['rule']};stroke-width:1;}} .rule{{stroke:{color['rule']};stroke-width:1;}}",
        f".title{{fill:{color['text']};font:700 38px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-1px;}}",
        f".handle{{fill:{color['accent']};font:600 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:.2px;}}",
        f".subtitle{{fill:{color['muted']};font:400 17px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".section{{fill:{color['muted']};font:600 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:.1px;}}",
        f".project{{fill:{color['text']};font:650 18px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.2px;}}",
        f".detail{{fill:{color['muted']};font:400 15px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".metric{{fill:{color['text']};font:700 29px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.5px;}}",
        f".metric-label{{fill:{color['muted']};font:400 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".accent{{fill:{color['accent']};font:700 34px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-1px;}}",
        "</style>",
        '<rect class="panel" x=".5" y=".5" width="839" height="439" rx="12"/>',
        text(48, 50, "@Tharun-code-08 · Chennai, India", "handle"),
        text(48, 98, "Tharun Adhithya", "title"),
        text(48, 130, "From retail operations to creator tools and playable interfaces.", "subtitle"),
        '<line class="rule" x1="48" y1="164" x2="792" y2="164"/>',
        '<line class="rule" x1="520" y1="194" x2="520" y2="386"/>',
        text(48, 204, "Current builds", "section"),
        text(552, 204, "Activity", "section"),
    ]

    for index, (project, description) in enumerate(work):
        y = 245 + index * 54
        out.append(f'<rect x="48" y="{y - 13}" width="4" height="30" rx="2" fill="{color["accent"]}"/>')
        out.append(text(68, y, project, "project"))
        out.append(text(68, y + 23, description, "detail"))

    out.extend(
        [
            text(552, 245, number(github["repositories"]), "metric"),
            text(552, 268, "public repositories", "metric-label"),
            text(692, 245, number(github["commits"]), "metric"),
            text(692, 268, "public commits", "metric-label"),
            text(552, 306, f"{number(github['stars'])} stars on GitHub", "detail"),
            '<line class="rule" x1="552" y1="326" x2="792" y2="326"/>',
            text(552, 354, "LeetCode", "section"),
            text(552, 392, f"{number(leetcode['total'])} solved", "accent"),
            text(552, 416, f"{leetcode['easy']} easy · {leetcode['medium']} medium · {leetcode['hard']} hard", "detail"),
            text(48, 412, "TypeScript · React · Node.js · PostgreSQL · Redis · Docker", "detail"),
        ]
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    github = fetch_github_stats()
    leetcode = fetch_leetcode_stats()
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, github, leetcode), encoding="utf-8")


if __name__ == "__main__":
    main()
