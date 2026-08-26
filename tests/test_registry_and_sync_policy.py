from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.sync_upstream import (
    apply_upstream_commit,
    format_knowledge_count_table,
)
from scripts.validate_repository import (
    validate_registered_skill_directories,
    validate_registries,
    validate_source,
)


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "685469889fb72fd5adefae45e1645d527edcb5e7"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RegistryScaleAndRightsTests(unittest.TestCase):
    def registry_fixture(self, root: Path) -> tuple[dict, dict]:
        skills = load_json(ROOT / "registry" / "skills.json")
        sources = load_json(ROOT / "registry" / "sources.json")
        write_json(root / "registry" / "skills.json", skills)
        write_json(root / "registry" / "sources.json", sources)
        write_json(
            root / "sources" / "awesome-gpt-image-2" / "source.lock.json",
            load_json(ROOT / "sources" / "awesome-gpt-image-2" / "source.lock.json"),
        )
        source_root = root / "sources" / "awesome-gpt-image-2"
        (source_root / "LICENSE").write_text("fixture license\n", encoding="utf-8")
        disclaimer = source_root / "snapshot" / "docs" / "disclaimer.md"
        disclaimer.parent.mkdir(parents=True, exist_ok=True)
        disclaimer.write_text("fixture disclaimer\n", encoding="utf-8")
        attestation = skills["skills"][0]["trust_attestation"]
        acceptance_report = root / attestation["acceptance_report"]
        acceptance_report.parent.mkdir(parents=True, exist_ok=True)
        acceptance_report.write_text(
            (
                f"Accepted Skill {attestation['skill_name']} at upstream commit "
                f"{attestation['accepted_commit']}\n"
            ),
            encoding="utf-8",
        )
        return skills, sources

    def materialize_skill_contract(self, root: Path, skill: dict) -> None:
        skill_file = root / "skills" / skill["name"] / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(
            "---\n"
            f"name: {skill['name']}\n"
            f"description: {skill['description']}\n"
            "---\n"
            "\nUse the registered knowledge paths.\n",
            encoding="utf-8",
        )
        for key, path_text in skill["knowledge_source"].items():
            if key == "source_id":
                continue
            path = root / path_text
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(f"fixture {key}\n", encoding="utf-8")

    def test_registry_accepts_multiple_skills(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-multi-") as temp:
            root = Path(temp)
            skills, _ = self.registry_fixture(root)
            second = copy.deepcopy(skills["skills"][0])
            second["name"] = "second-professional-skill"
            second["description"] = "Second fixture skill backed by the same pinned source."
            second["knowledge_source"]["bundled_reference"] = (
                "skills/second-professional-skill/references/library.md"
            )
            second["knowledge_source"]["source_guide"] = (
                "skills/second-professional-skill/references/source.md"
            )
            second["trust_attestation"]["skill_name"] = second["name"]
            second["trust_attestation"]["acceptance_report"] = (
                "reports/acceptance/second-professional-skill.md"
            )
            skills["skills"].append(second)
            write_json(root / "registry" / "skills.json", skills)
            second_report = root / second["trust_attestation"]["acceptance_report"]
            second_report.parent.mkdir(parents=True, exist_ok=True)
            second_report.write_text(
                (
                    f"Accepted Skill {second['name']} at upstream commit "
                    f"{second['upstream_commit']}\n"
                ),
                encoding="utf-8",
            )
            for skill in skills["skills"]:
                self.materialize_skill_contract(root, skill)

            validated, _, _ = validate_registries(root)
            validate_registered_skill_directories(validated, root)
            self.assertEqual(
                [item["name"] for item in validated["skills"]],
                ["gpt-image-2-style-library", "second-professional-skill"],
            )

    def test_active_skill_rejects_missing_registered_knowledge_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-paths-") as temp:
            root = Path(temp)
            skills, _ = self.registry_fixture(root)
            skill = skills["skills"][0]
            self.materialize_skill_contract(root, skill)
            skill["knowledge_source"]["complete_cases"] = "sources/missing/cases.json"
            write_json(root / "registry" / "skills.json", skills)
            validated, _, _ = validate_registries(root)

            with self.assertRaisesRegex(AssertionError, "file does not exist"):
                validate_registered_skill_directories(validated, root)

    def test_registry_rejects_blanket_license_without_content_rights(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-rights-") as temp:
            root = Path(temp)
            _, sources = self.registry_fixture(root)
            del sources["sources"][0]["license"]["content_rights"]
            write_json(root / "registry" / "sources.json", sources)

            with self.assertRaisesRegex(AssertionError, "blanket-declared"):
                validate_registries(root)

    def test_awesome_source_rejects_repository_license_as_blanket_content_rights(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-rights-status-") as temp:
            root = Path(temp)
            _, sources = self.registry_fixture(root)
            sources["sources"][0]["license"]["content_rights"]["status"] = (
                "repository-license-applies"
            )
            write_json(root / "registry" / "sources.json", sources)

            with self.assertRaisesRegex(AssertionError, "cannot inherit.*blanket"):
                validate_registries(root)

    def test_trusted_skill_rejects_stale_commit_attestation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-trust-") as temp:
            root = Path(temp)
            skills, sources = self.registry_fixture(root)
            new_commit = "f" * 40
            skills["skills"][0]["upstream_commit"] = new_commit
            sources["sources"][0]["commit"] = new_commit
            write_json(root / "registry" / "skills.json", skills)
            write_json(root / "registry" / "sources.json", sources)
            lock_path = root / "sources" / "awesome-gpt-image-2" / "source.lock.json"
            lock = load_json(lock_path)
            lock["commit"] = new_commit
            write_json(lock_path, lock)

            with self.assertRaisesRegex(AssertionError, "acceptance is not bound"):
                validate_registries(root)

    def test_trusted_skill_rejects_another_skills_attestation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="registry-trust-skill-") as temp:
            root = Path(temp)
            skills, _ = self.registry_fixture(root)
            skills["skills"][0]["trust_attestation"]["skill_name"] = "another-skill"
            write_json(root / "registry" / "skills.json", skills)

            with self.assertRaisesRegex(AssertionError, "different Skill"):
                validate_registries(root)

    def test_source_validation_allows_variable_knowledge_counts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-counts-") as temp:
            root = Path(temp)
            source = root / "sources" / "awesome-gpt-image-2"
            snapshot = source / "snapshot"
            library = {
                "templates": [
                    {
                        "id": "one-template",
                        "anchor": "one-template",
                        "cover": "/images/template.png",
                        "exampleCases": [1],
                    }
                ],
                "categories": [
                    {
                        "id": "one-category",
                        "cover": "/images/category.png",
                    }
                ],
                "styles": [{"value": "one-style"}],
                "scenes": [{"value": "one-scene"}],
            }
            cases = {
                "totalCases": 1,
                "cases": [
                    {
                        "id": 1,
                        "image": "/images/case.png",
                        "prompt": "fixture",
                        "sourceLabel": "fixture-source",
                    }
                ],
            }
            write_json(snapshot / "data" / "style-library.json", library)
            write_json(snapshot / "data" / "cases.json", cases)
            (snapshot / "docs").mkdir(parents=True, exist_ok=True)
            (snapshot / "docs" / "templates.md").write_text(
                '<a name="one-template"></a>\n', encoding="utf-8"
            )
            (snapshot / "docs" / "disclaimer.md").write_text(
                "不主张对第三方原创内容的任何所有权\n不保证第三方内容可用于商业用途\n",
                encoding="utf-8",
            )
            generator = snapshot / "scripts" / "generate-style-skill.mjs"
            generator.parent.mkdir(parents=True, exist_ok=True)
            generator.write_text("// fixture\n", encoding="utf-8")
            upstream_skill = (
                snapshot
                / "agents"
                / "skills"
                / "gpt-image-2-style-library"
                / "SKILL.md"
            )
            upstream_skill.parent.mkdir(parents=True, exist_ok=True)
            upstream_skill.write_text("---\nname: fixture\n---\n", encoding="utf-8")
            images = snapshot / "data" / "images"
            images.mkdir(parents=True, exist_ok=True)
            (images / "template.png").write_bytes(b"template")
            (images / "category.png").write_bytes(b"category")
            source.mkdir(parents=True, exist_ok=True)
            (source / "LICENSE").write_text(
                "MIT License\nCopyright (c) 2026 freestylefly\n",
                encoding="utf-8",
            )
            write_json(
                source / "case-images.lock.json",
                {
                    "commit": COMMIT,
                    "asset_count": 1,
                    "assets": [
                        {
                            "case_id": 1,
                            "path": "data/images/case.png",
                            "blob_sha": "a" * 40,
                            "vendored": False,
                            "raw_url": (
                                "https://raw.githubusercontent.com/example/repo/"
                                f"{COMMIT}/data/images/case.png"
                            ),
                        }
                    ],
                },
            )

            validate_source({"commit": COMMIT}, root)


class SyncPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = load_json(ROOT / "registry" / "skills.json")
        self.sources = load_json(ROOT / "registry" / "sources.json")

    def test_changed_commit_downgrades_only_affected_skills(self) -> None:
        related = copy.deepcopy(self.skills["skills"][0])
        related["name"] = "second-related-skill"
        unrelated = copy.deepcopy(self.skills["skills"][0])
        unrelated["name"] = "unrelated-skill"
        unrelated["knowledge_source"]["source_id"] = "another-source"
        self.skills["skills"].extend([related, unrelated])
        new_commit = "f" * 40

        affected = apply_upstream_commit(
            self.skills,
            self.sources,
            source_id="awesome-gpt-image-2",
            old_commit=COMMIT,
            commit=new_commit,
        )

        changed, also_changed, unchanged = self.skills["skills"]
        self.assertEqual(
            affected,
            ["gpt-image-2-style-library", "second-related-skill"],
        )
        self.assertEqual(changed["trust_status"], "experimental")
        self.assertEqual(changed["trust_review"]["required_after_commit"], new_commit)
        self.assertEqual(changed["upstream_commit"], new_commit)
        self.assertEqual(also_changed["trust_status"], "experimental")
        self.assertEqual(also_changed["trust_review"]["required_after_commit"], new_commit)
        self.assertEqual(also_changed["upstream_commit"], new_commit)
        self.assertEqual(unchanged["trust_status"], "trusted")
        self.assertEqual(unchanged["upstream_commit"], COMMIT)
        self.assertEqual(self.sources["sources"][0]["commit"], new_commit)

    def test_same_commit_does_not_downgrade_trusted_skill(self) -> None:
        apply_upstream_commit(
            self.skills,
            self.sources,
            source_id="awesome-gpt-image-2",
            old_commit=COMMIT,
            commit=COMMIT,
        )
        skill = self.skills["skills"][0]
        self.assertEqual(skill["trust_status"], "trusted")
        self.assertNotIn("trust_review", skill)

    def test_count_changes_are_rendered_as_sync_report_deltas(self) -> None:
        table = format_knowledge_count_table(
            {
                "templates": 22,
                "categories": 13,
                "styles": 19,
                "scenes": 10,
                "cases": 529,
            },
            {
                "templates": 24,
                "categories": 13,
                "styles": 18,
                "scenes": 11,
                "cases": 540,
            },
        )
        self.assertIn("| Templates | 22 | 24 | +2 |", table)
        self.assertIn("| Style tags | 19 | 18 | -1 |", table)
        self.assertIn("| Case prompts | 529 | 540 | +11 |", table)


if __name__ == "__main__":
    unittest.main()
