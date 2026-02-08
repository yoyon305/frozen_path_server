from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# --- DATABASE (In-Memory) ---
LEADERBOARD_DATA = {}

# --- THE BRUTE FORCE CORS FIX ---
# במקום להסתמך על ספרייה, אנחנו מזריקים את האישור ידנית לכל תשובה.
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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

    current_score = LEADERBOARD_DATA.get(name, 0)
    
    if score > current_score:
        LEADERBOARD_DATA[name] = score
        print(f"Updated {name} to {score}")
    
    return jsonify({"status": "success", "new_high_score": LEADERBOARD_DATA[name]})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    sorted_scores = sorted(
        [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items()],
        key=lambda x: x['score'],
        reverse=True
    )
    return jsonify(sorted_scores[:10])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
