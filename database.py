import sqlite3
from datetime import datetime

class Database:
    
    def __init__(self, db_file="chat_history.db"):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                bot_gender TEXT DEFAULT NULL,
                user_gender TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                is_bot BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, username, first_name, last_name, bot_gender=None, user_gender=None):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, bot_gender, user_gender)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, bot_gender, user_gender))
        
        conn.commit()
        conn.close()

    def add_message(self, user_id: int, message_text: str, is_bot: bool):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO messages (user_id, message_text, is_bot, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            ''', (user_id, message_text, is_bot))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error adding message: {e}")

    def get_chat_history(self, user_id: int, limit: int = 10) -> list:
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute('''
                SELECT message_text, is_bot, timestamp
                FROM messages
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            messages = c.fetchall()
            conn.close()
            
            return messages[::-1] 
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []

    def clear_chat_history(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM messages
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error clearing chat history: {e}")

    def update_user_setting(self, user_id: int, setting_name: str, setting_value):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute(f'''
            UPDATE users 
            SET {setting_name} = ?
            WHERE user_id = ?
        ''', (setting_value, user_id))
        
        conn.commit()
        conn.close()

    def get_user_settings(self, user_id: int):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            SELECT bot_gender, user_gender
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        
        settings = c.fetchone()
        conn.close()
        return settings

    def close(self):
        """Close the database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.close() 