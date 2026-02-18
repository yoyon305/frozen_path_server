from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# --- CONFIG ---
ADMIN_KEY = "yonatan123" 

# --- JSONBIN CONFIG ---
JSONBIN_ID = "698a1b0bae596e708f1e0592"
JSONBIN_KEY = "$2a$10$IYrwOfBEItTfOQ8RSQcmDexCyllyHqxGJSIwG6utFfH0acVBxQ3JW"
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_KEY,
    "Content-Type": "application/json"
}

# --- DATABASE ---
# משנים ל-None כדי לדעת אם עוד לא טענו בכלל
LEADERBOARD_DATA = None 

def load_from_cloud():
    """Loads data and strictly extracts the 'record' content."""
    global LEADERBOARD_DATA
    try:
        print("DEBUG: Fetching from JSONBin...", flush=True)
        response = requests.get(JSONBIN_URL, headers=HEADERS, timeout=7) # הוספת Timeout
        
        if response.status_code == 200:
            raw_data = response.json()
            data = raw_data.get("record", raw_data)
            
            if not isinstance(data, dict):
                LEADERBOARD_DATA = {}
            else:
                LEADERBOARD_DATA = data
            print(f"DEBUG: Success! {len(LEADERBOARD_DATA)} players loaded.", flush=True)
        else:
            LEADERBOARD_DATA = {} # Default on error
    except Exception as e:
        print(f"DEBUG: Load error: {e}", flush=True)
        LEADERBOARD_DATA = {}

def ensure_data():
    """Helper to ensure data is loaded before any operation."""
    if LEADERBOARD_DATA is None:
        load_from_cloud()

def save_to_cloud():
    """Saves the current memory state to JSONBin."""
    try:
        # שומרים רק אם יש נתונים
        data_to_save = LEADERBOARD_DATA if LEADERBOARD_DATA is not None else {}
        requests.put(JSONBIN_URL, json=data_to_save, headers=HEADERS, timeout=5)
    except Exception as e:
        print(f"DEBUG: Save Crash: {e}", flush=True)

# --- CORS ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    # Render רואה את זה ועושה V על ה-Health Check מיד
    return "Server is Running."

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    ensure_data()
    try:
        # סינון ערכים לא מספריים (כדי למנוע קריסה על ה-'initialized' הישן)
        sorted_scores = sorted(
            [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items() if isinstance(v, (int, float))],
            key=lambda x: x['score'],
            reverse=True
        )
        return jsonify(sorted_scores)
    except Exception as e:
        return jsonify([])

@app.route('/submit', methods=['POST'])
def submit_score():
    ensure_data()
    data = request.json
    name = str(data.get("name"))
    score = data.get("score")

    if not name or score is None or not isinstance(score, (int, float)):
        return jsonify({"error": "Invalid data"}), 400

    if score > LEADERBOARD_DATA.get(name, 0):
        LEADERBOARD_DATA[name] = score
        save_to_cloud()
        return jsonify({"status": "updated"})
    
    return jsonify({"status": "ignored"})

@app.route('/admin/reset', methods=['GET'])
def reset_leaderboard():
    if request.args.get('key') != ADMIN_KEY: return "Forbidden", 403
    global LEADERBOARD_DATA
    LEADERBOARD_DATA = {}
    save_to_cloud()
    return "Wiped."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
