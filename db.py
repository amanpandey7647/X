# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                                 #
#                    XClient Framework - Database Module (db.py)                                  #
#                                                                                                 #
#   This module provides a universal, high-performance database interface for                     #
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

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Set, Union, Any


try:
    import pymongo
    from pymongo.collection import Collection
    from pymongo.database import Database
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False


class _SQLiteHandler:
    """Internal handler for all SQLite database operations. This is the fallback engine."""
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Creates all the necessary tables in the SQLite database if they don't already exist."""
        # --- Core & User Management Tables ---
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS env_vars (key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sudo_users (user_id INTEGER PRIMARY KEY)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY, first_name TEXT, start_date TEXT NOT NULL)''')

        # --- Moderation Tables ---
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS gban (user_id INTEGER PRIMARY KEY, reason TEXT, enforcer INTEGER, date TEXT NOT NULL)''')
        
        # --- Automation & Customisation Tables ---
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS notes (chat_id INTEGER, note_name TEXT, note_content TEXT, PRIMARY KEY (chat_id, note_name))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS stats (stat_name TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)''')
        self.conn.commit()

    def set_env(self, key: str, value: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO env_vars (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_env(self, key: str) -> Optional[str]:
        self.cursor.execute(
            "SELECT value FROM env_vars WHERE key = ?",
            (key,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def add_bot_user(self, user_id: int, first_name: str):
        self.cursor.execute(
            "INSERT OR IGNORE INTO bot_users (user_id, first_name, start_date) VALUES (?, ?, ?)",
            (user_id, first_name, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_bot_user_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM bot_users")
        count = self.cursor.fetchone()[0]
        return count
        
    def get_all_bot_users(self) -> List[int]:
        self.cursor.execute("SELECT user_id FROM bot_users")
        users = [row[0] for row in self.cursor.fetchall()]
        return users

    def add_sudo(self, user_id: int):
        self.cursor.execute(
            "INSERT OR IGNORE INTO sudo_users (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def remove_sudo(self, user_id: int):
        self.cursor.execute(
            "DELETE FROM sudo_users WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
        
    def get_all_sudo(self) -> Set[int]:
        self.cursor.execute("SELECT user_id FROM sudo_users")
        sudoers = {row[0] for row in self.cursor.fetchall()}
        return sudoers
        
    def gban_user(self, user_id: int, enforcer: int, reason: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO gban (user_id, enforcer, reason, date) VALUES (?, ?, ?, ?)",
            (user_id, enforcer, reason, datetime.now().isoformat())
        )
        self.conn.commit()

    def ungban_user(self, user_id: int) -> bool:
        self.cursor.execute(
            "DELETE FROM gban WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def is_gban(self, user_id: int) -> Optional[Dict]:
        self.cursor.execute(
            "SELECT reason, enforcer, date FROM gban WHERE user_id = ?",
            (user_id,)
        )
        row = self.cursor.fetchone()
        return {'reason': row[0], 'enforcer': row[1], 'date': row[2]} if row else None
        
    def save_note(self, chat_id: int, note_name: str, content: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO notes (chat_id, note_name, note_content) VALUES (?, ?, ?)",
            (chat_id, note_name, content)
        )
        self.conn.commit()

    def get_note(self, chat_id: int, note_name: str) -> Optional[str]:
        self.cursor.execute(
            "SELECT note_content FROM notes WHERE chat_id = ? AND note_name = ?",
            (chat_id, note_name)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def clear_note(self, chat_id: int, note_name: str) -> bool:
        self.cursor.execute(
            "DELETE FROM notes WHERE chat_id = ? AND note_name = ?",
            (chat_id, note_name)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_notes(self, chat_id: int) -> List[str]:
        self.cursor.execute(
            "SELECT note_name FROM notes WHERE chat_id = ?",
            (chat_id,)
        )
        notes = [row[0] for row in self.cursor.fetchall()]
        return notes
        
    def increment_stat(self, stat_name: str, amount: int = 1):
        self.cursor.execute(
            "UPDATE stats SET value = value + ? WHERE stat_name = ?",
            (amount, stat_name)
        )
        if self.cursor.rowcount == 0:
            self.cursor.execute(
                "INSERT INTO stats (stat_name, value) VALUES (?, ?)",
                (stat_name, amount)
            )
        self.conn.commit()

    def get_stat(self, stat_name: str) -> int:
        self.cursor.execute(
            "SELECT value FROM stats WHERE stat_name = ?",
            (stat_name,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def close(self):
        self.conn.close()

class _MongoHandler:
    """Internal handler for all MongoDB database operations."""
    def __init__(self, mongo_url: str):
        self.client = pymongo.MongoClient(mongo_url)
        self.db = self.client.get_default_database()

        # Define collections (equivalent to tables)
        self.env_vars: Collection = self.db.env_vars
        self.sudo_users: Collection = self.db.sudo_users
        self.bot_users: Collection = self.db.bot_users
        self.gban: Collection = self.db.gban
        self.notes: Collection = self.db.notes
        self.stats: Collection = self.db.stats

        self._create_indexes()

    def _create_indexes(self):
        """Creates indexes on collections to ensure efficient queries and enforce uniqueness where needed."""
        self.env_vars.create_index("key", unique=True)
        self.sudo_users.create_index("user_id", unique=True)
        self.bot_users.create_index("user_id", unique=True)
        self.gban.create_index("user_id", unique=True)
        self.notes.create_index([("chat_id", pymongo.ASCENDING), ("note_name", pymongo.ASCENDING)], unique=True)
        self.stats.create_index("stat_name", unique=True)

    def set_env(self, key: str, value: str):
        self.env_vars.update_one({'key': key}, {'$set': {'value': value}}, upsert=True)

    def get_env(self, key: str) -> Optional[str]:
        doc = self.env_vars.find_one({'key': key})
        return doc['value'] if doc else None

    def add_bot_user(self, user_id: int, first_name: str):
        self.bot_users.update_one(
            {'user_id': user_id},
            {'$setOnInsert': {'first_name': first_name, 'start_date': datetime.now().isoformat()}},
            upsert=True
        )

    def get_bot_user_count(self) -> int:
        return self.bot_users.count_documents({})
        
    def get_all_bot_users(self) -> List[int]:
        cursor = self.bot_users.find({}, {'user_id': 1})
        return [doc['user_id'] for doc in cursor]

    def add_sudo(self, user_id: int):
        self.sudo_users.update_one({'user_id': user_id}, {'$set': {'user_id': user_id}}, upsert=True)

    def remove_sudo(self, user_id: int):
        self.sudo_users.delete_one({'user_id': user_id})
        
    def get_all_sudo(self) -> Set[int]:
        cursor = self.sudo_users.find({}, {'user_id': 1})
        return {doc['user_id'] for doc in cursor}
        
    def gban_user(self, user_id: int, enforcer: int, reason: str):
        self.gban.update_one(
            {'user_id': user_id},
            {'$set': {'reason': reason, 'enforcer': enforcer, 'date': datetime.now().isoformat()}},
            upsert=True
        )

    def ungban_user(self, user_id: int) -> bool:
        result = self.gban.delete_one({'user_id': user_id})
        return result.deleted_count > 0

    def is_gban(self, user_id: int) -> Optional[Dict]:
        doc = self.gban.find_one({'user_id': user_id})
        if not doc:
            return None
        return {'reason': doc.get('reason'), 'enforcer': doc.get('enforcer'), 'date': doc.get('date')}
        
    def save_note(self, chat_id: int, note_name: str, content: str):
        self.notes.update_one(
            {'chat_id': chat_id, 'note_name': note_name},
            {'$set': {'note_content': content}},
            upsert=True
        )

    def get_note(self, chat_id: int, note_name: str) -> Optional[str]:
        doc = self.notes.find_one({'chat_id': chat_id, 'note_name': note_name})
        return doc['note_content'] if doc else None

    def clear_note(self, chat_id: int, note_name: str) -> bool:
        result = self.notes.delete_one({'chat_id': chat_id, 'note_name': note_name})
        return result.deleted_count > 0

    def get_all_notes(self, chat_id: int) -> List[str]:
        cursor = self.notes.find({'chat_id': chat_id}, {'note_name': 1})
        return [doc['note_name'] for doc in cursor]
        
    def increment_stat(self, stat_name: str, amount: int = 1):
        self.stats.update_one(
            {'stat_name': stat_name},
            {'$inc': {'value': amount}},
            upsert=True
        )

    def get_stat(self, stat_name: str) -> int:
        doc = self.stats.find_one({'stat_name': stat_name})
        return doc['value'] if doc else 0

    def close(self):
        self.client.close()

class XDB:
    """
    The main Database class that provides a unified, high-level interface.
    It intelligently selects between a MongoDB or SQLite backend.
    """
    def __init__(self, db_path: str = "xclient_fallback.db"):
        """
        Initialises the database, connecting to MongoDB if MONGO_URL is set,
        otherwise falling back to the specified SQLite database path.
        """
        mongo_url = os.getenv("MONGO_URL")
        self._handler: Union[_MongoHandler, _SQLiteHandler]
        
        if mongo_url and MONGO_AVAILABLE:
            try:
                print("INFO: MONGO_URL found. Attempting to connect to MongoDB...")
                self._handler = _MongoHandler(mongo_url)
                print("SUCCESS: MongoDB connection established.")
            except Exception as e:
                print(f"ERROR: MongoDB connection failed: {e}. Falling back to SQLite.")
                self._handler = _SQLiteHandler(db_path)
        else:
            if not mongo_url:
                print("INFO: MONGO_URL not set. Falling back to SQLite.")
            elif not MONGO_AVAILABLE:
                print("WARNING: MONGO_URL is set, but 'pymongo' is not installed. Falling back to SQLite.")
            self._handler = _SQLiteHandler(db_path)
    
    # --- Expanded, Multi-line Delegation Methods ---

    def set_env(self, key: str, value: str):
        """
        Sets a persistent environment variable in the database.
        These can be used for bot settings that you want to change without restarting.

        Args:
            key (str): The name of the variable (e.g., 'WELCOME_MESSAGE').
            value (str): The value to store.
        """
        return self._handler.set_env(key, value)

    def get_env(self, key: str) -> Optional[str]:
        """
        Retrieves a persistent environment variable from the database.

        Args:
            key (str): The name of the variable.
            
        Returns:
            Optional[str]: The stored value, or None if it's not found.
        """
        return self._handler.get_env(key)
        
    def add_bot_user(self, user_id: int, first_name: str):
        """
        Logs a new user who has started the bot for the first time.
        This is useful for tracking the user base.

        Args:
            user_id (int): The user's unique Telegram ID.
            first_name (str): The user's first name.
        """
        return self._handler.add_bot_user(user_id, first_name)
    
    def get_bot_user_count(self) -> int:
        """
        Counts the total number of unique users who have started the bot.
        
        Returns:
            int: The total count of users in the bot_users table.
        """
        return self._handler.get_bot_user_count()

    def get_all_bot_users(self) -> List[int]:
        """
        Retrieves a list of all user IDs who have ever started the bot.

        Returns:
            List[int]: A list containing all user IDs.
        """
        return self._handler.get_all_bot_users()

    def add_sudo(self, user_id: int):
        """
        Adds a user to the persistent sudo/admin list.

        Args:
            user_id (int): The user's Telegram ID to grant sudo privileges.
        """
        return self._handler.add_sudo(user_id)
        
    def remove_sudo(self, user_id: int):
        """
        Removes a user from the persistent sudo/admin list.

        Args:
            user_id (int): The user's Telegram ID to revoke sudo privileges from.
        """
        return self._handler.remove_sudo(user_id)
        
    def get_all_sudo(self) -> Set[int]:
        """
        Retrieves the complete set of all sudo user IDs from the database.

        Returns:
            Set[int]: A set of all user IDs with sudo privileges.
        """
        return self._handler.get_all_sudo()

    def gban_user(self, user_id: int, enforcer: int, reason: str):
        """
        Globally bans a user across all chats where the bot is an admin.
        The ban information is stored persistently.

        Args:
            user_id (int): The ID of the user to ban.
            enforcer (int): The ID of the admin who is performing the ban.
            reason (str): The reason for the global ban.
        """
        return self._handler.gban_user(user_id, enforcer, reason)
        
    def ungban_user(self, user_id: int) -> bool:
        """
        Removes a user from the global ban list.

        Args:
            user_id (int): The ID of the user to unban.
            
        Returns:
            bool: True if the user was found and unbanned, False otherwise.
        """
        return self._handler.ungban_user(user_id)
        
    def is_gban(self, user_id: int) -> Optional[Dict]:
        """
        Checks if a user is on the global ban list.

        Args:
            user_id (int): The ID of the user to check.
            
        Returns:
            Optional[Dict]: A dictionary with ban details if banned, otherwise None.
        """
        return self._handler.is_gban(user_id)

    def save_note(self, chat_id: int, note_name: str, content: str):
        """
        Saves a note with a specific name in a particular chat.
        This will overwrite any existing note with the same name.

        Args:
            chat_id (int): The chat where the note should be saved.
            note_name (str): The name to identify the note (e.g., 'rules').
            content (str): The text content of the note.
        """
        return self._handler.save_note(chat_id, note_name, content)
        
    def get_note(self, chat_id: int, note_name: str) -> Optional[str]:
        """
        Retrieves a saved note from a chat.

        Args:
            chat_id (int): The chat from which to retrieve the note.
            note_name (str): The name of the note to get.
            
        Returns:
            Optional[str]: The content of the note, or None if not found.
        """
        return self._handler.get_note(chat_id, note_name)
        
    def clear_note(self, chat_id: int, note_name: str) -> bool:
        """
        Deletes a saved note from a chat.

        Args:
            chat_id (int): The chat where the note is saved.
            note_name (str): The name of the note to delete.
            
        Returns:
            bool: True if the note was found and deleted, False otherwise.
        """
        return self._handler.clear_note(chat_id, note_name)
        
    def get_all_notes(self, chat_id: int) -> List[str]:
        """
        Gets a list of all saved note names for a specific chat.

        Args:
            chat_id (int): The chat to check for notes.
            
        Returns:
            List[str]: A list of all note names.
        """
        return self._handler.get_all_notes(chat_id)

    def increment_stat(self, stat_name: str, amount: int = 1):
        """
        Increments a named statistic in the database.
        Useful for tracking command usage, messages processed, etc.

        Args:
            stat_name (str): The name of the statistic to increment.
            amount (int, optional): The amount to increment by. Defaults to 1.
        """
        return self._handler.increment_stat(stat_name, amount)
        
    def get_stat(self, stat_name: str) -> int:
        """
        Retrieves the current value of a named statistic.

        Args:
            stat_name (str): The name of the statistic.
            
        Returns:
            int: The current value of the statistic, or 0 if it doesn't exist.
        """
        return self._handler.get_stat(stat_name)

    def close(self):
        """
        Properly closes the connection to the database.
        This should be called when the client application is shutting down.
        """
        return self._handler.close()