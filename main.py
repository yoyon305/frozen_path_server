from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allows your game to talk to this server

# --- DATABASE (In-Memory) ---
# This resets if the server restarts. 
# For a real permanent DB, you'd need a file or database connection, 
# but this is perfect for a first test.
LEADERBOARD_DATA = {
    "PenguinDev": 55,
    "BetaTester": 20
}

@app.route('/')
def home():
    return "Frozen Path Leaderboard is Alive!"

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.json
    name = data.get("name")
    score = data.get("score")

    if not name or score is None:
        return jsonify({"error": "Missing data"}), 400

    # LOGIC: Only update if the new score is HIGHER
    # We treat the input as "Total Stars"
    current_score = LEADERBOARD_DATA.get(name, 0)
    
    if score > current_score:
        LEADERBOARD_DATA[name] = score
        print(f"Updated {name} to {score}")
    
    return jsonify({"status": "success", "new_high_score": LEADERBOARD_DATA[name]})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # Sort by score (descending) and return top 10
    sorted_scores = sorted(
        [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items()],
        key=lambda x: x['score'],
        reverse=True
    )
    return jsonify(sorted_scores[:10])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)