from flask import Flask, request, jsonify, send_file
from personality_test import PersonalityTest
from marvi_matcher import MatchingEngine
from database import load_users, save_user

app = Flask(__name__)
test_engine = PersonalityTest()
match_engine = MatchingEngine()

# Serve the UI
@app.route('/')
def serve_ui():
    return send_file('ui.html')

# Handle test submission
@app.route('/submit', methods=['POST'])
def submit_answers():
    data = request.json

    user_answers = data.get('answers')                 # Answers from form
    user_name = data.get('name', 'Anonymous')          # Name from frontend

    # Step 1: Score the user's traits
    traits = test_engine.calculate_traits(user_answers)

    # Step 2: Save this user to database
    save_user({ "name": user_name, "traits": traits })

    # Step 3: Load others (excluding current user)
    all_users = load_users()
    match_pool = [u for u in all_users if u["name"] != user_name]

    # Step 4: Find matches
    matches = match_engine.find_matches(traits, match_pool)

    return jsonify({
        'your_traits': traits,
        'matches': matches
    })

if __name__ == '__main__':
    app.run(debug=True)

