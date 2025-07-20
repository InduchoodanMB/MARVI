import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatingAppMatcher:
    def __init__(self, db_path="dating_app.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Trait weights for more refined matching
        self.trait_weights = {
            'openness': 1.0,
            'conscientiousness': 1.1,      # Slightly more important
            'extraversion': 1.0,
            'agreeableness': 1.2,          # Most important for harmony
            'neuroticism': 1.1             # Important for stability
        }
        
        # Compatibility matrix - which personality ranges work well together
        self.compatibility_matrix = {
            "openness": {
                "very_low": ["low", "moderate"],           
                "low": ["very_low", "moderate", "high"],   
                "moderate": ["low", "moderate", "high"],   
                "high": ["low", "moderate", "high"],       
                "very_high": ["moderate", "high"]          
            },
            "conscientiousness": {
                "very_low": ["moderate", "high"],          
                "low": ["moderate", "high"],               
                "moderate": ["low", "moderate", "high"],   
                "high": ["very_low", "low", "moderate"],   
                "very_high": ["low", "moderate"]           
            },
            "extraversion": {
                "very_low": ["low", "moderate"],           
                "low": ["very_low", "moderate", "high"],   
                "moderate": ["low", "moderate", "high"],   
                "high": ["low", "moderate", "high"],       
                "very_high": ["moderate", "high"]          
            },
            "agreeableness": {
                "very_low": ["high", "very_high"],         
                "low": ["moderate", "high"],               
                "moderate": ["moderate", "high"],          
                "high": ["very_low", "low", "moderate", "high"],  
                "very_high": ["very_low", "low", "moderate"]      
            },
            "neuroticism": {
                "very_low": ["moderate", "high", "very_high"],    
                "low": ["moderate", "high"],               
                "moderate": ["very_low", "low", "moderate"], 
                "high": ["very_low", "low"],               
                "very_high": ["very_low", "low"]           
            }
        }

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
                    last_matched TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Personality scores table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personality_scores (
                    user_id INTEGER,
                    openness INTEGER CHECK(openness >= 4 AND openness <= 20),
                    conscientiousness INTEGER CHECK(conscientiousness >= 4 AND conscientiousness <= 20),
                    extraversion INTEGER CHECK(extraversion >= 4 AND extraversion <= 20),
                    agreeableness INTEGER CHECK(agreeableness >= 4 AND agreeableness <= 20),
                    neuroticism INTEGER CHECK(neuroticism >= 4 AND neuroticism <= 20),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Enhanced matches table with feedback system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    match_user_id INTEGER,
                    compatibility_score REAL,
                    match_explanation TEXT,
                    is_accepted BOOLEAN DEFAULT NULL,
                    feedback_notes TEXT,
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
        except Exception as e:
            logger.error(f"Unexpected error during database setup: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_user(self, name: str, age: int, gender: str, personality_scores: Dict[str, int]) -> Optional[int]:
        """Add a new user with their personality scores with error handling"""
        conn = None
        try:
            # Validate personality scores
            required_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            for trait in required_traits:
                if trait not in personality_scores:
                    logger.error(f"Missing personality trait: {trait}")
                    return None
                if not (4 <= personality_scores[trait] <= 20):
                    logger.error(f"Invalid score for {trait}: {personality_scores[trait]} (must be 4-20)")
                    return None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (name, age, gender) VALUES (?, ?, ?)",
                (name, age, gender)
            )
            user_id = cursor.lastrowid
            
            # Insert personality scores
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
        except Exception as e:
            logger.error(f"Unexpected error adding user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def categorize_score(self, score: int) -> str:
        """Convert numeric score to personality category"""
        if score <= 7:
            return "very_low"
        elif score <= 11:
            return "low"
        elif score <= 15:
            return "moderate"
        elif score <= 18:
            return "high"
        else:  # 19-20
            return "very_high"

    def calculate_compatibility(self, user1_scores: Dict, user2_scores: Dict) -> Tuple[float, List[str]]:
        """Calculate weighted compatibility percentage and explanations"""
        compatible_traits = 0
        total_weighted_score = 0
        total_possible_weight = 0
        explanations = []
        
        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        for trait in traits:
            if trait in user1_scores and trait in user2_scores:
                # Get categories
                cat1 = self.categorize_score(user1_scores[trait])
                cat2 = self.categorize_score(user2_scores[trait])
                
                # Check compatibility
                compatible_ranges = self.compatibility_matrix[trait][cat1]
                is_compatible = cat2 in compatible_ranges
                
                # Apply weight
                weight = self.trait_weights.get(trait, 1.0)
                total_possible_weight += weight
                
                if is_compatible:
                    compatible_traits += 1
                    total_weighted_score += weight
                    status = "✅ Compatible"
                else:
                    status = "❌ May conflict"
                
                explanations.append(f"{trait.capitalize()}: {status} ({cat1} + {cat2})")
        
        # Calculate weighted percentage
        compatibility_percentage = (total_weighted_score / total_possible_weight * 100) if total_possible_weight > 0 else 0
        
        return compatibility_percentage, explanations

    def find_matches(self, user_id: int, minimum_compatibility: float = 60.0, 
                    gender_filter: str = None, respect_ttl: bool = True, ttl_hours: int = 24) -> List[Dict]:
        """Find compatible matches for a user with error handling and optional filters"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check TTL if enabled
            if respect_ttl:
                cursor.execute("SELECT last_matched FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    last_matched = datetime.fromisoformat(result[0])
                    time_since_match = datetime.now() - last_matched
                    if time_since_match < timedelta(hours=ttl_hours):
                        logger.info(f"User {user_id} matched recently, respecting TTL")
                        return []
            
            # Get target user's scores
            cursor.execute('''
                SELECT u.name, u.age, u.gender, p.openness, p.conscientiousness, 
                       p.extraversion, p.agreeableness, p.neuroticism
                FROM users u
                JOIN personality_scores p ON u.user_id = p.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            target_user = cursor.fetchone()
            if not target_user:
                logger.warning(f"User {user_id} not found")
                return []
            
            target_name, target_age, target_gender, *target_scores = target_user
            target_personality = {
                'openness': target_scores[0],
                'conscientiousness': target_scores[1],
                'extraversion': target_scores[2], 
                'agreeableness': target_scores[3],
                'neuroticism': target_scores[4]
            }
            
            # Build query with optional gender filter
            query = '''
                SELECT u.user_id, u.name, u.age, u.gender, p.openness, p.conscientiousness,
                       p.extraversion, p.agreeableness, p.neuroticism
                FROM users u
                JOIN personality_scores p ON u.user_id = p.user_id  
                WHERE u.user_id != ?
            '''
            params = [user_id]
            
            if gender_filter:
                query += " AND u.gender = ?"
                params.append(gender_filter)
            
            cursor.execute(query, params)
            potential_matches = cursor.fetchall()
            matches = []
            
            for match_data in potential_matches:
                match_id, name, age, gender, *scores = match_data
                match_personality = {
                    'openness': scores[0],
                    'conscientiousness': scores[1],
                    'extraversion': scores[2],
                    'agreeableness': scores[3], 
                    'neuroticism': scores[4]
                }
                
                # Calculate compatibility
                compatibility, explanations = self.calculate_compatibility(target_personality, match_personality)
                
                if compatibility >= minimum_compatibility:
                    matches.append({
                        'user_id': match_id,
                        'name': name,
                        'age': age,
                        'gender': gender,
                        'compatibility_score': compatibility,
                        'personality_scores': match_personality,
                        'explanations': explanations
                    })
            
            # Sort by compatibility score
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            # Save matches to database and update last_matched timestamp
            if matches:
                self.save_matches(user_id, matches)
                cursor.execute("UPDATE users SET last_matched = ? WHERE user_id = ?", 
                             (datetime.now().isoformat(), user_id))
                conn.commit()
            
            logger.info(f"Found {len(matches)} matches for user {user_id}")
            return matches
            
        except sqlite3.Error as e:
            logger.error(f"Database error finding matches: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error finding matches: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def save_matches(self, user_id: int, matches: List[Dict]):
        """Save match results to database with error handling"""
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
        except Exception as e:
            logger.error(f"Unexpected error saving matches: {e}")
        finally:
            if conn:
                conn.close()

    def provide_match_feedback(self, user_id: int, match_user_id: int, is_accepted: bool, notes: str = ""):
        """Record user feedback on matches for future improvement"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE matches 
                SET is_accepted = ?, feedback_notes = ?
                WHERE user_id = ? AND match_user_id = ?
            ''', (is_accepted, notes, user_id, match_user_id))
            
            conn.commit()
            logger.info(f"Feedback recorded for user {user_id}, match {match_user_id}: {'Accepted' if is_accepted else 'Rejected'}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error recording feedback: {e}")
        finally:
            if conn:
                conn.close()

    def display_matches(self, user_id: int, limit: int = 5):
        """Display matches for a user in a nice format - FIXED formatting issues"""
        matches = self.find_matches(user_id)
        
        if not matches:
            print(f"❌ No compatible matches found for user {user_id}")
            return
        
        # FIXED: Properly format the header without line breaks in f-strings
        print(f"🎯 MATCHES FOR USER {user_id}")
        print("=" * 60)
        
        for i, match in enumerate(matches[:limit], 1):
            # FIXED: Split complex f-strings to avoid line break issues
            match_header = f"💕 MATCH #{i}: {match['name'].upper()}"
            print(f"\n{match_header}")
            print(f"Age: {match['age']} | Gender: {match['gender']}")
            print(f"Compatibility: {match['compatibility_score']:.1f}%")
            
            print("\nPersonality Profile:")
            for trait, score in match['personality_scores'].items():
                category = self.categorize_score(score)
                print(f"  {trait.capitalize()}: {score}/20 ({category})")
            
            print("\nCompatibility Analysis:")
            for explanation in match['explanations']:
                print(f"  {explanation}")
            
            print("-" * 40)

    def get_matches_json(self, user_id: int, limit: int = 5) -> str:
        """Get matches in JSON format for web integration"""
        matches = self.find_matches(user_id)
        
        # Prepare data for JSON serialization
        json_data = {
            'user_id': user_id,
            'matches_found': len(matches),
            'matches': matches[:limit]
        }
        
        return json.dumps(json_data, indent=2)

    def get_user_stats(self) -> Dict:
        """Get comprehensive statistics about users and matches in the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic user stats
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT gender, COUNT(*) FROM users GROUP BY gender")
            gender_breakdown = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM matches")
            total_matches = cursor.fetchone()[0]
            
            # Feedback stats
            cursor.execute("SELECT COUNT(*) FROM matches WHERE is_accepted = 1")
            accepted_matches = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM matches WHERE is_accepted = 0")
            rejected_matches = cursor.fetchone()[0]
            
            # Average compatibility score
            cursor.execute("SELECT AVG(compatibility_score) FROM matches")
            avg_compatibility = cursor.fetchone()[0] or 0
            
            return {
                'total_users': total_users,
                'gender_breakdown': gender_breakdown,
                'total_matches_generated': total_matches,
                'accepted_matches': accepted_matches,
                'rejected_matches': rejected_matches,
                'average_compatibility': round(avg_compatibility, 2),
                'acceptance_rate': round((accepted_matches / total_matches * 100), 2) if total_matches > 0 else 0
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting stats: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def get_personality_insights(self, user_id: int) -> Dict:
        """Get detailed personality insights for a user"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.name, p.openness, p.conscientiousness, p.extraversion, 
                       p.agreeableness, p.neuroticism
                FROM users u
                JOIN personality_scores p ON u.user_id = p.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return {}
            
            name, *scores = result
            traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            insights = {
                'name': name,
                'personality_profile': {},
                'dominant_traits': [],
                'areas_for_growth': []
            }
            
            for trait, score in zip(traits, scores):
                category = self.categorize_score(score)
                insights['personality_profile'][trait] = {
                    'score': score,
                    'category': category,
                    'percentile': round((score / 20) * 100)
                }
                
                # Identify dominant traits (high scores)
                if score >= 16:
                    insights['dominant_traits'].append(trait)
                
                # Identify areas for growth (low scores that might benefit from improvement)
                if score <= 8 and trait in ['conscientiousness', 'agreeableness']:
                    insights['areas_for_growth'].append(trait)
            
            return insights
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting personality insights: {e}")
            return {}
        finally:
            if conn:
                conn.close()

# Enhanced demo with new features
def run_enhanced_dating_app_demo():
    """Demo the enhanced dating app matching system"""
    
    try:
        # Initialize the matcher
        matcher = DatingAppMatcher()
        
        print("🚀 ENHANCED DATING APP MATCHING SYSTEM")
        print("=" * 50)
        
        # Add sample users with validation
        users_data = [
            {
                "name": "Sarah", "age": 28, "gender": "Female",
                "personality": {
                    "openness": 17, "conscientiousness": 16, "extraversion": 18,
                    "agreeableness": 14, "neuroticism": 8
                }
            },
            {
                "name": "Mike", "age": 30, "gender": "Male", 
                "personality": {
                    "openness": 12, "conscientiousness": 13, "extraversion": 9,
                    "agreeableness": 16, "neuroticism": 6
                }
            },
            {
                "name": "Alex", "age": 26, "gender": "Male",
                "personality": {
                    "openness": 6, "conscientiousness": 5, "extraversion": 4,
                    "agreeableness": 18, "neuroticism": 17
                }
            },
            {
                "name": "Jenny", "age": 29, "gender": "Female",
                "personality": {
                    "openness": 13, "conscientiousness": 14, "extraversion": 12,
                    "agreeableness": 15, "neuroticism": 10
                }
            },
            {
                "name": "David", "age": 32, "gender": "Male",
                "personality": {
                    "openness": 20, "conscientiousness": 9, "extraversion": 11,
                    "agreeableness": 1, "neuroticism": 2
                }
            }
        ]
        
        # Add users to database
        user_ids = []
        for user_data in users_data:
            user_id = matcher.add_user(
                user_data["name"], 
                user_data["age"], 
                user_data["gender"],
                user_data["personality"]
            )
            if user_id:
                user_ids.append(user_id)
        
        print(f"\n✅ Successfully added {len(user_ids)} users to the database")
        
        # Show enhanced database stats
        stats = matcher.get_user_stats()
        print(f"\n📊 ENHANCED DATABASE STATS:")
        print(f"Total Users: {stats.get('total_users', 0)}")
        print(f"Gender Breakdown: {stats.get('gender_breakdown', {})}")
        print(f"Average Compatibility: {stats.get('average_compatibility', 0)}%")
        
        # Show personality insights
        if user_ids:
            print(f"\n🧠 PERSONALITY INSIGHTS FOR SARAH:")
            insights = matcher.get_personality_insights(user_ids[0])
            if insights:
                for trait, data in insights['personality_profile'].items():
                    print(f"  {trait.capitalize()}: {data['score']}/20 ({data['category']}) - {data['percentile']}th percentile")
                if insights['dominant_traits']:
                    print(f"  Dominant traits: {', '.join(insights['dominant_traits'])}")
        
        # Find matches with different filters
        if user_ids:
            print(f"\n🔍 Finding matches for Sarah (Female users only)...")
            sarah_matches = matcher.find_matches(user_ids[0], gender_filter="Male")
            matcher.display_matches(user_ids[0], limit=3)
            
            # Simulate feedback
            if sarah_matches:
                print(f"\n💬 Recording feedback...")
                matcher.provide_match_feedback(user_ids[0], sarah_matches[0]['user_id'], True, "Great match!")
                matcher.provide_match_feedback(user_ids[0], sarah_matches[1]['user_id'], False, "Not compatible")
            
            # Show JSON output
            print(f"\n📄 JSON OUTPUT SAMPLE:")
            json_output = matcher.get_matches_json(user_ids[0], limit=2)
            print(json_output[:200] + "..." if len(json_output) > 200 else json_output)
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"❌ Demo failed: {e}")

# Run the enhanced demo
if __name__ == "__main__":
    run_enhanced_dating_app_demo()
