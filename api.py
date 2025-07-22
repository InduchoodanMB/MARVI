"""
REST API for Dating App Frontend Integration
FastAPI-based backend for web/mobile frontend
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
import logging

from database import DatabaseManager
from personality_test import PersonalityTest
from matching_engine import MatchingEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Dating App API",
    description="Personality-based dating app backend API",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
personality_test = PersonalityTest()
matching_engine = MatchingEngine()

# Pydantic models for API
class UserCreate(BaseModel):
    name: str
    age: int
    gender: str
    location: Optional[str] = ""
    bio: Optional[str] = ""
    
    @validator('age')
    def validate_age(cls, v):
        if not (18 <= v <= 100):
            raise ValueError('Age must be between 18 and 100')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        valid_genders = ['Male', 'Female', 'Non-binary', 'Other']
        if v not in valid_genders:
            raise ValueError(f'Gender must be one of: {valid_genders}')
        return v

class PersonalityScores(BaseModel):
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int
    
    @validator('*')
    def validate_scores(cls, v):
        if not (1 <= v <= 20):
            raise ValueError('Personality scores must be between 1 and 20')
        return v

class UserProfile(BaseModel):
    user_data: UserCreate
    personality_scores: PersonalityScores

class PersonalityTestResponse(BaseModel):
    responses: Dict[int, int]  # question_id -> response (1-5)

class MatchRequest(BaseModel):
    user_id: int
    gender_filter: Optional[str] = None
    minimum_compatibility: Optional[float] = 60.0
    limit: Optional[int] = 10

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Smart Dating App API is running!", "version": "1.0.0"}

@app.get("/personality-questions")
async def get_personality_questions():
    """Get all personality test questions"""
    try:
        questions = personality_test.get_all_questions()
        return {
            "questions": questions,
            "total_questions": len(questions),
            "instructions": {
                "scale": "1-5 (1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree)",
                "description": "Rate each statement based on how well it describes you"
            }
        }
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve questions")

@app.post("/calculate-personality")
async def calculate_personality_scores(responses: PersonalityTestResponse):
    """Calculate personality scores from test responses"""
    try:
        scores = personality_test.calculate_scores_from_responses(responses.responses)
        
        # Add descriptions for each trait
        detailed_results = {}
        for trait, score in scores.items():
            category = personality_test.categorize_score(score)
            description = personality_test.get_trait_description(trait, score)
            detailed_results[trait] = {
                "score": score,
                "category": category,
                "description": description
            }
        
        return {
            "personality_scores": scores,
            "detailed_results": detailed_results,
            "summary": "Personality assessment completed successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating personality: {e}")
        raise HTTPException(status_code=400, detail="Failed to calculate personality scores")

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user_profile: UserProfile):
    """Create a new user with personality profile"""
    try:
        user_id = db.add_user(
            name=user_profile.user_data.name,
            age=user_profile.user_data.age,
            gender=user_profile.user_data.gender,
            location=user_profile.user_data.location,
            bio=user_profile.user_data.bio,
            personality_scores=user_profile.personality_scores.dict()
        )
        
        if user_id:
            return {
                "user_id": user_id,
                "message": f"User {user_profile.user_data.name} created successfully",
                "profile": user_profile.dict()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user profile by ID"""
    try:
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add personality descriptions if available
        if user_data['personality_scores']:
            personality_details = {}
            for trait, score in user_data['personality_scores'].items():
                if score is not None:
                    category = personality_test.categorize_score(score)
                    description = personality_test.get_trait_description(trait, score)
                    personality_details[trait] = {
                        "score": score,
                        "category": category,
                        "description": description
                    }
            user_data['personality_details'] = personality_details
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/matches")
async def find_matches(match_request: MatchRequest):
    """Find matches for a user"""
    try:
        # Get user data
        user_data = db.get_user_by_id(match_request.user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user_data.get('personality_scores'):
            raise HTTPException(status_code=400, detail="User must complete personality test first")
        
        # Get potential matches
        potential_matches = db.get_all_users_except(
            match_request.user_id, 
            match_request.gender_filter
        )
        
        if not potential_matches:
            return {
                "matches": [],
                "total_matches": 0,
                "message": "No potential matches found"
            }
        
        # Find compatible matches
        matches = matching_engine.find_matches_for_user(
            user_data, 
            potential_matches,
            match_request.minimum_compatibility
        )
        
        # Limit results
        limited_matches = matches[:match_request.limit]
        
        # Add detailed chemistry analysis for each match
        for match in limited_matches:
            chemistry = matching_engine.calculate_overall_chemistry(
                user_data['personality_scores'],
                match['personality_scores']
            )
            match['chemistry_breakdown'] = chemistry
            
            # Add relationship advice
            advice = matching_engine.get_relationship_advice(
                user_data['personality_scores'],
                match['personality_scores']
            )
            match['relationship_tips'] = advice
        
        # Save matches to database
        if limited_matches:
            db.save_matches(match_request.user_id, limited_matches)
        
        return {
            "matches": limited_matches,
            "total_matches": len(limited_matches),
            "total_potential": len(potential_matches),
            "user_profile": {
                "name": user_data['name'],
                "age": user_data['age'],
                "gender": user_data['gender']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_app_statistics():
    """Get application statistics"""
    try:
        stats = db.get_user_stats()
        return {
            "statistics": stats,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/compatibility/{user1_id}/{user2_id}")
async def get_compatibility_analysis(user1_id: int, user2_id: int):
    """Get detailed compatibility analysis between two users"""
    try:
        # Get both users
        user1 = db.get_user_by_id(user1_id)
        user2 = db.get_user_by_id(user2_id)
        
        if not user1 or not user2:
            raise HTTPException(status_code=404, detail="One or both users not found")
        
        if not user1.get('personality_scores') or not user2.get('personality_scores'):
            raise HTTPException(status_code=400, detail="Both users must have personality scores")
        
        # Calculate compatibility
        compatibility_score, explanations = matching_engine.calculate_compatibility(
            user1['personality_scores'],
            user2['personality_scores']
        )
        
        # Get chemistry breakdown
        chemistry = matching_engine.calculate_overall_chemistry(
            user1['personality_scores'],
            user2['personality_scores']
        )
        
        # Get relationship advice
        advice = matching_engine.get_relationship_advice(
            user1['personality_scores'],
            user2['personality_scores']
        )
        
        return {
            "user1": {"name": user1['name'], "id": user1_id},
            "user2": {"name": user2['name'], "id": user2_id},
            "overall_compatibility": compatibility_score,
            "compatibility_explanations": explanations,
            "chemistry_breakdown": chemistry,
            "relationship_advice": advice
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing compatibility: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)