from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# --- CONFIG ---
# זו הסיסמה הסודית שלך לניהול.
# תשנה את זה למשהו שרק אתה יודע!
ADMIN_KEY = "yonatan123" 

# --- DATABASE (In-Memory) ---
# הנתונים נשמרים בזיכרון. אם השרת עושה ריסטארט, זה מתאפס.
LEADERBOARD_DATA = {}

# --- CORS FIX (התיקון הקריטי ל-itch.io) ---
# זה מוסיף את האישור לכל תשובה שהשרת שולח
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return "Frozen Path Leaderboard is Alive!"

# --- PUBLIC ROUTES (המשחק משתמש בזה) ---

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.json
    name = data.get("name")
    score = data.get("score")

    if not name or score is None:
        return jsonify({"error": "Missing data"}), 400

    # --- ההגנה שביקשת ---
    # 1. קבל את הניקוד הנוכחי של השחקן (0 אם הוא חדש)
    current_score = LEADERBOARD_DATA.get(name, 0)
    
    # 2. עדכן רק אם הניקוד החדש גבוה יותר!
    # אם User1 מנסה לשלוח 1 כוכב אבל יש לו כבר 50, השרת יתעלם מזה.
    if score > current_score:
        LEADERBOARD_DATA[name] = score
        print(f"Updated {name} to {score}")
        return jsonify({"status": "success", "new_high_score": score})
    
    else:
        print(f"Ignored score {score} for {name} (Current is {current_score})")
        return jsonify({"status": "ignored", "current_high_score": current_score})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # מחזיר רק את ה-10 הטובים ביותר
    sorted_scores = sorted(
        [{"name": k, "score": v} for k, v in LEADERBOARD_DATA.items()],
        key=lambda x: x['score'],
        reverse=True
    )
    return jsonify(sorted_scores[:10])

# --- ADMIN ROUTES (רק לך - דרך הדפדפן) ---

# כדי למחוק שחקן ספציפי:
# https://YOUR-URL/admin/delete?name=BadGuy&key=yonatan123
@app.route('/admin/delete', methods=['GET'])
def delete_player():
    key = request.args.get('key')
    name = request.args.get('name')

    if key != ADMIN_KEY:
        return "Wrong Password!", 403
    
    if name in LEADERBOARD_DATA:
        del LEADERBOARD_DATA[name]
        return f"Deleted player: {name}"
    else:
        return f"Player {name} not found."

# כדי לאפס את כל הטבלה:
# https://YOUR-URL/admin/reset?key=yonatan123
@app.route('/admin/reset', methods=['GET'])
def reset_leaderboard():
    key = request.args.get('key')
    
    if key != ADMIN_KEY:
        return "Wrong Password!", 403
        
    LEADERBOARD_DATA.clear()
    return "Leaderboard has been wiped clean."

# כדי לראות את כל הנתונים (כולל אלו שלא בטופ 10):
# https://YOUR-URL/admin/dump?key=yonatan123
@app.route('/admin/dump', methods=['GET'])
def dump_data():
    key = request.args.get('key')
    if key != ADMIN_KEY: return "Wrong Password!", 403
    return jsonify(LEADERBOARD_DATA)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
