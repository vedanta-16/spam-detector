# ============================================================
#  model.py  —  SpamDetector ML Model
#  Uses:  scikit-learn TF-IDF + Multinomial Naive Bayes
#  This file is imported by app.py  →  from model import predict_spam
# ============================================================

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np


# ============================================================
#  TRAINING DATA
#  label 1 = spam,  label 0 = ham (legitimate)
# ============================================================

SPAM_SAMPLES = [
    "Congratulations! You won a $1000 gift card. Click here now!",
    "FREE iPhone! Limited offer, claim your prize today!",
    "You have been selected for a lottery. Send your bank details.",
    "Buy cheap meds online. No prescription needed!",
    "Earn $5000 a week working from home. No experience needed!",
    "URGENT: Your account will be suspended. Verify now!",
    "Hot singles in your area! Click to meet them now.",
    "100% FREE. No credit card needed. Sign up today!",
    "Winner! You have been chosen. Claim your reward now.",
    "Make money fast. Wire transfer your details immediately.",
    "Exclusive deal! Act now before offer expires. Order now!",
    "Dear friend, I have a million dollars inheritance for you.",
]

HAM_SAMPLES = [
    "Hey, can we reschedule our meeting to 3pm tomorrow?",
    "Please find the attached quarterly report for your review.",
    "Thanks for your help with the project last week.",
    "Reminder: Team standup is at 10am in conference room B.",
    "Could you review my pull request when you have time?",
    "I wanted to follow up on our conversation from yesterday.",
    "The client meeting went well, they approved the proposal.",
    "Can you send me the login credentials for the staging server?",
    "Hi, just checking in on the project status. Let me know.",
    "Please confirm your attendance for the annual conference.",
    "Your invoice has been processed and payment is on its way.",
    "Thank you for your application. We will be in touch shortly.",
]


# ============================================================
#  TRAIN THE MODEL (runs once when app.py imports this file)
# ============================================================

labels = [1] * len(SPAM_SAMPLES) + [0] * len(HAM_SAMPLES)
data   = SPAM_SAMPLES + HAM_SAMPLES

vectorizer = TfidfVectorizer(stop_words='english')
X          = vectorizer.fit_transform(data)

classifier = MultinomialNB()
classifier.fit(X, labels)

print("ML model trained and ready")


# ============================================================
#  PREDICT FUNCTION — called by app.py detect() route
#  Returns:  { is_spam: bool, label: str, confidence: float }
# ============================================================

def predict_spam(email_text):
    """
    Takes email text (subject + body combined),
    returns a dict with:
      - is_spam     : True or False
      - label       : 'SPAM' or 'NOT SPAM'
      - confidence  : float between 0 and 100
    """
    X_input     = vectorizer.transform([email_text])
    prediction  = classifier.predict(X_input)[0]
    probability = classifier.predict_proba(X_input)[0]
    confidence  = round(float(np.max(probability)) * 100, 2)

    return {
        "is_spam":    bool(prediction),
        "label":      "SPAM" if prediction == 1 else "NOT SPAM",
        "confidence": confidence
    }