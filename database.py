import sqlite3
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import json


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            import os
            # Use a persistent location on Streamlit Cloud
            if os.path.exists('/mount'):
                db_path = '/mount/queryguard.db'
            else:
                db_path = 'queryguard.db'
        self.db_path = db_path
        self.init_tables()

    def init_tables(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                api_key TEXT UNIQUE,
                company TEXT,
                queries_limit INTEGER DEFAULT 1000
            )
        """)

        # Query history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query_text TEXT,
                predicted_cost REAL,
                actual_cost REAL,
                bytes_scanned INTEGER,
                execution_time REAL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Cost alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query_text TEXT,
                predicted_cost REAL,
                threshold REAL,
                is_resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Saved queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                query_text TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    # User methods
    def create_user(self, email: str, username: str, password: str, company: str = None) -> Dict:
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Generate API key
        import secrets
        api_key = secrets.token_urlsafe(32)

        try:
            cursor.execute("""
                INSERT INTO users (email, username, password_hash, api_key, company)
                VALUES (?, ?, ?, ?, ?)
            """, (email, username, password_hash, api_key, company))
            conn.commit()

            user_id = cursor.lastrowid
            return {
                'id': user_id,
                'email': email,
                'username': username,
                'api_key': api_key
            }
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3]):
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'is_admin': user[7],
                'api_key': user[8]
            }
        return None

    def get_user_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get user by API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'is_admin': user[7]
            }
        return None

    # Query history methods
    def save_query_history(self, user_id: int, query_text: str, predicted_cost: float,
                           actual_cost: float = None, bytes_scanned: int = None,
                           execution_time: float = None, status: str = 'predicted'):
        """Save query to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO query_history (user_id, query_text, predicted_cost, actual_cost, 
                                      bytes_scanned, execution_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, query_text, predicted_cost, actual_cost, bytes_scanned, execution_time, status))

        conn.commit()
        conn.close()

    def get_user_history(self, user_id: int, limit: int = 50) -> pd.DataFrame:
        """Get user's query history"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT query_text, predicted_cost, actual_cost, created_at, status
            FROM query_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, conn, params=(user_id, limit))
        conn.close()
        return df

    # Alert methods
    def create_alert(self, user_id: int, query_text: str, predicted_cost: float, threshold: float):
        """Create a cost alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cost_alerts (user_id, query_text, predicted_cost, threshold)
            VALUES (?, ?, ?, ?)
        """, (user_id, query_text, predicted_cost, threshold))

        conn.commit()
        conn.close()

    def get_unresolved_alerts(self, user_id: int) -> List[Dict]:
        """Get unresolved alerts for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, query_text, predicted_cost, threshold, created_at
            FROM cost_alerts
            WHERE user_id = ? AND is_resolved = 0
            ORDER BY created_at DESC
        """, (user_id,))

        alerts = [{'id': row[0], 'query_text': row[1], 'predicted_cost': row[2],
                   'threshold': row[3], 'created_at': row[4]} for row in cursor.fetchall()]
        conn.close()
        return alerts

    # Saved queries methods
    def save_query(self, user_id: int, name: str, query_text: str, description: str = None):
        """Save a query for later use"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saved_queries (user_id, name, query_text, description)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, query_text, description))

        conn.commit()
        conn.close()

    def get_saved_queries(self, user_id: int) -> List[Dict]:
        """Get user's saved queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, query_text, description, created_at
            FROM saved_queries
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))

        queries = [{'id': row[0], 'name': row[1], 'query_text': row[2],
                    'description': row[3], 'created_at': row[4]} for row in cursor.fetchall()]
        conn.close()
        return queries


# Initialize database
db = Database()