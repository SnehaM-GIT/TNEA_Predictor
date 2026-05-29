// ========== STORAGE KEYS ==========
const USERS_KEY = 'pickmyseat_users';
const CURRENT_USER_KEY = 'pickmyseat_current_user';
const PREDICTIONS_KEY = 'pickmyseat_predictions';

// ========== HELPERS ==========
function getUsers() { return JSON.parse(localStorage.getItem(USERS_KEY) || '[]'); }
function saveUsers(u) { localStorage.setItem(USERS_KEY, JSON.stringify(u)); }
function getCurrentUser() { return JSON.parse(localStorage.getItem(CURRENT_USER_KEY) || 'null'); }
function setCurrentUser(u) { localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(u)); }
function clearCurrentUser() { localStorage.removeItem(CURRENT_USER_KEY); }
function getPredictions() { return JSON.parse(localStorage.getItem(PREDICTIONS_KEY) || '[]'); }
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

// ========== PAGE ROUTER ==========
document.addEventListener('DOMContentLoaded', function() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  console.log('PAGE LOADED:', page);
  setupLogout();

  if (page === 'login.html') initLogin();
  else if (page === 'signup.html') initSignup();
  else if (page === 'dashboard.html') initDashboard();
  else if (page === 'profile.html') initProfile();
  else if (page === 'payment.html') initPayment();
  else if (page === 'predict.html') initPredict();
});

// ========== SIGNUP ==========
function initSignup() {
  const form = document.getElementById('signup-form');
  if (!form) { console.error('signup form missing'); return; }

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    console.log('SIGNUP submitted');

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const pw = document.getElementById('password').value;
    const cpw = document.getElementById('confirm-password').value;

    if (pw !== cpw) { showAlert('Passwords do not match'); return; }
    if (pw.length < 6) { showAlert('Password must be at least 6 characters'); return; }

    const users = getUsers();
    if (users.find(u => u.email === email)) { showAlert('Email already registered. Please login.'); return; }

    const newUser = {
      id: generateId(), name, email, phone, password: pw,
      has_paid: false, category: '', district: '', school: '',
      tenth_mark: '', twelfth_mark: '', created_at: new Date().toISOString()
    };
    users.push(newUser);
    saveUsers(users);

    const { password, ...safe } = newUser;
    setCurrentUser(safe);
    showAlert('Account created! Redirecting...', 'success');
    setTimeout(() => { window.location.href = 'profile.html'; }, 800);
  });

  const g = document.getElementById('google-signup-btn');
  if (g) g.addEventListener('click', () => showAlert('Google signup needs Firebase', 'info'));
}

// ========== LOGIN ==========
function initLogin() {
  const form = document.getElementById('login-form');
  if (!form) { console.error('login form missing'); return; }

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    console.log('LOGIN submitted');

    const email = document.getElementById('email').value.trim();
    const pw = document.getElementById('password').value;

    const users = getUsers();
    const user = users.find(u => u.email === email && u.password === pw);

    if (user) {
      const { password, ...safe } = user;
      setCurrentUser(safe);
      showAlert('Login successful! Redirecting...', 'success');
      setTimeout(() => { window.location.href = 'dashboard.html'; }, 800);
    } else {
      showAlert('Invalid email or password. Sign up first if new.');
    }
  });

  const g = document.getElementById('google-login-btn');
  if (g) g.addEventListener('click', () => showAlert('Google login needs Firebase', 'info'));
}

// ========== DASHBOARD ==========
function initDashboard() {
  const user = checkAuth();
  if (!user) return;

  const emailEl = document.getElementById('user-email');
  if (emailEl) emailEl.textContent = user.name || user.email;

  const statusEl = document.getElementById('account-status');
  const actionBtn = document.getElementById('quick-action-btn');

  if (user.has_paid) {
    if (statusEl) statusEl.innerHTML = '<span class="badge badge-success">Premium ✓</span>';
    if (actionBtn) { actionBtn.textContent = 'New Prediction'; actionBtn.onclick = () => window.location.href = 'predict.html'; }
  } else {
    if (statusEl) statusEl.innerHTML = '<span class="badge badge-secondary">Free</span>';
    if (actionBtn) { actionBtn.textContent = 'Unlock Premium'; actionBtn.onclick = () => window.location.href = 'payment.html'; }
  }

  const preds = getPredictions().filter(p => p.user_id === user.id);
  const totalEl = document.getElementById('total-predictions');
  if (totalEl) totalEl.textContent = preds.length;

  const container = document.getElementById('predictions-container');
  if (!container) return;

  if (preds.length === 0) {
    container.innerHTML = `
      <div class="card empty-state">
        <div class="empty-state-icon">📊</div>
        <div class="empty-state-title">No predictions yet</div>
        <div class="empty-state-description">Make your first prediction</div>
        <button class="btn btn-primary" onclick="window.location.href='${user.has_paid ? 'predict.html' : 'payment.html'}'">
          ${user.has_paid ? 'Make Prediction' : 'Unlock Premium'}
        </button>
      </div>`;
  } else {
    container.innerHTML = preds.map(p => `
      <div class="card college-card mb-4"><div class="card-body">
        <p class="text-sm text-secondary">${new Date(p.created_at).toLocaleDateString('en-IN')}</p>
        <div class="grid grid-cols-3 gap-4 mt-4">
          <div><p class="text-sm text-secondary">Total</p><p class="text-lg font-bold">${p.total}</p></div>
          <div><p class="text-sm text-secondary">Rank</p><p class="text-lg font-bold text-primary">${p.rank_low.toLocaleString()} - ${p.rank_high.toLocaleString()}</p></div>
          <div><p class="text-sm text-secondary">Dept</p><p class="text-lg font-bold">${p.department}</p></div>
        </div>
      </div></div>`).join('');
  }
}

// ========== PROFILE ==========
function initProfile() {
  const user = checkAuth();
  if (!user) return;

  const view = document.getElementById('profile-view');
  const edit = document.getElementById('profile-edit');
  const isComplete = user.name && user.phone && user.category;

  function showView() {
    if (view) view.classList.remove('hidden');
    if (edit) edit.classList.add('hidden');
    const data = document.getElementById('profile-data');
    if (data) {
      const fields = [
        { l: 'Email', v: user.email }, { l: 'Name', v: user.name }, { l: 'Phone', v: user.phone },
        { l: 'Category', v: user.category }, { l: 'District', v: user.district }, { l: 'School', v: user.school },
        { l: '10th Mark', v: user.tenth_mark ? user.tenth_mark + '%' : '' },
        { l: '12th Mark', v: user.twelfth_mark ? user.twelfth_mark + '%' : '' },
        { l: 'Payment', v: user.has_paid ? '<span class="badge badge-success">Paid ✓</span>' : '<span class="badge badge-warning">Not Paid</span>' }
      ];
      data.innerHTML = fields.filter(f => f.v).map(f =>
        `<div style="border-bottom:1px solid var(--border-color);padding-bottom:0.75rem;"><p class="text-sm text-secondary">${f.l}</p><p class="text-lg font-bold mt-1">${f.v}</p></div>`).join('');
    }
    const notice = document.getElementById('payment-notice');
    if (notice && !user.has_paid) notice.classList.remove('hidden');
  }

  function showEdit() {
    if (view) view.classList.add('hidden');
    if (edit) edit.classList.remove('hidden');
    const set = (id, v) => { const e = document.getElementById(id); if (e) e.value = v || ''; };
    set('name', user.name); set('phone', user.phone); set('category', user.category);
    set('district', user.district); set('school', user.school);
    set('tenth-mark', user.tenth_mark); set('twelfth-mark', user.twelfth_mark);
  }

  if (isComplete) showView(); else showEdit();

  const editBtn = document.getElementById('edit-profile-btn');
  if (editBtn) editBtn.addEventListener('click', showEdit);

  const cancelBtn = document.getElementById('cancel-edit-btn');
  if (cancelBtn) cancelBtn.addEventListener('click', () => {
    if (isComplete) showView(); else window.location.href = 'dashboard.html';
  });

  const form = document.getElementById('profile-form');
  if (form) form.addEventListener('submit', function(e) {
    e.preventDefault();
    const get = id => { const el = document.getElementById(id); return el ? el.value.trim() : ''; };
    updateUserData({
      name: get('name'), phone: get('phone'), category: get('category'),
      district: get('district'), school: get('school'),
      tenth_mark: get('tenth-mark'), twelfth_mark: get('twelfth-mark')
    });
    showAlert('Profile saved successfully!', 'success');
    setTimeout(() => location.reload(), 1000);
  });
}

// ========== PAYMENT ==========
function initPayment() {
  const user = checkAuth();
  if (!user) return;
  if (user.has_paid) { window.location.href = 'predict.html'; return; }

  const btn = document.getElementById('pay-btn');
  if (btn) btn.addEventListener('click', function() {
    btn.disabled = true;
    btn.innerHTML = 'Processing...';
    setTimeout(() => {
      updateUserData({ has_paid: true, paid_at: new Date().toISOString(), razorpay_payment_id: 'demo_' + Date.now() });
      showAlert('Payment successful! 🎉 Redirecting...', 'success');
      setTimeout(() => { window.location.href = 'predict.html'; }, 1000);
    }, 1500);
  });
}

// ========== PREDICT ==========
function initPredict() {
  const user = checkAuth();
  if (!user) return;
  if (!user.has_paid) { window.location.href = 'payment.html'; return; }

  const formContainer = document.getElementById('marks-form-container');
  const resultsContainer = document.getElementById('results-container');
  const form = document.getElementById('marks-form');

  const updateTotal = () => {
    const m = parseFloat(document.getElementById('maths').value) || 0;
    const p = parseFloat(document.getElementById('physics').value) || 0;
    const c = parseFloat(document.getElementById('chemistry').value) || 0;
    const el = document.getElementById('total-marks');
    if (el) el.textContent = (m + p + c).toFixed(2);
  };
  ['maths', 'physics', 'chemistry'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateTotal);
  });

  if (form) form.addEventListener('submit', function(e) {
    e.preventDefault();
    const maths = parseFloat(document.getElementById('maths').value);
    const physics = parseFloat(document.getElementById('physics').value);
    const chemistry = parseFloat(document.getElementById('chemistry').value);
    const department = document.getElementById('department').value;

    if (!department) { showAlert('Please select a department'); return; }

    const total = maths + physics + chemistry;
    const rankLow = Math.max(1, Math.floor((600 - total) * 150) - 500);
    const rankHigh = Math.floor((600 - total) * 150) + 500;
    const cat = user.category || 'OC';

    const colleges = [
      { college_name: "Anna University, Chennai", department, opening_rank: Math.max(1, rankLow - 5000), closing_rank: rankLow + 2000, category: cat, location: "Chennai", match_probability: "high", score: 0.92 },
      { college_name: "College of Engineering, Guindy", department, opening_rank: Math.max(1, rankLow - 3000), closing_rank: rankLow + 5000, category: cat, location: "Chennai", match_probability: "high", score: 0.88 },
      { college_name: "PSG College of Technology", department, opening_rank: rankLow, closing_rank: rankHigh + 3000, category: cat, location: "Coimbatore", match_probability: "medium", score: 0.75 },
      { college_name: "Thiagarajar College of Engineering", department, opening_rank: rankLow + 2000, closing_rank: rankHigh + 5000, category: cat, location: "Madurai", match_probability: "medium", score: 0.68 },
      { college_name: "SSN College of Engineering", department, opening_rank: rankHigh, closing_rank: rankHigh + 8000, category: cat, location: "Chennai", match_probability: "low", score: 0.54 }
    ];

    const preds = getPredictions();
    preds.push({ id: generateId(), user_id: user.id, maths, physics, chemistry, total, department, category: cat, rank_low: rankLow, rank_high: rankHigh, colleges, created_at: new Date().toISOString() });
    localStorage.setItem(PREDICTIONS_KEY, JSON.stringify(preds));

    displayResults({ maths, physics, chemistry, total, rank_low: rankLow, rank_high: rankHigh, colleges });
  });

  const newBtn = document.getElementById('new-prediction-btn');
  if (newBtn) newBtn.addEventListener('click', () => {
    if (formContainer) formContainer.classList.remove('hidden');
    if (resultsContainer) resultsContainer.classList.add('hidden');
    if (form) form.reset();
    const t = document.getElementById('total-marks');
    if (t) t.textContent = '0.00';
  });

  function displayResults(p) {
    if (formContainer) formContainer.classList.add('hidden');
    if (resultsContainer) resultsContainer.classList.remove('hidden');
    const set = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
    set('rank-low', p.rank_low.toLocaleString());
    set('rank-high', p.rank_high.toLocaleString());
    set('result-total', p.total);
    set('result-maths', p.maths);
    set('result-physics', p.physics);
    set('result-chemistry', p.chemistry);

    const list = document.getElementById('colleges-list');
    if (list) list.innerHTML = p.colleges.map(c => `
      <div class="card college-card mb-4"><div class="card-body">
        <div class="college-card-header">
          <div><h3 class="college-name">${c.college_name}</h3><p class="college-department">${c.department}</p></div>
          <span class="badge ${c.match_probability === 'high' ? 'badge-success' : c.match_probability === 'medium' ? 'badge-warning' : 'badge-danger'}">${c.match_probability} chance</span>
        </div>
        <div class="college-stats">
          <div class="college-stat"><p class="college-stat-label">Opening</p><p class="college-stat-value">${c.opening_rank.toLocaleString()}</p></div>
          <div class="college-stat"><p class="college-stat-label">Closing</p><p class="college-stat-value">${c.closing_rank.toLocaleString()}</p></div>
          <div class="college-stat"><p class="college-stat-label">Your Rank</p><p class="college-stat-value text-primary">${p.rank_low.toLocaleString()} - ${p.rank_high.toLocaleString()}</p></div>
          <div class="college-stat"><p class="college-stat-label">Category</p><p class="college-stat-value">${c.category}</p></div>
        </div>
        <div style="margin-top:1rem;">
          <div class="flex justify-between text-sm text-secondary mb-2"><span>Match Score</span><span>${Math.round(c.score * 100)}%</span></div>
          <div class="match-score-bar"><div class="match-score-fill" style="width:${c.score * 100}%;"></div></div>
        </div>
      </div></div>`).join('');
  }
}