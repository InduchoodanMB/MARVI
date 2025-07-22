import sqlite3
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for the dating app"""
    
    def __init__(self, db_path="dating_app.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Create database tables if they don't exist with error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    location TEXT,
                    bio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Personality scores table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personality_scores (
                    user_id INTEGER,
                    openness INTEGER CHECK(openness >= 1 AND openness <= 20),
                    conscientiousness INTEGER CHECK(conscientiousness >= 1 AND conscientiousness <= 20),
                    extraversion INTEGER CHECK(extraversion >= 1 AND extraversion <= 20),
                    agreeableness INTEGER CHECK(agreeableness >= 1 AND agreeableness <= 20),
                    neuroticism INTEGER CHECK(neuroticism >= 1 AND neuroticism <= 20),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Matches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    match_user_id INTEGER,
                    compatibility_score REAL,
                    match_explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (match_user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
            logger.info("Database tables created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database error during setup: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_user(self, name: str, age: int, gender: str, location: str = "", bio: str = "", 
                 personality_scores: Dict[str, int] = None) -> Optional[int]:
        """Add a new user with their personality scores"""
        conn = None
        try:
            # Validate personality scores
            if personality_scores:
                required_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
                for trait in required_traits:
                    if trait not in personality_scores:
                        logger.error(f"Missing personality trait: {trait}")
                        return None
                    if not (1 <= personality_scores[trait] <= 20):
                        logger.error(f"Invalid score for {trait}: {personality_scores[trait]} (must be 1-20)")
                        return None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (name, age, gender, location, bio) VALUES (?, ?, ?, ?, ?)",
                (name, age, gender, location, bio)
            )
            user_id = cursor.lastrowid
            
            # Insert personality scores if provided
            if personality_scores:
                cursor.execute('''
                    INSERT INTO personality_scores 
                    (user_id, openness, conscientiousness, extraversion, agreeableness, neuroticism)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    personality_scores['openness'],
                    personality_scores['conscientiousness'], 
                    personality_scores['extraversion'],
                    personality_scores['agreeableness'],
                    personality_scores['neuroticism']
                ))
            
            conn.commit()
            logger.info(f"User '{name}' added with ID: {user_id}")
            return user_id
            
        except sqlite3.Error as e:
            logger.error(f"Database error adding user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user data by ID"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.user_id, u.name, u.age, u.gender, u.location, u.bio,
                       p.openness, p.conscientiousness, p.extraversion, p.agreeableness, p.neuroticism
                FROM users u
                LEFT JOIN personality_scores p ON u.user_id = p.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                user_data = {
                    'user_id': result[0],
                    'name': result[1],
                    'age': result[2],
                    'gender': result[3],
                    'location': result[4],
                    'bio': result[5],
                    'personality_scores': {
                        'openness': result[6],
                        'conscientiousness': result[7],
                        'extraversion': result[8],
                        'agreeableness': result[9],
                        'neuroticism': result[10]
                    } if result[6] is not None else None
                }
                return user_data
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_users_except(self, exclude_user_id: int, gender_filter: str = None) -> List[Dict]:
        """Get all users except the specified one, with optional gender filter"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT u.user_id, u.name, u.age, u.gender, u.location, u.bio,
                       p.openness, p.conscientiousness, p.extraversion, p.agreeableness, p.neuroticism
                FROM users u
                JOIN personality_scores p ON u.user_id = p.user_id  
                WHERE u.user_id != ?
            '''
            params = [exclude_user_id]
            
            if gender_filter:
                query += " AND u.gender = ?"
                params.append(gender_filter)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            users = []
            for result in results:
                user_data = {
                    'user_id': result[0],
                    'name': result[1],
                    'age': result[2],
                    'gender': result[3],
                    'location': result[4],
                    'bio': result[5],
                    'personality_scores': {
                        'openness': result[6],
                        'conscientiousness': result[7],
                        'extraversion': result[8],
                        'agreeableness': result[9],
                        'neuroticism': result[10]
                    }
                }
                users.append(user_data)
            
            return users
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def save_matches(self, user_id: int, matches: List[Dict]):
        """Save match results to database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear old matches for this user
            cursor.execute("DELETE FROM matches WHERE user_id = ?", (user_id,))
            
            # Insert new matches
            for match in matches:
                explanation = "; ".join(match['explanations'])
                cursor.execute('''
                    INSERT INTO matches (user_id, match_user_id, compatibility_score, match_explanation)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, match['user_id'], match['compatibility_score'], explanation))
            
            conn.commit()
            logger.info(f"Saved {len(matches)} matches for user {user_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving matches: {e}")
        finally:
            if conn:
                conn.close()

    def get_user_stats(self) -> Dict:
        """Get basic statistics about users in the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT gender, COUNT(*) FROM users GROUP BY gender")
            gender_breakdown = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM matches")
            total_matches = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'gender_breakdown': gender_breakdown,
                'total_matches_generated': total_matches
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting stats: {e}")
            return {}
        finally:
            if conn:
                conn.close()