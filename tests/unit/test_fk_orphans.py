"""
Test Foreign Key Integrity across Seed Files.

Ensures no seed file in data/seed/ (including personas) has any orphan values
violating declared foreign keys in docker/init.sql.
"""

import os
import unittest
from scripts.check_fk_orphans import check_all_foreign_keys, BASE_DIR

class TestForeignKeyOrphans(unittest.TestCase):
    def test_zero_foreign_key_orphans(self):
        """Verify that check_fk_orphans finds 0 orphan references across all seed files."""
        orphans = check_all_foreign_keys(BASE_DIR)
        if orphans:
            formatted_orphans = "\n".join(
                f"  - {o['file']}:{o['row']} {o['column']}='{o['value']}' -> {o['referenced_table']}({o['referenced_column']})"
                for o in orphans
            )
            self.fail(f"Found {len(orphans)} foreign key orphan violations:\n{formatted_orphans}")
        self.assertEqual(len(orphans), 0, "Seed dataset must contain zero foreign key orphans")

if __name__ == "__main__":
    unittest.main()
