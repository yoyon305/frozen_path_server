from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# --- הגדרות ---
ADMIN_KEY = "yonatan123" 

# --- כאן מדביקים את הנתונים מ-JSONBin ---
JSONBIN_ID = "698a1b0bae596e708f1e0592"
JSONBIN_KEY = "$2a$10$IYrwOfBEItTfOQ8RSQcmDexCyllyHqxGJSIwG6utFfH0acVBxQ3JW"

# כתובת הקסם לשמירה בענן
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_KEY,
    "Content-Type": "application/json"
}

# --- הזיכרון של השרת ---
LEADERBOARD_DATA = {}

# פונקציה שטוענת את הנתונים כשהשרת מתעורר
def load_data():
    global LEADERBOARD_DATA
    try:
        resp = requests.get(JSONBIN_URL, headers=HEADERS)
        if resp.status_code == 200:
            LEADERBOARD_DATA = resp.json().get("record", {})
            print("Server woke up: Data loaded from cloud!")
    except: pass

# פונקציה ששומרת לענן אחרי כל שינוי
def save_data():
    try:
        requests.put(JSONBIN_URL, json=LEADERBOARD_DATA, headers=HEADERS)
        print("Score saved to cloud!")
    except: pass

# טעינה ראשונית בהפעלה
with app.app_context():
    load_data()

# --- CORS FIX (חובה למשחק) ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return "Persistent Server is Running!"

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.json
    name = data.get("name")
    score = data.get("score")
    
    if not name or score is None: return jsonify({"error": "Missing data"}), 400

    current_score = LEADERBOARD_DATA.get(name, 0)
    
    # עדכון רק אם השיא נשבר
    if score > current_score:
        LEADERBOARD_DATA[name] = score
        # --- השורה שמצילה את הנתונים ---
        save_data() 
        return jsonify({"status": "saved", "score": score})
    
    return jsonify({"status": "ignored", "score": current_score})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # הגנה כפולה: אם הזיכרון ריק, נסה לטעון שוב מהענן
    if not LEADERBOARD_DATA:
        load_data()

    sorted_scores = sorted(
        [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items()],
        key=lambda x: x['score'],
        reverse=True
    )
    return jsonify(sorted_scores[:10])

# --- ניהול ---
@app.route('/admin/reset', methods=['GET'])
def reset_leaderboard():
    if request.args.get('key') != ADMIN_KEY: return "Wrong Password", 403
    LEADERBOARD_DATA.clear()
    save_data()
    return "Leaderboard wiped clean."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
