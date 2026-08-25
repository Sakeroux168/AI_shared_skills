#!/usr/bin/env python3
"""Refresh the curated awesome-gpt-image-2 snapshot on a review branch."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "sources" / "awesome-gpt-image-2"
LOCK_PATH = SOURCE_DIR / "source.lock.json"
SNAPSHOT_DIR = SOURCE_DIR / "snapshot"
ACTIVE_SKILL_DIR = REPO_ROOT / "skills" / "gpt-image-2-style-library"
SKILLS_REGISTRY = REPO_ROOT / "registry" / "skills.json"
SOURCES_REGISTRY = REPO_ROOT / "registry" / "sources.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CURATED_PATHS = [
    ".github/workflows/publish-style-skill.yml",
    "LICENSE",
    "README.md",
    "README.zh-CN.md",
    "package.json",
    "agents/skills/gpt-image-2-style-library/SKILL.md",
    "agents/skills/gpt-image-2-style-library/agents/openai.yaml",
    "agents/skills/gpt-image-2-style-library/assets/city-life-system-map.png",
    "agents/skills/gpt-image-2-style-library/bin/install.mjs",
    "agents/skills/gpt-image-2-style-library/package.json",
    "agents/skills/gpt-image-2-style-library/references/style-library.md",
    "data/cases.json",
    "data/style-library.json",
    "docs/templates.md",
    "scripts/generate-style-skill.mjs",
    "scripts/install-style-skill.mjs",
]

DOCS_WITH_LOCK = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "SKILLS.md",
    REPO_ROOT / "SOURCES.md",
    REPO_ROOT / "THIRD_PARTY_NOTICES.md",
]


def run(command: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def run_bytes(command: list[str], *, cwd: Path | None = None) -> bytes:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def assert_review_branch(allow_default_branch: bool) -> str:
    branch = run(["git", "branch", "--show-current"], cwd=REPO_ROOT).strip()
    if not branch:
        raise RuntimeError("Synchronization requires a named Git branch")
    if branch in {"main", "master"} and not allow_default_branch:
        raise RuntimeError("Refusing to synchronize on the default branch")
    return branch


def assert_clean(allow_dirty: bool) -> None:
    if allow_dirty:
        return
    status = run(["git", "status", "--porcelain"], cwd=REPO_ROOT)
    if status.strip():
        raise RuntimeError("Working tree is not clean; commit or stash before synchronization")


def ensure_checkout(repo: str, branch: str, commit: str, source_checkout: Path | None):
    if source_checkout:
        checkout = source_checkout.resolve()
        run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=checkout)
        yield checkout
        return

    with tempfile.TemporaryDirectory(prefix="ai-shared-upstream-") as temp:
        checkout = Path(temp) / "upstream"
        run(["git", "clone", "--filter=blob:none", "--no-checkout", repo, str(checkout)])
        try:
            run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=checkout)
        except subprocess.CalledProcessError:
            run(["git", "fetch", "--depth=1", "origin", commit], cwd=checkout)
        yield checkout


def git_file(checkout: Path, commit: str, path: str) -> bytes:
    return run_bytes(["git", "show", f"{commit}:{path}"], cwd=checkout)


def tree_blobs(checkout: Path, commit: str, prefix: str) -> dict[str, str]:
    raw = run_bytes(["git", "ls-tree", "-r", "-z", commit, "--", prefix], cwd=checkout)
    result: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        _, object_type, sha = metadata.decode("ascii").split()
        if object_type == "blob":
            result[path_bytes.decode("utf-8")] = sha
    return result


def write_snapshot(
    checkout: Path,
    commit: str,
    *,
    with_case_images: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="snapshot-", dir=SOURCE_DIR) as temp:
        staging = Path(temp) / "snapshot"
        for path in CURATED_PATHS:
            destination = staging / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(git_file(checkout, commit, path))

        library = load_json(staging / "data" / "style-library.json")
        cases = load_json(staging / "data" / "cases.json")
        essential_images = {
            "agents/skills/gpt-image-2-style-library/assets/city-life-system-map.png"
        }
        for collection in (library["categories"], library["templates"]):
            for item in collection:
                cover = item["cover"].removeprefix("/images/")
                essential_images.add(f"data/images/{cover}")
        if with_case_images:
            essential_images.update(
                f"data/{case['image'].removeprefix('/')}" for case in cases["cases"]
            )
        for path in sorted(essential_images):
            destination = staging / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(git_file(checkout, commit, path))

        backup = SOURCE_DIR / ".snapshot.previous"
        if backup.exists():
            shutil.rmtree(backup)
        if SNAPSHOT_DIR.exists():
            SNAPSHOT_DIR.replace(backup)
        staging.replace(SNAPSHOT_DIR)
        if backup.exists():
            shutil.rmtree(backup)

    blobs = tree_blobs(checkout, commit, "data/images")
    raw_root = "https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2"
    entries = []
    for case in cases["cases"]:
        path = f"data/{case['image'].removeprefix('/')}"
        if path not in blobs:
            raise RuntimeError(f"Case image is absent from locked Git tree: {path}")
        entries.append(
            {
                "case_id": case["id"],
                "path": path,
                "blob_sha": blobs[path],
                "vendored": (SNAPSHOT_DIR / path).is_file(),
                "raw_url": f"{raw_root}/{commit}/{path}",
            }
        )
    manifest = {
        "schema_version": "1.0.0",
        "source_id": "awesome-gpt-image-2",
        "commit": commit,
        "asset_count": len(entries),
        "assets": entries,
    }
    write_json(SOURCE_DIR / "case-images.lock.json", manifest)
    shutil.copy2(SNAPSHOT_DIR / "LICENSE", SOURCE_DIR / "LICENSE")
    return library, cases


def update_active_skill(commit: str) -> None:
    ACTIVE_SKILL_DIR.mkdir(parents=True, exist_ok=True)
    upstream_skill = SNAPSHOT_DIR / "agents" / "skills" / "gpt-image-2-style-library"
    for relative in [
        Path("agents/openai.yaml"),
        Path("assets/city-life-system-map.png"),
    ]:
        destination = ACTIVE_SKILL_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(upstream_skill / relative, destination)

    reference = (upstream_skill / "references" / "style-library.md").read_text(encoding="utf-8")
    reference = reference.replace(
        "https://github.com/freestylefly/awesome-gpt-image-2/blob/main/",
        f"https://github.com/freestylefly/awesome-gpt-image-2/blob/{commit}/",
    )
    if "## Contents\n" not in reference:
        reference = reference.replace(
            "## Selection Rules\n",
            "## Contents\n\n"
            "- [Selection Rules](#selection-rules)\n"
            "- [Template Index](#template-index)\n"
            "- [Categories](#categories)\n"
            "- [Styles](#styles)\n"
            "- [Scenes](#scenes)\n\n"
            "## Selection Rules\n",
            1,
        )
    reference_path = ACTIVE_SKILL_DIR / "references" / "style-library.md"
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_text(reference, encoding="utf-8")

    guide = f"""# Source knowledge lookup

The active source is freestylefly/awesome-gpt-image-2, branch main, commit {commit}.

## Repository checkout

From this skill directory, the complete managed knowledge is available at:

- ../../sources/awesome-gpt-image-2/snapshot/docs/templates.md
- ../../sources/awesome-gpt-image-2/snapshot/data/style-library.json
- ../../sources/awesome-gpt-image-2/snapshot/data/cases.json
- ../../sources/awesome-gpt-image-2/case-images.lock.json

Use style-library.json for exact IDs and tag values. Use templates.md for full reusable prompt templates and pitfalls. Use cases.json to find close examples and their original source attribution. The case image manifest distinguishes vendored covers from optional remotely managed images.

## Standalone immutable fallbacks

- Templates: https://github.com/freestylefly/awesome-gpt-image-2/blob/{commit}/docs/templates.md
- Structured library: https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/{commit}/data/style-library.json
- Cases: https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/{commit}/data/cases.json
- Upstream skill: https://github.com/freestylefly/awesome-gpt-image-2/tree/{commit}/agents/skills/gpt-image-2-style-library
- License: https://github.com/freestylefly/awesome-gpt-image-2/blob/{commit}/LICENSE

Do not replace the commit with main. The controlled sync script regenerates this file and the compact reference in the same review branch.
"""
    (ACTIVE_SKILL_DIR / "references" / "source-knowledge.md").write_text(
        guide, encoding="utf-8"
    )


def update_registries(old_commit: str, commit: str) -> None:
    skills = load_json(SKILLS_REGISTRY)
    skill = next(item for item in skills["skills"] if item["name"] == "gpt-image-2-style-library")
    skill["upstream_commit"] = commit
    write_json(SKILLS_REGISTRY, skills)

    sources = load_json(SOURCES_REGISTRY)
    source = next(item for item in sources["sources"] if item["id"] == "awesome-gpt-image-2")
    source["commit"] = commit
    write_json(SOURCES_REGISTRY, sources)

    for path in DOCS_WITH_LOCK:
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old_commit, commit), encoding="utf-8")


def write_report(
    checkout: Path,
    old_commit: str,
    commit: str,
    branch: str,
    library: dict[str, Any],
    cases: dict[str, Any],
    with_case_images: bool,
) -> Path:
    now = datetime.now(timezone.utc)
    label = "initial" if old_commit == commit else f"{old_commit[:12]}-to-{commit[:12]}"
    report_path = REPO_ROOT / "reports" / "sync" / f"{now.date().isoformat()}-{label}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    changes = "Initial curated snapshot at the already selected lock."
    if old_commit != commit:
        try:
            changes = run(
                ["git", "diff", "--name-status", old_commit, commit, "--", *CURATED_PATHS],
                cwd=checkout,
            ).strip() or "No allowlisted path changed."
        except subprocess.CalledProcessError:
            changes = "Unable to compute the old-to-new allowlist diff; review the branch diff."
    content = f"""# Upstream synchronization report

- Source: freestylefly/awesome-gpt-image-2
- Branch: main
- Previous commit: {old_commit}
- New commit: {commit}
- Local review branch: {branch}
- Generated: {now.isoformat()}
- Full case image hydration: {str(with_case_images).lower()}

## Knowledge counts

- Templates: {len(library['templates'])}
- Categories: {len(library['categories'])}
- Style tags: {len(library['styles'])}
- Scene tags: {len(library['scenes'])}
- Case prompts: {len(cases['cases'])}

## Allowlisted upstream changes

    {changes.replace(chr(10), chr(10) + '    ')}

## Required review

- Inspect upstream SKILL.md and generator changes against the active integration skill.
- Inspect template/category/tag changes and case additions or removals.
- Run repository validation and the five prompt acceptance scenarios.
- Keep the skill experimental when a required acceptance item is not complete.
- Open a draft PR; do not merge automatically.
"""
    report_path.write_text(content, encoding="utf-8")
    return report_path


def synchronize(args: argparse.Namespace) -> Path:
    if not SHA_RE.fullmatch(args.to_commit):
        raise ValueError("--to-commit must be a full 40-character lowercase Git SHA")
    branch = assert_review_branch(args.allow_default_branch)
    assert_clean(args.allow_dirty)
    lock = load_json(LOCK_PATH)
    old_commit = lock["commit"]

    checkout_context = ensure_checkout(
        lock["repo"],
        lock["branch"],
        args.to_commit,
        args.source_checkout,
    )
    for checkout in checkout_context:
        resolved = run(["git", "rev-parse", args.to_commit], cwd=checkout).strip()
        if resolved != args.to_commit:
            raise RuntimeError(f"Requested commit did not resolve exactly: {resolved}")
        library, cases = write_snapshot(
            checkout,
            args.to_commit,
            with_case_images=args.with_case_images,
        )
        update_active_skill(args.to_commit)
        update_registries(old_commit, args.to_commit)
        lock["commit"] = args.to_commit
        lock["synced_at"] = datetime.now(timezone.utc).isoformat()
        write_json(LOCK_PATH, lock)
        return write_report(
            checkout,
            old_commit,
            args.to_commit,
            branch,
            library,
            cases,
            args.with_case_images,
        )
    raise RuntimeError("Unable to prepare an upstream checkout")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to-commit", required=True)
    parser.add_argument("--source-checkout", type=Path)
    parser.add_argument("--with-case-images", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--allow-default-branch", action="store_true")
    args = parser.parse_args()
    report = synchronize(args)
    print(f"Synchronized curated source; review report: {report.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
