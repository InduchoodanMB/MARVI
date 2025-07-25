import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Handles compatibility calculations and matching logic"""
    
    def __init__(self):
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

    def find_matches_for_user(self, target_user: Dict, potential_matches: List[Dict], 
                             minimum_compatibility: float = 60.0) -> List[Dict]:
        """
        Find compatible matches for a target user from potential matches
        """
        matches = []
        target_personality = target_user.get('personality_scores')
        
        if not target_personality:
            logger.warning(f"No personality scores found for user {target_user.get('user_id')}")
            return matches
        
        for potential_match in potential_matches:
            match_personality = potential_match.get('personality_scores')
            
            if not match_personality:
                continue
            
            # Calculate compatibility
            compatibility, explanations = self.calculate_compatibility(target_personality, match_personality)
            
            if compatibility >= minimum_compatibility:
                match_data = {
                    'user_id': potential_match['user_id'],
                    'name': potential_match['name'],
                    'age': potential_match['age'],
                    'gender': potential_match['gender'],
                    'location': potential_match.get('location', ''),
                    'bio': potential_match.get('bio', ''),
                    'compatibility_score': compatibility,
                    'personality_scores': match_personality,
                    'explanations': explanations
                }
                matches.append(match_data)
        
        # Sort by compatibility score (highest first)
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return matches

    def get_match_reasons(self, compatibility_explanations: List[str]) -> Dict[str, List[str]]:
        """Parse compatibility explanations into positive and negative reasons"""
        positive_reasons = []
        negative_reasons = []
        
        for explanation in compatibility_explanations:
            if "✅ Compatible" in explanation:
                positive_reasons.append(explanation.replace("✅ Compatible", "Good match"))
            elif "❌ May conflict" in explanation:
                negative_reasons.append(explanation.replace("❌ May conflict", "Potential challenge"))
        
        return {
            'positive': positive_reasons,
            'negative': negative_reasons
        }

    def calculate_overall_chemistry(self, user1_scores: Dict, user2_scores: Dict) -> Dict[str, float]:
        """Calculate different aspects of relationship compatibility"""
        
        # Communication style compatibility (based on extraversion and openness)
        comm_score1 = (user1_scores['extraversion'] + user1_scores['openness']) / 2
        comm_score2 = (user2_scores['extraversion'] + user2_scores['openness']) / 2
        communication_compatibility = 100 - abs(comm_score1 - comm_score2) * 5
        
        # Lifestyle compatibility (based on conscientiousness and neuroticism)
        lifestyle_score1 = (user1_scores['conscientiousness'] + (20 - user1_scores['neuroticism'])) / 2
        lifestyle_score2 = (user2_scores['conscientiousness'] + (20 - user2_scores['neuroticism'])) / 2
        lifestyle_compatibility = 100 - abs(lifestyle_score1 - lifestyle_score2) * 5
        
        # Emotional compatibility (based on agreeableness and neuroticism)
        emotional_score1 = (user1_scores['agreeableness'] + (20 - user1_scores['neuroticism'])) / 2
        emotional_score2 = (user2_scores['agreeableness'] + (20 - user2_scores['neuroticism'])) / 2
        emotional_compatibility = 100 - abs(emotional_score1 - emotional_score2) * 5
        
        # Ensure scores are between 0 and 100
        return {
            'communication': max(0, min(100, communication_compatibility)),
            'lifestyle': max(0, min(100, lifestyle_compatibility)),
            'emotional': max(0, min(100, emotional_compatibility))
        }

    def get_relationship_advice(self, user1_scores: Dict, user2_scores: Dict) -> List[str]:
        """Generate relationship advice based on personality compatibility"""
        advice = []
        
        # Openness advice
        if abs(user1_scores['openness'] - user2_scores['openness']) > 8:
            advice.append("Balance adventure and routine - plan both exciting activities and comfortable downtime")
        
        # Conscientiousness advice
        if abs(user1_scores['conscientiousness'] - user2_scores['conscientiousness']) > 6:
            advice.append("Respect different approaches to planning and organization")
        
        # Extraversion advice
        if abs(user1_scores['extraversion'] - user2_scores['extraversion']) > 8:
            advice.append("Balance social activities with quiet time together")
        
        # Agreeableness advice
        if user1_scores['agreeableness'] < 10 or user2_scores['agreeableness'] < 10:
            advice.append("Practice active listening and express appreciation regularly")
        
        # Neuroticism advice
        if user1_scores['neuroticism'] > 15 or user2_scores['neuroticism'] > 15:
            advice.append("Create a supportive environment and communicate openly about stress")
        
        return advice if advice else ["You have great natural compatibility! Focus on open communication and mutual respect."]

    def find_matches(self, user_traits: Dict[str, float], other_users: List[Dict]) -> List[Dict]:
        """
        user_traits: { "openness": 70.0, ... }
        other_users: [ { "name": "Alex", "traits": {...} }, ... ]
        Returns top matches based on lowest trait distance.
        """
        def trait_distance(t1, t2):
            return sum(
                self.trait_weights[trait] * abs(t1[trait] - t2[trait])
                for trait in self.trait_weights
            )

        matches = []
        for user in other_users:
            distance = trait_distance(user_traits, user["traits"])
            matches.append({
                "name": user["name"],
                "compatibility": round(100 - distance, 2)
            })

        return sorted(matches, key=lambda x: -x["compatibility"])
