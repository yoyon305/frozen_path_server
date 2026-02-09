from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# --- CONFIG ---
ADMIN_KEY = "yonatan123" 

# --- JSONBIN CONFIG ---
# Make sure these are correct!
JSONBIN_ID = "698a1b0bae596e708f1e0592"
JSONBIN_KEY = "$2a$10$IYrwOfBEItTfOQ8RSQcmDexCyllyHqxGJSIwG6utFfH0acVBxQ3JW"

JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_KEY,
    "Content-Type": "application/json"
}

# --- DATABASE ---
LEADERBOARD_DATA = {}

# --- CRITICAL FIX: UNWRAP THE DATA ---
def load_from_cloud():
    """Loads data and strictly extracts the 'record' content."""
    global LEADERBOARD_DATA
    try:
        print("DEBUG: Loading from JSONBin...", flush=True)
        response = requests.get(JSONBIN_URL, headers=HEADERS)
        
        if response.status_code == 200:
            raw_data = response.json()
            
            # 1. Check if the data is wrapped in "record" (JSONBin V3 standard)
            if "record" in raw_data:
                LEADERBOARD_DATA = raw_data["record"]
            else:
                # Fallback: maybe it's not wrapped (V2 or custom)
                LEADERBOARD_DATA = raw_data
            
            # 2. Sanity Check: Ensure LEADERBOARD_DATA is actually a dict
            if not isinstance(LEADERBOARD_DATA, dict):
                print("DEBUG: Data format warning! Resetting to empty dict.", flush=True)
                LEADERBOARD_DATA = {}
                
            print(f"DEBUG: Success! Loaded {len(LEADERBOARD_DATA)} players.", flush=True)
            print(f"DEBUG: Sample Data: {list(LEADERBOARD_DATA.items())[:3]}", flush=True)
            
        else:
            print(f"DEBUG: Cloud Error {response.status_code}: {response.text}", flush=True)
            
    except Exception as e:
        print(f"DEBUG: Crash during load: {e}", flush=True)

def save_to_cloud():
    """Saves the data to the cloud."""
    try:
        # JSONBin automatically wraps this in "record" when we PUT
        response = requests.put(JSONBIN_URL, json=LEADERBOARD_DATA, headers=HEADERS)
        if response.status_code == 200:
            print("DEBUG: Cloud Save Success", flush=True)
        else:
            print(f"DEBUG: Cloud Save Failed: {response.text}", flush=True)
    except Exception as e:
        print(f"DEBUG: Save Crash: {e}", flush=True)

# Load data immediately when server starts
with app.app_context():
    load_from_cloud()

# --- CORS FIX ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return f"Server is Running. Players loaded: {len(LEADERBOARD_DATA)}"

# --- DEBUG ROUTE (Use this to verify what the server sees) ---
@app.route('/debug/raw', methods=['GET'])
def debug_raw():
    # Use this in browser to see EXACTLY what is in memory
    if request.args.get('key') != ADMIN_KEY: return "Privileged Access Only", 403
    return jsonify({
        "memory_data": LEADERBOARD_DATA,
        "type": str(type(LEADERBOARD_DATA))
    })

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.json
    name = data.get("name")
    score = data.get("score")

    if not name or score is None:
        return jsonify({"error": "Missing data"}), 400

    # Ensure name is a string to prevent issues
    name = str(name)
    
    current_score = LEADERBOARD_DATA.get(name, 0)
    
    # Logic: Only update if score is higher
    if score > current_score:
        LEADERBOARD_DATA[name] = score
        # Save to cloud immediately
        save_to_cloud()
        return jsonify({"status": "updated", "new_score": score})
    
    return jsonify({"status": "ignored", "current_score": current_score})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # Defensive coding: If data is corrupted or empty, try reloading
    if not LEADERBOARD_DATA:
        load_from_cloud()

    # Create the sorted list
    try:
        sorted_scores = sorted(
            [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items() if isinstance(v, (int, float))],
            key=lambda x: x['score'],
            reverse=True
        )
        return jsonify(sorted_scores[:10])
    except Exception as e:
        print(f"DEBUG: Sort Error: {e}", flush=True)
        return jsonify([])

# --- ADMIN ROUTES ---
@app.route('/admin/reset', methods=['GET'])
def reset_leaderboard():
    if request.args.get('key') != ADMIN_KEY: return "Wrong Password", 403
    LEADERBOARD_DATA.clear()
    save_to_cloud()
    return "Leaderboard wiped."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
