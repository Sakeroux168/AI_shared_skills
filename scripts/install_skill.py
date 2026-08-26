#!/usr/bin/env python3
"""Safely copy a registered skill into an explicit harness skill root."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"


def default_target_root(target: str) -> Path:
    home = Path.home()
    if target == "codex":
        base = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    elif target == "claude-code":
        base = Path(os.environ.get("CLAUDE_HOME", home / ".claude"))
    elif target == "agents":
        base = Path(os.environ.get("AGENTS_HOME", home / ".agents"))
    else:
        raise ValueError(f"Unsupported target: {target}")
    return base / "skills"


def assert_safe_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    forbidden = {
        Path(resolved.anchor),
        Path.home().resolve(),
        REPO_ROOT.resolve(),
        REPO_ROOT.parent.resolve(),
    }
    if resolved in forbidden:
        raise ValueError(f"Refusing broad installation root: {resolved}")
    return resolved


def install_one(skill_name: str, root: Path, *, force: bool, dry_run: bool) -> dict[str, str | None]:
    source = SKILLS_ROOT / skill_name
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"Registered skill is missing SKILL.md: {source}")
    root = assert_safe_root(root)
    target = root / skill_name
    backup: Path | None = None

    if target.exists():
        if not force:
            raise FileExistsError(
                f"Target already exists: {target}. Re-run with --force to preserve a backup and replace it."
            )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = root / f"{skill_name}.backup-{stamp}"
        if backup.exists():
            raise FileExistsError(f"Backup path already exists: {backup}")

    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.replace(backup)
        try:
            shutil.copytree(source, target)
        except Exception:
            if backup and backup.exists() and not target.exists():
                backup.replace(target)
            raise
        if not (target / "SKILL.md").is_file():
            raise RuntimeError(f"Installation verification failed: {target}")

    return {
        "skill": skill_name,
        "source": str(source),
        "target": str(target),
        "backup": str(backup) if backup else None,
        "mode": "dry-run" if dry_run else "copied",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_name")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument(
        "--target",
        choices=["codex", "claude-code", "agents", "all"],
        help="Use a known local skill root.",
    )
    destination.add_argument(
        "--target-root",
        type=Path,
        help="Exact verified directory that contains skill folders.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.target_root:
        roots = [args.target_root]
    else:
        names = ["codex", "claude-code", "agents"] if args.target == "all" else [args.target]
        roots = [default_target_root(name) for name in names]

    results = [
        install_one(args.skill_name, root, force=args.force, dry_run=args.dry_run)
        for root in roots
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

