"""
Database models for Waffle House Simulator
"""
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

DATABASE = 'wafflehouse.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db(cursor):
    """Apply database migrations for schema changes"""
    # Check if 'cash' column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'cash' not in columns:
        print("Adding 'cash' column to users table...")
        cursor.execute('ALTER TABLE users ADD COLUMN cash REAL DEFAULT 100.0')
        # Update existing users to have $100
        cursor.execute('UPDATE users SET cash = 100.0 WHERE cash IS NULL')
    
    # Check if supplies table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplies'")
    if not cursor.fetchone():
        print("Creating supplies table...")
        cursor.execute('''
            CREATE TABLE supplies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                supply_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, supply_name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    
    # Check if achievements table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='achievements'")
    if not cursor.fetchone():
        print("Creating achievements table...")
        cursor.execute('''
            CREATE TABLE achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_name TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

def init_db():
    """Initialize the database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_orders INTEGER DEFAULT 0,
            total_dishes_cooked INTEGER DEFAULT 0,
            total_cleanings INTEGER DEFAULT 0,
            total_events_witnessed INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            highest_streak INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            cash REAL DEFAULT 100.0
        )
    ''')
    
    # Run migrations to add missing columns to existing tables
    migrate_db(cursor)
    
    # Active sessions table (for multiplayer state)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            station TEXT,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Orders table (for order taking activity)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number INTEGER NOT NULL,
            items TEXT NOT NULL,
            taken_by INTEGER,
            completed_by INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (taken_by) REFERENCES users(id),
            FOREIGN KEY (completed_by) REFERENCES users(id)
        )
    ''')
    
    # Cooking queue (for cooking station activity)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooking_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_name TEXT NOT NULL,
            cook_time INTEGER NOT NULL,
            started_by INTEGER,
            status TEXT DEFAULT 'queued',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (started_by) REFERENCES users(id)
        )
    ''')
    
    # Cleaning tasks (for maintenance activity)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleaning_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            location TEXT NOT NULL,
            cleaned_by INTEGER,
            status TEXT DEFAULT 'dirty',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (cleaned_by) REFERENCES users(id)
        )
    ''')
    
    # Events log (track surreal events that have occurred)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            event_data TEXT NOT NULL,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            FOREIGN KEY (resolved_by) REFERENCES users(id)
        )
    ''')
    
    # Achievements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_name TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, achievement_name)
        )
    ''')
    
    # Supplies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            supply_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, supply_name)
        )
    ''')
    
    conn.commit()
    conn.close()

class User:
    """User model for authentication and stats"""
    
    @staticmethod
    def create(username, password):
        """Create a new user"""
        conn = get_db()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            # Initialize starter supplies
            Supplies.initialize_starter_supplies(user_id)
            
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = dict(row)
            # Ensure user has starter supplies
            Supplies.ensure_initialized(user_id)
            return user
        return None
    
    @staticmethod
    def verify_password(username, password):
        """Verify user password"""
        user = User.get_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    
    @staticmethod
    def update_stats(user_id, **kwargs):
        """Update user statistics and check for level-up"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current user data
        cursor.execute('SELECT level, experience, cash FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        old_level = row['level']
        old_xp = row['experience']
        current_cash = row['cash']
        
        # Update stats
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        
        # Check for level up (100 XP per level)
        new_xp = kwargs.get('experience', old_xp)
        new_level = 1 + (new_xp // 100)
        
        level_up_rewards = {}
        if new_level > old_level:
            # Level up rewards
            levels_gained = new_level - old_level
            cash_reward = levels_gained * 50  # $50 per level
            
            # Update level and grant cash reward
            cursor.execute('UPDATE users SET level = ?, cash = cash + ? WHERE id = ?', 
                          (new_level, cash_reward, user_id))
            
            level_up_rewards = {
                'levels_gained': levels_gained,
                'new_level': new_level,
                'cash_reward': cash_reward
            }
        
        conn.commit()
        conn.close()
        
        return level_up_rewards
    
    @staticmethod
    def get_leaderboard(limit=10):
        """Get top players by experience"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, level, experience, total_orders, 
                   total_dishes_cooked, total_cleanings, highest_streak
            FROM users
            ORDER BY experience DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

class GameState:
    """Manage global game state and multiplayer interactions"""
    
    @staticmethod
    def get_active_players():
        """Get all currently active players"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, a.station, a.last_active
            FROM active_sessions a
            JOIN users u ON a.user_id = u.id
            WHERE datetime(a.last_active) > datetime('now', '-5 minutes')
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_session(user_id, session_id, station=None):
        """Update user's active session"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete old session
        cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
        
        # Insert new session
        cursor.execute('''
            INSERT INTO active_sessions (user_id, session_id, station, last_active)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, session_id, station))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def log_event(event_id, event_data):
        """Log a surreal event occurrence"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events_log (event_id, event_data)
            VALUES (?, ?)
        ''', (event_id, json.dumps(event_data)))
        conn.commit()
        event_log_id = cursor.lastrowid
        conn.close()
        return event_log_id
    
    @staticmethod
    def resolve_event(event_log_id, user_id):
        """Mark an event as resolved by a user"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE events_log
            SET resolved = 1, resolved_by = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user_id, event_log_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_active_events():
        """Get all unresolved events"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, event_id, event_data, triggered_at
            FROM events_log
            WHERE resolved = 0
            ORDER BY triggered_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        events = []
        for row in rows:
            event = dict(row)
            event['event_data'] = json.loads(event['event_data'])
            events.append(event)
        return events

class Supplies:
    """Manage user supplies"""
    
    @staticmethod
    def get_user_supplies(user_id):
        """Get all supplies for a user"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT supply_name, quantity FROM supplies WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return {row['supply_name']: row['quantity'] for row in rows}
    
    @staticmethod
    def ensure_initialized(user_id):
        """Ensure user has supplies initialized (for existing users after migration)"""
        supplies = Supplies.get_user_supplies(user_id)
        if not supplies:
            Supplies.initialize_starter_supplies(user_id)
    
    @staticmethod
    def initialize_starter_supplies(user_id):
        """Give new user starter supplies"""
        starter = {
            'batter': 10,
            'eggs': 12,
            'bacon': 8,
            'sausage': 8,
            'coffee_beans': 15,
            'hash_browns': 10,
            'bread': 10
        }
        conn = get_db()
        cursor = conn.cursor()
        for supply_name, quantity in starter.items():
            cursor.execute('''
                INSERT OR REPLACE INTO supplies (user_id, supply_name, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, supply_name, quantity))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_supply(user_id, supply_name, quantity_change):
        """Update supply quantity (can be positive or negative)"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current quantity
        cursor.execute('SELECT quantity FROM supplies WHERE user_id = ? AND supply_name = ?',
                      (user_id, supply_name))
        row = cursor.fetchone()
        current = row['quantity'] if row else 0
        new_quantity = max(0, current + quantity_change)
        
        cursor.execute('''
            INSERT OR REPLACE INTO supplies (user_id, supply_name, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, supply_name, new_quantity))
        
        conn.commit()
        conn.close()
        return new_quantity
    
    @staticmethod
    def check_and_consume(user_id, required_supplies):
        """Check if user has required supplies and consume them if so"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user has all required supplies
        for supply_name, required_qty in required_supplies.items():
            cursor.execute('SELECT quantity FROM supplies WHERE user_id = ? AND supply_name = ?',
                          (user_id, supply_name))
            row = cursor.fetchone()
            current = row['quantity'] if row else 0
            print(f"[SUPPLY CHECK] User {user_id}: {supply_name} needed={required_qty}, available={current}")
            if current < required_qty:
                conn.close()
                return False, supply_name
        
        # Consume supplies
        for supply_name, required_qty in required_supplies.items():
            cursor.execute('''
                UPDATE supplies 
                SET quantity = quantity - ?
                WHERE user_id = ? AND supply_name = ?
            ''', (required_qty, user_id, supply_name))
        
        conn.commit()
        conn.close()
        return True, None

class Achievements:
    """Manage achievements"""
    
    ACHIEVEMENT_DEFS = {
        'first_order': {'name': 'First Order', 'icon': '🔰', 'condition': lambda u: u['total_orders'] >= 1},
        'cook_10': {'name': 'Line Cook', 'icon': '👨‍🍳', 'condition': lambda u: u['total_dishes_cooked'] >= 10},
        'cook_50': {'name': 'Head Chef', 'icon': '🍳', 'condition': lambda u: u['total_dishes_cooked'] >= 50},
        'clean_25': {'name': 'Neat Freak', 'icon': '✨', 'condition': lambda u: u['total_cleanings'] >= 25},
        'event_5': {'name': 'Reality Bender', 'icon': '🌀', 'condition': lambda u: u['total_events_witnessed'] >= 5},
        'rich': {'name': 'Capitalist', 'icon': '💰', 'condition': lambda u: u['cash'] >= 500},
        'veteran': {'name': 'Veteran', 'icon': '⭐', 'condition': lambda u: u['experience'] >= 500},
    }
    
    @staticmethod
    def check_and_award(user_id):
        """Check user progress and award new achievements"""
        user = User.get_by_id(user_id)
        if not user:
            return []
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current achievements
        cursor.execute('SELECT achievement_name FROM achievements WHERE user_id = ?', (user_id,))
        current = {row['achievement_name'] for row in cursor.fetchall()}
        
        # Check for new achievements
        newly_earned = []
        for achievement_id, achievement_def in Achievements.ACHIEVEMENT_DEFS.items():
            if achievement_id not in current:
                if achievement_def['condition'](user):
                    cursor.execute('''
                        INSERT INTO achievements (user_id, achievement_name)
                        VALUES (?, ?)
                    ''', (user_id, achievement_id))
                    newly_earned.append({
                        'id': achievement_id,
                        'name': achievement_def['name'],
                        'icon': achievement_def['icon']
                    })
        
        conn.commit()
        conn.close()
        return newly_earned
    
    @staticmethod
    def get_user_achievements(user_id):
        """Get all achievements for a user"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT achievement_name FROM achievements WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        achievements = []
        for row in rows:
            achievement_id = row['achievement_name']
            if achievement_id in Achievements.ACHIEVEMENT_DEFS:
                achievement_def = Achievements.ACHIEVEMENT_DEFS[achievement_id]
                achievements.append({
                    'id': achievement_id,
                    'name': achievement_def['name'],
                    'icon': achievement_def['icon']
                })
        return achievements
