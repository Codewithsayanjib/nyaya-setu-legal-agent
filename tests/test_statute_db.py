import unittest
from src.statute_db import StatuteDatabase

class TestStatuteDatabase(unittest.TestCase):
    def setUp(self):
        self.db = StatuteDatabase()

    def test_database_loading(self):
        statutes = self.db.get_all()
        self.assertGreater(len(statutes), 0)

    def test_find_theft_and_robbery(self):
        robbery = self.db.find_by_bns("309")
        self.assertIsNotNone(robbery)
        self.assertEqual(robbery["ipc_equivalent"], "392")
        self.assertTrue(len(robbery["ingredients"]) > 0)

    def test_catalog_summary(self):
        summary = self.db.get_catalog_summary()
        self.assertIn("Section BNS 309", summary)
        self.assertIn("Statutory Ingredients Required", summary)

if __name__ == "__main__":
    unittest.main()
