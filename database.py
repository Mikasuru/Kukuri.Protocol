import sqlite3
from datetime import datetime

class ChatDatabase:
    def __init__(self, db_name="chat.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def get_user_chat_history(self, username):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT sender, receiver, message_type, content, timestamp
            FROM chat_history
            WHERE sender = ? OR receiver = ?
            ORDER BY timestamp ASC
        """, (username, username))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'sender': row[0],
                'receiver': row[1],
                'message_type': row[2],
                'content': row[3],
                'timestamp': row[4]
            })
        return history

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users")
        return cursor.fetchall()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table with profile fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            display_name TEXT,
            status_message TEXT,
            profile_image TEXT,
            additional_image TEXT,
            registration_date DATETIME NOT NULL,
            last_seen DATETIME
        )
        ''')
        
        # chat_history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (sender) REFERENCES users (username),
            FOREIGN KEY (receiver) REFERENCES users (username)
        )
        ''')
        
        self.conn.commit()
    
    def register_user(self, username, password, display_name=None, profile_image=None, additional_image=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO users 
                   (username, password, display_name, profile_image, additional_image, registration_date) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, password, display_name or username, profile_image, additional_image, datetime.now())
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        return result is not None and result[0] == password
    
    def update_user_status(self, username, is_online):
        cursor = self.conn.cursor()
        last_seen = datetime.now() if is_online else None
        cursor.execute(
            "UPDATE users SET last_seen = ? WHERE username = ?",
            (last_seen, username)
        )
        self.conn.commit()
    
    def save_message(self, sender, receiver, message_type, content):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO chat_history 
               (sender, receiver, message_type, content, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (sender, receiver, message_type, content, datetime.now())
        )
        self.conn.commit()
    
    def get_chat_history(self, user1, user2):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT sender, receiver, message_type, content, timestamp
               FROM chat_history
               WHERE (sender = ? AND receiver = ?) 
                  OR (sender = ? AND receiver = ?)
               ORDER BY timestamp ASC""",
            (user1, user2, user2, user1)
        )
        return cursor.fetchall()
    
    def get_user_chat_history(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT sender, receiver, message_type, content, timestamp
               FROM chat_history
               WHERE sender = ? OR receiver = ?
               ORDER BY timestamp ASC""",
            (username, username)
        )
        history = []
        for row in cursor.fetchall():
            history.append({
                'sender': row[0],
                'receiver': row[1],
                'message_type': row[2],
                'content': row[3],
                'timestamp': row[4]
            })
        return history

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users")
        return [row[0] for row in cursor.fetchall()]  # username

    def update_profile(self, username: str, display_name: str = None, 
                      status_message: str = None, profile_picture: str = None,
                      current_theme: str = None) -> bool:
        try:
            cursor = self.conn.cursor()
            updates = []
            values = []
            
            if display_name is not None:
                updates.append("display_name = ?")
                values.append(display_name)
            
            if status_message is not None:
                updates.append("status_message = ?")
                values.append(status_message)
            
            if profile_picture is not None:
                updates.append("profile_picture = ?")
                values.append(profile_picture)
            
            if current_theme is not None:
                updates.append("current_theme = ?")
                values.append(current_theme)
            
            if not updates:
                return False
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
            values.append(username)
            
            cursor.execute(query, values)
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
    
    def get_profile(self, username: str) -> dict:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT username, display_name, status_message, 
                       profile_picture, current_theme, last_seen
                FROM users WHERE username = ?
            """, (username,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'username': result[0],
                    'display_name': result[1] or result[0],
                    'status_message': result[2] or "",
                    'profile_picture': result[3],
                    'current_theme': result[4],
                    'last_seen': result[5]
                }
            return None
            
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
        
    def get_user_profile(self, username):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT username, display_name, status_message, 
                   profile_image, additional_image, last_seen
            FROM users WHERE username = ?
        """, (username,))
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0],
                'display_name': row[1],
                'status_message': row[2],
                'profile_image': row[3],
                'additional_image': row[4],
                'last_seen': row[5]
            }
        return None

    def get_all_users_with_profiles(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT username, display_name, status_message, 
                   profile_image, additional_image, last_seen
            FROM users
        """)
        return [{
            'username': row[0],
            'display_name': row[1],
            'status_message': row[2],
            'profile_image': row[3],
            'additional_image': row[4],
            'last_seen': row[5]
        } for row in cursor.fetchall()]