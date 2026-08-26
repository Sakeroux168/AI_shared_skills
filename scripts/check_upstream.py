#!/usr/bin/env python3
"""Compare the locked upstream commit with the configured remote branch."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "sources" / "awesome-gpt-image-2" / "source.lock.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_lock() -> dict[str, str]:
    with LOCK_PATH.open("r", encoding="utf-8") as handle:
        lock = json.load(handle)
    for key in ("repo", "branch", "commit"):
        if not lock.get(key):
            raise ValueError(f"Source lock is missing {key}")
    if not SHA_RE.fullmatch(lock["commit"]):
        raise ValueError("Source lock commit is not a full Git SHA")
    return lock


def remote_commit(repo: str, branch: str) -> str:
    completed = subprocess.run(
        ["git", "ls-remote", repo, f"refs/heads/{branch}"],
        check=True,
        capture_output=True,
        text=True,
    )
    fields = completed.stdout.strip().split()
    if len(fields) != 2 or not SHA_RE.fullmatch(fields[0]):
        raise RuntimeError(f"Unable to resolve {repo} branch {branch}")
    return fields[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--github-output",
        type=Path,
        default=Path(os.environ["GITHUB_OUTPUT"]) if os.environ.get("GITHUB_OUTPUT") else None,
        help="Append values to a GitHub Actions output file.",
    )
    args = parser.parse_args()

    lock = load_lock()
    remote = remote_commit(lock["repo"], lock["branch"])
    result = {
        "source_id": lock["source_id"],
        "repo": lock["repo"],
        "branch": lock["branch"],
        "locked_commit": lock["commit"],
        "remote_commit": remote,
        "update_available": remote != lock["commit"],
    }
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"locked_commit={lock['commit']}\n")
            handle.write(f"remote_commit={remote}\n")
            handle.write(f"update_available={str(result['update_available']).lower()}\n")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        state = "update available" if result["update_available"] else "up to date"
        print(f"{lock['source_id']}: {state} ({lock['commit']} -> {remote})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

