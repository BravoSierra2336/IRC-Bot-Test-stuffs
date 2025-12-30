import unittest
import os
from pathlib import Path

from irc_bot.profiles import ProfileStore


class TestViewStore(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(".tmp_profiles_test.json")
        try:
            os.remove(self.tmp)
        except Exception:
            pass

    def tearDown(self):
        try:
            os.remove(self.tmp)
        except Exception:
            pass

    def test_store_and_retrieve_other(self):
        store = ProfileStore(path=str(self.tmp))
        store.update_profile("alice", {"age": "28", "location": "NY", "bio": "Hello"})
        prof = store.get_profile("alice")
        self.assertIsNotNone(prof)
        self.assertEqual(prof["age"], 28)
        self.assertEqual(prof["location"], "NY")
        self.assertEqual(prof["bio"], "Hello")


if __name__ == "__main__":
    unittest.main()
