/* ============================================================
   PICKMYSEAT.AI — app.js
   Grade 3: guest, 1 college, 1 course, 1 prediction (cookie)
   Grade 2: registered, 5 colleges, 3 courses, marks locked
   Grade 1: premium, all features + ₹25 mark update
   ============================================================ */

'use strict';

// ============================================================
// STATE
// ============================================================
const App = {
  currentPage:     'landing',
  currentUser:     null,
  userGrade:       3,
  liveCount:       342,
  slotsLeft:       23,
  rankPhase:       'pre',
  counsellingStep: 0,

  profile: {
    name:              '',
    email:             '',
    mobile:            '',
    category:          '',
    maths:             null,
    physics:           null,
    chemistry:         null,
    marksLocked:       false,
    rank:              null,
    rankPhase:         'pre',
    hasPaid:           false,
    preferredColleges: [],
    preferredCourses:  [],
  }
};

// ============================================================
// DATA
// ============================================================
const DATA = {
  colleges: [
    { id:'ceg',         name:'College of Engineering Guindy',           type:'government', district:'Chennai'       },
    { id:'mit',         name:'MIT Campus, Anna University',              type:'government', district:'Chennai'       },
    { id:'actech',      name:'Alagappa Chettiar Tech, Karaikudi',       type:'government', district:'Sivaganga'     },
    { id:'gce_salem',   name:'Govt. College of Engineering Salem',       type:'government', district:'Salem'         },
    { id:'gce_tirun',   name:'Govt. College of Engineering Tirunelveli', type:'government', district:'Tirunelveli'  },
    { id:'psg',         name:'PSG College of Technology',                type:'aided',      district:'Coimbatore'   },
    { id:'thiagarajar', name:'Thiagarajar College of Engineering',       type:'aided',      district:'Madurai'      },
    { id:'bsau',        name:'B.S. Abdur Rahman Crescent Inst.',         type:'aided',      district:'Chennai'      },
    { id:'mepco',       name:'Mepco Schlenk Engineering College',        type:'aided',      district:'Virudhunagar' },
    { id:'kct',         name:'Kumaraguru College of Technology',          type:'private',    district:'Coimbatore'   },
    { id:'srmist',      name:'SRM Institute of Science & Tech.',         type:'private',    district:'Chennai'      },
    { id:'vit',         name:'Vellore Institute of Technology',           type:'private',    district:'Vellore'      },
    { id:'sastra',      name:'SASTRA Deemed University',                  type:'private',    district:'Thanjavur'    },
    { id:'kongu',       name:'Kongu Engineering College',                 type:'private',    district:'Erode'        },
    { id:'srm_rmp',     name:'SRM Ramapuram',                            type:'private',    district:'Chennai'      },
  ],

  courses: [
    { id:'cse',   name:'Computer Science & Engineering',   dept:'CS', cutoffBase:195 },
    { id:'aids',  name:'AI & Data Science',                dept:'CS', cutoffBase:192 },
    { id:'csbs',  name:'CS & Business Systems',            dept:'CS', cutoffBase:190 },
    { id:'it',    name:'Information Technology',           dept:'IT', cutoffBase:188 },
    { id:'ece',   name:'Electronics & Communication Eng.', dept:'EC', cutoffBase:185 },
    { id:'eee',   name:'Electrical & Electronics Eng.',    dept:'EE', cutoffBase:175 },
    { id:'bio',   name:'Biotechnology',                    dept:'BT', cutoffBase:172 },
    { id:'mech',  name:'Mechanical Engineering',           dept:'ME', cutoffBase:170 },
    { id:'chem',  name:'Chemical Engineering',             dept:'CH', cutoffBase:165 },
    { id:'civil', name:'Civil Engineering',                dept:'CV', cutoffBase:160 },
  ],

  districts: [
    'Chennai','Coimbatore','Tiruchirappalli','Madurai',
    'Salem','Erode','Vellore','Thanjavur','Tirunelveli',
    'Kancheepuram','Sivaganga','Virudhunagar'
  ],

  collegeTypeAdjust: { government:0, aided:-5, private:-15 },

  testimonials: [
    { name:'Priya R.',   sub:'CSE · Anna University · 2024', text:'Got exactly the college PickMySeat predicted! Saved so many hours of confusion during counselling.', stars:5 },
    { name:'Karthik S.', sub:'ECE · PSG Tech · 2024',        text:'The AI Choice List helped me order my preferences perfectly. Made 3x smarter decisions.',            stars:5 },
    { name:'Ananya M.',  sub:'IT · SRM IST · 2024',          text:'Even without my rank, the marks-based prediction was spot on. Worth every rupee.',                    stars:5 },
    { name:'Vijay K.',   sub:'Mech · Thiagarajar · 2024',    text:'Used the counselling simulation to practice. When real day came, I was fully confident.',             stars:5 },
    { name:'Deepika T.', sub:'EEE · CEG · 2024',             text:'Loved how simple it was. Just entered marks, got my prediction in seconds. Brilliant!',               stars:5 },
    { name:'Ravi N.',    sub:'Civil · Kongu Engg · 2024',    text:'The probability ordering is genius. Knew exactly which college to put first in my list.',            stars:4 },
  ],

  tickerEvents: [
    'Priya from Chennai just predicted her seat 🎯',
    'Karthik unlocked Premium access ⚡',
    'Ananya got 94% probability for CSE at Anna Univ 🏛️',
    'Vijay ran the Counselling Simulation 🎓',
    'Deepika from Coimbatore got her AI Choice List 📋',
    'Ravi predicted rank band: 1200–1800 🏆',
    'Sneha unlocked 15 college-course combos 🚀',
    '3 students joined PickMySeat in the last hour 🔥',
  ],
};

// ============================================================
// ROUTING
// ============================================================
function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  const target = document.getElementById(`page-${page}`);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }
  App.currentPage = page;
  window.scrollTo({ top:0, behavior:'smooth' });
  updateNav();
  if (page === 'dashboard')    renderDashboard();
  if (page === 'profile')      renderProfile();
  if (page === 'free-predict') initFreePredictPage();
  if (page === 'landing')      initLanding();
}

// ============================================================
// NAV
// ============================================================
function updateNav() {
  const navUser    = document.getElementById('navUserBlock');
  const navLogin   = document.getElementById('navLoginBtn');
  const navUpgrade = document.getElementById('navUpgradeBtn');
  const navDash    = document.getElementById('navDashboard');
  const navProf    = document.getElementById('navProfile');

  if (App.currentUser) {
    navUser.classList.remove('hidden');
    navLogin.classList.add('hidden');
    navDash.classList.remove('hidden');
    navProf.classList.remove('hidden');
    document.getElementById('navAvatar').textContent =
      (App.profile.name || App.profile.email || 'S')[0].toUpperCase();
    document.getElementById('navUserName').textContent =
      App.profile.name ? App.profile.name.split(' ')[0] : 'Student';
    document.getElementById('dropdownInfo').textContent = App.profile.email || '';
    navUpgrade.classList.toggle('hidden', App.userGrade === 1);
  } else {
    navUser.classList.add('hidden');
    navLogin.classList.remove('hidden');
    navUpgrade.classList.add('hidden');
    navDash.classList.add('hidden');
    navProf.classList.add('hidden');
  }
}

function toggleUserMenu() {
  document.getElementById('userDropdown')?.classList.toggle('hidden');
}

document.addEventListener('click', e => {
  const dd = document.getElementById('userDropdown');
  if (dd && !dd.classList.contains('hidden') && !e.target.closest('.nav-user')) {
    dd.classList.add('hidden');
  }
});

// ============================================================
// TOAST
// ============================================================
function showToast(msg, type = 'info', duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ============================================================
// LANDING
// ============================================================
function initLanding() {
  renderTicker();
  renderTestimonials();
  updateLiveCounts();
  observeScrollAnimations();
}

function renderTicker() {
  const track = document.getElementById('tickerTrack');
  if (!track) return;
  const doubled = [...DATA.tickerEvents, ...DATA.tickerEvents];
  track.innerHTML = doubled.map(ev => `<span class="ticker-item">🟢 ${ev}</span>`).join('');
}

function renderTestimonials() {
  const grid = document.getElementById('testimonialsGrid');
  if (!grid) return;
  grid.innerHTML = DATA.testimonials.map(t => `
    <div class="testimonial-card animate-on-scroll">
      <div class="testimonial-stars">${'★'.repeat(t.stars)}${'☆'.repeat(5 - t.stars)}</div>
      <p class="testimonial-text">"${t.text}"</p>
      <div class="testimonial-author">
        <div class="testimonial-avatar">${t.name[0]}</div>
        <div>
          <div class="testimonial-name">${t.name}</div>
          <div class="testimonial-sub">${t.sub}</div>
        </div>
      </div>
    </div>`).join('');
}

function updateLiveCounts() {
  const heroCount  = document.getElementById('heroLiveCount');
  const modalCount = document.getElementById('liveCount');
  const update = () => {
    if (heroCount)  heroCount.textContent  = App.liveCount;
    if (modalCount) modalCount.textContent = App.liveCount;
  };
  update();
  setInterval(() => {
    if (Math.random() > 0.7) { App.liveCount++; update(); }
  }, 8000);
}

function observeScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'slideUp 0.5s ease forwards';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold:0.1 });
  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });
}

// ============================================================
// AGGREGATE FORMULA
// Always: Maths + Physics + Chemistry
// (M/2) + (P/4) + (C/4)  → max 100 → ×2 = max 200
// ============================================================
function calculateAggregate(maths, physics, chemistry) {
  const m = Math.min(100, Math.max(0, parseFloat(maths)     || 0));
  const p = Math.min(100, Math.max(0, parseFloat(physics)   || 0));
  const c = Math.min(100, Math.max(0, parseFloat(chemistry) || 0));
  return Math.round(((m / 2) + (p / 4) + (c / 4)) * 2 * 100) / 100;
}

// ============================================================
// PREDICTION ENGINE
// Simulates XGBoost backend — replace with POST /predict/rank
// ============================================================
function predictRankBand(aggregate) {
  const r = parseFloat(aggregate) / 200;
  if (r >= 0.975) return { low:1,     high:200   };
  if (r >= 0.95)  return { low:200,   high:600   };
  if (r >= 0.925) return { low:600,   high:1500  };
  if (r >= 0.90)  return { low:1500,  high:3000  };
  if (r >= 0.875) return { low:3000,  high:5500  };
  if (r >= 0.85)  return { low:5500,  high:9000  };
  if (r >= 0.825) return { low:9000,  high:14000 };
  if (r >= 0.80)  return { low:14000, high:20000 };
  if (r >= 0.75)  return { low:20000, high:30000 };
  if (r >= 0.70)  return { low:30000, high:45000 };
  return                  { low:45000, high:80000 };
}

function predictProbability(aggregate, collegeName, courseName) {
  const course  = DATA.courses.find(c  => c.name  === courseName);
  const college = DATA.colleges.find(c => c.name  === collegeName);
  if (!course || !college) return 50;
  const adj  = DATA.collegeTypeAdjust[college.type] || 0;
  const diff = parseFloat(aggregate) - (course.cutoffBase + adj);
  let prob;
  if      (diff >= 15)  prob = 90 + Math.min(9, diff - 15);
  else if (diff >= 8)   prob = 75 + (diff - 8) * 2;
  else if (diff >= 0)   prob = 55 + diff * 2.5;
  else if (diff >= -8)  prob = 40 + (diff + 8) * 2;
  else if (diff >= -15) prob = 20 + (diff + 15) * 3;
  else                  prob = Math.max(3, 20 + diff);
  return Math.round(Math.min(99, Math.max(2, prob)));
}

function getLastYearCutoff(collegeName, courseName) {
  const course  = DATA.courses.find(c  => c.name === courseName);
  const college = DATA.colleges.find(c => c.name === collegeName);
  if (!course || !college) return '—';
  return (course.cutoffBase + (DATA.collegeTypeAdjust[college.type] || 0)).toFixed(1);
}

function getProbClass(prob) {
  if (prob >= 65) return { cls:'high', barCls:'high', status:'Likely',   statusCls:'status-likely'   };
  if (prob >= 35) return { cls:'mid',  barCls:'mid',  status:'Possible', statusCls:'status-possible' };
  return           { cls:'low',  barCls:'low',  status:'Unlikely', statusCls:'status-unlikely' };
}

// ============================================================
// FREE PREDICT — Grade 3
// ============================================================
function initFreePredictPage() {
  const used = getCookie('pms_free_used');
  const bar  = document.getElementById('cookieUsageBar');

  if (used === '1') {
    bar.textContent = '🔒 Free prediction used · Login to predict more';
    bar.style.display = 'inline-block';
    document.getElementById('freePredictForm')
      ?.querySelectorAll('input,select')
      .forEach(el => el.disabled = true);
    const btn = document.querySelector('#freePredictForm .btn-primary');
    if (btn) btn.disabled = true;
  } else {
    bar.textContent = '✅ 1 free prediction available — no signup needed';
    bar.style.display = 'inline-block';
  }

  populateDistricts('freeDistrict');
  populateAllColleges();
  populateAllCourses();
  document.getElementById('freeResultCard').classList.add('hidden');
}

function populateDistricts(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  while (sel.options.length > 1) sel.remove(1);
  DATA.districts.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d; opt.textContent = d; sel.appendChild(opt);
  });
}

function populateAllColleges() {
  const sel = document.getElementById('freeCollege');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select a college...</option>';
  DATA.colleges.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name; opt.textContent = c.name; sel.appendChild(opt);
  });
}

function populateAllCourses() {
  const sel = document.getElementById('freeCourse');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select a course...</option>';
  DATA.courses.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name; opt.textContent = c.name; sel.appendChild(opt);
  });
}

function filterFreeColleges() {
  const type     = document.getElementById('freeCollegeType')?.value || '';
  const district = document.getElementById('freeDistrict')?.value   || '';
  const sel      = document.getElementById('freeCollege');
  if (!sel) return;
  const filtered = DATA.colleges.filter(c =>
    (!type     || c.type     === type) &&
    (!district || c.district === district)
  );
  sel.innerHTML = '<option value="">Select a college...</option>';
  filtered.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name; opt.textContent = c.name; sel.appendChild(opt);
  });
}

function updateFreeAggregate() {
  const m   = document.getElementById('freeMath')?.value     || 0;
  const p   = document.getElementById('freePhysics')?.value  || 0;
  const c   = document.getElementById('freeChemistry')?.value|| 0;
  const agg = calculateAggregate(m, p, c);
  const el  = document.getElementById('freeAggValue');
  if (el) el.textContent = agg > 0 ? `${agg} / 200` : '— / 200';
  updateBar('mathBar',    m, 100);
  updateBar('physicsBar', p, 100);
  updateBar('chemBar',    c, 100);
}

function updateBar(id, value, max) {
  const bar = document.getElementById(id);
  if (bar) bar.style.width = `${Math.min(100,(parseFloat(value)/max)*100)}%`;
}

function runFreePrediction() {
  if (getCookie('pms_free_used') === '1') {
    showToast('Free prediction already used. Please login to continue.', 'error'); return;
  }
  const m       = document.getElementById('freeMath')?.value      || '';
  const p       = document.getElementById('freePhysics')?.value   || '';
  const c       = document.getElementById('freeChemistry')?.value || '';
  const college = document.getElementById('freeCollege')?.value;
  const course  = document.getElementById('freeCourse')?.value;

  if (!m || !p || !c) {
    showToast('Please enter all three marks', 'error'); return;
  }
  if (parseFloat(m)>100 || parseFloat(p)>100 || parseFloat(c)>100) {
    showToast('Each mark must be between 0 and 100', 'error'); return;
  }
  if (!college) { showToast('Please select a college', 'error'); return; }
  if (!course)  { showToast('Please select a course',  'error'); return; }

  const agg      = calculateAggregate(m, p, c);
  const prob     = predictProbability(agg, college, course);
  const rankBand = predictRankBand(agg);
  const cutoff   = getLastYearCutoff(college, course);

  renderFreeResult({ agg, prob, rankBand, cutoff, college, course });
  setCookie('pms_free_used', '1', 7);

  // Disable form after use
  document.getElementById('freePredictForm')
    ?.querySelectorAll('input,select').forEach(el => el.disabled = true);
  const btn = document.querySelector('#freePredictForm .btn-primary');
  if (btn) btn.disabled = true;

  const bar = document.getElementById('cookieUsageBar');
  if (bar) bar.textContent = '🔒 Free prediction used · Login to predict more';
}

function renderFreeResult({ agg, prob, rankBand, cutoff, college, course }) {
  document.getElementById('resultCollegeName').textContent = college;
  document.getElementById('resultCourseName').textContent  = course;
  document.getElementById('resultAggregate').textContent   = `${agg} / 200`;
  document.getElementById('resultCutoff').textContent      = cutoff;
  document.getElementById('resultRankBand').textContent    =
    rankBand.low ? `${rankBand.low.toLocaleString()} – ${rankBand.high.toLocaleString()}` : '—';

  const pc   = getProbClass(prob);
  const ring = document.getElementById('probRingCircle');
  ring.style.stroke = prob>=65 ? 'var(--success)' : prob>=35 ? 'var(--warning)' : 'var(--danger)';
  ring.style.strokeDashoffset = 314 - (314 * prob / 100);

  document.getElementById('resultProbPercent').textContent = `${prob}%`;
  document.getElementById('resultStatus').textContent      = pc.status;
  document.getElementById('resultStatus').style.color      =
    prob>=65 ? 'var(--success)' : prob>=35 ? 'var(--warning)' : 'var(--danger)';

  const msgEl = document.getElementById('resultMessage');
  if (prob >= 65) {
    msgEl.textContent = `🎉 Strong chance! Your aggregate of ${agg} is above the typical cutoff for ${course} at ${college}.`;
    msgEl.className   = 'result-message success';
  } else if (prob >= 35) {
    msgEl.textContent = `⚡ Possible. You're in the competitive zone. Rank ${rankBand.low?.toLocaleString()}–${rankBand.high?.toLocaleString()} may get you in.`;
    msgEl.className   = 'result-message warning';
  } else {
    msgEl.textContent = `⚠️ Very competitive. Your aggregate of ${agg} is below the typical cutoff of ${cutoff}. Consider safer alternatives.`;
    msgEl.className   = 'result-message danger';
  }

  document.getElementById('freeResultCard').classList.remove('hidden');
  document.getElementById('freeResultCard').scrollIntoView({ behavior:'smooth', block:'start' });
}

// ============================================================
// AUTH
// ============================================================
function switchAuth(mode) {
  document.getElementById('loginForm') ?.classList.toggle('hidden', mode !== 'login');
  document.getElementById('signupForm')?.classList.toggle('hidden', mode !== 'signup');
  document.getElementById('loginTab')  ?.classList.toggle('active', mode === 'login');
  document.getElementById('signupTab') ?.classList.toggle('active', mode === 'signup');
}

function loginUser() {
  const email    = document.getElementById('loginEmail')?.value?.trim();
  const password = document.getElementById('loginPassword')?.value;
  if (!email || !password) { showToast('Please enter email and password', 'error'); return; }
  // FIREBASE: firebase.auth().signInWithEmailAndPassword(email, password)
  simulateLogin({ email, name: email.split('@')[0], hasPaid: false });
}

function signupUser() {
  const name     = document.getElementById('signupName')?.value?.trim();
  const email    = document.getElementById('signupEmail')?.value?.trim();
  const mobile   = document.getElementById('signupMobile')?.value?.trim();
  const password = document.getElementById('signupPassword')?.value;
  if (!name || !email || !mobile || !password) {
    showToast('Please fill all fields', 'error'); return;
  }
  if (password.length < 8) {
    showToast('Password must be at least 8 characters', 'error'); return;
  }
  // FIREBASE: firebase.auth().createUserWithEmailAndPassword(email, password)
  simulateLogin({ email, name, mobile, hasPaid: false });
}

function loginGoogle() {
  // FIREBASE: firebase.auth().signInWithPopup(new firebase.auth.GoogleAuthProvider())
  simulateLogin({ email:'demo@gmail.com', name:'Demo Student', hasPaid:false });
}

function simulateLogin(userData) {
  App.currentUser     = userData;
  App.profile.email   = userData.email  || '';
  App.profile.name    = userData.name   || '';
  App.profile.mobile  = userData.mobile || '';
  App.profile.hasPaid = userData.hasPaid || false;
  App.userGrade       = userData.hasPaid ? 1 : 2;
  showToast(`Welcome${userData.name ? ', ' + userData.name.split(' ')[0] : ''}! 🎉`, 'success');
  navigateTo('profile');
}

function logout() {
  // FIREBASE: firebase.auth().signOut()
  App.currentUser = null;
  App.userGrade   = 3;
  App.profile     = {
    name:'', email:'', mobile:'', category:'',
    maths:null, physics:null, chemistry:null,
    marksLocked:false, rank:null, rankPhase:'pre',
    hasPaid:false, preferredColleges:[], preferredCourses:[],
  };
  showToast('Logged out', 'info');
  navigateTo('landing');
}

// ============================================================
// PROFILE
// ============================================================
function renderProfile() {
  if (!App.currentUser) { navigateTo('auth'); return; }

  document.getElementById('profileName').value     = App.profile.name     || '';
  document.getElementById('profileEmail').value    = App.profile.email    || '';
  document.getElementById('profileMobile').value   = App.profile.mobile   || '';
  document.getElementById('profileCategory').value = App.profile.category || '';

  const locked = App.profile.marksLocked;
  document.getElementById('marksLockedBanner')?.classList.toggle('hidden', !locked);

  const mathEl = document.getElementById('profileMath');
  const phyEl  = document.getElementById('profilePhysics');
  const chemEl = document.getElementById('profileChemistry');

  if (mathEl) { mathEl.value = App.profile.maths     ?? ''; mathEl.disabled = locked; }
  if (phyEl)  { phyEl.value  = App.profile.physics   ?? ''; phyEl.disabled  = locked; }
  if (chemEl) { chemEl.value = App.profile.chemistry ?? ''; chemEl.disabled = locked; }

  updateProfileAggregate();

  document.getElementById('profileRankSection')
    ?.classList.toggle('hidden', App.userGrade !== 1);

  if (App.userGrade === 1 && App.profile.rank) {
    const rankEl = document.getElementById('profileRank');
    if (rankEl) rankEl.value = App.profile.rank;
  }

  renderPreferredColleges();
  renderPreferredCourses();
}

function updateProfileAggregate() {
  const m   = document.getElementById('profileMath')?.value     || 0;
  const p   = document.getElementById('profilePhysics')?.value  || 0;
  const c   = document.getElementById('profileChemistry')?.value|| 0;
  const agg = calculateAggregate(m, p, c);
  const el  = document.getElementById('profileAggValue');
  if (el) el.textContent = agg > 0 ? `${agg} / 200` : '— / 200';
}

function markProfileDirty() {}

function setRankPhase(phase) {
  App.rankPhase = phase;
  App.profile.rankPhase = phase;
  const label = document.getElementById('rankInputLabel');
  const input = document.getElementById('profileRank');
  if (phase === 'post') {
    if (label) label.textContent = 'Your Actual TNEA Rank (will be verified)';
    if (input) input.setAttribute('placeholder','e.g. 4521');
  } else {
    if (label) label.textContent = 'Predicted Rank (optional)';
    if (input) input.setAttribute('placeholder','e.g. 5000');
  }
}

function renderPreferredColleges() {
  const grid = document.getElementById('preferredCollegesGrid');
  if (!grid) return;
  grid.innerHTML = '';
  const max = 5;
  for (let i = 0; i < max; i++) {
    const college = App.profile.preferredColleges[i];
    if (college) {
      grid.innerHTML += `
        <div class="preferred-slot filled">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content">
            <div class="slot-name">${college.name}</div>
            <div class="slot-sub">${college.type} · ${college.district}</div>
          </div>
          <button class="slot-remove" onclick="removePreferredCollege(${i})">✕</button>
        </div>`;
    } else if (i === App.profile.preferredColleges.length) {
      grid.innerHTML += `
        <div class="preferred-slot add-slot">
          <select class="select-input" onchange="addPreferredCollege(this.value);this.value=''">
            <option value="">+ Add College ${i+1}</option>
            ${DATA.colleges.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
          </select>
        </div>`;
    } else {
      grid.innerHTML += `
        <div class="preferred-slot" style="opacity:0.25;pointer-events:none">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content"><div class="slot-name">Add College ${i+1}</div></div>
        </div>`;
    }
  }
}

function renderPreferredCourses() {
  const grid = document.getElementById('preferredCoursesGrid');
  if (!grid) return;
  grid.innerHTML = '';
  const max = 3;
  for (let i = 0; i < max; i++) {
    const course = App.profile.preferredCourses[i];
    if (course) {
      grid.innerHTML += `
        <div class="preferred-slot filled">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content">
            <div class="slot-name">${course.name}</div>
            <div class="slot-sub">${course.dept}</div>
          </div>
          <button class="slot-remove" onclick="removePreferredCourse(${i})">✕</button>
        </div>`;
    } else if (i === App.profile.preferredCourses.length) {
      grid.innerHTML += `
        <div class="preferred-slot add-slot">
          <select class="select-input" onchange="addPreferredCourse(this.value);this.value=''">
            <option value="">+ Add Course ${i+1}</option>
            ${DATA.courses.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
          </select>
        </div>`;
    } else {
      grid.innerHTML += `
        <div class="preferred-slot" style="opacity:0.25;pointer-events:none">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content"><div class="slot-name">Add Course ${i+1}</div></div>
        </div>`;
    }
  }
}

function addPreferredCollege(id) {
  if (!id) return;
  const college = DATA.colleges.find(c => c.id === id);
  if (!college) return;
  if (App.profile.preferredColleges.find(c => c.id === id)) {
    showToast('College already added','error'); renderPreferredColleges(); return;
  }
  if (App.profile.preferredColleges.length >= 5) {
    showToast('Maximum 5 colleges','error'); return;
  }
  App.profile.preferredColleges.push(college);
  renderPreferredColleges();
}

function removePreferredCollege(i) {
  App.profile.preferredColleges.splice(i,1);
  renderPreferredColleges();
}

function addPreferredCourse(id) {
  if (!id) return;
  const course = DATA.courses.find(c => c.id === id);
  if (!course) return;
  if (App.profile.preferredCourses.find(c => c.id === id)) {
    showToast('Course already added','error'); renderPreferredCourses(); return;
  }
  if (App.profile.preferredCourses.length >= 3) {
    showToast('Maximum 3 courses','error'); return;
  }
  App.profile.preferredCourses.push(course);
  renderPreferredCourses();
}

function removePreferredCourse(i) {
  App.profile.preferredCourses.splice(i,1);
  renderPreferredCourses();
}

function saveProfile() {
  const name  = document.getElementById('profileName')?.value?.trim();
  const email = document.getElementById('profileEmail')?.value?.trim();

  if (!name)  { showToast('Please enter your name','error');  return; }
  if (!email) { showToast('Please enter your email','error'); return; }

  App.profile.name     = name;
  App.profile.email    = email;
  App.profile.mobile   = document.getElementById('profileMobile')?.value?.trim()    || '';
  App.profile.category = document.getElementById('profileCategory')?.value          || '';

  if (!App.profile.marksLocked) {
    const m = parseFloat(document.getElementById('profileMath')?.value)     || null;
    const p = parseFloat(document.getElementById('profilePhysics')?.value)  || null;
    const c = parseFloat(document.getElementById('profileChemistry')?.value)|| null;

    if (m !== null || p !== null || c !== null) {
      if (!m || !p || !c) {
        showToast('Please enter all three marks or leave all blank','error'); return;
      }
      if (m > 100 || p > 100 || c > 100) {
        showToast('Each mark must be between 0 and 100','error'); return;
      }
      App.profile.maths     = m;
      App.profile.physics   = p;
      App.profile.chemistry = c;
      App.profile.marksLocked = true;
    }
  }

  if (App.userGrade === 1) {
    const rank = parseFloat(document.getElementById('profileRank')?.value) || null;
    if (rank) {
      App.profile.rank      = rank;
      App.profile.rankPhase = App.rankPhase;
      if (App.rankPhase === 'post') {
        const agg  = calculateAggregate(App.profile.maths, App.profile.physics, App.profile.chemistry);
        const band = predictRankBand(agg);
        const verEl= document.getElementById('rankVerifyResult');
        if (verEl) {
          verEl.classList.remove('hidden');
          const within = rank >= band.low && rank <= band.high;
          verEl.style.cssText = within
            ? 'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:var(--success);padding:12px;border-radius:8px;font-size:13px;margin-top:8px'
            : 'background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:var(--danger);padding:12px;border-radius:8px;font-size:13px;margin-top:8px';
          verEl.textContent = within
            ? `✅ Rank ${rank.toLocaleString()} verified — within predicted band`
            : `⚠️ Rank ${rank.toLocaleString()} outside predicted band (${band.low.toLocaleString()}–${band.high.toLocaleString()}). Model updating.`;
        }
      }
    }
  }

  // FIRESTORE: db.collection('users').doc(uid).set({...App.profile},{merge:true})
  showToast('Profile saved ✅', 'success');
  setTimeout(() => navigateTo('dashboard'), 800);
}

// ============================================================
// MARKS UPDATE — ₹25 (Grade 1 only)
// ============================================================
function openMarksUpdate() {
  if (App.userGrade !== 1) { showUpgradeModal('marks-update'); return; }
  const mEl = document.getElementById('updateMath');
  const pEl = document.getElementById('updatePhysics');
  const cEl = document.getElementById('updateChemistry');
  if (mEl) mEl.value = App.profile.maths    || '';
  if (pEl) pEl.value = App.profile.physics  || '';
  if (cEl) cEl.value = App.profile.chemistry|| '';
  document.getElementById('marksUpdateModal')?.classList.remove('hidden');
}

function closeMarksUpdate() {
  document.getElementById('marksUpdateModal')?.classList.add('hidden');
}

function confirmMarksUpdate() {
  const m = parseFloat(document.getElementById('updateMath')?.value)     || null;
  const p = parseFloat(document.getElementById('updatePhysics')?.value)  || null;
  const c = parseFloat(document.getElementById('updateChemistry')?.value)|| null;

  if (!m || !p || !c) { showToast('Please enter all three marks','error'); return; }
  if (m>100 || p>100 || c>100) { showToast('Each mark must be 0–100','error'); return; }

  // RAZORPAY: ₹25 payment placeholder
  // new Razorpay({ key:'...', amount:2500, ... }).open()

  App.profile.maths     = m;
  App.profile.physics   = p;
  App.profile.chemistry = c;
  App.profile.marksLocked = true;

  closeMarksUpdate();
  showToast('Marks updated successfully ✅','success');
  renderDashboard();
}

// ============================================================
// DASHBOARD
// ============================================================
function renderDashboard() {
  if (!App.currentUser) { navigateTo('auth'); return; }

  const name = App.profile.name || App.profile.email || 'Student';
  document.getElementById('dashWelcome').textContent = `Welcome back, ${name.split(' ')[0]}`;

  const badge = document.getElementById('dashTierBadge');
  if (badge) {
    badge.textContent  = App.userGrade === 1 ? '⚡ Premium' : '🎓 Student';
    badge.style.cssText = App.userGrade === 1
      ? 'background:rgba(108,99,255,0.2);color:var(--accent);border:1px solid rgba(108,99,255,0.3);border-radius:100px;padding:6px 14px;font-size:12px;font-weight:700'
      : 'background:rgba(56,189,248,0.1);color:#38BDF8;border:1px solid rgba(56,189,248,0.2);border-radius:100px;padding:6px 14px;font-size:12px;font-weight:700';
  }

  renderDashProfileCard();
  renderAggBanner();
  renderComboProbCards();
  renderLockedSections();
}

function renderDashProfileCard() {
  const card = document.getElementById('dashProfileCard');
  if (!card) return;
  const initials = App.profile.name
    ? App.profile.name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2)
    : (App.profile.email||'S')[0].toUpperCase();

  card.innerHTML = `
    <div class="dash-avatar">${initials}</div>
    <div class="dash-user-info">
      <div class="dash-user-name">${App.profile.name || 'Student'}</div>
      <div class="dash-user-meta">
        ${App.profile.email || ''}
        ${App.profile.mobile   ? ' · ' + App.profile.mobile   : ''}
        ${App.profile.category ? ' · ' + App.profile.category : ''}
      </div>
      <div class="dash-marks-chips">
        ${App.profile.maths     != null ? `<span class="mark-chip">Maths: ${App.profile.maths}</span>`     : ''}
        ${App.profile.physics   != null ? `<span class="mark-chip">Physics: ${App.profile.physics}</span>` : ''}
        ${App.profile.chemistry != null ? `<span class="mark-chip">Chem: ${App.profile.chemistry}</span>`  : ''}
        ${App.profile.maths == null
          ? `<span class="mark-chip" style="color:var(--warning)">⚠️ Add marks in Profile</span>` : ''}
        ${App.profile.marksLocked
          ? `<span class="mark-chip" style="color:var(--text-muted);border-color:rgba(245,158,11,0.3)">🔒 Marks locked</span>` : ''}
      </div>
    </div>`;
}

function renderAggBanner() {
  const banner = document.getElementById('dashAggBanner');
  if (!banner) return;
  const agg = calculateAggregate(
    App.profile.maths    || 0,
    App.profile.physics  || 0,
    App.profile.chemistry|| 0
  );
  const lockNote = App.profile.marksLocked
    ? `<div class="agg-lock-row">🔒 Marks locked ·
        ${App.userGrade === 1
          ? `<button class="link-btn" onclick="openMarksUpdate()">Update for ₹25 after board results</button>`
          : `<button class="link-btn" onclick="showUpgradeModal('marks-update')">Upgrade to Premium to update marks</button>`}
       </div>`
    : `<div style="font-size:13px;color:var(--text-muted);margin-top:6px">Marks will lock after first save</div>`;

  banner.innerHTML = `
    <div class="agg-main">
      <div class="agg-banner-label">Your TNEA Aggregate</div>
      <div class="agg-banner-value">${agg > 0 ? agg : '—'}</div>
      <div class="agg-banner-sub">Out of 200 · Maths + Physics + Chemistry</div>
      ${lockNote}
    </div>
    <div class="agg-formula">
      = (${App.profile.maths||'M'}/2) + (${App.profile.physics||'P'}/4) + (${App.profile.chemistry||'C'}/4) × 2
    </div>`;
}

function renderComboProbCards() {
  const grid = document.getElementById('comboProbGrid');
  if (!grid) return;
  const colleges = App.profile.preferredColleges;
  const courses  = App.profile.preferredCourses;

  if (!colleges.length || !courses.length) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:48px;color:var(--text-muted)">
        <div style="font-size:40px;margin-bottom:16px">🏛️</div>
        <p style="font-size:17px;font-weight:700;margin-bottom:8px;color:var(--text-dim)">No Preferences Added Yet</p>
        <p style="font-size:14px;margin-bottom:24px">
          Add your preferred colleges and courses in your profile to see all probability predictions
        </p>
        <button class="btn-primary" onclick="navigateTo('profile')">Add Preferences →</button>
      </div>`;
    return;
  }

  const agg = calculateAggregate(
    App.profile.maths    || 0,
    App.profile.physics  || 0,
    App.profile.chemistry|| 0
  );
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      combos.push({ college, course, prob: predictProbability(agg, college.name, course.name) });
    });
  });
  combos.sort((a,b) => b.prob - a.prob);

  grid.innerHTML = combos.map(combo => {
    const pc     = getProbClass(combo.prob);
    const cutoff = getLastYearCutoff(combo.college.name, combo.course.name);
    return `
      <div class="combo-card prob-${pc.cls}">
        <div class="combo-college">${combo.college.name}</div>
        <div class="combo-course">${combo.course.name}</div>
        <div class="combo-prob-bar-wrap">
          <div class="combo-prob-bar ${pc.barCls}" style="width:${combo.prob}%"></div>
        </div>
        <div class="combo-prob-row">
          <div>
            <div class="combo-prob-pct" style="color:${pc.cls==='high'?'var(--success)':pc.cls==='mid'?'var(--warning)':'var(--danger)'}">
              ${combo.prob}%
            </div>
            <div class="combo-prob-label">Probability · Cutoff: ${cutoff}</div>
          </div>
          <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
        </div>
      </div>`;
  }).join('');
}

function renderLockedSections() {
  const isPremium = App.userGrade === 1;
  document.getElementById('rankLockOverlay')       ?.style.setProperty('display', isPremium?'none':'flex');
  document.getElementById('choiceLockOverlay')     ?.style.setProperty('display', isPremium?'none':'flex');
  document.getElementById('counsellingLockOverlay')?.style.setProperty('display', isPremium?'none':'flex');
  if (isPremium) {
    renderRankCard();
    renderChoiceList();
    renderCounsellingSimulation();
  }
}

function renderRankCard() {
  const card = document.getElementById('dashRankCard');
  if (!card) return;
  const agg      = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const rankBand = predictRankBand(agg);
  const phase    = App.profile.rankPhase || 'pre';
  let verifyHtml = '';
  if (phase === 'post' && App.profile.rank) {
    const within = App.profile.rank >= rankBand.low && App.profile.rank <= rankBand.high;
    verifyHtml = within
      ? `<div style="margin-top:12px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:var(--success);padding:12px 16px;border-radius:8px;font-size:13px;font-weight:500">
           ✅ Rank #${App.profile.rank.toLocaleString()} verified — within predicted band
         </div>`
      : `<div style="margin-top:12px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:var(--danger);padding:12px 16px;border-radius:8px;font-size:13px;font-weight:500">
           ⚠️ Rank #${App.profile.rank.toLocaleString()} is outside predicted band
           (${rankBand.low.toLocaleString()}–${rankBand.high.toLocaleString()}). Model updating.
         </div>`;
  }
  card.innerHTML = `
    <div style="display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start">
      <div>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:6px">
          ${phase==='post' ? '🏆 Your Actual Rank' : '📊 Predicted Rank Band'}
        </div>
        <div style="font-size:36px;font-weight:900;color:var(--accent)">
          ${phase==='post' && App.profile.rank
            ? `#${App.profile.rank.toLocaleString()}`
            : agg > 0
              ? `${rankBand.low.toLocaleString()} – ${rankBand.high.toLocaleString()}`
              : 'Enter marks first'}
        </div>
        <div style="font-size:13px;color:var(--text-muted);margin-top:6px">
          Based on aggregate ${agg}/200 · TNEA 2024 model
        </div>
      </div>
      <div style="flex:1">
        ${verifyHtml}
        <div style="margin-top:12px;font-size:13px;color:var(--text-muted)">
          🔄 Probabilities update as more students submit marks
        </div>
      </div>
    </div>`;
}

function renderChoiceList() {
  const wrap = document.getElementById('choiceListWrap');
  if (!wrap) return;
  const colleges = App.profile.preferredColleges;
  const courses  = App.profile.preferredCourses;

  if (!colleges.length || !courses.length) {
    wrap.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted)">
      Add preferred colleges and courses in your profile to generate the AI Choice List
    </div>`;
    return;
  }

  const agg = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      combos.push({ college, course, prob: predictProbability(agg, college.name, course.name) });
    });
  });
  combos.sort((a,b) => b.prob - a.prob);

  const viable   = combos.filter(c => c.prob >= 35);
  const unlikely = combos.filter(c => c.prob <  35);

  wrap.innerHTML = `
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px;font-style:italic;padding:10px 14px;background:var(--surface2);border-radius:8px">
      🤖 AI-generated priority order based on your marks and TNEA 2021–2024 cutoff data.
      Submit your choices in this exact order for the best outcome.
    </div>
    ${viable.map((combo,idx) => {
      const pc = getProbClass(combo.prob);
      return `
        <div class="choice-item">
          <div class="choice-rank-num">${idx+1}</div>
          <div class="choice-info">
            <div class="choice-college">${combo.college.name}</div>
            <div class="choice-course">${combo.course.name}</div>
          </div>
          <div style="text-align:right">
            <div class="choice-prob" style="color:${combo.prob>=65?'var(--success)':'var(--warning)'}">
              ${combo.prob}%
            </div>
            <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
          </div>
        </div>`;
    }).join('')}
    ${unlikely.length > 0 ? `
      <div class="choice-no-chance">
        ⚠️ ${unlikely.length} combination${unlikely.length>1?'s':''} below 35% probability —
        you are unlikely to be allotted these with your current marks:<br/>
        <span style="font-size:12px;margin-top:6px;display:block">
          ${unlikely.map(c=>`${c.college.name} · ${c.course.name} (${c.prob}%)`).join(' | ')}
        </span>
      </div>` : ''}`;
}

function renderCounsellingSimulation() {
  const sim = document.getElementById('counsellingSim');
  if (!sim) return;
  const steps = [
    { icon:'📝', title:'Registration',         desc:'Online registration on tnea.ac.in with your board roll number, date of birth and marks.' },
    { icon:'✅', title:'Rank Publication',      desc:'TNEA publishes your rank. Compare it here against our AI prediction for accuracy.' },
    { icon:'📋', title:'Choice Filling',        desc:'Fill college-course choices in priority order. Use your AI Choice List above for best results.' },
    { icon:'🔒', title:'Choice Locking',        desc:'Lock your list before the deadline. No changes allowed after locking.' },
    { icon:'🏛️', title:'Round 1 Allotment',     desc:'Seats allotted based on rank and choices. AI predicts your most likely allotment.' },
    { icon:'🎯', title:'Acceptance / Upgrade',  desc:'Accept current seat or wait for Round 2 for a potentially better option.' },
    { icon:'🎓', title:'Reporting to College',  desc:'Report to allotted college with originals. Admission confirmed.' },
  ];
  sim.innerHTML = `
    <div class="sim-steps">
      ${steps.map((step,idx) => `
        <div class="sim-step ${idx===App.counsellingStep?'active':idx<App.counsellingStep?'done':''}">
          <div class="sim-step-icon">${idx<App.counsellingStep?'✅':step.icon}</div>
          <div>
            <div class="sim-step-title">Step ${idx+1}: ${step.title}</div>
            <div class="sim-step-desc">${step.desc}</div>
          </div>
        </div>`).join('')}
    </div>
    <div style="margin-top:20px;display:flex;align-items:center;gap:16px">
      ${App.counsellingStep < steps.length-1
        ? `<button class="btn-primary" onclick="advanceCounselling()">Simulate Next Step →</button>`
        : `<button class="btn-outline" onclick="resetCounselling()">🔄 Restart Simulation</button>`}
      <span style="font-size:13px;color:var(--text-muted)">
        Step ${App.counsellingStep+1} of ${steps.length}
      </span>
    </div>`;
}

function advanceCounselling() { App.counsellingStep++; renderCounsellingSimulation(); }
function resetCounselling()   { App.counsellingStep=0; renderCounsellingSimulation(); }

// ============================================================
// UPGRADE MODAL
// ============================================================
function showUpgradeModal(source) {
  const reasons = {
    'nav':          'Upgrade to Premium for rank prediction, AI Choice List and counselling simulation.',
    'rank':         '🏆 Rank Prediction & Verification requires Premium access.',
    'choice':       '📋 AI Choice List is a Premium-only feature.',
    'counselling':  '🎓 Full Counselling Simulation is available for Premium users only.',
    'result':       '🚀 See all 15 college-course combinations with detailed probabilities.',
    'tier':         'Get complete TNEA counselling intelligence for just ₹149.',
    'cta':          'Students with Premium made 3x better college choices.',
    'marks-update': '📝 Marks update after board results requires Premium access.',
  };
  const el = document.getElementById('upgradeReason');
  const sl = document.getElementById('slotsLeft');
  if (el) el.textContent = reasons[source] || 'Unlock full Premium access for ₹149.';
  if (sl) sl.textContent = App.slotsLeft;
  document.getElementById('upgradeModal')?.classList.remove('hidden');
}

function closeUpgradeModal() {
  document.getElementById('upgradeModal')?.classList.add('hidden');
}

function initiatePayment() {
  closeUpgradeModal();
  const agg     = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const content = document.getElementById('payConfirmContent');
  if (content) {
    content.innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr>
          <td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Name</td>
          <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.name||'—'}</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Email</td>
          <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.email||'—'}</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Mathematics</td>
          <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.maths??'—'} / 100</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Physics</td>
          <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.physics??'—'} / 100</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Chemistry</td>
          <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.chemistry??'—'} / 100</td>
        </tr>
        <tr>
          <td style="padding:14px 0;font-weight:700;font-size:15px">TNEA Aggregate</td>
          <td style="padding:14px 0;font-weight:900;color:var(--accent);font-size:24px;text-align:right">${agg>0?agg:'—'} / 200</td>
        </tr>
      </table>
      <div style="font-size:12px;color:var(--text-muted);margin-top:8px;text-align:center">
        Marks are locked after payment · Update costs ₹25
      </div>`;
  }
  document.getElementById('payConfirmModal')?.classList.remove('hidden');
}

function closePayConfirm() {
  document.getElementById('payConfirmModal')?.classList.add('hidden');
}

function confirmPayment() {
  closePayConfirm();
  // RAZORPAY PLACEHOLDER:
  // const options = {
  //   key: 'YOUR_RAZORPAY_KEY_ID',
  //   amount: 14900,
  //   currency: 'INR',
  //   name: 'PickMySeat.AI',
  //   description: 'Premium Access — One Time',
  //   handler: (response) => handlePaymentSuccess(response.razorpay_payment_id)
  // };
  // new Razorpay(options).open();
  handlePaymentSuccess('pay_demo_' + Date.now());
}

function handlePaymentSuccess(paymentId) {
  App.profile.hasPaid     = true;
  App.profile.marksLocked = true;
  App.userGrade           = 1;
  App.slotsLeft           = Math.max(0, App.slotsLeft - 1);
  // FIRESTORE: db.collection('users').doc(uid).update({ has_paid:true, paid_at:new Date(), razorpay_payment_id:paymentId })
  showToast('🎉 Premium unlocked! Welcome to full access.', 'success', 5000);
  setTimeout(() => navigateTo('dashboard'), 1000);
}

// ============================================================
// COOKIES
// ============================================================
function setCookie(name, value, days) {
  const exp = new Date();
  exp.setTime(exp.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${exp.toUTCString()};path=/`;
}

function getCookie(name) {
  const eq = name + '=';
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(eq))
    ?.substring(eq.length) || null;
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  navigateTo('landing');
  // FIREBASE: firebase.auth().onAuthStateChanged(user => { ... })
});