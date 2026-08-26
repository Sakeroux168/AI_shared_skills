from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install_skill import SKILLS_ROOT, install_one


def file_set(root: Path) -> set[str]:
    return {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


class InstallerTests(unittest.TestCase):
    def test_copy_and_recoverable_force_update(self) -> None:
        skill_name = "gpt-image-2-style-library"
        with tempfile.TemporaryDirectory(prefix="shared-skills-test-") as temp:
            target_root = Path(temp) / ".agents" / "skills"
            first = install_one(skill_name, target_root, force=False, dry_run=False)
            target = Path(str(first["target"]))
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertEqual(file_set(SKILLS_ROOT / skill_name), file_set(target))

            second = install_one(skill_name, target_root, force=True, dry_run=False)
            backup = Path(str(second["backup"]))
            self.assertTrue((backup / "SKILL.md").is_file())
            self.assertEqual(file_set(SKILLS_ROOT / skill_name), file_set(target))

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="shared-skills-dry-") as temp:
            target_root = Path(temp) / "skills"
            result = install_one(
                "gpt-image-2-style-library",
                target_root,
                force=False,
                dry_run=True,
            )
            self.assertEqual(result["mode"], "dry-run")
            self.assertFalse(Path(str(result["target"])).exists())


if __name__ == "__main__":
    unittest.main()

