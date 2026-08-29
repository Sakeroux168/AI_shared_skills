from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.style_library import CASES_PATH, LIBRARY_PATH, build_prompt, load_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "prompt_cases.json"
REQUIRED_BLOCKS = {
    "subject_and_task",
    "composition_and_layout",
    "visual_style_and_materials",
    "text_and_label_requirements",
    "aspect_ratio_and_output_format",
    "constraints_and_negative_details",
}


class PromptAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        cls.library = load_json(LIBRARY_PATH)
        cls.cases = load_json(CASES_PATH)
        cls.template_ids = {item["id"] for item in cls.library["templates"]}
        cls.style_values = {item["value"] for item in cls.library["styles"]}
        cls.scene_values = {item["value"] for item in cls.library["scenes"]}
        cls.case_ids = {int(item["id"]) for item in cls.cases["cases"]}

    def test_five_required_domains(self) -> None:
        self.assertEqual(len(self.fixtures), 5)
        for fixture in self.fixtures:
            with self.subTest(fixture=fixture["id"]):
                output = build_prompt(fixture["query"], aspect_ratio="4:5")
                self.assertEqual(output["template_id"], fixture["expected_template"])
                self.assertEqual(output["category"], fixture["expected_category"])
                self.assertIn(fixture["expected_style"], output["styles"])
                self.assertIn(fixture["expected_scene"], output["scenes"])
                self.assertIn(output["template_id"], self.template_ids)
                self.assertTrue(set(output["styles"]) <= self.style_values)
                self.assertTrue(set(output["scenes"]) <= self.scene_values)
                self.assertTrue(set(output["example_case_ids"]) <= self.case_ids)
                self.assertEqual(set(output["prompt"]), REQUIRED_BLOCKS)
                self.assertTrue(all(value.strip() for value in output["prompt"].values()))
                library_path = output["source"]["library"].replace("\\", "/")
                self.assertIn("sources/awesome-gpt-image-2", library_path)


if __name__ == "__main__":
    unittest.main()
