import sqlite3
from datetime import datetime
from typing import Optional, List, Dict


class DatabaseManager:
    def __init__(self, db_path: str = "sqlite.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def connect(self):
        """Create a database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def initialize_database(self):
        """Create necessary tables if they don't exist"""
        self.connect()
        try:
            # Create requests table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS translation_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_file TEXT NOT NULL,
                    output_file TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def log_request(self, input_file: str, output_file: str) -> int:
        """Log a new translation request"""
        self.connect()
        try:
            self.cursor.execute('''
                INSERT INTO translation_requests (input_file, output_file, status)
                VALUES (?, ?, ?)
            ''', (input_file, output_file, 'pending'))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def update_request_status(self, request_id: int, status: str, error_message: Optional[str] = None):
        """Update the status of a translation request"""
        self.connect()
        try:
            if status == 'completed':
                self.cursor.execute('''
                    UPDATE translation_requests 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE id = ?
                ''', (status, error_message, request_id))
            else:
                self.cursor.execute('''
                    UPDATE translation_requests 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                ''', (status, error_message, request_id))
            self.conn.commit()
        finally:
            self.disconnect()

    def get_request_history(self, limit: int = 10) -> List[Dict]:
        """Get the history of translation requests"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT id, input_file, output_file, status, created_at, completed_at, error_message
                FROM translation_requests
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    def get_request_status(self, request_id: int) -> Dict:
        """Get the status of a specific request"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT id, input_file, output_file, status, created_at, completed_at, error_message
                FROM translation_requests
                WHERE id = ?
            ''', (request_id,))
            columns = [description[0] for description in self.cursor.description]
            row = self.cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        finally:
            self.disconnect() 