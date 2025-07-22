import logging
from typing import Dict, List, Optional
from database import DatabaseManager
from personality_test import PersonalityTest
from matching_engine import MatchingEngine

logger = logging.getLogger(__name__)

class UserInterface:
    """Handles all user interactions and display logic"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.personality_test = PersonalityTest()
        self.matching_engine = MatchingEngine()
    
    def display_welcome(self):
        """Display welcome message"""
        print("💕 WELCOME TO SMART DATING APP 💕")
        print("=" * 50)
        print("Find your perfect match based on personality compatibility!")
        print("=" * 50)
    
    def get_user_profile(self) -> Dict:
        """Get user profile information interactively"""
        print("\n📝 CREATE YOUR PROFILE")
        print("-" * 30)
        
        # Basic info
        name = input("Enter your name: ").strip()
        while not name:
            name = input("Name cannot be empty. Please enter your name: ").strip()
        
        # Age validation
        while True:
            try:
                age = int(input("Enter your age: "))
                if 18 <= age <= 100:
                    break
                else:
                    print("Age must be between 18 and 100")
            except ValueError:
                print("Please enter a valid age")
        
        # Gender
        print("\nGender options:")
        print("1. Male")
        print("2. Female") 
        print("3. Non-binary")
        print("4. Other")
        
        gender_map = {1: "Male", 2: "Female", 3: "Non-binary", 4: "Other"}
        while True:
            try:
                gender_choice = int(input("Choose gender (1-4): "))
                if gender_choice in gender_map:
                    gender = gender_map[gender_choice]
                    break
                else:
                    print("Please choose 1, 2, 3, or 4")
            except ValueError:
                print("Please enter a valid number")
        
        # Optional info
        location = input("Enter your location (optional): ").strip()
        bio = input("Enter a short bio (optional): ").strip()
        
        return {
            'name': name,
            'age': age,
            'gender': gender,
            'location': location,
            'bio': bio
        }
    
    def register_new_user(self) -> Optional[int]:
        """Complete user registration process"""
        print("\n🎉 LET'S GET YOU SIGNED UP!")
        
        # Get profile
        profile = self.get_user_profile()
        
        # Take personality test
        print(f"\nGreat {profile['name']}! Now let's discover your personality...")
        input("Press Enter to start the personality test...")
        
        personality_scores = self.personality_test.get_interactive_test()
        
        # Save to database
        user_id = self.db.add_user(
            name=profile['name'],
            age=profile['age'],
            gender=profile['gender'],
            location=profile['location'],
            bio=profile['bio'],
            personality_scores=personality_