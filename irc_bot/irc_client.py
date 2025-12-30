import asyncio
import ssl
from typing import Callable, Optional, Dict, Any, List, Tuple
from collections import defaultdict


def parse_irc_message(line: str) -> Dict[str, Any]:
    """Parse a single IRC message line into components.

    Returns a dict with keys: prefix, command, params (list), trailing.
    """
    original = line
    line = line.rstrip("\r\n")
    prefix = None
    trailing = None

    if line.startswith(":"):
        try:
            prefix, line = line[1:].split(" ", 1)
        except ValueError:
            # Only a prefix? Unusual; fall back to whole line
            prefix = line[1:]
            line = ""

    if " :" in line:
        line, trailing = line.split(" :", 1)

    parts = line.split()
    command = parts[0] if parts else ""
    params = parts[1:] if len(parts) > 1 else []

    return {
        "prefix": prefix,
        "command": command,
        "params": params,
        "trailing": trailing,
        "raw": original,
    }


class IRCClient:
    def __init__(
        self,
        server: str,
        port: int,
        tls: bool,
        nickname: str,
        username: str,
        realname: str,
        password: Optional[str] = None,
        channels: Optional[List[str]] = None,
        sasl_enabled: bool = False,
        sasl_username: Optional[str] = None,
        sasl_password: Optional[str] = None,
        nickserv_enabled: bool = False,
        nickserv_username: Optional[str] = None,
        nickserv_password: Optional[str] = None,
    ) -> None:
        self.server = server
        self.port = port
        self.tls = tls
        self.nickname = nickname
        self.username = username
        self.realname = realname
        self.password = password
            debug: bool = False,
        self.channels = channels or []
        self.sasl_enabled = sasl_enabled
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.nickserv_enabled = nickserv_enabled
        self.nickserv_username = nickserv_username
        self.nickserv_password = nickserv_password

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

        # Callbacks
        self.on_welcome: Optional[Callable[[], None]] = None
        self.on_privmsg: Optional[Callable[[str, str, str], None]] = None  # nick, target, message

            self.debug = debug
        # Channel user modes: channel -> nick -> set of mode letters {q,a,o,h,v}
        self.channel_modes: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
            if self.debug:
                print(f"-> JOIN {channel}")
            await self.send_raw(f"JOIN {channel}")
        # Internal SASL state
        self._sasl_requested: bool = False
        self._sasl_in_progress: bool = False
        self._sasl_done: bool = False
        self._sasl_success: bool = False

    async def connect(self) -> None:
        ssl_ctx = None
        if self.tls:
            ssl_ctx = ssl.create_default_context()
            if self.debug:
                print(f"Connecting with TLS to {self.server}:{self.port}")
        else:
            if self.debug:
                print(f"Connecting without TLS to {self.server}:{self.port}")

        try:
            self.reader, self.writer = await asyncio.open_connection(self.server, self.port, ssl=ssl_ctx)
        except ssl.SSLError as e:
            # Common when TLS is enabled on a plaintext port: WRONG_VERSION_NUMBER
            if self.tls:
                if self.debug:
                    print(f"TLS handshake failed ({getattr(e, 'reason', 'SSLError')}). Retrying without TLS...")
                # Retry without TLS
                self.tls = False
                self.reader, self.writer = await asyncio.open_connection(self.server, self.port, ssl=None)
            else:
                raise
        except Exception:
            # If plaintext connection fails but we're targeting 6697, try TLS
            if not self.tls and self.port == 6697:
                if self.debug:
                    print("Plaintext connection to 6697 failed. Retrying with TLS...")
                ssl_ctx = ssl.create_default_context()
                self.tls = True
                self.reader, self.writer = await asyncio.open_connection(self.server, self.port, ssl=ssl_ctx)
            else:
                raise

                                if self.debug:
                                    print("SASL: requested AUTHENTICATE PLAIN")
        # Request SASL if enabled
        if self.sasl_enabled:
            await self.send_raw("CAP REQ :sasl")
            self._sasl_requested = True

        # PASS for server-level password (not SASL)
        if self.password and not self.sasl_enabled:
            await self.send_raw(f"PASS {self.password}")

        await self.send_raw(f"NICK {self.nickname}")
        # USER <username> 0 * :<realname>
        await self.send_raw(f"USER {self.username} 0 * :{self.realname}")

                            if self.debug:
                                print("SASL: sent credentials payload")
    async def send_raw(self, data: str) -> None:
        if not self.writer:
            return
        self.writer.write((data + "\r\n").encode("utf-8"))
        await self.writer.drain()

    async def join(self, channel: str) -> None:
                        if self.debug:
                            print("SASL: success")
        await self.send_raw(f"JOIN {channel}")

    async def send_privmsg(self, target: str, message: str) -> None:
        await self.send_raw(f"PRIVMSG {target} :{message}")

                        if self.debug:
                            print(f"SASL: failure numeric {cmd}")
    async def run(self) -> None:
        if not self.reader:
            raise RuntimeError("Client not connected. Call connect() first.")

        while True:
                    if self.debug:
                        params = msg.get("params", [])
                        channel = params[-1] if params else ""
                        print(f"Join: names list for {channel}")
            raw = await self.reader.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="ignore")
                    if self.debug:
                        params = msg.get("params", [])
                        ch = params[0] if params else ""
                        print(f"Mode change on {ch}: {' '.join(params[1:])}")
            msg = parse_irc_message(line)
                # End of NAMES list means channel join completed
                if cmd == "366":
                    params = msg.get("params", [])
                    ch = params[1] if len(params) > 1 else (params[0] if params else "")
                    if self.debug:
                        print(f"Joined {ch}")
            cmd = msg["command"].upper()
                # Common join failure numerics
                if cmd in {"471", "473", "474", "475", "476", "477"}:
                    trailing = msg.get("trailing") or ""
                    if self.debug:
                        print(f"Join failed ({cmd}): {trailing}")

            if cmd == "PING":
                arg = msg.get("trailing") or (msg["params"][0] if msg["params"] else "server")
                await self.send_raw(f"PONG :{arg}")
                continue

            # 001 = welcome message after successful registration
            if cmd == "001":
                if self.on_welcome:
                    self.on_welcome()
                # If NickServ is enabled and SASL not used or failed, identify first
                if self.nickserv_enabled and (not self.sasl_enabled or not self._sasl_success):
                    if self.nickserv_username and self.nickserv_password:
                        await self.send_privmsg("NickServ", f"IDENTIFY {self.nickserv_username} {self.nickserv_password}")
                        # Give some time for identification, then join
                        asyncio.create_task(self._delayed_join())
                    else:
                        # Missing creds, join anyway
                        for ch in self.channels:
                            await self.join(ch)
                else:
                    # Join channels immediately
                    for ch in self.channels:
                        await self.join(ch)
                continue

            if cmd == "PRIVMSG":
                prefix = msg.get("prefix") or ""
                nick = prefix.split("!", 1)[0] if "!" in prefix else prefix
                target = msg["params"][0] if msg["params"] else ""
                text = msg.get("trailing") or ""
                if self.on_privmsg:
                    self.on_privmsg(nick, target, text)

            # RPL_NAMREPLY (353): build initial channel mode map from nick prefixes
            if cmd == "353":
                self._update_names_from_353(msg)

            # MODE changes: update channel mode map
            if cmd == "MODE":
                self._update_modes(msg)

            # SASL negotiation
            if self.sasl_enabled and not self._sasl_done:
                if cmd == "CAP":
                    # Expect ACK :sasl
                    params = msg.get("params", [])
                    subcmd = params[1] if len(params) > 1 else ""
                    if subcmd.upper() == "ACK":
                        trailing = msg.get("trailing") or ""
                        if "sasl" in trailing.lower():
                            await self.send_raw("AUTHENTICATE PLAIN")
                            self._sasl_in_progress = True
                            continue
                if cmd == "AUTHENTICATE" and self._sasl_in_progress:
                    # Server sends '+' to request payload
                    plus = msg.get("params") or []
                    token = plus[0] if plus else (msg.get("trailing") or "")
                    if token.strip() == "+":
                        import base64
                        authzid = self.nickname or ""
                        authcid = self.sasl_username or self.username
                        passwd = self.sasl_password or ""
                        payload = f"{authzid}\0{authcid}\0{passwd}".encode("utf-8")
                        b64 = base64.b64encode(payload).decode("ascii")
                        await self.send_raw(f"AUTHENTICATE {b64}")
                        continue
                # Numeric replies for SASL
                if cmd in {"903"}:  # RPL_SASLSUCCESS
                    await self.send_raw("CAP END")
                    self._sasl_done = True
                    self._sasl_success = True
                    self._sasl_in_progress = False
                    continue
                if cmd in {"904", "905", "906", "907"}:  # various SASL failures
                    await self.send_raw("CAP END")
                    self._sasl_done = True
                    self._sasl_in_progress = False
                    continue

    async def _delayed_join(self) -> None:
        # Delay to allow NickServ to identify
        await asyncio.sleep(2)
        for ch in self.channels:
            await self.join(ch)

    # Permissions helpers
    def is_op_or_above(self, channel: str, nick: str) -> bool:
        roles = self.channel_modes.get(channel, {}).get(nick, set())
        return any(r in roles for r in ("o", "a", "q"))

    # Internal: parse 353 names list
    def _update_names_from_353(self, msg: Dict[str, Any]) -> None:
        params = msg.get("params", [])
        channel = params[-1] if params else ""
        names_str = msg.get("trailing") or ""
        if not channel or not names_str:
            return
        for token in names_str.split():
            prefix = token[0]
            name = token
            mode = None
            if prefix in ("@", "&", "~", "%", "+"):
                name = token[1:]
                mode = {
                    "@": "o",
                    "&": "a",
                    "~": "q",
                    "%": "h",
                    "+": "v",
                }[prefix]
            if name:
                if mode:
                    self.channel_modes[channel][name].add(mode)
                else:
                    # Ensure entry exists
                    _ = self.channel_modes[channel][name]

    # Internal: parse MODE change
    def _update_modes(self, msg: Dict[str, Any]) -> None:
        params = msg.get("params", [])
        if not params:
            return
        channel = params[0]
        if len(params) < 2:
            return
        modes = params[1]
        args = params[2:]
        sign = "+"
        i = 0
        need_arg = set("qahov")
        for ch in modes:
            if ch in "+-":
                sign = ch
                continue
            if ch in need_arg:
                if i >= len(args):
                    break
                nick = args[i]
                i += 1
                role = ch
                if sign == "+":
                    self.channel_modes[channel][nick].add(role)
                else:
                    self.channel_modes[channel][nick].discard(role)

    async def close(self) -> None:
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
