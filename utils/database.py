import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import os


class DatabaseManager:
    def __init__(self, db_path: str = "data/translation_requests.db"):
        """Initialize database connection"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
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
            # Create user_commands table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT,
                    command TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def log_command(self, user_id: int, command: str, user_name: str = None) -> int:
        """Log a user command"""
        self.connect()
        try:
            self.cursor.execute('''
                INSERT INTO user_commands (user_id, user_name, command)
                VALUES (?, ?, ?)
            ''', (user_id, user_name, command))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def get_user_history(self, user_id: int, limit: int = 10) -> List[str]:
        """Get command history for a specific user"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT user_name, command, created_at
                FROM user_commands
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            activities = []
            for row in self.cursor.fetchall():
                user_name, command, timestamp = row
                formatted_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                display_name = user_name if user_name else f"User {user_id}"
                activities.append(f"[{formatted_date}] {display_name}: {command}")
            
            return activities
        finally:
            self.disconnect()

    def get_all_history(self, limit: int = 50) -> List[str]:
        """Get command history for all users"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT user_id, user_name, command, created_at
                FROM user_commands
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            activities = []
            for row in self.cursor.fetchall():
                user_id, user_name, command, timestamp = row
                formatted_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                display_name = user_name if user_name else f"User {user_id}"
                activities.append(f"[{formatted_date}] {display_name}: {command}")
            
            return activities
        finally:
            self.disconnect()

    def get_command_stats(self) -> List[Tuple[int, str, str, int]]:
        """Get statistics of commands used by each user"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT 
                    user_id,
                    user_name,
                    command,
                    COUNT(*) as count
                FROM user_commands
                GROUP BY user_id, command
                ORDER BY user_id, count DESC
            ''')
            
            return self.cursor.fetchall()
        finally:
            self.disconnect()

    def get_user_stats(self, user_id: int) -> List[Tuple[str, int]]:
        """Get command usage statistics for a specific user"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT 
                    command,
                    COUNT(*) as count
                FROM user_commands
                WHERE user_id = ?
                GROUP BY command
                ORDER BY count DESC
            ''', (user_id,))
            
            return self.cursor.fetchall()
        finally:
            self.disconnect()

    def format_user_report(self, user_id: int) -> str:
        """Format a complete user report including command counts and history"""
        # Get user stats
        stats = self.get_user_stats(user_id)
        history = self.get_user_history(user_id, limit=5)  # Last 5 commands
        
        # Get user name
        self.connect()
        try:
            self.cursor.execute('SELECT DISTINCT user_name FROM user_commands WHERE user_id = ? LIMIT 1', (user_id,))
            result = self.cursor.fetchone()
            user_name = result[0] if result and result[0] else f"User {user_id}"
        finally:
            self.disconnect()

        # Format report
        report = f"📊 Report for {user_name}\n\n"
        
        # Command statistics
        report += "Command Usage:\n"
        for command, count in stats:
            report += f"/{command}: {count} times\n"
        
        # Total commands
        total_commands = sum(count for _, count in stats)
        report += f"\nTotal commands used: {total_commands}\n"
        
        # Recent activity
        report += "\nRecent Activity:\n"
        for activity in history:
            report += f"{activity}\n"
            
        return report

    def format_global_report(self) -> str:
        """Format a complete report for all users"""
        stats = self.get_command_stats()
        
        # Group by user
        user_stats = {}
        for user_id, user_name, command, count in stats:
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'name': user_name or f"User {user_id}",
                    'commands': {},
                    'total': 0
                }
            user_stats[user_id]['commands'][command] = count
            user_stats[user_id]['total'] += count

        # Format report
        report = "📊 Global Usage Report\n\n"
        
        # Sort users by total command usage
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for user_id, stats in sorted_users:
            report += f"👤 {stats['name']}:\n"
            for command, count in sorted(stats['commands'].items(), key=lambda x: x[1], reverse=True):
                report += f"  /{command}: {count} times\n"
            report += f"  Total: {stats['total']} commands\n\n"

        return report

    def get_command_time_stats(self) -> Dict[str, Dict[str, int]]:
        """Get command usage statistics grouped by different time periods"""
        self.connect()
        try:
            # Get daily stats (last 7 days)
            daily_stats = self.cursor.execute('''
                SELECT 
                    date(created_at) as day,
                    command,
                    COUNT(*) as count
                FROM user_commands
                WHERE created_at >= date('now', '-7 days')
                GROUP BY day, command
                ORDER BY day DESC, count DESC
            ''').fetchall()

            # Get weekly stats (last 4 weeks)
            weekly_stats = self.cursor.execute('''
                SELECT 
                    strftime('%Y-W%W', created_at) as week,
                    command,
                    COUNT(*) as count
                FROM user_commands
                WHERE created_at >= date('now', '-28 days')
                GROUP BY week, command
                ORDER BY week DESC, count DESC
            ''').fetchall()

            # Get monthly stats (last 3 months)
            monthly_stats = self.cursor.execute('''
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    command,
                    COUNT(*) as count
                FROM user_commands
                WHERE created_at >= date('now', '-90 days')
                GROUP BY month, command
                ORDER BY month DESC, count DESC
            ''').fetchall()

            return {
                'daily': self._format_time_stats(daily_stats),
                'weekly': self._format_time_stats(weekly_stats),
                'monthly': self._format_time_stats(monthly_stats)
            }
        finally:
            self.disconnect()

    def _format_time_stats(self, stats: List[Tuple]) -> Dict[str, Dict[str, int]]:
        """Helper method to format time-based statistics"""
        formatted_stats = {}
        for period, command, count in stats:
            if period not in formatted_stats:
                formatted_stats[period] = {}
            formatted_stats[period][command] = count
        return formatted_stats

    def format_time_report(self) -> str:
        """Format a report showing command usage over time"""
        stats = self.get_command_time_stats()
        
        report = "📈 Command Usage Over Time\n\n"
        
        # Daily stats
        report += "📅 Last 7 Days:\n"
        for day, commands in stats['daily'].items():
            report += f"\n{day}:\n"
            for command, count in sorted(commands.items(), key=lambda x: x[1], reverse=True):
                report += f"  /{command}: {count} times\n"
        
        # Weekly stats
        report += "\n📆 Last 4 Weeks:\n"
        for week, commands in stats['weekly'].items():
            report += f"\n{week}:\n"
            for command, count in sorted(commands.items(), key=lambda x: x[1], reverse=True):
                report += f"  /{command}: {count} times\n"
        
        # Monthly stats
        report += "\n📅 Last 3 Months:\n"
        for month, commands in stats['monthly'].items():
            report += f"\n{month}:\n"
            for command, count in sorted(commands.items(), key=lambda x: x[1], reverse=True):
                report += f"  /{command}: {count} times\n"
        
        return report

    def get_all_users_history(self, days: int = 7, limit: int = 100) -> str:
        """Get detailed history of all users' activities for the specified number of days"""
        self.connect()
        try:
            self.cursor.execute('''
                SELECT 
                    user_commands.user_id,
                    user_commands.user_name,
                    user_commands.command,
                    user_commands.created_at,
                    COUNT(*) OVER (PARTITION BY user_commands.user_id) as total_commands
                FROM user_commands
                WHERE created_at >= datetime('now', ?) 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (f'-{days} days', limit))
            
            results = self.cursor.fetchall()
            
            if not results:
                return "No activity in the specified time period."
            
            report = f"👥 User Activity Report (Last {days} days)\n\n"
            current_user = None
            
            for user_id, user_name, command, timestamp, total_commands in results:
                display_name = user_name if user_name else f"User {user_id}"
                
                if current_user != user_id:
                    current_user = user_id
                    report += f"\n👤 {display_name} (Total commands: {total_commands}):\n"
                
                formatted_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                report += f"  [{formatted_time}] /{command}\n"
            
            return report
        finally:
            self.disconnect() 