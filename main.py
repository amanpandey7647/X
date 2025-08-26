# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                    XClient Framework - Main Execution File
#
#   This file serves as the main entry point for the XClient Framework.
#   It initialises all core components, dynamically loads all plugins, and
#   concurrently runs both a bot and a user client.
#
#   Copyright (C) 2025-2026 Aman Pandey. All Rights Reserved.
#
#   This file is part of the XClient Framework. It is proprietary and confidential.
#   Unauthorised copying, modification, distribution, or use of this file,
#   via any medium, is strictly prohibited without the express written
#   permission of the copyright holder.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import asyncio
import importlib
import os
import sys
import traceback
v2 = "https://github.com/LonamiWebs/Telethon/archive/v2.zip#subdirectory=client"
os.system(f"pip install {v2}")
# ==============================================================================
#  CORE FRAMEWORK IMPORTS
# ==============================================================================
from client import XClient
from db import XDB
from decorators import CommandHandler
from misc import Misc
from utils import Utils

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
# IMPORTANT: Fill these values with your own details.
API_ID = os.environ.get("API_ID", None) or 123456
API_HASH = os.environ.get("API_HASH", None) or "your_api_hash"
BOT_TOKEN = os.environ.get("BOT_TOKEN", None) or "your_bot_token"

# --- Optional but Recommended ---
# The primary session for the userbot.
USER_SESSION_NAME = "X"
# Your user ID. This will be the main sudo user for both the bot and userbot.
OWNER_ID = os.environ.get("OWNER_ID", None) or 123456789
# A private chat/channel ID where the bots will send logs.
LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID", None) or -1001234567890

# ==============================================================================
#  GLOBAL INSTANCES (for plugins to import)
# ==============================================================================
bot: 'XClient' = None
user_client: 'XClient' = None

# ==============================================================================
#  PLUGIN LOADER
# ==============================================================================

def load_plugins(plugin_path: str):
    """
    Dynamically discovers and imports all Python files from a specified plugin directory.
    """
    if not os.path.isdir(plugin_path):
        print(f"INFO: '{plugin_path}' directory not found. Skipping plugin loading for this client.")
        return

    print(f"Loading plugins from '{plugin_path}'...")
    for filename in os.listdir(plugin_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            plugin_name = filename[:-3]
            try:
                importlib.import_module(f"{plugin_path}.{plugin_name}")
                print(f"  - Successfully loaded plugin: {plugin_name}")
            except Exception as e:
                print(f"  - FAILED to load plugin '{plugin_name}': {e}")
                traceback.print_exc()

# ==============================================================================
#  CLIENT STARTUP COROUTINES
# ==============================================================================

async def start_bot():
    """
    Initialises, configures, and runs the bot client.
    """
    global bot
    bot = XClient(
        session_name="bot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        admin_ids=[OWNER_ID],
        log_chat_id=LOG_CHAT_ID
    )
    bot.misc = Misc(bot)
    bot.utils = Utils(bot)
    bot.x_cmd = CommandHandler(bot, prefix="/")
    
    load_plugins("botplugins")
    
    async with bot:
        await bot.start()
        await bot.run_until_disconnected()

async def start_user_client():
    """
    Initialises, configures, and runs the user client (userbot).
    """
    global user_client
    user_client = XClient(
        session_name=USER_SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        admin_ids=[OWNER_ID],
        log_chat_id=LOG_CHAT_ID
    )
    user_client.misc = Misc(user_client)
    user_client.utils = Utils(user_client)
    user_client.x_cmd = CommandHandler(user_client, prefix=".")
    
    load_plugins("uplugins")
    
    async with user_client:
        await user_client.start()
        await user_client.run_until_disconnected()

# ==============================================================================
#  MAIN ASYNCHRONOUS FUNCTION
# ==============================================================================

async def main():
    """
    The main asynchronous function that orchestrates the concurrent execution
    of both the bot and the user client.
    """
    print("XClient Framework starting up...")
    print("Starting both Bot and User clients concurrently.")
    
    await asyncio.gather(
        start_bot(),
        start_user_client()
    )

# ==============================================================================
#  SCRIPT ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Check for placeholder configuration
    if API_ID == 12345 or API_HASH == "0123456789abcdef0123456789abcdef":
        print("FATAL ERROR: Please fill in your API_ID and API_HASH in main.py before running.")
    else:
        try:
            # Run the main asynchronous event loop
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Shutting down...")
        except Exception as e:
            print(f"An unexpected error occurred in the main execution loop: {e}")
            traceback.print_exc()
