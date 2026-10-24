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
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360" role="img" aria-labelledby="title desc">',
        '<title id="title">Tharun Adhithya — full-stack developer</title>',
        '<desc id="desc">A profile card showing current projects and live GitHub and LeetCode activity.</desc>',
        "<style>",
        f".bg{{fill:{color['background']};}} .surface{{fill:{color['surface']};}} .rule{{stroke:{color['rule']};}}",
        f".title{{fill:{color['text']};font:700 31px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.7px;}}",
        f".subtitle{{fill:{color['muted']};font:400 16px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".section{{fill:{color['muted']};font:600 13px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:.2px;}}",
        f".project{{fill:{color['text']};font:600 15px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".detail{{fill:{color['muted']};font:400 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".metric{{fill:{color['text']};font:600 16px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}",
        f".accent{{fill:{color['accent']};font:700 25px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.7px;}}",
        f".mono{{fill:{color['background']};font:700 20px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:-1.5px;}}",
        "</style>",
        '<rect class="bg" width="960" height="360"/>',
        '<rect class="surface" x="24" y="24" width="912" height="312" rx="12"/>',
        f'<rect x="48" y="52" width="58" height="58" rx="10" fill="{color["accent"]}"/>',
        text(59, 88, "TA", "mono"),
        text(128, 76, "Tharun Adhithya", "title"),
        text(128, 103, "Full-stack developer building practical software for teams and creators.", "subtitle"),
        '<line class="rule" x1="48" y1="136" x2="912" y2="136"/>',
        '<line class="rule" x1="570" y1="160" x2="570" y2="302"/>',
        text(48, 174, "Building now", "section"),
        text(602, 174, "Live activity", "section"),
    ]

    for index, (project, description) in enumerate(work):
        y = 211 + index * 31
        out.append(text(48, y, project, "project"))
        out.append(text(202, y, f"— {description}", "detail"))

    out.extend(
        [
            text(602, 211, "GitHub", "detail"),
            text(685, 211, f"{number(github['repositories'])} repos · {number(github['commits'])} commits · {number(github['stars'])} stars", "metric"),
            text(602, 251, "LeetCode", "detail"),
            text(685, 251, f"{number(leetcode['total'])} solved", "accent"),
            text(685, 277, f"{leetcode['easy']} easy · {leetcode['medium']} medium · {leetcode['hard']} hard", "detail"),
            text(48, 316, "TypeScript · React · Node.js · PostgreSQL · Redis · Docker", "detail"),
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
