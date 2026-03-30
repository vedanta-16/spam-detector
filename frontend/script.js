const API_URL = 'https://spam-detector-3-z7p0.onrender.com';
let history = [];

async function analyzeEmail() {
  const subject = document.getElementById('subject').value.trim();
  const body = document.getElementById('body').value.trim();

  if (!subject && !body) {
    alert('Please enter a subject or body to analyze.');
    return;
  }

  const btn = document.querySelector('.btn-analyze');
  btn.innerHTML = '<div class="spinner"></div> Analyzing...';
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const response = await fetch(`${API_URL}/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });

    if (!response.ok) throw new Error('Server error');

    const data = await response.json();
    displayResult(data, subject);
    addToHistory(subject || 'No subject', data);

  } catch (error) {
    alert('❌ Could not connect to server. Make sure the Flask backend is running on port 5000.');
    console.error(error);
  } finally {
    btn.innerHTML = '<span class="btn-icon">🔍</span> Analyze Email';
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

function displayResult(data, subject) {
  const resultCard = document.getElementById('resultCard');
  const resultHeader = document.getElementById('resultHeader');
  const resultIcon = document.getElementById('resultIcon');
  const resultTitle = document.getElementById('resultTitle');
  const resultSubtitle = document.getElementById('resultSubtitle');
  const confidenceFill = document.getElementById('confidenceFill');
  const confidenceValue = document.getElementById('confidenceValue');
  const spamScore = document.getElementById('spamScore');
  const verdictText = document.getElementById('verdictText');
  const keywordsSection = document.getElementById('keywordsSection');
  const keywordsList = document.getElementById('keywordsList');

  resultCard.style.display = 'block';
  resultCard.classList.add('fade-in');

  // Clear previous classes
  resultHeader.className = 'result-header';
  confidenceFill.className = 'confidence-fill';

  if (data.result === 'SPAM') {
    resultHeader.classList.add('spam-bg');
    resultIcon.textContent = '🚨';
    resultTitle.textContent = 'SPAM Detected!';
    resultTitle.style.color = '#ef4444';
    resultSubtitle.textContent = 'This email shows strong spam indicators.';
    confidenceFill.classList.add('spam-fill');
    verdictText.style.color = '#ef4444';
  } else if (data.result === 'LIKELY SPAM') {
    resultHeader.classList.add('warning-bg');
    resultIcon.textContent = '⚠️';
    resultTitle.textContent = 'Likely Spam';
    resultTitle.style.color = '#eab308';
    resultSubtitle.textContent = 'This email has some suspicious characteristics.';
    confidenceFill.classList.add('warn-fill');
    verdictText.style.color = '#eab308';
  } else {
    resultHeader.classList.add('safe-bg');
    resultIcon.textContent = '✅';
    resultTitle.textContent = 'Looks Safe!';
    resultTitle.style.color = '#22c55e';
    resultSubtitle.textContent = 'This email appears to be legitimate.';
    confidenceFill.classList.add('safe-fill');
    verdictText.style.color = '#22c55e';
  }

  // Confidence bar animation
  setTimeout(() => {
    confidenceFill.style.width = data.confidence + '%';
  }, 100);
  confidenceValue.textContent = data.confidence + '%';
  spamScore.textContent = data.spam_score;
  verdictText.textContent = data.result;

  // Keywords
  if (data.triggered_keywords && data.triggered_keywords.length > 0) {
    keywordsSection.style.display = 'block';
    keywordsList.innerHTML = data.triggered_keywords
      .map(kw => `<span class="keyword-tag">${kw}</span>`)
      .join('');
  } else {
    keywordsSection.style.display = 'none';
  }

  resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function addToHistory(subject, data) {
  history.unshift({ subject, result: data.result, confidence: data.confidence });
  if (history.length > 5) history.pop();

  const historyCard = document.getElementById('historyCard');
  const historyList = document.getElementById('historyList');

  historyCard.style.display = 'block';
  historyList.innerHTML = history.map(item => {
    let badgeClass = 'badge-safe';
    if (item.result === 'SPAM') badgeClass = 'badge-spam';
    else if (item.result === 'LIKELY SPAM') badgeClass = 'badge-warn';
    return `
      <div class="history-item">
        <span class="history-subject">${item.subject}</span>
        <span class="history-badge ${badgeClass}">${item.result}</span>
      </div>
    `;
  }).join('');
}

function loadSample(type) {
  if (type === 'spam') {
    document.getElementById('subject').value = 'CONGRATULATIONS!!! You WON $1,000,000 - CLAIM NOW!!!';
    document.getElementById('body').value = `Dear Friend,

You have been SELECTED as our lucky winner! Click here NOW to claim your FREE prize money of $1,000,000 dollars!!!

This is a LIMITED TIME offer - ACT NOW before it expires!

To claim your guaranteed prize, simply wire transfer your bank account details to us immediately. This is 100% FREE and risk free!

Click below to verify your account and CLAIM YOUR CASH now!

www.claim-your-prize-now.com/winner

Don't miss this exclusive deal! Order now!

Congratulations once again!!!!!!`;
  } else {
    document.getElementById('subject').value = 'Team meeting rescheduled to Friday 3pm';
    document.getElementById('body').value = `Hi everyone,

Just a quick note to let you know the weekly team sync has been moved from Thursday to Friday at 3:00 PM.

Please update your calendars. The meeting link remains the same as before. We'll be covering Q3 project updates and the new onboarding process.

Let me know if you have any conflicts.

Best regards,
Sarah Johnson
Project Manager`;
  }
}

function clearForm() {
  document.getElementById('subject').value = '';
  document.getElementById('body').value = '';
  document.getElementById('resultCard').style.display = 'none';
}

// Allow Enter key in subject to focus body
document.getElementById('subject').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    document.getElementById('body').focus();
  }
});