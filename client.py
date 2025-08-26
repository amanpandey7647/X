# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                    XClient Framework - Core Client Module (client.py)
#
#   This module provides the core XClient class, a database-integrated,
#   full-fledged framework built upon the Telethon library.
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
import getpass
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union

from telethon import Client, events, types
from telethon.types import User, Message, ChatRestriction, PasswordToken
from db import XDB
# ==============================================================================
#  THE PRECISE & OPTIMIZED XCLIENT FRAMEWORK CLASS
# ==============================================================================

class XClient(Client):
    """An advanced, database-integrated client framework built on Telethon."""
    def __init__(self, session_name: str, api_id: int, api_hash: str, **kwargs):
        """Initialises the XClient, its database, and all configurations."""
        super().__init__(session_name, api_id, api_hash)
        
        self.db = XDB(db_path=kwargs.get("db_path", f"{session_name}.db"))
        self.bot_token = kwargs.get("bot_token")
        self.password = kwargs.get("password")
        self.admin_ids = self.db.get_all_sudo().union(set(kwargs.get("admin_ids", [])))
        self.log_chat_id = kwargs.get("log_chat_id")
        self._me: Optional[User] = kwargs.get("OWNER_ID") or None
        
        print(f"XClient '{session_name}' initialised. Sudo Admins: {self.admin_ids or 'None'}")

    async def start(self) -> 'XClient':
        """Connects and logs in using the strict, unified interactive procedure."""
        print(f"[{self.session.filename}] Starting client...")
        if not self.is_connected():
            await self.connect()
            
        await self.interactive_login(self.bot_token, password=self.password)
        
        self._me = await self.get_me()
        if not self.bot_token and self._me.id not in self.admin_ids:
            self.admin_ids.add(self._me.id)
            self.db.add_sudo(self._me.id)

        try:
            if isinstance(self._me, User):
                self.db.cache_user(self._me)
        except:
            pass
        if isinstance(self._me, User):
            self.db.add_bot_user(self._me.id, self._me.first_name)
            
        print(f"[{self.session.filename}] Startup complete. Logged in as: {self._me.first_name}")
        return self

    async def stop(self):
        """Gracefully closes the database and disconnects."""
        print(f"[{self.session.filename}] Stopping XClient...")
        self.db.close()
        await self.disconnect()
        print(f"[{self.session.filename}] Client disconnected.")

    # --- Core Decorators ---
    def on_command(self, command: Union[str, List[str]], **kwargs):
        """Decorator for standard text commands (e.g., /start)."""
        cmds = [command] if isinstance(command, str) else command
        return self.on(events.NewMessage(pattern=f'/({"|".join(cmds)})', **kwargs))

    def on_admin_command(self, command: Union[str, List[str]], **kwargs):
        """Decorator for commands restricted to admin_ids."""
        if not self.admin_ids: raise ValueError("admin_ids not set.")
        cmds = [command] if isinstance(command, str) else command
        return self.on(events.NewMessage(pattern=f'/({"|".join(cmds)})', from_users=self.admin_ids, **kwargs))

    # --- Important High-Level Methods ---
    async def log(self, message: str, level: str = "INFO"):
        """Logs a message to the configured log_chat_id."""
        if self.log_chat_id:
            try: await self.send_message(self.log_chat_id, f"**{level}:** `{message}`", parse_mode='md')
            except Exception as e: print(f"LOGGING FAILED: {e}")

    async def ask(self, peer, question: str, *, timeout=60) -> Optional[Message]:
        """Asks a question and waits for a reply from the same user."""
        async with self.conversation(peer, timeout=timeout) as conv:
            await conv.send_message(question)
            try:
                response = await conv.get_response()
                return response
            except asyncio.TimeoutError:
                return None

    async def get_user_info(self, entity, force_api=False) -> Optional[Dict]:
        """Gets user info, using the database cache first for speed."""
        try:
            # The client's get_entity method itself is the resolver now.
            if isinstance(entity, int) and not force_api and (cached := self.db.get_user_from_cache(entity)):
                return cached
            e = await self.get_entity(entity)
            try:
                if isinstance(e, User):
                    # Log the user in the bot_users table for tracking purposes
                    self.db.add_bot_user(e.id, e.first_name)
                    return {'id': e.id, 'username': e.username, 'first_name': e.first_name}
            except:
                pass
            if isinstance(e, User): self.db.cache_user(e)
            return {'id': e.id, 'username': e.username, 'first_name': e.first_name}
        except: return None
        
    async def purge(self, event: Message, limit: int = 100):
        """Deletes messages from a target user up to the replied message."""
        if not event.is_reply: return await event.edit("Reply to a message to start purging.")
        
        reply_msg = await event.get_reply_message()
        target_user_id = reply_msg.sender_id
        
        message_ids = [msg.id async for msg in self.iter_messages(event.chat_id, limit=limit, min_id=reply_msg.id - 1) if msg.sender_id == target_user_id]
        message_ids.append(event.id)
        
        count = await self.delete_messages(event.chat_id, message_ids, revoke=True)
        confirm = await self.send_message(event.chat_id, f"Purged {len(count)} messages.")
        await asyncio.sleep(3); await confirm.delete()

    async def promote(self, chat_id, user_id, rank="Admin"):
        """Promotes a user to admin with default rights."""
        # Use the types factory to create the ChatAdminRights object.
        rights = types.ChatAdminRights(post_messages=True, add_admins=False, invite_users=True, change_info=True, ban_users=True, delete_messages=True, pin_messages=True)
        await self.edit_admin(chat_id, user_id, admin_rights=rights, rank=rank)
