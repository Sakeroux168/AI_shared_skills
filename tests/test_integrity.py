from __future__ import annotations

import unittest

from scripts.validate_repository import (
    validate_active_skill,
    validate_registries,
    validate_skill_frontmatter,
    validate_source,
)


class RepositoryIntegrityTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self) -> None:
        validate_skill_frontmatter()

    def test_registry_lock_and_harness_matrix(self) -> None:
        _, _, lock = validate_registries()
        self.assertEqual(len(lock["commit"]), 40)

    def test_source_and_active_skill_integrity(self) -> None:
        _, _, lock = validate_registries()
        validate_source(lock)
        validate_active_skill(lock)


if __name__ == "__main__":
    unittest.main()

