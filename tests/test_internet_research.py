from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "internet-research"
AGENT_REACH_COMMIT = "06c202b03400a7d31886bf4399213706da1a0324"
ACCEPTANCE_REPORT = "reports/acceptance/2026-08-30-internet-research-v1.md"


class InternetResearchSkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_references_exist(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertIn("name: internet-research", match.group(1))
        for path in (
            SKILL / "references" / "runtime-contract.md",
            SKILL / "references" / "evidence-method.md",
            SKILL / "references" / "source-knowledge.md",
        ):
            self.assertTrue(path.is_file(), path)

    def test_safety_and_degradation_contract_is_explicit(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("READ ONLY", text)
        self.assertIn(
            "One unavailable platform must not block the entire research task",
            text,
        )
        self.assertIn("Never auto-login", text)
        self.assertIn("Never autonomously perform payment", text)
        self.assertIn("negative evidence", text.lower())
        self.assertIn("never export or print cookies", text.lower())

    def test_registry_records_trusted_forward_acceptance(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        skill = next(item for item in registry["skills"] if item["name"] == "internet-research")
        self.assertEqual(skill["local"]["status"], "active")
        self.assertEqual(skill["trust_status"], "trusted")
        self.assertEqual(skill["knowledge_source"]["source_id"], "agent-reach")
        self.assertEqual(skill["upstream_commit"], AGENT_REACH_COMMIT)
        attestation = skill["trust_attestation"]
        self.assertEqual(attestation["skill_name"], "internet-research")
        self.assertEqual(attestation["accepted_commit"], AGENT_REACH_COMMIT)
        self.assertEqual(attestation["acceptance_report"], ACCEPTANCE_REPORT)
        self.assertTrue((ROOT / ACCEPTANCE_REPORT).is_file())

    def test_runtime_reference_records_accepted_versions_without_claiming_stage1_as_trust(self) -> None:
        text = (SKILL / "references" / "runtime-contract.md").read_text(encoding="utf-8")
        self.assertIn("Agent Reach `v1.5.0`", text)
        self.assertIn("OpenCLI `v1.8.7`", text)
        self.assertIn("Browser Bridge extension `v1.0.23`", text)
        self.assertIn("does **not** by itself promote", text)


if __name__ == "__main__":
    unittest.main()
