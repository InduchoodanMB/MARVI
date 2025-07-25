from typing import Dict, List

class PersonalityTest:
    """Handles personality assessment through questions"""
    
    def __init__(self):
        # Big Five personality questions with scoring direction
        self.questions = {
            'openness': [
                ("I enjoy trying new and unusual experiences", True),
                ("I prefer routine and familiar activities", False),
                ("I love exploring new ideas and concepts", True),
                ("I'm curious about how things work", True)
            ],
            'conscientiousness': [
                ("I always complete tasks on time", True),
                ("I keep my workspace organized", True),
                ("I often procrastinate on important tasks", False),
                ("I pay attention to details", True)
            ],
            'extraversion': [
                ("I enjoy being the center of attention", True),
                ("I feel energized after social gatherings", True),
                ("I prefer quiet, solitary activities", False),
                ("I find it easy to start conversations", True)
            ],
            'agreeableness': [
                ("I try to help others when I can", True),
                ("I trust people easily", True),
                ("I often get into arguments with others", False),
                ("I'm sympathetic to others' problems", True)
            ],
            'neuroticism': [
                ("I often worry about things", True),
                ("I get stressed easily", True),
                ("I remain calm under pressure", False),
                ("I rarely feel anxious or nervous", False)
            ]
        }
    
    def get_all_questions(self) -> List[Dict]:
        """Get all questions in a structured format for frontend use"""
        all_questions = []
        question_id = 1
        
        for trait, questions in self.questions.items():
            for question_text, is_positive in questions:
                all_questions.append({
                    'id': question_id,
                    'trait': trait,
                    'question': question_text,
                    'is_positive': is_positive
                })
                question_id += 1
        
        return all_questions
    
    def calculate_scores_from_responses(self, responses: Dict[int, int]) -> Dict[str, int]:
        """
        Calculate personality scores from responses
        responses: dict mapping question_id to answer (1-5 scale)
        Returns: dict mapping trait to score (1-20 scale)
        """
        trait_scores = {trait: 0 for trait in self.questions.keys()}
        questions_data = self.get_all_questions()
        
        for question_data in questions_data:
            question_id = question_data['id']
            trait = question_data['trait']
            is_positive = question_data['is_positive']
            
            if question_id in responses:
                response = responses[question_id]
                
                # For negative questions, reverse the score
                if not is_positive:
                    response = 6 - response  # Convert 1->5, 2->4, 3->3, 4->2, 5->1
                
                trait_scores[trait] += response
        
        return trait_scores
    
    def get_interactive_test(self) -> Dict[str, int]:
        """Run interactive personality test through console"""
        print("🧠 PERSONALITY TEST")
        print("=" * 40)
        print("Rate each statement on a scale of 1-5:")
        print("1 = Strongly Disagree")
        print("2 = Disagree")
        print("3 = Neutral")
        print("4 = Agree")
        print("5 = Strongly Agree")
        print("-" * 40)
        
        responses = {}
        questions_data = self.get_all_questions()
        
        for i, question_data in enumerate(questions_data, 1):
            print(f"\nQuestion {i}/{len(questions_data)}:")
            print(f"'{question_data['question']}'")
            
            while True:
                try:
                    response = int(input("Your rating (1-5): "))
                    if 1 <= response <= 5:
                        responses[question_data['id']] = response
                        break
                    else:
                        print("Please enter a number between 1 and 5")
                except ValueError:
                    print("Please enter a valid number")
        
        # Calculate scores
        scores = self.calculate_scores_from_responses(responses)
        
        print("\n🎯 YOUR PERSONALITY SCORES:")
        print("=" * 40)
        for trait, score in scores.items():
            category = self.categorize_score(score)
            print(f"{trait.capitalize()}: {score}/20 ({category})")
        
        return scores
    
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
    
    def get_trait_description(self, trait: str, score: int) -> str:
        """Get description of what a trait score means"""
        category = self.categorize_score(score)
        
        descriptions = {
            'openness': {
                'very_low': "You prefer familiar routines and traditional approaches",
                'low': "You tend to be practical and prefer conventional ways",
                'moderate': "You balance creativity with practicality",
                'high': "You're curious and enjoy exploring new ideas",
                'very_high': "You're highly creative and love novel experiences"
            },
            'conscientiousness': {
                'very_low': "You tend to be spontaneous and flexible with schedules",
                'low': "You're somewhat disorganized but adaptable",
                'moderate': "You balance structure with flexibility",
                'high': "You're organized, reliable, and goal-oriented",
                'very_high': "You're highly disciplined and detail-oriented"
            },
            'extraversion': {
                'very_low': "You strongly prefer solitude and quiet environments",
                'low': "You tend to be reserved and introspective",
                'moderate': "You enjoy both social time and alone time",
                'high': "You're sociable and gain energy from others",
                'very_high': "You're highly outgoing and love being around people"
            },
            'agreeableness': {
                'very_low': "You tend to be competitive and skeptical of others",
                'low': "You can be somewhat critical or argumentative",
                'moderate': "You balance cooperation with standing your ground",
                'high': "You're trusting, helpful, and empathetic",
                'very_high': "You're extremely compassionate and generous"
            },
            'neuroticism': {
                'very_low': "You're exceptionally calm and emotionally stable",
                'low': "You handle stress well and stay composed",
                'moderate': "You experience normal levels of stress and emotion",
                'high': "You tend to worry and feel stress more intensely",
                'very_high': "You often experience anxiety and emotional ups and downs"
            }
        }
        
        return descriptions.get(trait, {}).get(category, "No description available")
    
    def calculate_traits(self, answers: Dict[str, List[int]]) -> Dict[str, float]:
        """
        Takes a dictionary of answers like:
        {
            'openness': [1, 0, 1, 1],
            'conscientiousness': [1, 1, 0, 1],
            ...
        }
        and returns normalized trait scores as percentages.
        """
        trait_scores = {}
        for trait, questions in self.questions.items():
            total_questions = len(questions)
            total_score = sum(answers.get(trait, []))
            trait_scores[trait] = round((total_score / total_questions) * 100, 2) if total_questions else 0.0
        return trait_scores
