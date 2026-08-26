#!/usr/bin/env python3
"""Validate registries, skills, source locks, rights metadata, and knowledge integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_SKILL_NAME = "gpt-image-2-style-library"
TARGET_SOURCE_ID = "awesome-gpt-image-2"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_HARNESSES = {
    "Codex",
    "Claude Code",
    "Hermes",
    "DeepSeek Harness",
    "generic .agents/skills",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source_directory(source: dict[str, Any], repo_root: Path) -> Path:
    snapshot_path = Path(source["snapshot"]["path"])
    require(not snapshot_path.is_absolute(), f"Source {source['id']} snapshot path must be relative")
    require(".." not in snapshot_path.parts, f"Source {source['id']} snapshot path escapes repository")
    return repo_root / snapshot_path.parent


def validate_skill_frontmatter(
    skill_name: str = TARGET_SKILL_NAME,
    repo_root: Path = REPO_ROOT,
) -> None:
    skill_file = repo_root / "skills" / skill_name / "SKILL.md"
    require(skill_file.is_file(), f"Missing {skill_file.relative_to(repo_root)}")
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    require(bool(match), f"{skill_name}/SKILL.md must start with YAML frontmatter")
    fields = []
    for line in match.group(1).splitlines():
        if line and not line.startswith((" ", "\t")) and ":" in line:
            fields.append(line.split(":", 1)[0])
    require(
        fields == ["name", "description"],
        f"{skill_name}/SKILL.md frontmatter must contain only name and description",
    )
    require(f"name: {skill_name}" in match.group(1), f"Skill name mismatch: {skill_name}")
    require(len(text.splitlines()) < 500, f"{skill_name}/SKILL.md exceeds progressive-disclosure limit")


def require_repository_file(path_text: str, repo_root: Path, label: str) -> None:
    path = Path(path_text)
    require(not path.is_absolute(), f"{label} path must be relative")
    require(".." not in path.parts, f"{label} path escapes repository")
    require((repo_root / path).is_file(), f"{label} file does not exist: {path_text}")


def validate_rights_model(source: dict[str, Any], repo_root: Path) -> None:
    license_record = source["license"]
    repository_license = license_record.get("repository_license", {})
    require(bool(repository_license.get("spdx")), "Source repository license identifier is missing")
    require(bool(repository_license.get("file")), "Repository license file is not recorded")
    require(bool(repository_license.get("verified_from")), "Repository license verification source is missing")
    require_repository_file(repository_license["file"], repo_root, "Repository license")

    content_rights = license_record.get("content_rights", {})
    require(
        content_rights.get("status")
        in {"repository-license-applies", "mixed", "separate-or-unknown"},
        "Content-rights status must be explicit; third-party content must not be blanket-declared",
    )
    require(bool(content_rights.get("upstream_disclaimer")), "Upstream disclaimer path is missing")
    require(bool(content_rights.get("commercial_use")), "Commercial-use rights guidance is missing")
    require(bool(content_rights.get("attribution")), "Third-party attribution policy is missing")
    require_repository_file(content_rights["upstream_disclaimer"], repo_root, "Upstream disclaimer")


def validate_trust_state(skill: dict[str, Any], repo_root: Path) -> None:
    name = skill["name"]
    if skill["trust_status"] == "trusted":
        require("trust_review" not in skill, f"Trusted skill still has a pending trust review: {name}")
        attestation = skill.get("trust_attestation", {})
        require(bool(attestation), f"Trusted skill is missing a trust attestation: {name}")
        require(
            attestation.get("skill_name") == name,
            f"Trust attestation belongs to a different Skill: {name}",
        )
        require(
            attestation.get("accepted_commit") == skill["upstream_commit"],
            f"Trusted skill acceptance is not bound to its current upstream commit: {name}",
        )
        report_path = attestation.get("acceptance_report")
        require(bool(report_path), f"Trusted skill acceptance report is missing: {name}")
        require_repository_file(report_path, repo_root, f"Trust acceptance report for {name}")
        report_text = (repo_root / report_path).read_text(encoding="utf-8")
        require(
            skill["upstream_commit"] in report_text,
            f"Trust acceptance report does not identify the accepted commit: {name}",
        )
        require(
            name in report_text,
            f"Trust acceptance report does not identify the accepted Skill: {name}",
        )
    elif "trust_review" in skill:
        review = skill["trust_review"]
        require(
            skill["trust_status"] == "experimental",
            f"Pending trust review requires experimental status: {name}",
        )
        require(
            review.get("required_after_commit") == skill["upstream_commit"],
            f"Pending trust review is not bound to the current upstream commit: {name}",
        )


def validate_registries(
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    skills_registry = load_json(repo_root / "registry" / "skills.json")
    sources_registry = load_json(repo_root / "registry" / "sources.json")
    skills = skills_registry.get("skills")
    sources = sources_registry.get("sources")
    require(isinstance(skills, list), "Skill registry skills must be an array")
    require(isinstance(sources, list), "Source registry sources must be an array")

    skill_names = [item.get("name") for item in skills]
    source_ids = [item.get("id") for item in sources]
    require(len(skill_names) == len(set(skill_names)), "Duplicate skill registry name")
    require(len(source_ids) == len(set(source_ids)), "Duplicate source registry ID")
    source_map = {item["id"]: item for item in sources}
    locks: dict[str, dict[str, Any]] = {}

    required_source_fields = {
        "id",
        "repository",
        "branch",
        "commit",
        "sync_mode",
        "license",
        "author",
        "snapshot",
        "update_strategy",
    }
    for source in sources:
        require(required_source_fields <= set(source), f"Source {source.get('id')} is missing required fields")
        require(SHA_RE.fullmatch(source["commit"]) is not None, f"Invalid source commit: {source['id']}")
        require(source["sync_mode"] == "review", f"Source {source['id']} must use review sync")
        validate_rights_model(source, repo_root)
        if source["id"] == TARGET_SOURCE_ID:
            require(
                source["license"]["content_rights"]["status"] == "separate-or-unknown",
                f"{TARGET_SOURCE_ID} community content cannot inherit the repository license as a blanket",
            )
        lock_path = source_directory(source, repo_root) / "source.lock.json"
        require(lock_path.is_file(), f"Missing source lock: {lock_path.relative_to(repo_root)}")
        lock = load_json(lock_path)
        require(lock.get("source_id") == source["id"], f"Source lock ID mismatch: {source['id']}")
        require(lock.get("sync_mode") == "review", f"Source lock must use review sync: {source['id']}")
        require(lock.get("commit") == source["commit"], f"Source registry and lock commits disagree: {source['id']}")
        locks[source["id"]] = lock

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
    valid_harness_states = {"verified", "theoretical", "incompatible", "unknown"}
    for skill in skills:
        name = skill.get("name", "<unnamed>")
        require(required_skill_fields <= set(skill), f"Skill {name} is missing required fields")
        require(skill["trust_status"] in {"trusted", "experimental", "disabled"}, f"Invalid trust status: {name}")
        require(skill["local"]["status"] in {"active", "disabled"}, f"Invalid local status: {name}")
        require(SHA_RE.fullmatch(skill["upstream_commit"]) is not None, f"Invalid skill commit: {name}")
        require(
            {"source_id", "bundled_reference", "source_guide"}
            <= set(skill["knowledge_source"]),
            f"Skill knowledge source is missing required paths: {name}",
        )
        source_id = skill["knowledge_source"].get("source_id")
        require(source_id in source_map, f"Skill {name} references unknown source: {source_id}")
        source = source_map[source_id]
        require(
            skill["upstream_commit"] == source["commit"] == locks[source_id]["commit"],
            f"Skill, source registry, and lock commits disagree: {name}",
        )
        actual_harnesses = {item["name"] for item in skill["compatible_harnesses"]}
        require(EXPECTED_HARNESSES <= actual_harnesses, f"Harness compatibility matrix is incomplete: {name}")
        require(
            all(item["status"] in valid_harness_states for item in skill["compatible_harnesses"]),
            f"Invalid harness compatibility state: {name}",
        )
        validate_trust_state(skill, repo_root)

    return skills_registry, sources_registry, locks


def validate_registered_skill_directories(
    skills_registry: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    for skill in skills_registry["skills"]:
        skill_dir = repo_root / "skills" / skill["name"]
        if skill["local"]["status"] == "active" or skill_dir.exists():
            validate_skill_frontmatter(skill["name"], repo_root)
        if skill["local"]["status"] != "active":
            continue
        for key, path_text in skill["knowledge_source"].items():
            if key == "source_id":
                continue
            require(isinstance(path_text, str), f"Knowledge path must be a string: {skill['name']}.{key}")
            require_repository_file(
                path_text,
                repo_root,
                f"Knowledge source {skill['name']}.{key}",
            )
        for key in ("bundled_reference", "source_guide"):
            path = Path(skill["knowledge_source"][key])
            require(
                path.parts[:2] == ("skills", skill["name"]),
                f"{skill['name']} {key} must belong to its own Skill directory",
            )


def validate_source(
    lock: dict[str, Any],
    repo_root: Path = REPO_ROOT,
    source_id: str = TARGET_SOURCE_ID,
) -> None:
    source_dir = repo_root / "sources" / source_id
    snapshot = source_dir / "snapshot"
    required = [
        snapshot / "data" / "style-library.json",
        snapshot / "data" / "cases.json",
        snapshot / "docs" / "templates.md",
        snapshot / "docs" / "disclaimer.md",
        snapshot / "scripts" / "generate-style-skill.mjs",
        snapshot / "agents" / "skills" / TARGET_SKILL_NAME / "SKILL.md",
        source_dir / "LICENSE",
        source_dir / "case-images.lock.json",
    ]
    for path in required:
        require(path.is_file(), f"Missing source file: {path.relative_to(repo_root)}")

    license_text = (source_dir / "LICENSE").read_text(encoding="utf-8")
    require("MIT License" in license_text, "Upstream repository license is not MIT")
    require("Copyright (c) 2026 freestylefly" in license_text, "Upstream repository copyright missing")
    disclaimer = (snapshot / "docs" / "disclaimer.md").read_text(encoding="utf-8")
    require(bool(disclaimer.strip()), "Upstream disclaimer is empty")

    library = load_json(snapshot / "data" / "style-library.json")
    cases = load_json(snapshot / "data" / "cases.json")
    templates_text = (snapshot / "docs" / "templates.md").read_text(encoding="utf-8")
    for key in ("templates", "categories", "styles", "scenes"):
        require(isinstance(library.get(key), list), f"style-library.json {key} must be an array")
        require(bool(library[key]), f"style-library.json {key} must not be empty")
    require(isinstance(cases.get("cases"), list), "cases.json cases must be an array")
    require(cases.get("totalCases") == len(cases["cases"]), "cases.json totalCases mismatch")

    template_ids = [item["id"] for item in library["templates"]]
    require(len(template_ids) == len(set(template_ids)), "Duplicate template ID")
    case_ids_list = [int(item["id"]) for item in cases["cases"]]
    require(len(case_ids_list) == len(set(case_ids_list)), "Duplicate case ID")
    for template in library["templates"]:
        require(
            f'<a name="{template["anchor"]}"></a>' in templates_text,
            f"Missing full template anchor: {template['anchor']}",
        )
    for collection in (library["categories"], library["templates"]):
        for item in collection:
            cover = snapshot / "data" / item["cover"].removeprefix("/")
            require(cover.is_file(), f"Missing required cover: {item['cover']}")

    case_ids = set(case_ids_list)
    for template in library["templates"]:
        missing = set(template.get("exampleCases", [])) - case_ids
        require(not missing, f"Template {template['id']} cites missing cases: {sorted(missing)}")

    manifest = load_json(source_dir / "case-images.lock.json")
    require(manifest["commit"] == lock["commit"], "Case asset manifest commit disagrees with lock")
    require(manifest["asset_count"] == len(cases["cases"]), "Case asset manifest count mismatch")
    manifest_ids = {int(item["case_id"]) for item in manifest["assets"]}
    require(manifest_ids == case_ids, "Case asset manifest IDs disagree with cases.json")
    for asset in manifest["assets"]:
        require(SHA_RE.fullmatch(asset["blob_sha"]) is not None, "Invalid case image blob SHA")
        require(f"/{lock['commit']}/" in asset["raw_url"], "Case image URL is not immutable")
        if asset["vendored"]:
            require((snapshot / asset["path"]).is_file(), f"Vendored case image is missing: {asset['path']}")


def validate_active_skill(
    lock: dict[str, Any],
    repo_root: Path = REPO_ROOT,
    skill_name: str = TARGET_SKILL_NAME,
    source_id: str = TARGET_SOURCE_ID,
) -> None:
    skill_dir = repo_root / "skills" / skill_name
    required = [
        skill_dir / "SKILL.md",
        skill_dir / "agents" / "openai.yaml",
        skill_dir / "assets" / "city-life-system-map.png",
        skill_dir / "references" / "style-library.md",
        skill_dir / "references" / "source-knowledge.md",
    ]
    for path in required:
        require(path.is_file(), f"Missing active skill file: {path.relative_to(repo_root)}")
    reference = (skill_dir / "references" / "style-library.md").read_text(encoding="utf-8")
    guide = (skill_dir / "references" / "source-knowledge.md").read_text(encoding="utf-8")
    require("/blob/main/" not in reference, "Active reference contains a mutable main link")
    require("/raw/main/" not in reference, "Active reference contains a mutable raw main link")
    require(lock["commit"] in guide, "Source guide does not contain the locked commit")
    library = load_json(repo_root / "sources" / source_id / "snapshot" / "data" / "style-library.json")
    for template in library["templates"]:
        require(template["id"] in reference, f"Active reference omits {template['id']}")


def main() -> int:
    skills_registry, _, locks = validate_registries()
    validate_registered_skill_directories(skills_registry)
    if TARGET_SOURCE_ID in locks:
        validate_source(locks[TARGET_SOURCE_ID])
    target_names = {item["name"] for item in skills_registry["skills"]}
    if TARGET_SKILL_NAME in target_names:
        validate_active_skill(locks[TARGET_SOURCE_ID])
    print(f"Repository validation passed for {len(skills_registry['skills'])} registered skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
