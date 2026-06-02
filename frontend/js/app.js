// ========== STORAGE KEYS ==========
const USERS_KEY = 'pickmyseat_users';
const CURRENT_USER_KEY = 'pickmyseat_current_user';
const PREDICTIONS_KEY = 'pickmyseat_predictions';
const GUEST_PREDICTIONS_KEY = 'pickmyseat_guest_count';
const GUEST_HISTORY_KEY = 'pickmyseat_guest_history';
const RANK_DATA_KEY = 'pickmyseat_rank_data';

// ========== USER TYPES ==========
const USER_TYPES = {
  GUEST: 3,
  EXPLORER: 2,
  PREMIUM: 1
};

// ========== HELPER FUNCTIONS ==========
function getUsers() { return JSON.parse(localStorage.getItem(USERS_KEY) || '[]'); }
function saveUsers(u) { localStorage.setItem(USERS_KEY, JSON.stringify(u)); }
function getCurrentUser() { return JSON.parse(localStorage.getItem(CURRENT_USER_KEY) || 'null'); }
function setCurrentUser(u) { localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(u)); }
function clearCurrentUser() { localStorage.removeItem(CURRENT_USER_KEY); }
function getPredictions() { return JSON.parse(localStorage.getItem(PREDICTIONS_KEY) || '[]'); }
function savePredictions(p) { localStorage.setItem(PREDICTIONS_KEY, JSON.stringify(p)); }
function getRankData() { return JSON.parse(localStorage.getItem(RANK_DATA_KEY) || '[]'); }
function saveRankData(d) { localStorage.setItem(RANK_DATA_KEY, JSON.stringify(d)); }
function generateId() { return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9); }

function showAlert(msg, type = 'error') {
  const c = document.getElementById('alert-container');
  if (!c) { alert(msg); return; }
  const cls = type === 'error' ? 'alert-error' : type === 'success' ? 'alert-success' : type === 'warning' ? 'alert-warning' : 'alert-info';
  c.innerHTML = `<div class="alert ${cls}">${msg}</div>`;
  setTimeout(() => { c.innerHTML = ''; }, 5000);
}

function checkAuth() {
  const u = getCurrentUser();
  if (!u) { window.location.href = 'login.html'; return null; }
  return u;
}

function updateUserData(updates) {
  const u = getCurrentUser();
  const updated = { ...u, ...updates };
  setCurrentUser(updated);
  const users = getUsers();
  const i = users.findIndex(x => x.id === u.id);
  if (i !== -1) { users[i] = { ...users[i], ...updates }; saveUsers(users); }
  return updated;
}

function setupLogout() {
  const btn = document.getElementById('logout-btn');
  if (btn) btn.addEventListener('click', () => { clearCurrentUser(); window.location.href = 'login.html'; });
}

// ========== GUEST PREDICTION TRACKING ==========
function getGuestPredictionCount() {
  const data = localStorage.getItem(GUEST_PREDICTIONS_KEY);
  if (!data) return 0;
  const parsed = JSON.parse(data);
  if (Date.now() - parsed.timestamp > 24 * 60 * 60 * 1000) {
    localStorage.removeItem(GUEST_PREDICTIONS_KEY);
    return 0;
  }
  return parsed.count;
}

function incrementGuestPrediction() {
  const count = getGuestPredictionCount();
  localStorage.setItem(GUEST_PREDICTIONS_KEY, JSON.stringify({
    count: count + 1,
    timestamp: Date.now()
  }));
  return count + 1;
}

function clearGuestData() {
  localStorage.removeItem(GUEST_PREDICTIONS_KEY);
  localStorage.removeItem(GUEST_HISTORY_KEY);
  showToast('Guest data cleared! You can make 2 more predictions.', 'success');
  setTimeout(() => location.reload(), 1000);
}

window.clearGuestData = clearGuestData;

// ========== GUEST HISTORY ==========
function getGuestHistory() {
  const history = localStorage.getItem(GUEST_HISTORY_KEY);
  return history ? JSON.parse(history) : [];
}

function saveGuestHistory(prediction) {
  const history = getGuestHistory();
  history.push({
    ...prediction,
    timestamp: new Date().toISOString()
  });
  if (history.length > 2) history.shift();
  localStorage.setItem(GUEST_HISTORY_KEY, JSON.stringify(history));
}

function clearGuestHistory() {
  localStorage.removeItem(GUEST_HISTORY_KEY);
  const historyContainer = document.getElementById('guest-history');
  if (historyContainer) historyContainer.classList.add('hidden');
  showToast('Prediction history cleared!', 'success');
}

window.clearGuestHistory = clearGuestHistory;

function displayGuestHistory() {
  const history = getGuestHistory();
  const container = document.getElementById('guest-history');
  const listContainer = document.getElementById('guest-history-list');
  
  if (!container || !listContainer) return;
  
  if (history.length === 0) {
    container.classList.add('hidden');
    return;
  }
  
  container.classList.remove('hidden');
  
  listContainer.innerHTML = history.map((pred, index) => `
    <div class="card mb-3" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);">
      <div class="card-body">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm text-secondary">Prediction ${index + 1}</p>
            <p class="font-bold text-lg">${pred.collegeName}</p>
            <p class="font-bold">${pred.course}</p>
            <p class="text-sm">Marks: ${pred.marks} / 200</p>
          </div>
          <div class="text-right">
            <div class="text-3xl font-bold text-primary">${pred.probability}%</div>
            <p class="text-sm text-secondary">${pred.label}</p>
          </div>
        </div>
        <div class="mt-2 text-xs text-secondary">
          ${new Date(pred.timestamp).toLocaleString('en-IN')}
        </div>
      </div>
    </div>
  `).join('');
}

// ========== PROBABILITY CALCULATOR (Updated for 200 marks) ==========
function calculateProbability(marks, cutoff) {
  const ratio = marks / cutoff;
  if (ratio >= 1.15) return { value: 95, label: 'Very High' };
  if (ratio >= 1.08) return { value: 85, label: 'High' };
  if (ratio >= 1.0) return { value: 70, label: 'Good' };
  if (ratio >= 0.92) return { value: 50, label: 'Medium' };
  if (ratio >= 0.85) return { value: 30, label: 'Low' };
  return { value: 10, label: 'Very Low' };
}

// ========== MOCK CUTOFF DATA (Updated for 200 marks scale) ==========
const COLLEGE_CUTOFFS = {
  'CEG_CSE': 198, 'CEG_IT': 196, 'CEG_ECE': 194, 'CEG_EEE': 192, 'CEG_MECH': 190, 'CEG_CIVIL': 188,
  'CEG_AI&DS': 197, 'CEG_AIML': 197.5,
  'MIT_CSE': 196, 'MIT_IT': 194, 'MIT_ECE': 192, 'MIT_EEE': 190, 'MIT_MECH': 188, 'MIT_CIVIL': 186,
  'MIT_AI&DS': 195, 'MIT_AIML': 195.5,
  'ACT_CSE': 194, 'ACT_IT': 192, 'ACT_ECE': 190, 'ACT_EEE': 188, 'ACT_MECH': 186, 'ACT_CIVIL': 184,
  'ACT_AI&DS': 193, 'ACT_AIML': 193.5,
  'PSG_CSE': 192, 'PSG_IT': 190, 'PSG_ECE': 188, 'PSG_EEE': 186, 'PSG_MECH': 184, 'PSG_CIVIL': 182,
  'PSG_AI&DS': 191, 'PSG_AIML': 191.5,
  'TCE_CSE': 190, 'TCE_IT': 188, 'TCE_ECE': 186, 'TCE_EEE': 184, 'TCE_MECH': 182, 'TCE_CIVIL': 180,
  'TCE_AI&DS': 189, 'TCE_AIML': 189.5,
  'SSN_CSE': 188, 'SSN_IT': 186, 'SSN_ECE': 184, 'SSN_EEE': 182, 'SSN_MECH': 180, 'SSN_CIVIL': 178,
  'SSN_AI&DS': 187, 'SSN_AIML': 187.5,
  'REC_CSE': 186, 'REC_IT': 184, 'REC_ECE': 182, 'REC_EEE': 180, 'REC_MECH': 178, 'REC_CIVIL': 176,
  'REC_AI&DS': 185, 'REC_AIML': 185.5
};

function getCutoff(college, course) {
  const key = `${college}_${course}`;
  return COLLEGE_CUTOFFS[key] || 150;
}

// ========== RANK PREDICTOR (Updated for 200 marks) ==========
function predictRank(totalMarks, category = 'OC') {
  let multiplier = 500;
  const categoryMultipliers = { 'OC': 500, 'BC': 430, 'BCM': 430, 'MBC': 400, 'SC': 370, 'ST': 330 };
  multiplier = categoryMultipliers[category] || 500;
  
  const baseRank = Math.floor((200 - totalMarks) * multiplier);
  const variance = Math.floor(baseRank * 0.08);
  
  return {
    rank_low: Math.max(1, baseRank - variance),
    rank_high: baseRank + variance,
    predicted: baseRank
  };
}

// ========== AGGREGATE CALCULATOR (Corrected) ==========
function calculateAggregate(maths, physics, chemistry) {
  // Corrected formula: Math + (Physics/2) + (Chemistry/2)
  return maths + (physics / 2) + (chemistry / 2);
}

// ========== TOAST NOTIFICATIONS ==========
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <p class="font-bold">${message}</p>
  `;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// ========== COUNTDOWN TIMER ==========
function startCountdown(hoursId, minutesId, secondsId, totalHours = 48) {
  const endTime = Date.now() + (totalHours * 60 * 60 * 1000);
  
  function update() {
    const now = Date.now();
    const remaining = Math.max(0, endTime - now);
    
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
    
    const hEl = document.getElementById(hoursId);
    const mEl = document.getElementById(minutesId);
    const sEl = document.getElementById(secondsId);
    
    if (hEl) hEl.textContent = String(hours).padStart(2, '0');
    if (mEl) mEl.textContent = String(minutes).padStart(2, '0');
    if (sEl) sEl.textContent = String(seconds).padStart(2, '0');
    
    if (remaining > 0) {
      setTimeout(update, 1000);
    }
  }
  
  update();
}

// ========== PAGE ROUTER ==========
document.addEventListener('DOMContentLoaded', function() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  console.log('PAGE:', page);
  setupLogout();

  // Start countdowns
  startCountdown('hours', 'minutes', 'seconds', 48);
  startCountdown('pay-hours', 'pay-minutes', 'pay-seconds', 48);

  if (page === 'index.html') initIndex();
  else if (page === 'signup.html') initSignup();
  else if (page === 'login.html') initLogin();
  else if (page === 'dashboard-grade1.html') initDashboardGrade1();
  else if (page === 'dashboard-grade2.html') initDashboardGrade2();
  else if (page === 'profile.html') initProfile();
  else if (page === 'payment.html') initPayment();
  else if (page === 'predict.html') initPredict();
  else if (page === 'counselling-simulator.html') initCounselling();
  else if (page === 'choice-builder.html') initChoiceBuilder();
});

// ========== INDEX PAGE (Guest Predictor) ==========
function initIndex() {
  const slider = document.getElementById('guest-marks-slider');
  const display = document.getElementById('guest-marks-display');
  const predictBtn = document.getElementById('guest-predict-btn');
  const result = document.getElementById('guest-result');
  const courseSelect = document.getElementById('guest-course');
  const collegeSelect = document.getElementById('guest-college');
  const counterEl = document.getElementById('guest-prediction-counter');
  const remainingEl = document.getElementById('guest-remaining-count');

  if (!slider) return;

  if (counterEl) counterEl.classList.remove('hidden');

  const updateRemainingCount = () => {
    const count = getGuestPredictionCount();
    const remaining = 2 - count;
    if (remainingEl) remainingEl.textContent = remaining;
    
    const predRemainingSpan = document.getElementById('predictions-remaining');
    if (predRemainingSpan) {
      predRemainingSpan.textContent = `${remaining}/2`;
      if (remaining === 0) {
        predRemainingSpan.classList.remove('text-primary');
        predRemainingSpan.classList.add('text-danger');
      }
    }
  };

  updateRemainingCount();
  displayGuestHistory();

  slider.addEventListener('input', () => {
    display.textContent = `${slider.value} / 200`;
  });

  predictBtn.addEventListener('click', () => {
    const count = getGuestPredictionCount();
    if (count >= 2) {
      showUpgradeModal();
      return;
    }

    const marks = parseInt(slider.value);
    const course = courseSelect.value;
    const college = collegeSelect.value;

    if (!course || !college) {
      showToast('⚠️ Please select both course and college', 'warning');
      return;
    }

    const cutoff = getCutoff(college, course);
    const prob = calculateProbability(marks, cutoff);

    saveGuestHistory({
      marks,
      course,
      college,
      collegeName: collegeSelect.options[collegeSelect.selectedIndex].text,
      cutoff,
      probability: prob.value,
      label: prob.label
    });

    result.classList.remove('hidden');
    const indicator = document.getElementById('guest-prob-indicator');
    const label = document.getElementById('guest-prob-label');
    const text = document.getElementById('guest-prob-text');

    indicator.style.left = `${prob.value}%`;
    label.textContent = `${prob.value}%`;
    label.style.left = `${prob.value}%`;

    const newCount = incrementGuestPrediction();
    const remaining = 2 - newCount;

    text.innerHTML = `
      <div class="mb-4">
        <div class="text-3xl font-bold mb-2">${prob.value}% Probability</div>
        <div class="text-xl">${prob.label} Chance</div>
      </div>
      <div class="p-4" style="background: rgba(255,255,255,0.2); border-radius: 0.5rem;">
        <p class="mb-2">Getting <strong>${course}</strong> at</p>
        <p class="text-lg font-bold">${collegeSelect.options[collegeSelect.selectedIndex].text}</p>
      </div>
      <div class="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div><strong>Cutoff:</strong> ${cutoff}/200</div>
        <div><strong>Your Marks:</strong> ${marks}/200</div>
        <div><strong>Difference:</strong> ${marks - cutoff > 0 ? '+' : ''}${(marks - cutoff).toFixed(1)}</div>
        <div><strong>Predictions Left:</strong> ${remaining}/2</div>
      </div>
      ${remaining === 0 ? `
        <div class="mt-4 p-3" style="background: rgba(239, 68, 68, 0.2); border-radius: 0.5rem;">
          <p class="font-bold text-sm">⚠️ You've used all free predictions!</p>
        </div>
      ` : ''}
    `;

    updateRemainingCount();
    displayGuestHistory();
    result.scrollIntoView({ behavior: 'smooth', block: 'center' });

    if (remaining === 0) {
      setTimeout(() => {
        showUpgradeModal();
      }, 3000);
    }
  });
}

// ========== UPGRADE MODAL ==========
function showUpgradeModal() {
  const modal = document.createElement('div');
  modal.className = 'modal active';
  modal.innerHTML = `
    <div class="modal-content" style="max-width: 700px;">
      <div class="modal-header">
        <h3 class="modal-title">🎉 Unlock Premium Features</h3>
        <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
      </div>
      <div class="modal-body">
        <div class="social-proof mb-4">
          <p class="font-bold mb-2">⚠️ Students with Premium made 3x better college choices</p>
          <p class="text-sm">Without Choice Builder, you might miss your dream college</p>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="card">
            <div class="card-body text-center">
              <div class="text-2xl mb-2">📊</div>
              <h4 class="font-bold mb-2">Explorer</h4>
              <div class="text-2xl font-bold text-primary mb-2">FREE</div>
              <ul class="text-sm text-left space-y-1 mb-4">
                <li>✓ 3 Courses + 5 Colleges</li>
                <li>✓ 15 Combinations</li>
                <li>✓ Save Your Data</li>
                <li>✓ Unlimited Predictions</li>
              </ul>
              <a href="signup.html?type=2" class="btn btn-primary btn-block">Sign Up Free</a>
            </div>
          </div>
          
          <div class="card" style="border: 3px solid var(--success-color);">
            <div class="card-body text-center">
              <div class="badge badge-success mb-2">BEST VALUE</div>
              <div class="text-2xl mb-2">🏆</div>
              <h4 class="font-bold mb-2">Premium</h4>
              <div class="mb-2">
                <span class="text-3xl font-bold text-success">₹149</span>
                <span class="text-secondary" style="text-decoration: line-through;">₹500</span>
              </div>
              <p class="text-sm text-success font-bold mb-3">Save ₹351 (70% OFF)</p>
              <ul class="text-sm text-left space-y-1 mb-4">
                <li>✓ Everything in Explorer</li>
                <li>✓ Rank Prediction (95%)</li>
                <li>✓ AI Choice Builder</li>
                <li>✓ Counselling Simulation</li>
              </ul>
              <a href="signup.html?type=1" class="btn btn-success btn-block">Get Premium</a>
            </div>
          </div>
        </div>
        
        <p class="text-center text-sm text-secondary">
          Or <a href="#" onclick="clearGuestData(); this.closest('.modal').remove(); return false;" class="text-primary font-bold">reset predictions</a> to continue with limited access
        </p>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

window.showUpgradeModal = showUpgradeModal;

// ========== SIGNUP ==========
let selectedType = 2;

function selectUserType(type) {
  selectedType = type;
  document.querySelectorAll('.user-type-card').forEach(card => {
    card.classList.remove('selected');
  });
  const selectedCard = document.querySelector(`.user-type-card[data-type="${type}"]`);
  if (selectedCard) selectedCard.classList.add('selected');
  
  setTimeout(() => {
    const typeSelection = document.getElementById('type-selection');
    const registrationForm = document.getElementById('registration-form');
    if (typeSelection) typeSelection.classList.add('hidden');
    if (registrationForm) registrationForm.classList.remove('hidden');
    
    const userTypeInput = document.getElementById('user-type');
    if (userTypeInput) userTypeInput.value = type;
    
    const planText = document.getElementById('selected-plan-text');
    if (planText) {
      if (type === 1) {
        planText.textContent = 'Continue to Payment (₹149)';
      } else {
        planText.textContent = 'Create Free Account';
      }
    }
  }, 300);
}

function showTypeSelection() {
  const typeSelection = document.getElementById('type-selection');
  const registrationForm = document.getElementById('registration-form');
  if (typeSelection) typeSelection.classList.remove('hidden');
  if (registrationForm) registrationForm.classList.add('hidden');
}

window.selectUserType = selectUserType;
window.showTypeSelection = showTypeSelection;

function initSignup() {
  const urlParams = new URLSearchParams(window.location.search);
  const typeParam = urlParams.get('type');
  if (typeParam) {
    selectUserType(parseInt(typeParam));
  }

  const form = document.getElementById('signup-form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const category = document.getElementById('category').value;
    const pw = document.getElementById('password').value;
    const cpw = document.getElementById('confirm-password').value;
    const userType = parseInt(document.getElementById('user-type').value);

    if (pw !== cpw) { showAlert('Passwords do not match'); return; }
    if (pw.length < 6) { showAlert('Password must be at least 6 characters'); return; }

    const users = getUsers();
    if (users.find(u => u.email === email)) { 
      showAlert('Email already registered. Please login.'); 
      return; 
    }

    const newUser = {
      id: generateId(),
      name, email, phone, category,
      password: pw,
      user_type: userType,
      has_paid: false,
      marks_locked: false,
      marks_revision_count: 0,
      preferred_courses: [],
      preferred_colleges: [],
      created_at: new Date().toISOString()
    };

    users.push(newUser);
    saveUsers(users);

    const { password, ...safe } = newUser;
    setCurrentUser(safe);

    showAlert('Account created successfully!', 'success');
    
    setTimeout(() => {
      if (userType === USER_TYPES.PREMIUM) {
        window.location.href = 'payment.html';
      } else {
        window.location.href = 'profile.html';
      }
    }, 800);
  });
}

// ========== LOGIN ==========
function initLogin() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const pw = document.getElementById('password').value;

    const users = getUsers();
    const user = users.find(u => u.email === email && u.password === pw);

    if (user) {
      const { password, ...safe } = user;
      setCurrentUser(safe);
      showAlert('Login successful!', 'success');
      
      setTimeout(() => {
        if (user.user_type === USER_TYPES.PREMIUM && !user.has_paid) {
          window.location.href = 'payment.html';
        } else if (user.user_type === USER_TYPES.PREMIUM) {
          window.location.href = 'dashboard-grade1.html';
        } else {
          window.location.href = 'dashboard-grade2.html';
        }
      }, 800);
    } else {
      showAlert('Invalid email or password');
    }
  });
}

// ========== DASHBOARD GRADE 1 ==========
function initDashboardGrade1() {
  const user = checkAuth();
  if (!user) return;

  if (user.user_type !== USER_TYPES.PREMIUM) {
    window.location.href = 'dashboard-grade2.html';
    return;
  }

  if (!user.has_paid) {
    window.location.href = 'payment.html';
    return;
  }

  const emailEl = document.getElementById('user-email');
  if (emailEl) emailEl.textContent = user.name || user.email;

  const marksLockedEl = document.getElementById('marks-locked-status');
  if (marksLockedEl) {
    if (user.marks_locked) {
      marksLockedEl.innerHTML = '<span class="badge badge-success">✓ Confirmed</span>';
    } else {
      marksLockedEl.innerHTML = '<span class="badge badge-warning">⚠ Not Confirmed</span>';
    }
  }

  const revisionCountEl = document.getElementById('revision-count');
  if (revisionCountEl) {
    revisionCountEl.textContent = user.marks_revision_count || 0;
  }

  const preds = getPredictions().filter(p => p.user_id === user.id);
  const totalEl = document.getElementById('total-predictions');
  if (totalEl) totalEl.textContent = preds.length;

  const container = document.getElementById('predictions-container');
  if (container) {
    if (preds.length === 0) {
      container.innerHTML = `
        <div class="card empty-state">
          <div class="empty-state-icon">🎓</div>
          <div class="empty-state-title">No predictions yet</div>
          <div class="empty-state-description">Start by entering your marks</div>
          <button class="btn btn-primary" onclick="window.location.href='predict.html'">
            Enter Marks
          </button>
        </div>`;
    } else {
      const latest = preds[preds.length - 1];
      container.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h3 class="text-lg font-bold mb-4">Latest Prediction</h3>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <p class="text-sm text-secondary">Total Marks</p>
                <p class="text-2xl font-bold">${latest.total}/200</p>
              </div>
              <div>
                <p class="text-sm text-secondary">Predicted Rank</p>
                <p class="text-2xl font-bold text-primary">${latest.rank_low?.toLocaleString()} - ${latest.rank_high?.toLocaleString()}</p>
              </div>
              <div>
                <p class="text-sm text-secondary">Aggregate</p>
                <p class="text-2xl font-bold text-success">${latest.aggregate?.toFixed(2) || 'N/A'}</p>
              </div>
            </div>
            <div class="flex gap-4 mt-6">
              <button class="btn btn-success" onclick="window.location.href='choice-builder.html'">
                🎯 Build Choice List
              </button>
              <button class="btn btn-outline" onclick="window.location.href='counselling-simulator.html'">
                ⚡ Run Simulation
              </button>
            </div>
          </div>
        </div>`;
    }
  }

  // Show tip after 3 seconds
  setTimeout(() => {
    if (preds.length > 0 && !localStorage.getItem('tip_shown')) {
      showToast('💡 Try the Choice Builder to maximize your chances!', 'info');
      localStorage.setItem('tip_shown', 'true');
    }
  }, 3000);
}

// ========== DASHBOARD GRADE 2 ==========
function initDashboardGrade2() {
  const user = checkAuth();
  if (!user) return;

  if (user.user_type === USER_TYPES.PREMIUM) {
    window.location.href = 'dashboard-grade1.html';
    return;
  }

  const emailEl = document.getElementById('user-email');
  if (emailEl) emailEl.textContent = user.name || user.email;

  const coursesEl = document.getElementById('preferred-courses');
  const collegesEl = document.getElementById('preferred-colleges');

  if (coursesEl) {
    coursesEl.textContent = (user.preferred_courses?.length || 0) + ' / 3';
  }
  if (collegesEl) {
    collegesEl.textContent = (user.preferred_colleges?.length || 0) + ' / 5';
  }

  loadPreferenceMatrix();
}

function loadPreferenceMatrix() {
  const user = getCurrentUser();
  const container = document.getElementById('preference-matrix');
  if (!container) return;

  const courses = user.preferred_courses || [];
  const colleges = user.preferred_colleges || [];

  if (courses.length === 0 || colleges.length === 0) {
    container.innerHTML = `
      <div class="card empty-state">
        <div class="empty-state-icon">🎯</div>
        <div class="empty-state-title">Set Your Preferences</div>
        <div class="empty-state-description">Choose courses and colleges</div>
        <button class="btn btn-primary" onclick="window.location.href='profile.html'">
          Set Preferences
        </button>
      </div>`;
    return;
  }

  let html = '<div class="preference-matrix">';
  let totalCombos = 0;
  courses.forEach(course => {
    colleges.forEach(college => {
      const cutoff = getCutoff(college.code, course.code);
      const marks = user.total_marks || 0;
      const prob = calculateProbability(marks, cutoff);
      
      html += `
        <div class="preference-cell ${prob.value > 60 ? 'selected' : ''}">
          <div style="font-weight: 700; font-size: 0.625rem;">${college.short}</div>
          <div style="font-size: 0.5rem; opacity: 0.8;">${course.short}</div>
          <div style="font-weight: 700; margin-top: 0.25rem;">${prob.value}%</div>
        </div>`;
      totalCombos++;
    });
  });
  html += '</div>';
  html += `<p class="text-center mt-4 text-sm text-secondary">${totalCombos} combinations available</p>`;
  container.innerHTML = html;
}

window.loadPreferenceMatrix = loadPreferenceMatrix;

// ========== PROFILE ==========
function initProfile() {
  const user = checkAuth();
  if (!user) return;

  const view = document.getElementById('profile-view');
  const edit = document.getElementById('profile-edit');
  const preferenceSection = document.getElementById('preference-section');

  if (preferenceSection && user.user_type === USER_TYPES.EXPLORER) {
    preferenceSection.classList.remove('hidden');
    loadPreferenceForm();
  }

  const isComplete = user.name && user.phone && user.category;

  function showView() {
    if (view) view.classList.remove('hidden');
    if (edit) edit.classList.add('hidden');
    loadViewData();
  }

  function showEdit() {
    if (view) view.classList.add('hidden');
    if (edit) edit.classList.remove('hidden');
    loadFormData();
  }

  function loadViewData() {
    const data = document.getElementById('profile-data');
    if (!data) return;
    
    const userTypeLabel = user.user_type === USER_TYPES.PREMIUM ? 'Premium' : 'Explorer';
    
    const fields = [
      { l: 'Email', v: user.email },
      { l: 'Name', v: user.name },
      { l: 'Phone', v: user.phone },
      { l: 'Category', v: user.category },
      { l: 'Account Type', v: `<span class="badge ${user.user_type === 1 ? 'badge-success' : 'badge-secondary'}">${userTypeLabel}</span>` },
      { l: 'Payment Status', v: user.has_paid ? '<span class="badge badge-success">Paid ✓</span>' : '<span class="badge badge-warning">Not Paid</span>' }
    ];
    
    data.innerHTML = fields.filter(f => f.v).map(f =>
      `<div style="border-bottom:1px solid var(--border-color);padding-bottom:0.75rem;">
        <p class="text-sm text-secondary">${f.l}</p>
        <p class="text-lg font-bold mt-1">${f.v}</p>
      </div>`).join('');
  }

  function loadFormData() {
    const set = (id, v) => { const e = document.getElementById(id); if (e) e.value = v || ''; };
    set('name', user.name);
    set('phone', user.phone);
    set('category', user.category);
  }

  if (isComplete) showView(); else showEdit();

  const editBtn = document.getElementById('edit-profile-btn');
  if (editBtn) editBtn.addEventListener('click', showEdit);

  const cancelBtn = document.getElementById('cancel-edit-btn');
  if (cancelBtn) cancelBtn.addEventListener('click', () => {
    if (isComplete) showView(); 
    else window.location.href = user.user_type === 1 ? 'dashboard-grade1.html' : 'dashboard-grade2.html';
  });

  const form = document.getElementById('profile-form');
  if (form) form.addEventListener('submit', function(e) {
    e.preventDefault();
    const get = id => { const el = document.getElementById(id); return el ? el.value.trim() : ''; };
    updateUserData({
      name: get('name'),
      phone: get('phone'),
      category: get('category')
    });
    showAlert('Profile saved successfully!', 'success');
    setTimeout(() => location.reload(), 1000);
  });
}

function loadPreferenceForm() {
  const user = getCurrentUser();
  
  const coursesContainer = document.getElementById('courses-checkboxes');
  if (coursesContainer) {
    const allCourses = [
      { code: 'CSE', name: 'Computer Science Engineering', short: 'CSE' },
      { code: 'IT', name: 'Information Technology', short: 'IT' },
      { code: 'ECE', name: 'Electronics & Communication', short: 'ECE' },
      { code: 'EEE', name: 'Electrical & Electronics', short: 'EEE' },
      { code: 'MECH', name: 'Mechanical Engineering', short: 'MECH' },
      { code: 'CIVIL', name: 'Civil Engineering', short: 'CIVIL' },
      { code: 'AI&DS', name: 'AI & Data Science', short: 'AI&DS' },
      { code: 'AIML', name: 'AI & Machine Learning', short: 'AIML' }
    ];

    const selected = user.preferred_courses || [];
    coursesContainer.innerHTML = allCourses.map(c => `
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" class="course-checkbox" value='${JSON.stringify(c)}' 
          ${selected.find(s => s.code === c.code) ? 'checked' : ''}>
        <span>${c.name}</span>
      </label>
    `).join('');

    document.querySelectorAll('.course-checkbox').forEach(cb => {
      cb.addEventListener('change', () => {
        const checked = document.querySelectorAll('.course-checkbox:checked');
        if (checked.length > 3) {
          cb.checked = false;
          showToast('Maximum 3 courses allowed', 'warning');
        }
      });
    });
  }

  const collegesContainer = document.getElementById('colleges-checkboxes');
  if (collegesContainer) {
    const allColleges = [
      { code: 'CEG', name: 'College of Engineering, Guindy', short: 'CEG' },
      { code: 'MIT', name: 'MIT Campus, Anna University', short: 'MIT' },
      { code: 'ACT', name: 'Alagappa College of Technology', short: 'ACT' },
      { code: 'PSG', name: 'PSG College of Technology', short: 'PSG' },
      { code: 'TCE', name: 'Thiagarajar College of Engineering', short: 'TCE' },
      { code: 'SSN', name: 'SSN College of Engineering', short: 'SSN' },
      { code: 'REC', name: 'Regional Engineering College', short: 'REC' }
    ];

    const selected = user.preferred_colleges || [];
    collegesContainer.innerHTML = allColleges.map(c => `
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" class="college-checkbox" value='${JSON.stringify(c)}' 
          ${selected.find(s => s.code === c.code) ? 'checked' : ''}>
        <span>${c.name}</span>
      </label>
    `).join('');

    document.querySelectorAll('.college-checkbox').forEach(cb => {
      cb.addEventListener('change', () => {
        const checked = document.querySelectorAll('.college-checkbox:checked');
        if (checked.length > 5) {
          cb.checked = false;
          showToast('Maximum 5 colleges allowed', 'warning');
        }
      });
    });
  }

  const savePrefsBtn = document.getElementById('save-preferences-btn');
  if (savePrefsBtn) {
    savePrefsBtn.addEventListener('click', () => {
      const courses = Array.from(document.querySelectorAll('.course-checkbox:checked'))
        .map(cb => JSON.parse(cb.value));
      const colleges = Array.from(document.querySelectorAll('.college-checkbox:checked'))
        .map(cb => JSON.parse(cb.value));

      updateUserData({
        preferred_courses: courses,
        preferred_colleges: colleges
      });

      showAlert('Preferences saved successfully!', 'success');
      setTimeout(() => location.reload(), 1000);
    });
  }
}

// ========== PAYMENT ==========
function initPayment() {
  const user = checkAuth();
  if (!user) return;

  if (user.has_paid) {
    window.location.href = 'dashboard-grade1.html';
    return;
  }

  const btn = document.getElementById('pay-btn');
  if (btn) btn.addEventListener('click', function() {
    btn.disabled = true;
    btn.innerHTML = 'Processing Payment...';
    
    setTimeout(() => {
      updateUserData({
        has_paid: true,
        paid_at: new Date().toISOString(),
        razorpay_payment_id: 'demo_' + Date.now()
      });
      showAlert('Payment successful! 🎉 Welcome to Premium!', 'success');
      setTimeout(() => {
        window.location.href = 'dashboard-grade1.html';
      }, 1500);
    }, 1500);
  });
}

// ========== PREDICT ==========
function initPredict() {
  const user = checkAuth();
  if (!user) return;

  if (user.user_type === USER_TYPES.PREMIUM && !user.has_paid) {
    window.location.href = 'payment.html';
    return;
  }

  const form = document.getElementById('marks-form');
  const rankSection = document.getElementById('rank-section');
  const aggregateDisplay = document.getElementById('aggregate-display');

  if (rankSection && user.user_type === USER_TYPES.PREMIUM) {
    rankSection.classList.remove('hidden');
  }

  const updateCalculations = () => {
    const m = parseFloat(document.getElementById('maths')?.value) || 0;
    const p = parseFloat(document.getElementById('physics')?.value) || 0;
    const c = parseFloat(document.getElementById('chemistry')?.value) || 0;
    
    const total = m + p + c;
    const aggregate = calculateAggregate(m, p, c);
    
    const totalEl = document.getElementById('total-marks');
    if (totalEl) totalEl.textContent = total.toFixed(2);
    
    if (aggregateDisplay) {
      aggregateDisplay.innerHTML = `
        <div class="aggregate-calc">
          <h4 class="font-bold mb-2">Aggregate Calculation</h4>
          <div class="subject-weight">
            <span>Mathematics (×1):</span>
            <span class="weight-badge">${m.toFixed(2)}</span>
          </div>
          <div class="subject-weight">
            <span>Physics (×0.5):</span>
            <span class="weight-badge">${(p / 2).toFixed(2)}</span>
          </div>
          <div class="subject-weight">
            <span>Chemistry (×0.5):</span>
            <span class="weight-badge">${(c / 2).toFixed(2)}</span>
          </div>
          <hr style="margin: 1rem 0;">
          <div class="subject-weight">
            <span class="font-bold">Total Aggregate:</span>
            <span class="weight-badge" style="font-size: 1.125rem;">${aggregate.toFixed(2)}</span>
          </div>
        </div>`;
    }
  };

  ['maths', 'physics', 'chemistry'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateCalculations);
  });

  if (form) form.addEventListener('submit', function(e) {
    e.preventDefault();

    const maths = parseFloat(document.getElementById('maths').value);
    const physics = parseFloat(document.getElementById('physics').value);
    const chemistry = parseFloat(document.getElementById('chemistry').value);
    const actualRankInput = document.getElementById('actual-rank');
    const actualRank = actualRankInput ? actualRankInput.value : null;

    const total = maths + physics + chemistry;
    const aggregate = calculateAggregate(maths, physics, chemistry);
    const prediction = predictRank(total, user.category);

    let rankVerification = null;
    if (actualRank && user.user_type === USER_TYPES.PREMIUM) {
      const actual = parseInt(actualRank);
      const difference = Math.abs(actual - prediction.predicted);
      const accuracy = 100 - (difference / actual * 100);
      
      rankVerification = {
        actual,
        predicted: prediction.predicted,
        difference,
        accuracy: accuracy.toFixed(2),
        match: difference < (actual * 0.1)
      };

      const rankData = getRankData();
      rankData.push({
        marks: total,
        aggregate,
        category: user.category,
        actual_rank: actual,
        predicted_rank: prediction.predicted,
        timestamp: new Date().toISOString()
      });
      saveRankData(rankData);

      console.log('Training data added. Total points:', rankData.length);
    }

    const predictionData = {
      id: generateId(),
      user_id: user.id,
      maths, physics, chemistry, total, aggregate,
      category: user.category,
      ...prediction,
      rank_verification: rankVerification,
      created_at: new Date().toISOString()
    };

    const preds = getPredictions();
    preds.push(predictionData);
    savePredictions(preds);

    updateUserData({
      total_marks: total,
      aggregate: aggregate,
      last_prediction: predictionData
    });

    displayPredictionResults(predictionData);
  });
}

function displayPredictionResults(pred) {
  const formContainer = document.getElementById('marks-form-container');
  const resultsContainer = document.getElementById('results-container');
  
  if (formContainer) formContainer.classList.add('hidden');
  if (resultsContainer) resultsContainer.classList.remove('hidden');

  const set = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
  set('rank-low', pred.rank_low.toLocaleString());
  set('rank-high', pred.rank_high.toLocaleString());
  set('result-total', pred.total);
  set('result-aggregate', pred.aggregate.toFixed(2));

  const verifyContainer = document.getElementById('rank-verification-result');
  if (verifyContainer && pred.rank_verification) {
    const v = pred.rank_verification;
    verifyContainer.innerHTML = `
      <div class="rank-verify-box ${v.match ? 'verify-match' : 'verify-mismatch'}">
        <h4 class="font-bold mb-2">${v.match ? '✓ Verification Passed' : '⚠ Verification Alert'}</h4>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <p class="text-sm">Actual Rank</p>
            <p class="text-xl font-bold">${v.actual.toLocaleString()}</p>
          </div>
          <div>
            <p class="text-sm">Predicted Rank</p>
            <p class="text-xl font-bold">${v.predicted.toLocaleString()}</p>
          </div>
          <div>
            <p class="text-sm">Accuracy</p>
            <p class="text-xl font-bold">${v.accuracy}%</p>
          </div>
        </div>
        <p class="text-sm mt-4">
          ${v.match 
            ? '✓ Our prediction is highly accurate! Using this for college recommendations.' 
            : '⚠ Difference detected. Retraining model with your data for better accuracy.'}
        </p>
      </div>`;
  }

  const newPredBtn = document.getElementById('new-prediction-btn');
  if (newPredBtn) {
    newPredBtn.addEventListener('click', () => {
      location.reload();
    });
  }

  showToast('🎉 Prediction complete! Check Choice Builder for recommendations.', 'success');
}

// ========== CHOICE BUILDER ==========
function initChoiceBuilder() {
  const user = checkAuth();
  if (!user) return;

  if (!user.last_prediction) {
    showAlert('Please enter your marks first', 'warning');
    setTimeout(() => window.location.href = 'predict.html', 1500);
    return;
  }

  const pred = user.last_prediction;
  
  const userMarksEl = document.getElementById('user-marks');
  const userRankEl = document.getElementById('user-rank');
  
  if (userMarksEl) userMarksEl.textContent = `${pred.total}/200`;
  if (userRankEl) userRankEl.textContent = `${pred.rank_low.toLocaleString()} - ${pred.rank_high.toLocaleString()}`;
  
  loadChoiceList(pred);
}

function loadChoiceList(pred) {
  const container = document.getElementById('choice-list');
  if (!container) return;

  const allChoices = [];
  
  Object.keys(COLLEGE_CUTOFFS).forEach(key => {
    const [college, course] = key.split('_');
    const cutoff = COLLEGE_CUTOFFS[key];
    const prob = calculateProbability(pred.total, cutoff);
    
    allChoices.push({
      college,
      course,
      cutoff,
      probability: prob.value,
      label: prob.label
    });
  });

  allChoices.sort((a, b) => b.probability - a.probability);

  const totalChoicesEl = document.getElementById('total-choices');
  const highProbCountEl = document.getElementById('high-prob-count');
  
  if (totalChoicesEl) totalChoicesEl.textContent = allChoices.length;
  if (highProbCountEl) {
    const highCount = allChoices.filter(c => c.probability > 70).length;
    highProbCountEl.textContent = highCount;
  }

  let html = '<div class="mb-4"><p class="text-secondary text-sm">💡 Drag to reorder. Top choices recommended by AI based on your probability.</p></div>';
  
  allChoices.forEach((choice, index) => {
    const probClass = choice.probability > 70 ? 'high' : choice.probability > 40 ? 'medium' : 'low';
    const warning = choice.probability < 30 ? '<span class="badge badge-danger ml-2">⚠ Very Low</span>' : '';
    
    html += `
      <div class="choice-item" draggable="true" data-index="${index}">
        <div class="choice-number">${index + 1}</div>
        <div class="choice-details">
          <div class="font-bold">${getCollegeName(choice.college)} - ${getCourseName(choice.course)}</div>
          <div class="text-sm text-secondary">Cutoff: ${choice.cutoff}/200 | Your Marks: ${pred.total}/200</div>
        </div>
        <div class="choice-probability ${probClass}">
          ${choice.probability}% ${warning}
        </div>
      </div>`;
  });

  container.innerHTML = html;
  setupDragAndDrop();
}

function getCollegeName(code) {
  const names = {
    'CEG': 'CEG', 'MIT': 'MIT', 'ACT': 'ACT', 'PSG': 'PSG',
    'TCE': 'TCE', 'SSN': 'SSN', 'REC': 'REC'
  };
  return names[code] || code;
}

function getCourseName(code) {
  const names = {
    'CSE': 'CSE', 'IT': 'IT', 'ECE': 'ECE', 'EEE': 'EEE',
    'MECH': 'Mech', 'CIVIL': 'Civil', 'AI&DS': 'AI&DS', 'AIML': 'AIML'
  };
  return names[code] || code;
}

function setupDragAndDrop() {
  const items = document.querySelectorAll('.choice-item');
  let draggedItem = null;

  items.forEach(item => {
    item.addEventListener('dragstart', function() {
      draggedItem = this;
      setTimeout(() => this.classList.add('dragging'), 0);
    });

    item.addEventListener('dragend', function() {
      this.classList.remove('dragging');
    });

    item.addEventListener('dragover', function(e) {
      e.preventDefault();
    });

    item.addEventListener('drop', function() {
      if (draggedItem !== this) {
        const allItems = [...document.querySelectorAll('.choice-item')];
        const draggedIndex = allItems.indexOf(draggedItem);
        const droppedIndex = allItems.indexOf(this);

        if (draggedIndex < droppedIndex) {
          this.after(draggedItem);
        } else {
          this.before(draggedItem);
        }

        updateChoiceNumbers();
      }
    });
  });
}

function updateChoiceNumbers() {
  document.querySelectorAll('.choice-item').forEach((item, index) => {
    item.querySelector('.choice-number').textContent = index + 1;
  });
}

// ========== COUNSELLING SIMULATOR ==========
function initCounselling() {
  const user = checkAuth();
  if (!user) return;

  if (!user.last_prediction) {
    showAlert('Please enter your marks first', 'warning');
    setTimeout(() => window.location.href = 'predict.html', 1500);
    return;
  }

  const startBtn = document.getElementById('start-simulation-btn');
  if (startBtn) {
    startBtn.addEventListener('click', runCounsellingSimulation);
  }
}

function runCounsellingSimulation() {
  const user = getCurrentUser();
  const pred = user.last_prediction;
  const container = document.getElementById('simulation-steps');
  
  if (!container) return;

  showToast('Running TNEA counselling simulation...', 'info');

  const choices = [];
  Object.keys(COLLEGE_CUTOFFS).forEach(key => {
    const [college, course] = key.split('_');
    const cutoff = COLLEGE_CUTOFFS[key];
    const prob = calculateProbability(pred.total, cutoff);
    choices.push({ college, course, cutoff, probability: prob.value });
  });

  choices.sort((a, b) => b.probability - a.probability);
  const topChoices = choices.slice(0, 10);

  let html = '';
  let allotted = false;

  topChoices.forEach((choice, index) => {
    let status = '';
    let statusClass = '';
    let stepClass = '';

    if (!allotted) {
      if (choice.probability > 70) {
        status = 'ALLOTTED ✓';
        statusClass = 'allotted';
        stepClass = 'completed';
        allotted = true;
      } else if (choice.probability > 40) {
        status = 'WAITLIST';
        statusClass = 'waitlist';
        stepClass = 'active';
      } else {
        status = 'REJECTED';
        statusClass = 'rejected';
        stepClass = 'rejected';
      }
    } else {
      status = 'SKIPPED';
      statusClass = '';
      stepClass = 'completed';
    }

    html += `
      <div class="counselling-step ${stepClass} animate-fadeIn">
        <span class="step-number">${index + 1}</span>
        <strong>${getCollegeName(choice.college)} - ${getCourseName(choice.course)}</strong>
        <span class="step-status ${statusClass}">${status}</span>
        <p class="text-sm text-secondary mt-2">
          Cutoff: ${choice.cutoff}/200 | Your Marks: ${pred.total}/200 | Probability: ${choice.probability}%
        </p>
      </div>`;
  });

  container.innerHTML = html;

  setTimeout(() => {
    container.scrollIntoView({ behavior: 'smooth' });
    showToast('✓ Simulation complete!', 'success');
  }, 500);
}