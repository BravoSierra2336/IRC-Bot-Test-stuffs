import unittest

from irc_bot.irc_client import parse_irc_message


class TestParser(unittest.TestCase):
    def test_privmsg(self):
        line = ":nick!user@host PRIVMSG #channel :Hello world\r\n"
        msg = parse_irc_message(line)
        self.assertEqual(msg["command"], "PRIVMSG")
        self.assertEqual(msg["params"], ["#channel"])
        self.assertEqual(msg["trailing"], "Hello world")
        self.assertEqual(msg["prefix"], "nick!user@host")

    def test_ping(self):
        line = "PING :server.name\r\n"
        msg = parse_irc_message(line)
        self.assertEqual(msg["command"], "PING")
        self.assertEqual(msg["trailing"], "server.name")

    def test_welcome(self):
        line = ":server 001 nick :Welcome\r\n"
        msg = parse_irc_message(line)
        self.assertEqual(msg["command"], "001")
        self.assertEqual(msg["params"], ["nick"])
        self.assertEqual(msg["trailing"], "Welcome")


if __name__ == "__main__":
    unittest.main()
