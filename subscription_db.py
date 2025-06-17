import sqlite3
from datetime import datetime, timedelta
import math
import pytz
import uuid

class SubscriptionDB:
    def __init__(self, db_file="users.db"):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                is_premium BOOLEAN DEFAULT FALSE,
                trial_activated BOOLEAN DEFAULT FALSE,
                trial_start_date TEXT,
                activation_key TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS activation_keys (
                key TEXT PRIMARY KEY,
                is_used BOOLEAN DEFAULT FALSE,
                used_by_user_id INTEGER,
                created_at TEXT,
                used_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id: int):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR IGNORE INTO subscriptions (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()

    def activate_trial(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('SELECT trial_activated FROM subscriptions WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if result and result[0]:
            conn.close()
            return False
        
        moscow_tz = pytz.timezone('Europe/Moscow')
        trial_start_moscow = datetime.now(moscow_tz).isoformat()
        
        c.execute('''
            UPDATE subscriptions 
            SET trial_activated = TRUE,
                trial_start_date = ?
            WHERE user_id = ?
        ''', (trial_start_moscow, user_id))
        
        conn.commit()
        conn.close()
        return True

    def create_activation_key(self) -> str:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        new_key = str(uuid.uuid4())
        moscow_tz = pytz.timezone('Europe/Moscow')
        created_at_moscow = datetime.now(moscow_tz).isoformat()
        
        c.execute('''
            INSERT INTO activation_keys (key, created_at)
            VALUES (?, ?)
        ''', (new_key, created_at_moscow))
        
        conn.commit()
        conn.close()
        return new_key

    def delete_activation_key(self, key: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('DELETE FROM activation_keys WHERE key = ?', (key,))
        rows_affected = c.rowcount
        
        conn.commit()
        conn.close()
        return rows_affected > 0

    def use_activation_key(self, key: str, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('SELECT is_used FROM activation_keys WHERE key = ?', (key,))
        result = c.fetchone()
        
        if result and not result[0]: 
            moscow_tz = pytz.timezone('Europe/Moscow')
            used_at_moscow = datetime.now(moscow_tz).isoformat()
            c.execute('''
                UPDATE activation_keys 
                SET is_used = TRUE,
                    used_by_user_id = ?,
                    used_at = ?
                WHERE key = ?
            ''', (user_id, used_at_moscow, key))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False

    def activate_premium(self, user_id: int, activation_key: str) -> bool:
        if self.use_activation_key(activation_key, user_id):
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute('''
                UPDATE subscriptions 
                SET is_premium = TRUE,
                    activation_key = ?
                WHERE user_id = ?
            ''', (activation_key, user_id))
            
            conn.commit()
            conn.close()
            return True
        return False

    def check_subscription(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            SELECT is_premium, trial_activated, trial_start_date
            FROM subscriptions
            WHERE user_id = ?
        ''', (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return False
            
        is_premium, trial_activated, trial_start_date_str = result
        
        if is_premium:
            return True
            
        if trial_activated and trial_start_date_str:
            moscow_tz = pytz.timezone('Europe/Moscow')
            trial_start = datetime.fromisoformat(trial_start_date_str)
            trial_end = trial_start + timedelta(days=3)
            return datetime.now(moscow_tz) < trial_end
            
        return False

    def get_trial_days_left(self, user_id: int) -> int:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''
            SELECT trial_start_date
            FROM subscriptions
            WHERE user_id = ? AND trial_activated = TRUE
        ''', (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return 0
            
        moscow_tz = pytz.timezone('Europe/Moscow')
        trial_start = datetime.fromisoformat(result[0])
        trial_end = trial_start + timedelta(days=3)
        
        remaining_time = trial_end - datetime.now(moscow_tz)

        remaining_seconds = remaining_time.total_seconds() + 1

        print(f"[DEBUG] trial_start: {trial_start}")
        print(f"[DEBUG] trial_end: {trial_end}")
        print(f"[DEBUG] datetime.now(moscow_tz): {datetime.now(moscow_tz)}")
        print(f"[DEBUG] remaining_time.total_seconds() (before buffer): {remaining_time.total_seconds()}")
        print(f"[DEBUG] remaining_seconds (after buffer): {remaining_seconds}")

        if remaining_seconds <= 0:
            return 0
        
        days_left = math.ceil(remaining_seconds / (24 * 3600))
        
        return days_left