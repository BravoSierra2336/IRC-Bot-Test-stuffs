import json
from pathlib import Path
from typing import Any, Dict

REQUIRED_KEYS = [
    "server",
    "port",
    "tls",
    "nickname",
    "username",
    "realname",
    "channels",
]

DEFAULTS = {
    "password": None,
    "command_prefix": "!",
    "sasl_enabled": False,
    "sasl_username": None,
    "sasl_password": None,
    "nickserv_enabled": False,
    "nickserv_username": None,
    "nickserv_password": None,
    "admins": [],
    "say_channel": None,
    "say_require_op": True,
}


def load_config(path: str = "config.json") -> Dict[str, Any]:
    """Load and validate bot configuration from a JSON file.

    The config file is expected at the project root. Create it from
    `config.example.json` if it doesn't exist.
    """
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Missing {cfg_path.name}. Create it from config.example.json and edit your settings."
        )

    with cfg_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Apply defaults
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)

    # Basic validation
    for k in REQUIRED_KEYS:
        if k not in data:
            raise ValueError(f"Config missing required key: {k}")

    if not isinstance(data["channels"], list) or not all(isinstance(c, str) for c in data["channels"]):
        raise ValueError("`channels` must be a list of strings")

    if not isinstance(data["port"], int):
        raise ValueError("`port` must be an integer")

    if not isinstance(data["tls"], bool):
        raise ValueError("`tls` must be a boolean")

    if data.get("password") is not None and not isinstance(data["password"], str):
        raise ValueError("`password` must be a string or null")

    if not isinstance(data.get("command_prefix", "!"), str):
        raise ValueError("`command_prefix` must be a string")

    # SASL validation
    if not isinstance(data.get("sasl_enabled", False), bool):
        raise ValueError("`sasl_enabled` must be a boolean")
    if data.get("sasl_enabled"):
        if data.get("sasl_username") is None or data.get("sasl_password") is None:
            raise ValueError("When `sasl_enabled` is true, `sasl_username` and `sasl_password` must be set")
        if not isinstance(data.get("sasl_username"), str) or not isinstance(data.get("sasl_password"), str):
            raise ValueError("`sasl_username` and `sasl_password` must be strings when SASL is enabled")

    # NickServ validation
    if not isinstance(data.get("nickserv_enabled", False), bool):
        raise ValueError("`nickserv_enabled` must be a boolean")
    if data.get("nickserv_enabled"):
        if data.get("nickserv_username") is None or data.get("nickserv_password") is None:
            raise ValueError("When `nickserv_enabled` is true, `nickserv_username` and `nickserv_password` must be set")
        if not isinstance(data.get("nickserv_username"), str) or not isinstance(data.get("nickserv_password"), str):
            raise ValueError("`nickserv_username` and `nickserv_password` must be strings when NickServ is enabled")

    # Admins (fallback permission list)
    admins = data.get("admins", [])
    if not isinstance(admins, list) or not all(isinstance(a, str) for a in admins):
        raise ValueError("`admins` must be a list of nicknames (strings)")

    # Say command target channel and permission
    say_channel = data.get("say_channel")
    if say_channel is not None and not isinstance(say_channel, str):
        raise ValueError("`say_channel` must be a string channel name or null")
    if not isinstance(data.get("say_require_op", True), bool):
        raise ValueError("`say_require_op` must be a boolean")

    return data
