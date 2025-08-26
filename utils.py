# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                    XClient Framework - Utilities Module (utils.py)
#
#   This module provides the Utils class, a collection of stateless helper
#   functions for data processing, formatting, and object creation.
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

from typing import List, Tuple, Optional, Union, Dict
import re
from manager import *
# Use a forward reference for the XClient and event types to avoid circular imports
from telethon import types
from telethon import types, events # events is needed for event object hints

class Utils:
    """
    Provides a rich toolkit of stateless utility functions for the XClient framework.
    This class handles common data manipulation and formatting tasks without
    performing direct client actions.
    """
    def __init__(self, client: 'XClient'):
        """
        Initialises the Utils class.

        Args:
            client ('XClient'): The XClient instance this toolkit is attached to.
                                This is needed for context but methods here
                                should avoid making API calls.
        """
        self.client: 'XClient' = client

    # ==============================================================================
    # --- Command & Text Parsing ---
    # ==============================================================================

    def parse_command(self, text: str, prefix: str = "/") -> Tuple[str, List[str], Dict[str, str]]:
        """
        Parses a command string into a command, arguments, and keyword arguments.
        Example: /ban @user reason=spamming -> ('ban', ['@user'], {'reason': 'spamming'})

        Args:
            text (str): The command string to parse.
            prefix (str, optional): The command prefix (e.g., '/', '!', '.'). Defaults to "/".

        Returns:
            Tuple[str, List[str], Dict[str, str]]: A tuple containing the command, a list of args, and a dict of kwargs.
        """
        if not text or not text.startswith(prefix):
            return "", [], {}
            
        parts = text.split()
        command = parts[0][len(prefix):].lower()
        args = []
        kwargs = {}
        for part in parts[1:]:
            if "=" in part:
                try:
                    key, val = part.split('=', 1)
                    kwargs[key.lower()] = val
                except ValueError:
                    args.append(part) # Treat as a normal arg if split fails
            else:
                args.append(part)
        return command, args, kwargs

    async def extract_user_id(self, event: events.NewMessage) -> Optional[int]:
        """
        Reliably extracts a target user ID from a message event.
        It checks for replies, mentions, and command arguments in that order.

        Args:
            event (events.NewMessage): The message event object.

        Returns:
            Optional[int]: The extracted user ID, or None if no user could be found.
        """
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.sender_id:
                return reply_msg.sender_id

        # Check for mentions in the message entities using the types.MessageEntityMentionName class.
        if event.entities:
            for entity in event.entities:
                if isinstance(entity, types.MessageEntityMentionName): # Correct usage
                    return entity.user_id
                elif isinstance(entity, types.MessageEntityTextUrl): # Handle t.me/user?id=123 links
                    match = re.search(r'tg://user\?id=(\d+)', entity.url)
                    if match:
                        return int(match.group(1))

        # Check for a user ID or username in the command arguments
        _, args, _ = self.parse_command(event.text)
        if args:
            target = args[0]
            if target.isdigit():
                return int(target)
            elif target.startswith('@'):
                try:
                    user = await self.client.get_entity(target)
                    if isinstance(user, types.User): # Ensure it's a user
                        return user.id
                except:
                    pass # Entity not found or not a user
        return None

    def sanitize_markdown(self, text: str) -> str:
        """
        Escapes characters in a string that have special meaning in Telegram's MarkdownV2.

        Args:
            text (str): The input string.

        Returns:
            str: The sanitized string, safe to be sent with `parse_mode='md'`.
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    # ==============================================================================
    # --- Data Formatting ---
    # ==============================================================================

    async def format_peer(self, peer, *, bold: bool = False, code: bool = False) -> str:
        """
        Creates a clean, markdown-mentionable string for any user, chat, or channel.

        Args:
            peer: The entity identifier (ID, username, etc.).
            bold (bool, optional): If True, bolds the name. Defaults to False.
            code (bool, optional): If True, wraps the ID in backticks. Defaults to False.

        Returns:
            str: A formatted string like "[User Name](tg://user?id=12345)".
        """
        try:
            entity = await self.client.get_entity(peer)
            name = entity.first_name if isinstance(entity, types.User) else entity.title
            
            # Sanitise markdown-sensitive characters in the name
            name = self.sanitize_markdown(name)

            # Apply formatting
            if bold:
                name = f"**{name}**"
            
            id_str = f" `{entity.id}`" if code else ""
            
            # Use entity.mention if it's available and makes sense
            if isinstance(entity, types.User) and entity.mention:
                return f"{entity.mention}{id_str}"
            elif isinstance(entity, (types.User, types.Channel)):
                return f"[{name}](tg://user?id={entity.id}){id_str}"
            else:
                # Fallback for other peer types or if mention/ID link isn't possible
                return f"{name}{id_str}"
        except Exception:
            return f"Unknown Peer" + (f" `{peer}`" if isinstance(peer, (int, str)) else "")

    def format_duration(self, seconds: int) -> str:
        """
        Formats a duration in seconds into a human-readable string (e.g., 1d 2h 3m).

        Args:
            seconds (int): The total number of seconds.

        Returns:
            str: A formatted duration string.
        """
        if seconds <= 0: return "0s"
        m, s = divmod(seconds, 60); h, m = divmod(m, 60); d, h = divmod(h, 24)
        parts = [f"{d}d" if d else "", f"{h}h" if h else "", f"{m}m" if m else "", f"{s}s" if s or not any([d,h,m]) else ""]
        return " ".join(p for p in parts if p)

    def format_bytes(self, size_bytes: int) -> str:
        """
        Converts a size in bytes to a human-readable string (KB, MB, GB).

        Args:
            size_bytes (int): The size in bytes.

        Returns:
            str: A formatted size string like "1.23 MB".
        """
        if size_bytes == 0: return "0B"
        power = 1024; n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size_bytes >= power and n < len(power_labels) - 1:
            size_bytes /= power; n += 1
        return f"{size_bytes:.2f} {power_labels[n]}B"

    def humanize_list(self, items: List[str]) -> str:
        """
        Converts a list of strings into a grammatically correct, human-readable string.
        Example: ['A', 'B', 'C'] -> "A, B, and C"

        Args:
            items (List[str]): The list of strings to format.

        Returns:
            str: The formatted string.
        """
        if not items: return ""
        if len(items) == 1: return items[0]
        if len(items) == 2: return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    # ==============================================================================
    # --- Keyboard & UI Creation ---
    # ==============================================================================

    def create_inline_buttons(self, layout: List[List[Tuple[str, str]]]) -> List[List[types.Button]]:
        """
        Creates a list of inline keyboard buttons from a simple layout structure.
        The data part is encoded to bytes for callback queries.

        Args:
            layout (List[List[Tuple[str, str]]]): A list of rows, where each row is a list of (text, data) tuples.

        Returns:
            List[List[types.Button]]: The formatted list of buttons ready for use in `send_message`.
        """
        return [[types.Button.inline(text, data=data.encode()) for text, data in row] for row in layout]
    
    def create_url_buttons(self, layout: List[List[Tuple[str, str]]]) -> List[List[types.Button]]:
        """
        Creates a list of inline keyboard buttons that link to external URLs.

        Args:
            layout (List[List[Tuple[str, str]]]): A list of rows, where each row is a list of (text, url) tuples.

        Returns:
            List[List[types.Button]]: The formatted list of buttons ready for use in `send_message`.
        """
        return [[types.Button.url(text, url=url) for text, url in row] for row in layout]
