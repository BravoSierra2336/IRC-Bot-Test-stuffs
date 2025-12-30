import unittest

from irc_bot.profiles import ProfileStore


class TestProfiles(unittest.TestCase):
    def test_parse_updates(self):
        tokens = ["age=30", "location=NY", "bio=Hello", "ignored=val"]
        updates = ProfileStore.parse_updates(tokens)
        self.assertEqual(updates["age"], "30")
        self.assertEqual(updates["location"], "NY")
        self.assertEqual(updates["bio"], "Hello")
        self.assertNotIn("ignored", updates)


if __name__ == "__main__":
    unittest.main()
