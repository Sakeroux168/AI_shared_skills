#!/usr/bin/env python3
"""Validate registry, skill, source lock, attribution, and knowledge integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "gpt-image-2-style-library"
SOURCE_DIR = REPO_ROOT / "sources" / "awesome-gpt-image-2"
SNAPSHOT = SOURCE_DIR / "snapshot"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_skill_frontmatter() -> None:
    skill_file = SKILL_DIR / "SKILL.md"
    require(skill_file.is_file(), f"Missing {skill_file.relative_to(REPO_ROOT)}")
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    require(bool(match), "SKILL.md must start with YAML frontmatter")
    fields = []
    for line in match.group(1).splitlines():
        if line and not line.startswith((" ", "\t")) and ":" in line:
            fields.append(line.split(":", 1)[0])
    require(fields == ["name", "description"], "SKILL.md frontmatter must contain only name and description")
    require("name: gpt-image-2-style-library" in match.group(1), "Skill name mismatch")
    require(len(text.splitlines()) < 500, "SKILL.md exceeds the progressive-disclosure limit")


def validate_registries() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    skills_registry = load_json(REPO_ROOT / "registry" / "skills.json")
    sources_registry = load_json(REPO_ROOT / "registry" / "sources.json")
    lock = load_json(SOURCE_DIR / "source.lock.json")
    require(len(skills_registry["skills"]) == 1, "V1 must register exactly one professional skill")
    skill = skills_registry["skills"][0]
    source = sources_registry["sources"][0]

    required_skill_fields = {
        "name",
        "description",
        "source_repository",
        "upstream_branch",
        "upstream_commit",
        "local",
        "category",
        "capabilities",
        "dependencies",
        "knowledge_source",
        "update_strategy",
        "compatible_harnesses",
        "trust_status",
    }
    require(required_skill_fields <= set(skill), "Skill registry is missing required fields")
    require(skill["trust_status"] in {"trusted", "experimental", "disabled"}, "Invalid trust status")
    require(skill["local"]["status"] in {"active", "disabled"}, "Invalid local status")
    require(SHA_RE.fullmatch(skill["upstream_commit"]) is not None, "Invalid skill commit")
    require(source["sync_mode"] == "review", "Source must use review sync")
    require(source["license"]["spdx"] == "MIT", "Expected verified MIT source license")
    require(lock["sync_mode"] == "review", "Lock must use review sync")
    require(
        skill["upstream_commit"] == source["commit"] == lock["commit"],
        "Skill registry, source registry, and lock commits disagree",
    )
    expected_harnesses = {
        "Codex",
        "Claude Code",
        "Hermes",
        "DeepSeek Harness",
        "generic .agents/skills",
    }
    actual_harnesses = {item["name"] for item in skill["compatible_harnesses"]}
    require(actual_harnesses == expected_harnesses, "Harness compatibility matrix is incomplete")
    valid_harness_states = {"verified", "theoretical", "incompatible", "unknown"}
    require(
        all(item["status"] in valid_harness_states for item in skill["compatible_harnesses"]),
        "Invalid harness compatibility state",
    )
    return skill, source, lock


def validate_source(lock: dict[str, Any]) -> None:
    required = [
        SNAPSHOT / "data" / "style-library.json",
        SNAPSHOT / "data" / "cases.json",
        SNAPSHOT / "docs" / "templates.md",
        SNAPSHOT / "scripts" / "generate-style-skill.mjs",
        SNAPSHOT / "agents" / "skills" / "gpt-image-2-style-library" / "SKILL.md",
        SOURCE_DIR / "LICENSE",
        SOURCE_DIR / "case-images.lock.json",
    ]
    for path in required:
        require(path.is_file(), f"Missing source file: {path.relative_to(REPO_ROOT)}")

    license_text = (SOURCE_DIR / "LICENSE").read_text(encoding="utf-8")
    require("MIT License" in license_text, "Source license is not MIT")
    require("Copyright (c) 2026 freestylefly" in license_text, "Source copyright missing")

    library = load_json(SNAPSHOT / "data" / "style-library.json")
    cases = load_json(SNAPSHOT / "data" / "cases.json")
    templates_text = (SNAPSHOT / "docs" / "templates.md").read_text(encoding="utf-8")
    require(len(library["templates"]) == 22, "Unexpected template count")
    require(len(library["categories"]) == 13, "Unexpected category count")
    require(len(library["styles"]) == 19, "Unexpected style count")
    require(len(library["scenes"]) == 10, "Unexpected scene count")
    require(len(cases["cases"]) == cases["totalCases"] == 529, "Unexpected case count")

    template_ids = [item["id"] for item in library["templates"]]
    require(len(template_ids) == len(set(template_ids)), "Duplicate template ID")
    for template in library["templates"]:
        require(
            f'<a name="{template["anchor"]}"></a>' in templates_text,
            f"Missing full template anchor: {template['anchor']}",
        )
    for collection in (library["categories"], library["templates"]):
        for item in collection:
            cover = SNAPSHOT / "data" / item["cover"].removeprefix("/")
            require(cover.is_file(), f"Missing required cover: {item['cover']}")

    case_ids = {int(item["id"]) for item in cases["cases"]}
    for template in library["templates"]:
        missing = set(template.get("exampleCases", [])) - case_ids
        require(not missing, f"Template {template['id']} cites missing cases: {sorted(missing)}")

    manifest = load_json(SOURCE_DIR / "case-images.lock.json")
    require(manifest["commit"] == lock["commit"], "Case asset manifest commit disagrees with lock")
    require(manifest["asset_count"] == len(cases["cases"]), "Case asset manifest count mismatch")
    manifest_ids = {int(item["case_id"]) for item in manifest["assets"]}
    require(manifest_ids == case_ids, "Case asset manifest IDs disagree with cases.json")
    for asset in manifest["assets"]:
        require(SHA_RE.fullmatch(asset["blob_sha"]) is not None, "Invalid case image blob SHA")
        require(f"/{lock['commit']}/" in asset["raw_url"], "Case image URL is not immutable")
        if asset["vendored"]:
            require((SNAPSHOT / asset["path"]).is_file(), f"Vendored case image is missing: {asset['path']}")


def validate_active_skill(lock: dict[str, Any]) -> None:
    required = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "assets" / "city-life-system-map.png",
        SKILL_DIR / "references" / "style-library.md",
        SKILL_DIR / "references" / "source-knowledge.md",
    ]
    for path in required:
        require(path.is_file(), f"Missing active skill file: {path.relative_to(REPO_ROOT)}")
    reference = (SKILL_DIR / "references" / "style-library.md").read_text(encoding="utf-8")
    guide = (SKILL_DIR / "references" / "source-knowledge.md").read_text(encoding="utf-8")
    require("/blob/main/" not in reference, "Active reference contains a mutable main link")
    require("/raw/main/" not in reference, "Active reference contains a mutable raw main link")
    require(lock["commit"] in guide, "Source guide does not contain the locked commit")
    library = load_json(SNAPSHOT / "data" / "style-library.json")
    for template in library["templates"]:
        require(template["id"] in reference, f"Active reference omits {template['id']}")


def main() -> int:
    validate_skill_frontmatter()
    _, _, lock = validate_registries()
    validate_source(lock)
    validate_active_skill(lock)
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

