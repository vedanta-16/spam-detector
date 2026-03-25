from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import re
import os

# ── import the ML model ──────────────────────────────────────
from model import predict_spam

# ── app setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)   # allows your index.html (port 5500) to call Flask (port 5000)

app.secret_key = 'spamdetector-secret-key-2025'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400   # session lasts 24 hours


# ============================================================
#  DATABASE SETUP
# ============================================================

def init_db():
    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE,
            password   TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            email_preview  TEXT,
            result         TEXT,
            confidence     FLOAT,
            spam_score     INTEGER DEFAULT 0,
            links_detected INTEGER DEFAULT 0,
            scanned_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database ready")


init_db()


# ============================================================
#  KEYWORD SCORING — mirrors your frontend detectSpam()
# ============================================================

SPAM_KEYWORDS = [
    'free','winner','won','prize','claim','urgent','click here',
    'limited time','act now','guaranteed','no cost','risk free',
    '100% free','earn money','make money','cash bonus',
    'congratulations','selected','offer expires','dear friend',
    'nigerian','inheritance','lottery','bitcoin','crypto',
    'investment opportunity','work from home','double your',
    'million dollars','bank account','wire transfer',
    'verify your account','suspended','confirm your',
    'click below','buy now','order now','special promotion',
    'exclusive deal','you have been chosen','unclaimed','reward',
    'giveaway','no credit card','instant approval','pre-approved'
]

def keyword_score(subject, body):
    text      = (subject + ' ' + body).lower()
    score     = 0
    triggered = []

    for kw in SPAM_KEYWORDS:
        if kw in text:
            score += 1
            triggered.append(kw)

    letters     = re.sub(r'[^a-zA-Z]', '', subject + body)
    upper_count = len(re.sub(r'[^A-Z]', '', subject))
    if letters and upper_count / max(len(letters), 1) > 0.25:
        score += 2
        triggered.append('excessive caps')

    excl = len(re.findall(r'!', text))
    if excl > 2:
        score += 1
        triggered.append(f'{excl} exclamation marks')

    urls = len(re.findall(r'http|www\.|bit\.ly|tinyurl', text))
    if urls > 1:
        score += 2
        triggered.append('multiple URLs')

    if re.search(r'\$[\d,]+|\d+\s*dollars?|[\d,]+\s*usd', text, re.IGNORECASE):
        score += 1
        triggered.append('money references')

    if   score >= 5: result, confidence = 'SPAM',        min(97, 60 + score * 3)
    elif score >= 3: result, confidence = 'SPAM',        min(85, 50 + score * 5)
    elif score >= 1: result, confidence = 'LIKELY SPAM', min(75, 40 + score * 8)
    else:            result, confidence = 'NOT SPAM',    92

    return score, triggered[:10], result, confidence


# ============================================================
#  MAIN ROUTE — POST /detect
#  Your frontend calls:  fetch('http://localhost:5000/detect', { method:'POST' })
#  It sends:  { subject: "...", body: "..." }
#  It expects back: { result, confidence, spam_score, triggered_keywords, is_spam }
# ============================================================

@app.route('/detect', methods=['POST'])
def detect():
    data    = request.get_json()
    subject = data.get('subject', '').strip()
    body    = data.get('body',    '').strip()

    if not subject and not body:
        return jsonify({'error': 'Please provide subject or body text'}), 400

    email_text = subject + ' ' + body

    # step 1 — keyword scoring
    spam_score, triggered_keywords, kw_result, kw_confidence = keyword_score(subject, body)

    # step 2 — ML model
    try:
        ml            = predict_spam(email_text)
        ml_label      = ml['label']        # 'SPAM' or 'NOT SPAM'
        ml_confidence = ml['confidence']   # 0.00 to 100.00
    except Exception as e:
        print(f"ML model error: {e}")
        ml_label      = kw_result
        ml_confidence = kw_confidence

    # step 3 — combine both signals
    if kw_result == 'SPAM' or ml_label == 'SPAM':
        final_result = 'SPAM'
    elif kw_result == 'LIKELY SPAM':
        final_result = 'LIKELY SPAM'
    else:
        final_result = 'NOT SPAM'

    final_confidence = round((kw_confidence + ml_confidence) / 2, 2)

    # step 4 — build response (exact keys your displayResult() reads)
    response_data = {
        'result':             final_result,
        'confidence':         final_confidence,
        'spam_score':         spam_score,
        'triggered_keywords': triggered_keywords,
        'is_spam':            final_result != 'NOT SPAM',
        'ml_label':           ml_label,
        'ml_confidence':      ml_confidence
    }

    # step 5 — auto-save to DB if user is logged in
    if 'user_id' in session:
        _save_to_db(session['user_id'], subject, body, response_data)

    return jsonify(response_data)


# ============================================================
#  DATABASE HELPER
# ============================================================

def _save_to_db(user_id, subject, body, result_data):
    preview = (subject + ' ' + body)[:100]
    conn    = sqlite3.connect('database.db')
    cursor  = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO scan_history
              (user_id, email_preview, result, confidence, spam_score, links_detected)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            preview,
            result_data['result'],
            result_data['confidence'],
            result_data['spam_score'],
            0
        ))
        conn.commit()
    except Exception as e:
        print(f"DB save error: {e}")
        conn.rollback()
    finally:
        conn.close()


# ============================================================
#  POST /api/save-scan
# ============================================================

@app.route('/api/save-scan', methods=['POST'])
def api_save_scan():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data   = request.get_json()
    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO scan_history
              (user_id, email_preview, result, confidence, links_detected)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data.get('email_preview', '')[:100],
            data.get('result', ''),
            data.get('confidence', 0),
            data.get('links_detected', 0)
        ))
        conn.commit()
        return jsonify({'success': True, 'scan_id': cursor.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ============================================================
#  GET /api/get-history
# ============================================================

@app.route('/api/get-history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email_preview, result, confidence, spam_score, links_detected, scanned_at
        FROM scan_history
        WHERE user_id = ?
        ORDER BY scanned_at DESC
        LIMIT 50
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({'history': [
        {
            'id':            r[0],
            'email_preview': r[1],
            'result':        r[2],
            'confidence':    r[3],
            'spam_score':    r[4],
            'links_detected':r[5],
            'scanned_at':    r[6]
        }
        for r in rows
    ]})


# ============================================================
#  POST /api/login
# ============================================================

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username', '').strip()

    if not username:
        return jsonify({'error': 'Username required'}), 400

    session['user_id']  = abs(hash(username)) % (10**9)
    session['username'] = username
    session.permanent   = True

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email_preview, result, confidence, scanned_at
        FROM scan_history WHERE user_id = ?
        ORDER BY scanned_at DESC LIMIT 50
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        'success':  True,
        'username': username,
        'history':  [
            {'id':r[0],'email_preview':r[1],'result':r[2],'confidence':r[3],'scanned_at':r[4]}
            for r in rows
        ]
    })


# ============================================================
#  POST /api/logout
# ============================================================

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


# ============================================================
#  GET /api/health — backend health check
# ============================================================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status':  'running',
        'message': 'SpamDetector backend is live',
        'port':    5000,
        'routes':  [
            'GET  /',
            'POST /detect',
            'POST /api/login',
            'POST /api/logout',
            'POST /api/save-scan',
            'GET  /api/get-history',
            'GET  /api/health'
        ]
    })

# ============================================================
#  GET /  — serve frontend
# ============================================================

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


# ============================================================
#  RUN
# ============================================================

if __name__ == '__main__':
    print("\nSpamDetector Backend Starting...")
    print("URL  :  http://localhost:5000")
    print("Test :  http://localhost:5000/")
    print("Stop :  CTRL + C\n")
    app.run(debug=True, port=5000)