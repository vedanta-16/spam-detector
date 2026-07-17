# spam-detector
A machine learning-based web application for detecting spam emails with real-time analysis, security tools, and interactive dashboard.
# 🛡️ SpamDetector

> Stop Spam. Stay Safe.

A full-stack email spam detection web application that combines keyword-based scoring with a machine learning model to classify emails as **SPAM**, **LIKELY SPAM**, or **NOT SPAM**.

---

## 📁 Project Structure

```
SpamDetector/
├── index.html          # Main frontend (UI, styles, JS logic)
├── script.js           # Frontend spam detection & API calls
├── style.css           # Standalone stylesheet (simple version)
├── app.py              # Flask backend — REST API & session handling
├── model.py            # ML model — TF-IDF + Naive Bayes
├── database.db         # SQLite database (auto-created on first run)
└── README.md
```

---

## ⚙️ Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Backend    | Python, Flask                       |
| ML Model   | scikit-learn (Naive Bayes + TF-IDF) |
| Database   | SQLite (sqlite3)                    |
| Charts     | Chart.js 4.4                        |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/spamdetector.git
cd spamdetector
```

### 2. Install Dependencies

```bash
pip install flask scikit-learn numpy
```

### 3. Run the Backend

```bash
python app.py
```

The Flask server will start at `http://localhost:5000`

### 4. Open the Frontend

Open `index.html` directly in your browser, or serve it with:

```bash
# Using Python's built-in server
python -m http.server 8080
```

Then visit `http://localhost:8080`

---

## 🔌 API Endpoints

| Method | Endpoint           | Description                        | Auth     |
|--------|--------------------|------------------------------------|----------|
| POST   | `/detect`          | Analyze email for spam             | No       |
| POST   | `/api/save-scan`   | Save scan result to database       | Session  |
| GET    | `/api/get-history` | Retrieve user's scan history       | Session  |
| POST   | `/api/login`       | Start a user session               | No       |
| POST   | `/api/logout`      | Clear user session                 | Session  |

### Example Request — `/detect`

```json
POST http://localhost:5000/detect
Content-Type: application/json

{
  "subject": "You WON a $1,000,000 prize! CLAIM NOW!!!",
  "body": "Click here to claim your free gift card..."
}
```

### Example Response

```json
{
  "result": "SPAM",
  "confidence": 94,
  "spam_score": 8,
  "triggered_keywords": ["won", "free", "claim", "prize", "click here"],
  "is_spam": true
}
```

---

## 🧠 How It Works

### 1. Client-Side Keyword Scoring
When you click **Analyze**, the frontend instantly scans the email against 40+ spam keywords (e.g. `free`, `urgent`, `winner`, `click here`). Bonus points are added for excessive exclamation marks and ALL-CAPS words.

| Spam Score | Verdict      |
|------------|--------------|
| 6+         | SPAM         |
| 3 – 5      | LIKELY SPAM  |
| 0 – 2      | NOT SPAM     |

### 2. Backend ML Model
The Flask backend uses a **TF-IDF Vectorizer** + **Multinomial Naive Bayes** classifier trained on labelled spam and ham samples. It returns a confidence percentage alongside the verdict.

### 3. Database Logging
Every scan is saved to a local SQLite database (`database.db`) linked to the user's session, enabling history tracking and CSV export.

---

## 📊 Features

- ✅ Real-time spam analysis with confidence score
- ✅ Triggered keyword highlighting
- ✅ Scan history with date/time logging
- ✅ CSV export of scan history
- ✅ Dashboard with Chart.js visualisations (line, doughnut, bar)
- ✅ Sample spam/ham email loader for testing
- ✅ User login/logout with session persistence
- ✅ Community report submission (frontend)
- ✅ Link and attachment scanner (frontend)
- ✅ Password strength checker

---

## 🗄️ Database Schema

```sql
CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT UNIQUE,
    password   TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scan_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER,
    email_preview  TEXT,
    result         TEXT,
    confidence     FLOAT,
    links_detected INTEGER DEFAULT 0,
    scanned_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🔐 Security Notes

> These apply if you plan to deploy this project publicly.

- Replace `hash(username)` in `app.py` with proper **bcrypt** password hashing
- Move `app.secret_key` to an **environment variable**
- Add **CORS headers** via `flask-cors` if hosting frontend and backend on different origins
- Use **HTTPS** in production

---

## 📈 Improving the ML Model

The default model trains on a small built-in dataset. To improve accuracy:

1. Download a larger dataset:
   - [UCI SMS Spam Collection](https://archive.ics.uci.edu/ml/datasets/sms+spam+collection)
   - [Enron Email Dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset)

2. Save the trained model to disk to avoid retraining on every server start:

```python
import joblib
joblib.dump(vectorizer, 'vectorizer.pkl')
joblib.dump(classifier, 'classifier.pkl')
```

3. Load it in `app.py`:

```python
import joblib
vectorizer  = joblib.load('vectorizer.pkl')
classifier  = joblib.load('classifier.pkl')
```

---

## 📦 Dependencies

```
flask
scikit-learn
numpy
```

Install all at once:

```bash
pip install flask scikit-learn numpy
```

---

## 📄 License

This project is for educational purposes. Feel free to use and modify it.
