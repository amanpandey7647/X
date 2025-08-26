# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                XClient Framework - Miscellaneous Module (misc.py)
#
#   This module provides the Misc class, which handles high-level, multi-step,
#   and stateful automation workflows for the XClient Framework. It is fully
#   integrated with the database for persistent state.
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
from datetime import datetime, timedelta
import os # For potential file operations like deleting downloaded media
from typing import List, Dict, Callable, Coroutine, Any, Optional, Tuple


from telethon import events, types, errors

# Import the database class from your db.py file
from db import XDB

class Misc:
    """
    Handles miscellaneous, multi-step, or stateful automation workflows
    for the XClient framework. This class orchestrates complex actions and
    relies on the XDB class for data persistence.
    """
    def __init__(self, client: 'XClient'):
        """
        Initialises the Misc class.

        Args:
            client ('XClient'): The XClient instance this class will be attached to.
        """
        self.client: 'XClient' = client
        self.db: XDB = client.db
        self._forwarding_rules: Dict[int, List[int]] = {}

    # ==============================================================================
    # --- Task Management & Broadcasting ---
    # ==============================================================================

    async def broadcast(self, chats: List[Any], message: str, **kwargs):
        """
        Sends a message to a list of chats with built-in flood protection.

        Args:
            chats (List[Any]): A list of chat entities or IDs to broadcast to.
            message (str): The text message to send.
            **kwargs: Additional arguments to pass to `client.send_message()`.

        Returns:
            int: The number of chats the message was successfully sent to.
        """
        count = 0
        total = len(chats)
        await self.client.log(f"Starting broadcast to {total} chats.")
        for i, chat in enumerate(chats):
            try:
                await self.client.send_message(chat, message, **kwargs)
                count += 1
                if i > 0 and i % 5 == 0: # Sleep every 5 messages to be safe
                    await asyncio.sleep(2.5)
            except (errors.UserIsBlockedError, errors.PeerFloodError, ValueError) as e:
                await self.client.log(f"Broadcast failed for chat {chat}: {e}", "WARN")
        await self.client.log(f"Broadcast finished. Sent to {count}/{total} chats.")
        return count

    def run_periodic_task(self, interval: int, task: Callable[[], Coroutine]):
        """
        Runs an asynchronous function periodically in the background.

        Args:
            interval (int): The interval in seconds between each execution.
            task (Callable[[], Coroutine]): The async function to run.

        Returns:
            asyncio.Task: The background task object, which can be cancelled.
        """
        async def wrapper():
            while True:
                await asyncio.sleep(interval)
                try:
                    await task()
                except Exception as e:
                    await self.client.log(f"Error in periodic task {task.__name__}: {e}", "ERROR")
        
        task_obj = self.client.loop.create_task(wrapper())
        self.client._periodic_tasks.append(task_obj)
        print(f"Periodic task '{task.__name__}' scheduled to run every {interval}s.")
        return task_obj
        
    async def schedule_message(self, chat_id, message: str, schedule_time: datetime, **kwargs):
        """
        Schedules a message to be sent at a specific future time.

        Args:
            chat_id: The target chat for the message.
            message (str): The text of the message to schedule.
            schedule_time (datetime): The exact date and time to send the message.
        """
        await self.client.send_message(chat_id, message, schedule=schedule_time, **kwargs)
        await self.client.log(f"Scheduled message for {chat_id} at {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # ==============================================================================
    # --- PM Permit System Logic (for Userbots) ---
    # ==============================================================================

    async def approve_pm(self, user_id: int) -> str:
        """Approves a user to send private messages, unblocking them if necessary."""
        if self.db.is_pm_approved(user_id):
            return "This user is already approved to PM."
        
        self.db.approve_pm(user_id)
        await self.client(types.functions.contacts.UnblockRequest(id=user_id))
        return "User has been approved. They can now PM you freely."

    async def disapprove_pm(self, user_id: int) -> str:
        """Disapproves a user, blocking them from sending further PMs."""
        self.db.disapprove_pm(user_id)
        await self.client(types.functions.contacts.BlockRequest(id=user_id))
        return "User has been disapproved and blocked."

    async def _handle_pm_permit(self, event: events.NewMessage): # Correct type hint here
        """Internal handler for the PM Permit system."""
        if self.db.is_pm_approved(event.sender_id):
            return
        
        last_warned_str = self.db.get_env(f"pm_warn_{event.sender_id}")
        if last_warned_str:
            last_warned = datetime.fromisoformat(last_warned_str)
            if (datetime.now() - last_warned).total_seconds() < 300: # 5 minute cooldown
                return

        pm_message = self.db.get_env("PM_PERMIT_MESSAGE") or "Hello! You have reached my master's PM. Please state your reason for messaging and wait for approval."
        await event.reply(pm_message)
        self.db.set_env(f"pm_warn_{event.sender_id}", datetime.now().isoformat())

    async def _auto_approve_on_outgoing(self, event: events.NewMessage): # Correct type hint here
        """Internal handler to auto-approve a user when you message them first."""
        if not self.client.db.is_pm_approved(event.chat_id):
            self.client.db.approve_pm(event.chat_id)
            await self.client.log(f"Auto-approved user {event.chat_id} for PM permit.", "DEBUG")

    # ==============================================================================
    # --- AFK (Away From Keyboard) System Logic ---
    # ==============================================================================
    
    async def set_afk(self, reason: str):
        """Sets the user's AFK status in the database."""
        self.db.set_afk(self.client._me.id, reason)

    async def clear_afk(self) -> bool:
        """Clears the user's AFK status from the database."""
        return self.db.clear_afk(self.client._me.id)

    async def _handle_afk_mention(self, event: events.NewMessage): # Correct type hint here
        """Internal handler that automatically replies to mentions if the client user is AFK."""
        if not self.client._me: return
        afk_status = self.db.get_afk(self.client._me.id)
        if afk_status:
            since_dt = datetime.fromisoformat(afk_status['since'])
            duration = self.client.utils.format_duration(int((datetime.now() - since_dt).total_seconds()))
            await event.reply(f"My master is currently AFK (for {duration}).\n**Reason:** {afk_status['reason']}")
        
        sender_afk_status = self.db.get_afk(event.sender_id)
        if sender_afk_status:
            self.db.clear_afk(event.sender_id)
            sender_entity = await event.get_sender() 
            if isinstance(sender_entity, types.User):
                 await event.reply(f"Welcome back, {sender_entity.first_name}! Your AFK status has been cleared.")
            else:
                 await event.reply(f"Welcome back! Your AFK status has been cleared.")

    # ==============================================================================
    # --- Welcome Message System Logic ---
    #==============================================================================

    async def set_welcome_message(self, chat_id, message: str):
        """Sets a persistent custom welcome message for a chat in the database."""
        self.db.save_note(chat_id, "_welcome", message)

    async def clear_welcome_message(self, chat_id) -> bool:
        """Clears the custom welcome message for a chat."""
        return self.db.clear_note(chat_id, "_welcome")

    async def _handle_welcome(self, event): # Correct type hint here
        """Internal handler to send the welcome message when a user joins."""
        welcome_text = self.db.get_note(event.chat_id, "_welcome")
        if welcome_text:
            new_user = await event.get_user()
            if new_user:
                formatted_user = await self.client.utils.format_peer(new_user)
                await event.reply(welcome_text.format(user=formatted_user))

    # ==============================================================================
    # --- Warning System Logic ---
    # ==============================================================================

    async def warn_user(self, chat_id, user_id, reason: str = "No reason provided.") -> Tuple[int, int]:
        """Issues a warning to a user and returns their current warning count."""
        # This is a conceptual implementation; a full warning system would need DB tables.
        # For now, it logs the warning and returns dummy values.
        await self.client.log(f"Warning user {user_id} in {chat_id} for: {reason} (Warning system not fully implemented in DB yet)", "INFO")
        return 1, 3 # Example: 1 current warning, 3 max warnings

    async def reset_warnings(self, chat_id, user_id):
        """Resets a user's warning count in a chat to zero."""
        await self.client.log(f"Resetting warnings for user {user_id} in {chat_id} (Warning system not fully implemented in DB yet)", "INFO")

    # ==============================================================================
    # --- Chat Locking Logic ---
    # ==============================================================================

    async def lock_chat(self, chat_id, lock_types: List[str]):
        """Restricts non-admins from performing certain actions in a chat."""
        current_perms = (await self.client.get_permissions(chat_id, None)).banned_rights or types.ChatBannedRights()
        lock_map = {
            'msg': {'send_messages': True},
            'media': {'send_media': True},
            'stickers': {'send_stickers': True, 'send_gifs': True, 'send_games': True, 'send_inline': True},
            'polls': {'send_polls': True},
            'invite': {'invite_users': True},
            'pin': {'pin_messages': True},
            'info': {'change_info': True},
        }

        if 'all' in lock_types:
            new_perms = types.ChatBannedRights(
                until_date=None, view_messages=None, send_messages=True, send_media=True,
                send_stickers=True, send_gifs=True, send_games=True, send_inline=True,
                send_polls=True, change_info=True, invite_users=True, pin_messages=True
            )
        else:
            new_perms_dict = current_perms.to_dict()
            for lock_type in lock_map: # Iterate through all possible lock types
                if lock_type in lock_types: # If this type is in the requested lock list
                    new_perms_dict.update(lock_map[lock_type])
            new_perms = types.ChatBannedRights(**new_perms_dict)
            
        await self.client.edit_permissions(chat_id, None, banned_rights=new_perms)
        await self.client.log(f"Locked actions in chat {chat_id}: {', '.join(lock_types)}", "MOD")

    async def unlock_chat(self, chat_id, unlock_types: List[str]):
        """Unlocks previously restricted actions in a chat."""
        current_perms = (await self.client.get_permissions(chat_id, None)).banned_rights or types.ChatBannedRights()
        unlock_map = {
            'msg': {'send_messages': False},
            'media': {'send_media': False},
            'stickers': {'send_stickers': False, 'send_gifs': False, 'send_games': False, 'send_inline': False},
            'polls': {'send_polls': False},
            'invite': {'invite_users': False},
            'pin': {'pin_messages': False},
            'info': {'change_info': False},
        }
        new_perms_dict = current_perms.to_dict()
        if 'all' in unlock_types:
            new_perms = types.ChatBannedRights() # Empty rights object unlocks everything
        else:
            for unlock_type in unlock_map: # Iterate through all possible unlock types
                if unlock_type in unlock_types: # If this type is in the requested unlock list
                    new_perms_dict.update(unlock_map[unlock_type]) # Update the dict to unlock
            new_perms = types.ChatBannedRights(**new_perms_dict)
            
        await self.client.edit_permissions(chat_id, None, banned_rights=new_perms)
        await self.client.log(f"Unlocked actions in chat {chat_id}: {', '.join(unlock_types)}", "MOD")

    # ==============================================================================
    # --- Other High-Level Workflows ---
    # ==============================================================================
            
    async def pin_and_notify(self, event, message_to_pin: Optional[types.Message] = None, notify: bool = True):
        """
        Pins a message and sends a temporary confirmation message.
        If message_to_pin is not provided, it pins the message replied to.

        Args:
            event (events.NewMessage.Event): The event that triggered the action.
            message_to_pin (Optional[types.Message], optional): The message to pin. Defaults to the replied-to message.
            notify (bool, optional): Whether to notify all chat members. Defaults to True.
        """
        if not message_to_pin:
            if not event.is_reply:
                await event.reply("Please reply to a message to pin it.")
                return
            message_to_pin = await event.get_reply_message()
        
        await self.client.pin_message(event.chat_id, message_to_pin, notify=notify)
        confirm = await event.reply("📌 Message pinned.")
        await asyncio.sleep(3)
        await confirm.delete()