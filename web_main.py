from database import DatabaseManager
from flask import Flask, request, jsonify, send_file
from personality_test import PersonalityTest
from marvi_matcher import MatchingEngine
app = Flask(__name__)
test_engine = PersonalityTest()
match_engine = MatchingEngine()
db = DatabaseManager()


# Serve the UI
@app.route('/')
def serve_ui():
    return send_file('ui.html')

# Handle test submission
@app.route('/submit', methods=['POST'])
@app.route('/submit', methods=['POST'])
def submit_answers():
    data = request.json

    user_name = data.get('name', 'Anonymous')
    age = data.get('age', 0)
    gender = data.get('gender', 'unspecified')
    location = data.get('location', '')
    bio = data.get('bio', '')

    answers = data.get('answers')  # dict of trait: [1, 0, 1...]
    traits = test_engine.calculate_traits(answers)

    # Convert percent scores (0–100) to SQLite's 1–20 range
    personality_scores = {trait: max(1, min(20, round(score / 5))) for trait, score in traits.items()}

    user_id = db.add_user(
        name=user_name,
        age=age,
        gender=gender,
        location=location,
        bio=bio,
        personality_scores=personality_scores
    )

    if user_id is None:
        return jsonify({'error': 'Failed to save user'}), 400

    # Get all other users
    other_users = db.get_all_users_except(user_id)

    # Convert DB structure to what matcher expects
    match_input = []
    for u in other_users:
        match_input.append({
            'name': u['name'],
            'traits': u['personality_scores']
        })

    matches = match_engine.find_matches(traits, match_input)

    return jsonify({
        'your_traits': traits,
        'matches': matches
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


