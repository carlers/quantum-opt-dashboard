"""Read-only review graph of GitHub pull requests; never merge, write or deploy.

The raw GitHub pull list is an input, not an instruction. This tool identifies
parent-before-child review ordering across stacked draft scientific PRs. It
neither asserts scientific correctness nor requires all branches be merged.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_REPO = "carlers/quantum-opt-dashboard"
ROOT_BRANCHES = frozenset({"main", "preview"})
PAGE_SIZE = 100
MAX_PAGES = 10


def from_github(repo: str = DEFAULT_REPO, token: str | None = None) -> list[dict]:
    """Fetch public PR metadata via GitHub's read-only REST endpoint.

    Never log credentials. Pagination is explicit: a partial graph is worse
    than refusing a review readiness claim.
    """
    if repo != DEFAULT_REPO:
        raise ValueError("This audit is explicitly scoped to the research repo")
    out: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        url = (f"https://api.github.com/repos/{repo}/pulls"
               f"?state=open&per_page={PAGE_SIZE}&page={page}")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "quantum-opt-scientific-review-readonly",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with urlopen(Request(url, headers=headers), timeout=20) as response:
                if response.status != 200:
                    raise ValueError("Unexpected GitHub PR list response status")
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("Unable to obtain complete read-only PR listing") from exc
        if not isinstance(data, list):
            raise ValueError("GitHub PR response is not an array")
        out.extend(data)
        if len(data) < PAGE_SIZE:
            return out
    raise ValueError("PR audit exceeded bounded API pagination; incomplete graph")


def normalize(raw: list[dict], repo: str = DEFAULT_REPO) -> list[dict]:
    if not isinstance(raw, list):
        raise ValueError("Expected a list of GitHub PR objects")
    out = []
    numbers: set[int] = set()
    heads: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or item.get("state", "open") != "open":
            raise ValueError("Audit must receive open PR objects only")
        try:
            number = item["number"]
            title = item["title"]
            head = item["head"]["ref"]
            base = item["base"]["ref"]
        except (KeyError, TypeError) as exc:
            raise ValueError("Incomplete PR number/title/head/base metadata") from exc
        if (not isinstance(number, int) or isinstance(number, bool)
                or number < 1 or not isinstance(title, str) or not title.strip()
                or not isinstance(head, str) or not head.strip()
                or not isinstance(base, str) or not base.strip()):
            raise ValueError("Invalid PR identity or branch")
        if number in numbers:
            raise ValueError("Duplicate PR number")
        if head in heads:
            raise ValueError("More than one open PR uses the same source head branch")
        if head == base:
            raise ValueError("PR cannot target its own source branch")
        head_repo = item.get("head", {}).get("repo") or {}
        base_repo = item.get("base", {}).get("repo") or {}
        # Synthetic offline fixtures may omit repo metadata; live results must
        # keep fork status visible rather than pretending references match.
        head_repo_name = head_repo.get("full_name", repo)
        base_repo_name = base_repo.get("full_name", repo)
        if base_repo_name != repo:
            raise ValueError("Unexpected repository as base for scientific PR audit")
        numbers.add(number)
        heads.add(head)
        out.append({
            "number": number, "title": title, "head": head, "base": base,
            "draft": bool(item.get("draft", False)),
            "html_url": item.get("html_url") or
                        f"https://github.com/{repo}/pull/{number}",
            "head_repository": head_repo_name,
        })
    return out


def audit_open_prs(raw: list[dict], repo: str = DEFAULT_REPO) -> dict:
    prs = normalize(raw, repo)
    by_head = {pr["head"]: pr for pr in prs if pr["head_repository"] == repo}
    by_number = {pr["number"]: pr for pr in prs}
    memo: dict[int, tuple[int, int, list[int]]] = {}
    visiting: set[int] = set()

    def lineage(number: int) -> tuple[int, int, list[int]]:
        if number in memo:
            return memo[number]
        if number in visiting:
            raise ValueError("Cycle found among stacked PR bases; stop review")
        visiting.add(number)
        node = by_number[number]
        parent = by_head.get(node["base"])
        if parent is None:
            result = (0, number, [number])
        else:
            depth, root_number, path = lineage(parent["number"])
            result = (depth + 1, root_number, [*path, number])
        visiting.remove(number)
        memo[number] = result
        return result

    for p in prs:
        lineage(p["number"])

    # Topological reviewer order: all ancestors precede descendants.
    order = sorted(prs, key=lambda p: (memo[p["number"]][0], p["number"]))
    families: dict[int, dict] = {}
    for p in order:
        _, root, _ = memo[p["number"]]
        families.setdefault(root, {
            "root_pr": root,
            "root_base": by_number[root]["base"],
            "members_in_review_order": [],
        })["members_in_review_order"].append(p["number"])

    findings = []
    for p in order:
        depth, root, path = memo[p["number"]]
        if p["base"] not in ROOT_BRANCHES and p["base"] not in by_head:
            findings.append({
                "severity": "review",
                "number": p["number"],
                "kind": "unrepresented_base_branch",
                "base": p["base"],
                "note": ("Base is not among open PR heads or recognized stable roots. "
                         "It may exist but needs human verification; do not assume missing."),
            })
        if p["head_repository"] != repo:
            findings.append({
                "severity": "review", "number": p["number"],
                "kind": "external_head",
                "note": "Head is in a fork; branch-ref matching was not assumed.",
            })
        if depth > 0:
            parent = by_head.get(p["base"])
            if parent and parent["draft"] and not p["draft"]:
                findings.append({
                    "severity": "review", "number": p["number"],
                    "kind": "ready_child_of_draft_parent",
                    "parent": parent["number"],
                    "note": "Human approval required; green child CI does not approve parent.",
                })
    return {
        "schema_version": 1,
        "repository": repo,
        "scope": "open GitHub pull requests; read-only metadata",
        "total_open_prs": len(prs),
        "draft_prs": sum(p["draft"] for p in prs),
        "non_draft_prs": sum(not p["draft"] for p in prs),
        "family_count": len(families),
        # A stack is a branching DAG: the number of relatives is NOT its
        # deepest parent→child chain length (e.g. historical SA and UI fork).
        "longest_stack_pr_count": max(
            (depth + 1 for depth, _, _ in memo.values()),
            default=0,
        ),
        "largest_stack_family_members": max(
            (len(f["members_in_review_order"]) for f in families.values()),
            default=0,
        ),
        "families": [families[n] for n in sorted(families)],
        "review_order": [{
            **p,
            "stack_depth_from_root": memo[p["number"]][0],
            "root_pr": memo[p["number"]][1],
            "ancestor_chain_including_self": memo[p["number"]][2],
            "parent_pr": (
                by_head[p["base"]]["number"] if p["base"] in by_head else None
            ),
        } for p in order],
        "review_findings": findings,
        "interpretation_limits": [
            "PR graph integrity says nothing about correctness, licensing, or mergeability",
            "A draft child can be tested without its parent being approved for main",
            "Review order is not permission to merge any of these branches",
            "A base not represented by an open PR may still be a valid existing branch",
        ],
    }


def markdown_summary(report: dict) -> str:
    lines = [
        "# Open scientific and dashboard PR stack — review-only snapshot",
        "",
        ("Automated **read-only** audit. GitHub PR metadata is ephemeral: "
         "refresh before any reviewer or branch decisions."),
        "",
        f"- Open PRs: **{report['total_open_prs']}**; "
        f"draft: **{report['draft_prs']}**.",
        f"- Separate root stacks: **{report['family_count']}**; "
        f"deepest lineage: **{report['longest_stack_pr_count']}** PRs; "
        f"largest family: **{report['largest_stack_family_members']}** PRs.",
        "- This report does **not** merge, approve or validate scientific outputs.",
        "",
        "## Parent-before-child review order",
        "",
    ]
    for family in report["families"]:
        lines.append(
            f"### Root [PR #{family['root_pr']}]"
            f"(https://github.com/{report['repository']}/pull/{family['root_pr']})"
            f" (base: \`{family['root_base']}\`)"
        )
        lines.append("")
        for pr in report["review_order"]:
            if pr["root_pr"] != family["root_pr"]:
                continue
            label = "draft" if pr["draft"] else "ready"
            lines.append(
                f"- {'  ' * pr['stack_depth_from_root']}"
                f"[#{pr['number']}]({pr['html_url']})"
                f" — {pr['title']} ({label}; parent: "
                f"{'#' + str(pr['parent_pr']) if pr['parent_pr'] else pr['base']})"
            )
        lines.append("")
    lines.extend(["## Review warnings", ""])
    if report["review_findings"]:
        for finding in report["review_findings"]:
            lines.append(
                f"- PR #{finding['number']}: {finding['kind']} — {finding['note']}"
            )
    else:
        lines.append("No missing-parent or draft-ready structural warnings detected.")
    lines.extend([
        "", "**Next steps:** review from parents toward children; validate"
        " independent N20 and historical QUBO science; get owner/adviser"
        " permission before any merge, deployment, or manuscript corrections.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true",
                        help="Read GitHub PR list through public GET API only")
    source.add_argument("--input", type=Path,
                        help="Offline GitHub PR list JSON; no network")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    options = parser.parse_args()
    raw = (from_github(token=os.environ.get("GITHUB_TOKEN"))
           if options.live else json.loads(options.input.read_text(encoding="utf-8")))
    result = audit_open_prs(raw)
    if options.json_output:
        if options.json_output.exists():
            raise FileExistsError("Will not overwrite an existing research PR audit")
        options.json_output.parent.mkdir(parents=True, exist_ok=True)
        options.json_output.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    if options.markdown_output:
        if options.markdown_output.exists():
            raise FileExistsError("Will not overwrite an existing research review report")
        options.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        options.markdown_output.write_text(
            markdown_summary(result), encoding="utf-8"
        )
    print(json.dumps({
        "total_open": result["total_open_prs"],
        "draft": result["draft_prs"],
        "stacks": result["family_count"],
        "deepest": result["longest_stack_pr_count"],
        "review_warnings": len(result["review_findings"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
