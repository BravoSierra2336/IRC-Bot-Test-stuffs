import asyncio
from typing import Dict, Callable

# Robust imports: support running as a package or as a script (PyInstaller direct)
try:
    from .config import load_config
    from .irc_client import IRCClient
except ImportError:
    from irc_bot.config import load_config
    from irc_bot.irc_client import IRCClient


class Bot:
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.prefix = cfg.get("command_prefix", "!")
        self.client = IRCClient(
            server=cfg["server"],
            port=cfg["port"],
            tls=cfg["tls"],
            nickname=cfg["nickname"],
            username=cfg["username"],
            realname=cfg["realname"],
            password=cfg.get("password") or None,
            channels=cfg.get("channels", []),
            sasl_enabled=cfg.get("sasl_enabled", False),
            sasl_username=cfg.get("sasl_username") or None,
            sasl_password=cfg.get("sasl_password") or None,
            nickserv_enabled=cfg.get("nickserv_enabled", False),
            nickserv_username=cfg.get("nickserv_username") or None,
            nickserv_password=cfg.get("nickserv_password") or None,
            debug=cfg.get("debug", False),
        )

        self.commands: Dict[str, Callable[[str, str, list[str]], None]] = {
            "ping": self.cmd_ping,
            "hello": self.cmd_hello,
            "help": self.cmd_help,
            "profile": self.cmd_profile,
            "view": self.cmd_view,
            "say": self.cmd_say,
        }

        # Wire callbacks
        self.client.on_welcome = self.on_welcome
        self.client.on_privmsg = self.on_privmsg

    def on_welcome(self) -> None:
        print("Connected. Joining channels...")

    def on_privmsg(self, nick: str, target: str, text: str) -> None:
        # Only respond to commands
        if not text.startswith(self.prefix):
            return
        cmdline = text[len(self.prefix):].strip()
        if not cmdline:
            return
        parts = cmdline.split()
        name = parts[0].lower()
        args = parts[1:]
        handler = self.commands.get(name)
        if not handler:
            # Unknown command: show minimal help
            asyncio.create_task(self.client.send_privmsg(target, f"Unknown command '{name}'. Try {self.prefix}help"))
            return
        handler(target, nick, args)

    # Commands
    def cmd_ping(self, target: str, nick: str, args: list[str]) -> None:
        asyncio.create_task(self.client.send_privmsg(target, "Pong!"))

    def cmd_hello(self, target: str, nick: str, args: list[str]) -> None:
        asyncio.create_task(self.client.send_privmsg(target, f"Hello, {nick}!"))

    def cmd_help(self, target: str, nick: str, args: list[str]) -> None:
        names = ", ".join(sorted(self.commands.keys()))
        asyncio.create_task(self.client.send_privmsg(target, f"Commands: {names}"))

    # Profile command
    def cmd_profile(self, target: str, nick: str, args: list[str]) -> None:
        from .profiles import ProfileStore
        store = getattr(self, "_profile_store", None)
        if store is None:
            store = ProfileStore()
            self._profile_store = store

        async def send(msg: str) -> None:
            await self.client.send_privmsg(target, msg)

        if not args or args[0].lower() in {"help", "?"}:
            usage = (
                "Usage: !profile set key=value ... | !profile get | !profile clear | !profile help"
            )
            fields = "Fields: age, location, interests, bio"
            asyncio.create_task(send(usage))
            asyncio.create_task(send(fields))
            return

        sub = args[0].lower()
        if sub == "get":
            prof = store.get_profile(nick)
            if not prof:
                asyncio.create_task(send("No profile found. Use !profile set key=value"))
                return
            parts = [f"{k}={v}" for k, v in prof.items()]
            asyncio.create_task(send("Profile: " + ", ".join(parts)))
            return
        if sub == "clear" or sub == "delete":
            store.clear_profile(nick)
            asyncio.create_task(send("Profile cleared."))
            return
        if sub == "set":
            updates = store.parse_updates(args[1:])
            if not updates:
                asyncio.create_task(send("Provide fields as key=value (e.g., age=25 location=NY interests=gaming bio=Hi)"))
                return
            prof = store.update_profile(nick, updates)
            parts = [f"{k}={v}" for k, v in prof.items()]
            asyncio.create_task(send("Profile updated: " + ", ".join(parts)))
            return

        asyncio.create_task(send("Unknown subcommand. Try !profile help"))

    # View another user's profile
    def cmd_view(self, target: str, nick: str, args: list[str]) -> None:
        from .profiles import ProfileStore
        store = getattr(self, "_profile_store", None)
        if store is None:
            store = ProfileStore()
            self._profile_store = store

        async def send(msg: str) -> None:
            await self.client.send_privmsg(target, msg)

        if not args:
            asyncio.create_task(send("Usage: !view <nick>"))
            return
        other = args[0]
        prof = store.get_profile(other)
        if not prof:
            asyncio.create_task(send(f"No profile found for {other}."))
            return
        parts = [f"{k}={v}" for k, v in prof.items()]
        # Keep message reasonably short; split if necessary
        msg = f"Profile for {other}: " + ", ".join(parts)
        if len(msg) > 400:
            # Split into chunks
            chunks = []
            cur = ""
            for p in parts:
                if len(cur) + len(p) + 2 > 380:
                    chunks.append(cur)
                    cur = p
                else:
                    cur = p if not cur else (cur + ", " + p)
            if cur:
                chunks.append(cur)
            asyncio.create_task(send(f"Profile for {other}:"))
            for c in chunks:
                asyncio.create_task(send(c))
        else:
            asyncio.create_task(send(msg))

    # DM-based say: user DMs the bot, bot speaks in configured channel
    def cmd_say(self, target: str, nick: str, args: list[str]) -> None:
        async def reply(msg: str) -> None:
            await self.client.send_privmsg(target, msg)

        # Require DM to the bot (target is bot's nick), not a channel
        if target.startswith("#"):
            asyncio.create_task(reply("Please DM the bot: !say <message>"))
            return

        channel = self.cfg.get("say_channel")
        if not channel:
            asyncio.create_task(reply("No say channel configured. Set `say_channel` in config.json."))
            return

        if not args:
            asyncio.create_task(reply("Usage: !say <message>"))
            return

        text = " ".join(args).strip()
        if not text:
            asyncio.create_task(reply("Usage: !say <message>"))
            return

        # Permissions: require op in target channel unless disabled; or admin
        is_admin = nick in self.cfg.get("admins", [])
        require_op = self.cfg.get("say_require_op", True)
        is_op = True
        if require_op:
            is_op = self.client.is_op_or_above(channel, nick)
        if not (is_admin or is_op):
            asyncio.create_task(reply("Insufficient permissions. You must be a channel operator or listed admin."))
            return

        # Send to the configured channel; chunk long messages
        async def send_to_channel(msg: str) -> None:
            await self.client.send_privmsg(channel, msg)

        if len(text) > 400:
            chunks = []
            cur = ""
            for word in text.split():
                if len(cur) + len(word) + 1 > 380:
                    chunks.append(cur)
                    cur = word
                else:
                    cur = word if not cur else (cur + " " + word)
            if cur:
                chunks.append(cur)
            for c in chunks:
                asyncio.create_task(send_to_channel(c))
        else:
            asyncio.create_task(send_to_channel(text))


async def main() -> None:
    cfg = load_config()
    bot = Bot(cfg)
    await bot.client.connect()
    try:
        await bot.client.run()
    finally:
        await bot.client.close()


if __name__ == "__main__":
    asyncio.run(main())
