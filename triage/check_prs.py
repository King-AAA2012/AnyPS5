#!/usr/bin/env python3
"""For a list of issue numbers, check whether each has an open PR (via GitHub API)."""
import json, subprocess, sys, os

TOKEN = os.environ.get("GH_TOKEN", "")

def gh(args):
    p = subprocess.run(["gh"] + args, capture_output=True, text=True,
                        env={**os.environ, "GH_TOKEN": TOKEN})
    return p.stdout

issues = [int(x) for x in sys.argv[1:]]
rows = []
for num in issues:
    prs = gh(["pr", "list", "--repo", "boykopovar/AnyPS5", "--state", "open",
              "--search", f"issues/{num}.github.com in:body", "--json",
              "number,title,state,author,additions,deletions,changedFiles"])
    prs = json.loads(prs) if prs.strip() else []
    rows.append((num, prs))

print(f"{'ISSUE':>6} {'PRs':>4}  TITLE")
for num, prs in rows:
    if prs:
        for pr in prs:
            print(f"{num:>6}  #{pr['number']:>4} OPEN by {pr['author']['login']:12} {pr['title'][:60]}")
    else:
        print(f"{num:>6}  (none)  open")
