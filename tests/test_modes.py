import unittest

from irc_bot.irc_client import IRCClient, parse_irc_message


class TestModes(unittest.TestCase):
    def setUp(self):
        self.client = IRCClient(
            server="example", port=6667, tls=False, nickname="bot", username="bot", realname="bot"
        )

    def test_353_parsing_ops(self):
        msg = parse_irc_message(":server 353 me = #chan :@alice +bob charlie\r\n")
        self.client._update_names_from_353(msg)
        self.assertTrue(self.client.is_op_or_above("#chan", "alice"))
        self.assertFalse(self.client.is_op_or_above("#chan", "bob"))
        self.assertFalse(self.client.is_op_or_above("#chan", "charlie"))

    def test_mode_updates(self):
        # Grant op
        msg = parse_irc_message(":nick MODE #chan +o alice\r\n")
        self.client._update_modes(msg)
        self.assertTrue(self.client.is_op_or_above("#chan", "alice"))
        # Remove op
        msg2 = parse_irc_message(":nick MODE #chan -o alice\r\n")
        self.client._update_modes(msg2)
        self.assertFalse(self.client.is_op_or_above("#chan", "alice"))


if __name__ == "__main__":
    unittest.main()
