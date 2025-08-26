# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                                 #
#                   XClient Framework - Event Manager Module (manager.py)                         #
#                                                                                                 #
#   This module provides a universal, high-performance event handling interface for               #
#   the XClient Framework, designed for scalability and reliability.                              #
#                                                                                                 #
#   Copyright (C) 2025-2026 Aman Pandey. All Rights Reserved.                                     #
#                                                                                                 #
#   This file is part of the XClient Framework. It is proprietary and confidential.               #
#   Unauthorised copying, modification, distribution, or use of this file,                        #
#   via any medium, is strictly prohibited without the express written                            #
#   permission of the copyright holder.                                                           #
#                                                                                                 #
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                    #
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                      #
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                   #
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                        #
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                 #
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                 #
#   SOFTWARE.                                                                                     #
#                                                                                                 #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import asyncio
from typing import List, Dict, Callable, Coroutine, Union, Optional

# ==============================================================================
#  DEFINITIVE, PDF-COMPLIANT TELETHON IMPORTS (FINAL CORRECTED VERSION)
# ==============================================================================
# Corrected imports: Import 'events' and 'types' modules directly.
from telethon import events, types 

class EventManager:
    """
    Manages all event handling decorators for an XClient instance.
    This class provides a clean, high-level interface for responding to Telegram events,
    implementing abstractions for all filter types described in the PDF.
    """
    def __init__(self, client: 'XClient'):
        """
        Initialises the EventManager.

        Args:
            client ('XClient'): The XClient instance this manager will be attached to.
        """
        self.client: 'XClient' = client
        self._album_handlers: Dict[Callable, asyncio.Task] = {}
        # Corrected type hint to use types.Message directly.
        self._album_cache: Dict[int, List[types.Message]] = {}

    # ==============================================================================
    # --- Core Decorators for Message Handling ---
    # ==============================================================================

    def on_command(self, command: Union[str, List[str]], **kwargs):
        """
        Decorator to handle one or more standard text commands (e.g., /start).
        This is a high-level abstraction over `filters.Command`.

        Args:
            command (Union[str, List[str]]): A single command string or a list of command strings, without the leading slash.
            **kwargs: Additional arguments to pass to `client.on()`.
        """
        cmds = [command] if isinstance(command, str) else command
        # Use events.NewMessage directly
        return self.client.on(events.NewMessage(pattern=f'/({"|".join(cmds)})', **kwargs))

    def on_admin_command(self, command: Union[str, List[str]], **kwargs):
        """
        Decorator for commands that are restricted to the `admin_ids` list.
        This combines command matching with a `from_users` filter.

        Args:
            command (Union[str, List[str]]): The command or list of commands to handle.
            **kwargs: Additional arguments to pass to `client.on()`.
        """
        if not self.client.admin_ids:
            raise ValueError("admin_ids must be set in XClient to use on_admin_command.")
        cmds = [command] if isinstance(command, list) else [command]
        # Use events.NewMessage directly
        return self.client.on(events.NewMessage(pattern=f'/({"|".join(cmds)})', from_users=self.client.admin_ids, **kwargs))

    def on_text(self, pattern: Optional[str] = None, **kwargs):
        """
        Decorator to handle any text message, with an optional regex pattern.
        This is a direct abstraction over `filters.Text`.

        Args:
            pattern (Optional[str]): A regex pattern to match against the message text.
            **kwargs: Additional arguments to pass to `client.on()`.
        """
        # Use events.NewMessage directly
        return self.client.on(events.NewMessage(pattern=pattern, **kwargs))

    # ==============================================================================
    # --- Event Type Decorators ---
    # ==============================================================================

    def on_message_edit(self, **kwargs):
        """
        Decorator for when any message is edited. This abstracts `events.MessageEdited`.
        """
        # Use events.MessageEdited directly
        return self.client.on(events.MessageEdited(**kwargs))

    def on_message_delete(self, **kwargs):
        """
        Decorator for when one or more messages are deleted. This abstracts `events.MessageDeleted`.
        """
        # Use events.MessageDeleted directly
        return self.client.on(events.MessageDeleted(**kwargs))

    def on_callback_query(self, data: Optional[Union[bytes, str]] = None, **kwargs):
        """
        Decorator for handling inline button presses (callback queries). Abstracts `events.ButtonCallback`.

        Args:
            data (Optional[Union[bytes, str]]): If provided, the handler will only trigger for buttons with this specific data.
            **kwargs: Additional arguments to pass to `client.on()`.
        """
        if isinstance(data, str):
            data = data.encode()
        # Use events.ButtonCallback directly
        return self.client.on(events.ButtonCallback(data=data, **kwargs))

    def on_inline_query(self, **kwargs):
        """
        Decorator to handle incoming inline queries from users. Abstracts `events.InlineQuery`.
        """
        # Use events.InlineQuery directly
        return self.client.on(events.InlineQuery(**kwargs))
        
    # ==============================================================================
    # --- Granular Media Decorators (Implementing `filters.Media`) ---
    # ==============================================================================

    def on_photo(self, **kwargs):
        """Decorator for messages containing a photo."""
        return self.client.on(events.NewMessage(filters=events.filters.photo, **kwargs))

    def on_video(self, **kwargs):
        """Decorator for messages containing a video."""
        return self.client.on(events.NewMessage(filters=events.filters.video, **kwargs))

    def on_audio(self, **kwargs):
        """Decorator for messages containing audio (music files, not voice notes)."""
        return self.client.on(events.NewMessage(filters=events.filters.audio, **kwargs))

    def on_document(self, **kwargs):
        """Decorator for messages containing a generic file/document."""
        return self.client.on(events.NewMessage(filters=events.filters.document, **kwargs))

    def on_sticker(self, **kwargs):
        """Decorator for messages containing a sticker."""
        return self.client.on(events.NewMessage(filters=events.filters.sticker, **kwargs))

    def on_voice_note(self, **kwargs):
        """Decorator for messages containing a voice note."""
        return self.client.on(events.NewMessage(filters=events.filters.voice, **kwargs))

    def on_gif(self, **kwargs):
        """Decorator for messages containing an animated GIF."""
        return self.client.on(events.NewMessage(filters=events.filters.gif, **kwargs))

    def on_contact(self, **kwargs):
        """Decorator for messages sharing a contact."""
        return self.client.on(events.NewMessage(filters=events.filters.contact, **kwargs))

    def on_geo(self, **kwargs):
        """Decorator for messages sharing a geographic location."""
        return self.client.on(events.NewMessage(filters=events.filters.geo, **kwargs))

    # ==============================================================================
    # --- Advanced Album Decorator (Handles 'grouped_id') ---
    # ==============================================================================

    def on_album(self, func: Callable[[List[types.Message]], Coroutine]):
        """
        Decorator to handle albums (media sent together with the same grouped_id).
        This correctly implements the "album illusion" concept from the PDF by waiting
        for a short period to collect all parts of an album.

        Args:
            func (Callable[[List[types.Message]], Coroutine]): An async function that will receive a list of all message objects in the album.
        """
        async def album_timeout_task(event: events.NewMessage): # Correct type hint
            await asyncio.sleep(2.0)
            if event.grouped_id in self._album_cache:
                album_events = self._album_cache.pop(event.grouped_id)
                messages = [e.message for e in album_events]
                await func(messages)

        async def handler(event: events.NewMessage): # Correct type hint
            # This handler intercepts all new messages to check for albums.
            if event.grouped_id:
                if event.grouped_id not in self._album_cache:
                    self._album_cache[event.grouped_id] = []
                    asyncio.create_task(album_timeout_task(event))
                self._album_cache[event.grouped_id].append(event)
            else:
                # If it's a regular message, we still call the user's function,
                # but with a single-item list for consistency.
                await func([event.message])

        self.client.add_event_handler(handler, events.NewMessage)
        return handler

    # ==============================================================================
    # --- Chat & Message Property Decorators ---
    # ==============================================================================

    def on_user_join(self, **kwargs):
        """
        Decorator for when a user (or users) joins a chat. Abstracts `events.ChatAction`.
        The event object will have a `.user_ids` attribute.
        """
        # Use events.ChatAction directly.
        return self.client.on(events.ChatAction(func=lambda e: e.user_added or e.user_joined, **kwargs))

    def on_user_leave(self, **kwargs):
        """
        Decorator for when a user leaves or is kicked from a chat.
        The event object will have a `.user_id` attribute.
        """
        # Use events.ChatAction directly.
        return self.client.on(events.ChatAction(func=lambda e: e.user_left or e.user_kicked, **kwargs))
        
    def on_new_admin_event(self, **kwargs):
        """Decorator to track when chat admin permissions are changed."""
        # Use events.ChatAction directly.
        return self.client.on(events.ChatAction(func=lambda e: e.new_admin_rights is not None, **kwargs))

    def on_private_message(self, **kwargs):
        """Decorator that triggers only for messages in private chats (1-on-1)."""
        return self.client.on(events.NewMessage(func=lambda e: e.is_private, **kwargs))
    
    def on_group_message(self, **kwargs):
        """Decorator that triggers only for messages in groups (small groups or supergroups)."""
        return self.client.on(events.NewMessage(func=lambda e: e.is_group, **kwargs))
        
    def on_forward(self, **kwargs):
        """Decorator for messages that are forwards."""
        return self.client.on(events.NewMessage(func=lambda e: e.fwd_from, **kwargs))

    def on_reply(self, **kwargs):
        """Decorator for messages that are replies to another message."""
        return self.client.on(events.NewMessage(func=lambda e: e.is_reply, **kwargs))

    def on_outgoing(self, **kwargs):
        """Decorator for messages sent by the client itself (outgoing messages)."""
        return self.client.on(events.NewMessage(outgoing=True, **kwargs))