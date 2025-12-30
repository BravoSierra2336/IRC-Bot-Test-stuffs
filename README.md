# IRC Bot (Python)

A simple, modern IRC bot built with Python's asyncio and the IRC protocol. It connects to a server, joins channels, and responds to basic commands.

## Requirements
- Python 3.10 or newer (3.11+ recommended)
- Internet access to your IRC network (e.g., Libera, OFTC)

## Quick Start (Windows PowerShell)
1. Navigate to the project root:
```powershell
cd "c:\Users\Xxima\Desktop\IRC Bot Test stuffs"
```
2. (Optional) Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Copy the example config and edit it:
```powershell
Copy-Item config.example.json config.json
notepad config.json
```
4. Run the bot:
```powershell
python -m irc_bot.bot
```

## Configuration
Edit `config.json` (created from `config.example.json`) and set:
- `server`: IRC server hostname
- `port`: 6667 for plaintext or 6697 for TLS
- `tls`: `true` to use TLS (recommended), `false` otherwise
- `nickname`, `username`, `realname`: your identity
- `password`: optional server password or NickServ SASL password (if required by your network)
- `channels`: list of channels to auto-join
- `command_prefix`: bot command prefix (default `!`)

### Optional: SASL Authentication
- `sasl_enabled`: set to `true` to use SASL PLAIN
- `sasl_username`: your NickServ/account username (not email on Libera)
- `sasl_password`: your account password

When SASL is enabled, the bot negotiates `CAP REQ :sasl` and performs `AUTHENTICATE PLAIN` before joining channels.

### Optional: NickServ Fallback
- `nickserv_enabled`: set to `true` to identify with NickServ after connect
- `nickserv_username`: your NickServ/account name (often same as `nickname`)
- `nickserv_password`: your account password

If SASL is disabled or fails, the bot sends `PRIVMSG NickServ :IDENTIFY <user> <pass>` on welcome, waits briefly, then joins channels.

## Built-in Commands
- `!ping`: replies with "Pong!"
- `!hello`: replies with a friendly greeting
- `!help`: lists available commands
 - `!profile`: manage a simple user profile
 - `!view <nick>`: view another user's profile
- `!say <message>`: DM the bot to speak in a configured channel (ops/admins only)

### `!profile` usage
- Create/update: `!profile set age=25 location=NY interests=gaming bio=Hello there`
- View: `!profile get`
- Clear: `!profile clear`
- Help: `!profile help`

Fields stored: `age` (number), `location` (text), `interests` (text), `bio` (short description). Profiles are stored per-nickname in `profiles.json` in the project root.

### `!view` usage
- View another user's profile: `!view <nick>`

### `!say` usage
- DM the bot: `!say <message>` and it will post into the configured `say_channel`.
- Configure in `config.json`:
	- `say_channel`: target channel name (e.g., `#forbidden`)
	- `say_require_op`: `true` to require being op (`@`) or above in that channel
	- `admins`: fallback nicknames allowed regardless of channel mode
- Permissions:
	- Requires channel operator (op `@`) or above (`&` admin, `~` owner) when `say_require_op` is true. The bot learns this from `353` nicklists and `MODE` changes.
	- Alternatively, use the `admins` list.

## Notes
- If your nickname is in use, the server may assign a temporary nick. Update `nickname` or register it.
- Firewalls can block IRC ports. If you cannot connect, check Windows Defender Firewall and your network.
- Many IRC networks prefer TLS on port 6697. Set `tls` to `true` and `port` to `6697`.

## Run Tests
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Build Windows .exe
This project can be packaged into a standalone `.exe` using PyInstaller.

```powershell
cd "c:\Users\Xxima\Desktop\IRC Bot Test stuffs"
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

- The executable is created at `dist/AscensionismBot.exe`.
- Place `config.json` next to the `.exe` or run the `.exe` from the project directory so it can read your configuration and write `profiles.json`.
- Credentials inside `config.json` are not embedded into the `.exe` with this build script.

### Run the built executable
```powershell
cd "c:\Users\Xxima\Desktop\IRC Bot Test stuffs\dist"
./AscensionismBot.exe
```

## License
This project is provided as example code; adapt it freely for your needs.
