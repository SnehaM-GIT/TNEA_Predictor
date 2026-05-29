const icon = {
  dashboard: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 13h8V3H3v10Z"/><path d="M13 21h8V11h-8v10Z"/><path d="M13 3v6h8V3h-8Z"/><path d="M3 21h8v-6H3v6Z"/></svg>`,
  play: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m8 5 11 7-11 7V5Z"/></svg>`,
  chart: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-7"/></svg>`,
  heart: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7 7-7Z"/></svg>`,
  user: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21a7 7 0 0 0-14 0"/><circle cx="12" cy="7" r="4"/></svg>`,
  book: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/></svg>`,
  trophy: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v4a5 5 0 0 1-10 0V4Z"/><path d="M5 5H2v2a4 4 0 0 0 4 4"/><path d="M19 5h3v2a4 4 0 0 1-4 4"/></svg>`,
  clock: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`,
  star: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 21l1.1-6.5-4.7-4.6 6.5-.9L12 3Z"/></svg>`,
  wallet: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V8H5a2 2 0 0 1 0-4h14v4"/><path d="M4 6v14h16v-4"/><path d="M18 12h4v4h-4a2 2 0 0 1 0-4Z"/></svg>`,
  check: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m20 6-11 11-5-5"/></svg>`,
  arrow: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>`,
  upload: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/></svg>`,
  shield: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3v8Z"/></svg>`
};

const courses = ["Engineering", "Architecture", "Design", "Science", "Commerce", "Management", "Agriculture", "Pharmacy", "Law", "Medical"];
const baseColleges = [
  { id: 1, name: "Anna University, Chennai", branch: "Computer Science", cutoff: 197.5, chance: "Reach", score: 92 },
  { id: 2, name: "MIT Campus, Chennai", branch: "Electronics & Communication", cutoff: 194.25, chance: "Target", score: 88 },
  { id: 3, name: "College of Engineering, Guindy", branch: "Mechanical Engineering", cutoff: 188, chance: "Target", score: 83 },
  { id: 4, name: "PSG College of Technology", branch: "Information Technology", cutoff: 190, chance: "Target", score: 81 },
  { id: 5, name: "SSN College of Engineering", branch: "Computer Science", cutoff: 187.5, chance: "Safe", score: 78 },
  { id: 6, name: "Thiagarajar College of Engineering", branch: "Civil Engineering", cutoff: 176.5, chance: "Safe", score: 70 }
];

const state = {
  view: "dashboard",
  step: 0,
  paid: false,
  profile: {
    name: "",
    email: "",
    phone: "",
    state: "Tamil Nadu",
    stream: "Computer Science",
    maths: 96,
    physics: 94,
    chemistry: 91,
    overall: 93,
    category: "OC"
  },
  courses: ["Engineering"],
  choices: [1, 2, 3],
  prediction: null,
  saved: []
};

function $(selector) {
  return document.querySelector(selector);
}

function render() {
  document.getElementById("app").innerHTML = `
    <div class="app-shell">
      ${sidebar()}
      <main class="main">
        <div class="topbar">
          <span class="crumb">${icon.dashboard}<span>${labelForView()}</span></span>
          <div class="user-pill"><span>${state.paid ? "Premium active" : "Free preview"}</span><span class="avatar">${initials()}</span></div>
        </div>
        <div class="content">${views[state.view]()}</div>
      </main>
    </div>
  `;
  bind();
}

function labelForView() {
  return {
    dashboard: "Dashboard",
    predictor: "Rank Predictor",
    counselling: "Mock Counselling",
    progress: "Progress",
    saved: "Saved Choices",
    profile: "Profile"
  }[state.view];
}

function initials() {
  return state.profile.name ? state.profile.name.split(" ").map(part => part[0]).slice(0, 2).join("").toUpperCase() : "PS";
}

function sidebar() {
  const nav = [
    ["dashboard", icon.dashboard, "Overview"],
    ["predictor", icon.chart, "Predict"],
    ["counselling", icon.play, "Counselling"],
    ["progress", icon.trophy, "Progress"],
    ["saved", icon.heart, "Saved Choices"],
    ["profile", icon.user, "Profile"]
  ];
  return `
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">${icon.book}</span><span>PickMySeat.AI</span></div>
      <nav class="nav">
        ${nav.map(([key, svg, label]) => `<button class="${state.view === key ? "active" : ""}" data-view="${key}"><span class="nav-icon">${svg}</span>${label}</button>`).join("")}
      </nav>
    </aside>
  `;
}

const views = {
  dashboard() {
    return `
      <section class="hero">
        <div>
          <h1>Welcome to PickMySeat.AI</h1>
          <p>AI-powered TNEA rank prediction, cutoff trends, premium recommendations, and mock counselling.</p>
        </div>
        <div class="hero-icon">${icon.user}</div>
      </section>
      <section class="stats-grid">
        ${stat("Simulations", "3", icon.play, "")}
        ${stat("Predictions", state.prediction ? "1" : "0", icon.clock, "green")}
        ${stat("Model Confidence", "94%", icon.chart, "violet")}
        ${stat("Plan", state.paid ? "Paid" : "Free", icon.star, "orange")}
      </section>
      <section class="layout-grid">
        <div class="panel panel-pad">
          <div class="section-title">
            <div><h2>Counselling Simulations</h2><p>Walk through the TNEA flow before the real window opens.</p></div>
          </div>
          <div class="simulation-list">
            ${simulation("TNEA Counselling", "Tamil Nadu Engineering Admissions counselling process simulation", "2.5L+", "45 mins", "Intermediate", "4.7", "counselling", icon.book)}
            ${simulation("Rank & Seat Allotment", "Rank list, choice locking, tentative allotment, confirmation, and reporting", "1.8L+", "30 mins", "Guided", "4.8", "progress", icon.trophy)}
            ${simulation("Trend Analysis", "Year-on-year cutoff movement and safer branch targeting", "50K+", "12 mins", "Easy", "4.6", "predictor", icon.chart)}
          </div>
        </div>
        <div class="panel panel-pad">
          <div class="section-title"><div><h2>Premium Gate</h2><p>Matches the PDF flow: free preview, then Rs.149 unlock.</p></div></div>
          ${paywallBlock()}
        </div>
      </section>
    `;
  },

  predictor() {
    return wizard();
  },

  counselling() {
    return `
      <div class="wizard-wrap">
        ${counsellingProgress(1)}
        <section class="wizard-card">
          <div class="wizard-head">
            <div class="wizard-icon" style="color: var(--rose); background:#fce7f3">${icon.heart}</div>
            <div class="wizard-title"><h1>Choice Filling - Round 1</h1><p>Fill college and branch preferences. Order matters.</p></div>
          </div>
          <div class="choice-board">
            <div>
              <div class="section-title"><h2>Available Colleges & Branches</h2><span class="badge warn">Cutoff aware</span></div>
              <div class="choice-pool choice-list">${baseColleges.map(choicePoolRow).join("")}</div>
            </div>
            <div>
              <div class="section-title"><h2>Your Choices</h2><span class="badge blue">${state.choices.length} selected</span></div>
              <div class="choice-list">${state.choices.length ? state.choices.map((id, index) => selectedChoiceRow(id, index)).join("") : `<div class="empty">No choices added yet.</div>`}</div>
            </div>
          </div>
          <div class="notice">
            <h3>Important strategy tips</h3>
            <ul>
              <li>Order preferences from most desired to safest option.</li>
              <li>Mix reach, target, and safe choices for better outcomes.</li>
              <li>Lock choices only after checking cutoff trend movement.</li>
            </ul>
          </div>
          <div class="actions"><button class="secondary" data-view="predictor">Previous</button><button class="primary" data-view="progress">Lock Choices ${icon.arrow}</button></div>
        </section>
      </div>
    `;
  },

  progress() {
    const rank = state.prediction?.rank || 10848;
    return `
      <div class="wizard-wrap">
        ${preCounsellingProgress()}
        <section class="wizard-card">
          <div class="wizard-head">
            <div class="wizard-icon" style="background:#fef3c7;color:#b45309">${icon.user}</div>
            <div class="wizard-title"><h1>Rank List Publication</h1><p>Your rank has been calculated and published.</p></div>
          </div>
          <div class="rank-card">
            <span>Your TNEA Rank</span>
            <strong>${rank.toLocaleString("en-IN")}</strong>
            <span>Based on 12th standard marks, category, selected courses, and cutoff history.</span>
          </div>
          <div class="panel panel-pad" style="margin-top:18px;box-shadow:none;background:#eff6ff;border-color:#bfdbfe">
            <h3 style="margin-top:0;color:var(--blue)">Grievance Redressal</h3>
            <p style="color:#475569">You have one week to raise grievances regarding rank details before counselling rounds begin.</p>
            <button class="ghost">Raise Grievance</button>
          </div>
          <div class="actions"><button class="secondary" data-view="counselling">Previous</button><button class="primary" data-view="saved">Start Seat Allotment ${icon.arrow}</button></div>
        </section>
      </div>
    `;
  },

  saved() {
    const saved = state.saved.length ? state.saved : state.choices;
    return `
      <section class="panel panel-pad">
        <div class="section-title">
          <div><h2>Saved Choices</h2><p>Prediction-backed shortlist ready for real counselling.</p></div>
          <button class="primary" data-save-all>Save Current Choices</button>
        </div>
        <div class="college-list">
          ${saved.length ? saved.map(id => {
            const college = baseColleges.find(item => item.id === id);
            return `<article class="history-row"><span class="tile-icon">${icon.book}</span><div><h3>${college.name} - ${college.branch}</h3><p>Cutoff ${college.cutoff} • ${college.chance} • ${college.score}% fit score</p></div><button class="danger-lite" data-remove-saved="${id}">Remove</button></article>`;
          }).join("") : `<div class="empty">Your saved list is empty.</div>`}
        </div>
      </section>
    `;
  },

  profile() {
    return `
      <section class="panel panel-pad">
        <div class="section-title"><div><h2>Profile</h2><p>Stored like the Firebase user document described in the technical plan.</p></div><span class="badge ${state.paid ? "" : "warn"}">${state.paid ? "has_paid: true" : "has_paid: false"}</span></div>
        <div class="profile-grid">
          ${profileCard("Student", state.profile.name || "Not added", icon.user)}
          ${profileCard("Email", state.profile.email || "Not added", icon.wallet)}
          ${profileCard("Category", state.profile.category, icon.shield)}
          ${profileCard("Courses", state.courses.join(", "), icon.book)}
          ${profileCard("Marks", `${state.profile.maths}/${state.profile.physics}/${state.profile.chemistry}`, icon.chart)}
          ${profileCard("Payment", state.paid ? "Rs.149 paid" : "Pending", icon.check)}
        </div>
      </section>
    `;
  }
};

function stat(label, value, svg, tone) {
  return `<article class="stat"><div><small>${label}</small><strong>${value}</strong></div><span class="tile-icon ${tone}">${svg}</span></article>`;
}

function simulation(title, desc, participants, duration, difficulty, rating, target, svg) {
  return `
    <article class="simulation">
      <span class="tile-icon">${svg}</span>
      <div>
        <h3>${title}</h3><p>${desc}</p>
        <div class="mini-meta"><span>Participants <b>${participants}</b></span><span>Duration <b style="color:#16a34a">${duration}</b></span><span>Difficulty <b style="color:#ea580c">${difficulty}</b></span><span>Rating <b>${rating}</b></span></div>
      </div>
      <button class="link-btn" data-view="${target}">Start ${icon.arrow}</button>
    </article>
  `;
}

function paywallBlock() {
  if (state.paid) {
    return `<div class="paywall"><span class="badge">Premium unlocked</span><h3>Full predictions are active</h3><p>Rank bands, top colleges, trend charts, saved choices, and counselling simulation are available.</p><button class="primary" data-view="predictor">Run Prediction</button></div>`;
  }
  return `<div class="paywall"><span class="badge warn">Rs.149 one-time</span><h3>Unlock complete TNEA prediction</h3><p>The free tier previews flow and trends. Payment unlocks full college cards and choice prioritization.</p><button class="primary" data-pay>${icon.wallet} Pay and Unlock</button></div>`;
}

function wizard() {
  const steps = ["Personal Info", "Academic Details", "Course Preferences", "Prediction Results", "Paywall"];
  return `
    <div class="wizard-wrap">
      <div class="progress-line"><div class="progress-fill" style="width:${((state.step + 1) / steps.length) * 100}%"></div></div>
      <section class="wizard-card">
        ${wizardStep()}
      </section>
    </div>
  `;
}

function wizardStep() {
  const stepMap = [personalStep, academicStep, courseStep, resultStep, paywallStep];
  return stepMap[state.step]();
}

function personalStep() {
  return `
    <div class="wizard-head"><div class="wizard-icon">${icon.user}</div><div class="wizard-title"><h1>Personal Information</h1><p>Minimal data collection to start your prediction.</p></div></div>
    <div class="form-grid">
      ${input("name", "Full Name", "Enter your full name", state.profile.name)}
      ${input("email", "Email Address", "Enter your email", state.profile.email, "email")}
      ${input("phone", "Phone Number", "Enter your phone number", state.profile.phone)}
      ${select("state", "State", ["Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh"], state.profile.state)}
    </div>
    ${wizardActions(false, "Next")}
  `;
}

function academicStep() {
  return `
    <div class="wizard-head"><div class="wizard-icon" style="background:#dcfce7;color:#16a34a">${icon.book}</div><div class="wizard-title"><h1>Academic Details</h1><p>Tell us about your 12th grade performance.</p></div></div>
    <div class="form-grid">
      ${select("stream", "12th Stream", ["Computer Science", "Bio Maths", "Pure Science", "Vocational"], state.profile.stream)}
      ${select("category", "Community Category", ["OC", "BC", "BCM", "MBC", "SC", "ST"], state.profile.category)}
      ${input("maths", "Maths Marks", "100", state.profile.maths, "number")}
      ${input("physics", "Physics Marks", "100", state.profile.physics, "number")}
      ${input("chemistry", "Chemistry Marks", "100", state.profile.chemistry, "number")}
      ${input("overall", "Overall Percentage", "Enter overall percentage", state.profile.overall, "number")}
    </div>
    ${wizardActions(true, "Next")}
  `;
}

function courseStep() {
  return `
    <div class="wizard-head"><div class="wizard-title"><h1>Course Preferences</h1><p>Select your preferred courses. Multiple selection is allowed.</p></div></div>
    <div class="course-grid">
      ${courses.map(course => `<button class="course ${state.courses.includes(course) ? "selected" : ""}" data-course="${course}">${course}</button>`).join("")}
    </div>
    ${wizardActions(true, "Predict Rank")}
  `;
}

function resultStep() {
  const prediction = getPrediction();
  const hidden = !state.paid;
  return `
    <div class="wizard-head"><div class="wizard-icon" style="background:#dbeafe;color:var(--blue)">${icon.chart}</div><div class="wizard-title"><h1>Prediction Results</h1><p>Rank band, trend analysis, and college recommendations from cutoff history.</p></div></div>
    <div class="result-grid">
      <div>
        <div class="rank-card"><span>Predicted TNEA Rank Band</span><strong>${prediction.low.toLocaleString("en-IN")} - ${prediction.high.toLocaleString("en-IN")}</strong><span>Estimated aggregate: ${prediction.aggregate}/200</span></div>
        <div class="panel panel-pad" style="margin-top:18px;box-shadow:none">
          <h3 style="margin-top:0">Cutoff Trend</h3>
          <div class="chart">${[2021, 2022, 2023, 2024].map((year, i) => `<div class="bar"><span style="height:${70 + i * 8}%"></span><b>${year}</b></div>`).join("")}</div>
        </div>
      </div>
      <div>
        <div class="section-title"><h2>Recommended Colleges</h2><span class="badge ${hidden ? "warn" : ""}">${hidden ? "Premium locked" : "Top 5"}</span></div>
        <div class="college-list">
          ${baseColleges.slice(0, 5).map((college, index) => collegeRow(college, hidden && index > 1)).join("")}
        </div>
      </div>
    </div>
    <div class="actions"><button class="secondary" data-prev>Previous</button>${state.paid ? `<button class="primary" data-view="counselling">Continue to Choice Filling ${icon.arrow}</button>` : `<button class="primary" data-next>Unlock Full Results ${icon.arrow}</button>`}</div>
  `;
}

function paywallStep() {
  return `
    <div class="wizard-head"><div class="wizard-icon" style="background:#fef3c7;color:#b45309">${icon.wallet}</div><div class="wizard-title"><h1>Unlock Premium Prediction</h1><p>One-time Rs.149 payment unlocks full college recommendations and saved counselling choices.</p></div></div>
    <div style="max-width:620px;margin:0 auto">${paywallBlock()}</div>
    <div class="actions"><button class="secondary" data-prev>Previous</button><button class="ghost" data-view="dashboard">Back to Dashboard</button></div>
  `;
}

function input(key, label, placeholder, value, type = "text") {
  return `<label>${label}<input data-field="${key}" type="${type}" placeholder="${placeholder}" value="${value ?? ""}" /></label>`;
}

function select(key, label, options, selected) {
  return `<label>${label}<select data-field="${key}">${options.map(option => `<option ${option === selected ? "selected" : ""}>${option}</option>`).join("")}</select></label>`;
}

function wizardActions(canPrev, nextText) {
  return `<div class="actions"><button class="secondary" ${canPrev ? "data-prev" : "disabled"}>Previous</button><button class="primary" data-next>${nextText} ${icon.arrow}</button></div>`;
}

function getPrediction() {
  const aggregate = Number(((Number(state.profile.maths) / 2) + (Number(state.profile.physics) / 4) + (Number(state.profile.chemistry) / 4) + Number(state.profile.overall)).toFixed(1));
  const base = Math.max(850, Math.round(52000 - aggregate * 210 - (state.profile.category === "OC" ? 0 : 2500)));
  state.prediction = { aggregate, low: Math.max(1, base - 850), high: base + 1200, rank: base };
  return state.prediction;
}

function collegeRow(college, locked) {
  return `
    <article class="college" style="${locked ? "filter:blur(2px);opacity:.58" : ""}">
      <span class="tile-icon ${college.chance === "Safe" ? "green" : ""}">${icon.book}</span>
      <div><h3>${locked ? "Premium College Match" : `${college.name} - ${college.branch}`}</h3><p>${locked ? "Unlock to view cutoff, branch, and admission chance." : `Cutoff ${college.cutoff} • ${college.chance} chance • ${college.score}% fit score`}</p></div>
      <button class="link-btn" ${locked ? "data-next" : `data-add-choice="${college.id}"`}>${locked ? "Unlock" : "Add"} ${icon.arrow}</button>
    </article>
  `;
}

function counsellingProgress(active) {
  const items = ["Choice Filling", "Seat Allotment", "Confirmation", "Reporting"];
  return `<div style="display:flex;justify-content:space-between;margin-bottom:10px;color:#475569;font-weight:800"><span>Round 1 Counselling - Step ${active} of 4</span><span>${active * 25 + 42}% Complete</span></div><div class="progress-line"><div class="progress-fill" style="width:${active * 25 + 42}%"></div></div><div class="progress-strip">${items.map((item, index) => `<div class="step-pill ${index + 1 === active ? "active" : index + 1 < active ? "done" : ""}">${item}<br><small>${["Fill college and branch preferences", "Seat based on rank and choices", "Confirm allotted seat", "Report to college or TFC"][index]}</small></div>`).join("")}</div>`;
}

function preCounsellingProgress() {
  const items = ["Registration", "Application & Upload", "Random Number", "Verification", "Rank List"];
  return `<div style="display:flex;justify-content:space-between;margin-bottom:10px;color:#475569;font-weight:800"><span>Pre-Counselling - Step 5 of 5</span><span>100% Complete</span></div><div class="progress-line"><div class="progress-fill" style="width:100%;background:linear-gradient(90deg,#22c55e,#0f9f8f)"></div></div><div class="progress-strip">${items.map(item => `<div class="step-pill done">${item}<br><small>Completed</small></div>`).join("")}</div>`;
}

function choicePoolRow(college) {
  const already = state.choices.includes(college.id);
  return `<article class="choice-row"><div><h3>${college.name} - ${college.branch}</h3><p>Cutoff ${college.cutoff} | Your fit: ${college.score}% | ${college.chance}</p></div><button class="${already ? "secondary" : "ghost"}" data-add-choice="${college.id}" ${already ? "disabled" : ""}>${already ? "Added" : "Add"}</button></article>`;
}

function selectedChoiceRow(id, index) {
  const college = baseColleges.find(item => item.id === id);
  return `<article class="choice-row your-choice"><div><h3>#${index + 1} ${college.name} - ${college.branch}</h3><p>${college.chance} choice • ${college.score}% fit score</p></div><div class="choice-actions"><button class="square-btn" title="Move up" data-move-up="${id}">↑</button><button class="square-btn" title="Move down" data-move-down="${id}">↓</button><button class="square-btn" title="Remove" data-remove-choice="${id}">×</button></div></article>`;
}

function profileCard(label, value, svg) {
  return `<article class="stat"><div><small>${label}</small><strong style="font-size:18px">${value}</strong></div><span class="tile-icon">${svg}</span></article>`;
}

function bind() {
  document.querySelectorAll("[data-view]").forEach(button => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      render();
    });
  });
  document.querySelectorAll("[data-field]").forEach(field => {
    field.addEventListener("input", () => {
      state.profile[field.dataset.field] = field.value;
    });
  });
  document.querySelectorAll("[data-next]").forEach(button => button.addEventListener("click", () => {
    if (state.step === 2) getPrediction();
    state.step = Math.min(4, state.step + 1);
    render();
  }));
  document.querySelectorAll("[data-prev]").forEach(button => button.addEventListener("click", () => {
    state.step = Math.max(0, state.step - 1);
    render();
  }));
  document.querySelectorAll("[data-course]").forEach(button => button.addEventListener("click", () => {
    const course = button.dataset.course;
    state.courses = state.courses.includes(course) ? state.courses.filter(item => item !== course) : [...state.courses, course];
    if (!state.courses.length) state.courses = ["Engineering"];
    render();
  }));
  document.querySelectorAll("[data-pay]").forEach(button => button.addEventListener("click", () => {
    state.paid = true;
    state.step = 3;
    render();
  }));
  document.querySelectorAll("[data-add-choice]").forEach(button => button.addEventListener("click", () => {
    const id = Number(button.dataset.addChoice);
    if (!state.choices.includes(id)) state.choices.push(id);
    render();
  }));
  document.querySelectorAll("[data-remove-choice]").forEach(button => button.addEventListener("click", () => {
    state.choices = state.choices.filter(id => id !== Number(button.dataset.removeChoice));
    render();
  }));
  document.querySelectorAll("[data-move-up]").forEach(button => button.addEventListener("click", () => moveChoice(Number(button.dataset.moveUp), -1)));
  document.querySelectorAll("[data-move-down]").forEach(button => button.addEventListener("click", () => moveChoice(Number(button.dataset.moveDown), 1)));
  document.querySelectorAll("[data-save-all]").forEach(button => button.addEventListener("click", () => {
    state.saved = [...state.choices];
    render();
  }));
  document.querySelectorAll("[data-remove-saved]").forEach(button => button.addEventListener("click", () => {
    state.saved = (state.saved.length ? state.saved : state.choices).filter(id => id !== Number(button.dataset.removeSaved));
    render();
  }));
}

function moveChoice(id, direction) {
  const index = state.choices.indexOf(id);
  const next = index + direction;
  if (index < 0 || next < 0 || next >= state.choices.length) return;
  [state.choices[index], state.choices[next]] = [state.choices[next], state.choices[index]];
  render();
}

render();