# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#               XClient Framework - Decorators Module (decorators.py)
#
#   This module provides the CommandHandler class and the powerful @XEVENT and
#   @XCMD decorators, which serve as the single entry point for creating all
#   event handlers with rich, configurable permission handling, error reporting,
#   and a PDF-compliant filter system.
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
import traceback
import time
from functools import wraps
from typing import List, Dict, Callable, Coroutine, Union, Optional, Any

# Use forward references for XClient to avoid circular imports
from telethon import events
from telethon.events import filters

class CommandHandler:
    """
    Manages the registration and execution of all bot and userbot event handlers.
    This class contain @XEVENT and @XCMD decorators.
    """
    def __init__(self, client: 'XClient', prefix: str = "/"):
        """
        Initialises the CommandHandler.

        Args:
            client ('XClient'): The XClient instance this handler will be attached to.
            prefix (str, optional): The default character to be used for commands. Defaults to "/".
        """
        self.client: 'XClient' = client
        self.prefix: str = prefix
        self.registered_commands: Dict[str, Dict] = {}
        self.cooldowns: Dict[str, Dict[int, float]] = {}

    def XEVENT(
        self,
        event_type,
        filters: Optional[List[Callable]] = None,
        cooldown: int = 5,
        sudo_only: bool = False,
        owner_only: bool = False,
        **kwargs
    ) -> Callable:
        """
        The master decorator for handling all Telegram events with a rich filter system.
        This is the core of the event handling framework.

        Args:
            event_type: The type of event to listen for (e.g., `events.NewMessage`, `events.MessageEdited`).
            filters (Optional[List[Callable]], optional): A list of Telethon filter objects (e.g., `[filters.group, filters.photo]`).
            cooldown (int, optional): Per-user cooldown in seconds. Defaults to 5.
            sudo_only (bool, optional): Restricts the handler to registered sudo users. Defaults to False.
            owner_only (bool, optional): Restricts the handler to the bot/userbot owner. Defaults to False.
            **kwargs: Additional arguments to pass directly to `client.on()`.
        """
        def decorator(func: Callable) -> Callable:
            handler_name = func.__name__

            @wraps(func)
            async def wrapper(event):
                # --- Permission Checks ---
                if owner_only and event.sender_id != self.client._me.id:
                    return
                if sudo_only and event.sender_id not in self.client.admin_ids:
                    return

                # --- Cooldown Check ---
                if handler_name not in self.cooldowns:
                    self.cooldowns[handler_name] = {}
                
                user_cooldowns = self.cooldowns[handler_name]
                if event.sender_id in user_cooldowns:
                    time_since_last_call = time.time() - user_cooldowns[event.sender_id]
                    if time_since_last_call < cooldown:
                        return
                
                user_cooldowns[event.sender_id] = time.time()

                # --- Execution & Error Handling ---
                try:
                    await func(event)
                except Exception:
                    error_traceback = traceback.format_exc()
                    error_message = (
                        f"An error occurred in the handler `{handler_name}`.\n\n"
                        f"**Chat:** {getattr(event, 'chat_id', 'N/A')}\n"
                        f"**User:** {getattr(event, 'sender_id', 'N/A')}\n\n"
                        f"**Traceback:**\n```{error_traceback}```"
                    )
                    await self.client.log(error_message, "ERROR")
                    if hasattr(event, 'reply'):
                        await event.reply("An internal error occurred. The administrator has been notified.")

            # Combine filters if multiple are provided
            final_filter = filters.All(*filters) if filters and len(filters) > 1 else (filters[0] if filters else None)
            
            # Register the handler with Telethon
            self.client.on(event_type(pattern=kwargs.pop('pattern', None), func=final_filter, **kwargs))(wrapper)

            return wrapper
        return decorator

    def XCMD(
        self,
        command: Union[str, List[str]],
        category: str = "Misc",
        description: str = "No description provided.",
        usage: str = "",
        **kwargs
    ) -> Callable:
        """
        A convenience decorator for creating commands. It is a wrapper around @XEVENT.

        Args:
            command (Union[str, List[str]]): The command name or a list of aliases.
            category (str, optional): The category for the help menu. Defaults to "Misc".
            description (str, optional): A description for the help menu.
            usage (str, optional): Example usage for the help menu.
            **kwargs: All other arguments are passed directly to @XEVENT (e.g., `cooldown`, `sudo_only`).
        """
        cmds = [command] if isinstance(command, str) else command
        main_command = cmds[0]
        
        # Create a command filter based on the provided command names
        command_filter = filters.Command(cmds, prefix=self.prefix)
        
        # Get existing filters from kwargs and add the new command filter
        existing_filters = kwargs.pop('filters', [])
        if not isinstance(existing_filters, list):
            existing_filters = [existing_filters]
        all_filters = [command_filter] + existing_filters

        # Register the command for the help menu
        if main_command not in self.registered_commands:
            self.registered_commands[main_command] = {
                'category': category,
                'description': description,
                'usage': f"{self.prefix}{main_command} {usage}".strip(),
                'aliases': [f"{self.prefix}{c}" for c in cmds]
            }
            
        return self.XEVENT(events.NewMessage, filters=all_filters, **kwargs)

    def get_all_help_text(self, category_emojis: Optional[Dict[str, str]] = None) -> str:
        """
        Generates a beautifully formatted help string for all registered commands.

        Args:
            category_emojis (Optional[Dict[str, str]]): A dictionary mapping category names to emojis.

        Returns:
            str: The complete help text.
        """
        if not self.registered_commands:
            return "No commands are currently available."
            
        if category_emojis is None:
            category_emojis = {
                "Admin": "👑", "Misc": "🧩", "Fun": "😂", "Utils": "🛠️", "Database": "🗂️"
            }

        categorized = {}
        for cmd, data in self.registered_commands.items():
            cat = data['category']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(data)

        help_text = "Here are the available commands:\n\n"
        
        sorted_categories = sorted(categorized.keys())
        for category in sorted_categories:
            emoji = category_emojis.get(category, "🔹")
            help_text += f"{emoji} **{category}**\n"
            for cmd_data in sorted(categorized[category], key=lambda x: x['aliases'][0]):
                aliases_str = ", ".join(cmd_data['aliases'])
                help_text += f"  - {aliases_str}\n"
                help_text += f"    *Description:* {cmd_data['description']}\n"
                if cmd_data['usage']:
                    help_text += f"    *Usage:* `{cmd_data['usage']}`\n"
            help_text += "\n"
            
        return help_text.strip()
