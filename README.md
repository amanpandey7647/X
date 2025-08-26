
# XClient Framework

A **pluggable Telegram Userbot and Assistant Framework** built on Telethon, designed for power users, automation, and extensibility.

---

## Features

- **Userbot & Bot Mode**: Run as both a userbot and a bot, with seamless switching.
- **Pluggable Architecture**: Easily add, remove, or update plugins for new features.
- **Advanced Event Handling**: Rich decorators for commands, admin actions, media, and more.
- **Database Integration**: Persistent storage using SQLite (with optional MongoDB support).
- **Automation & Workflows**: Built-in support for multi-step, stateful automations.
- **Permission & Cooldown System**: Fine-grained access control and anti-spam.
- **Utilities Toolkit**: Helpers for parsing, formatting, and Telegram-specific tasks.
- **Modern Pythonic Codebase**: Type hints, async/await, and modular design.
- **Cross-Platform Scripts**: Utilities for Python upgrades and shell command execution.
- **Logging & Admin Controls**: Owner/sudo user system, log chat, and admin commands.

---

## Core Modules

- **client.py**: The main `XClient` class, extends Telethon’s Client with DB and admin logic.
- **db.py**: Database abstraction for user, admin, moderation, and automation data.
- **manager.py**: EventManager for all Telegram event decorators (commands, media, joins, etc).
- **decorators.py**: Powerful decorators for commands and events, with permission/cooldown.
- **utils.py**: Stateless helpers for parsing commands, formatting, and Telegram objects.
- **misc.py**: High-level automation and workflow orchestration.
- **mod.py**: Safe shell command execution utilities.
- **up.py** / **pyup.py.py**: Scripts for upgrading Python (macOS/Homebrew).

---

## Plugin System

- **botplugins/** and **uplugins/**: Drop-in folders for bot and userbot plugins.
- Plugins can register commands, event handlers, and automation tasks using the provided decorators.

---

## Getting Started

> **Note:** The main source code is currently private and will be made public soon.

### Requirements

- Python 3.8+
- Telethon (auto-installed)
- SQLite (default) or MongoDB (optional)
- macOS (for upgrade scripts) or Linux/Windows for core bot

### Quick Start

1. Clone the repo (when public).
2. Fill in your API credentials in `main.py` or via environment variables.
3. Add your plugins to `botplugins/` or `uplugins/`.
4. Run the bot:
	```bash
	python3 main.py
	```

---

## Security & License

- **License:** GNU Affero General Public License v3.0 (see LICENSE)
- **Copyright:** (C) 2025-2026 Aman Pandey. All Rights Reserved.
- **Warning:** Unauthorized copying, modification, or distribution is strictly prohibited.

---

## Credits

- Built on [Telethon](https://github.com/LonamiWebs/Telethon)
- Designed and maintained by Aman Pandey

---
