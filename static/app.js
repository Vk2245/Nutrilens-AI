/* NutriLens AI — Frontend Application Logic */

const API = '';
let currentUser = null;
let selectedImage = null;
let currentLang = 'en';

// ─── Tab Navigation ───
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => { n.classList.remove('active'); n.removeAttribute('aria-current'); });
  document.getElementById(tabId).classList.add('active');
  const navBtn = document.querySelector(`[data-tab="${tabId}"]`);
  if (navBtn) { navBtn.classList.add('active'); navBtn.setAttribute('aria-current', 'page'); }
  if (tabId === 'tabExplore') loadExploreData();
  if (tabId === 'tabDashboard') loadDashboard();
}

// ─── Auth ───
async function handleSignIn() {
  try {
    const resp = await fetch(`${API}/api/v1/auth/demo-login`);
    const data = await resp.json();
    currentUser = data;
    document.getElementById('btnSignIn').classList.add('hidden');
    const avatar = document.getElementById('userAvatar');
    avatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(data.name)}&background=00BFA5&color=000&bold=true`;
    avatar.classList.remove('hidden');
    announce(`Signed in as ${data.name}`);
    loadDashboard();
  } catch (e) { console.error('Sign-in error:', e); }
}

// ─── Dashboard ───
async function loadDashboard() {
  try {
    const resp = await fetch(`${API}/api/v1/dashboard/daily`);
    const data = await resp.json();
    const log = data.daily_log || {};
    const profile = data.profile || {};
    const meals = log.meals || [];

    // Update greeting
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
    const name = profile.name || 'there';
    document.getElementById('greetingText').textContent = `${greeting}, ${name}! 👋`;

    // Stats
    const totalCal = Math.round(log.total_calories || 0);
    const avgScore = Math.round(log.avg_health_score || 0);
    const streak = log.streak_count || 0;
    document.getElementById('statCal').textContent = totalCal;
    document.getElementById('statScore').textContent = avgScore;
    document.getElementById('statStreak').textContent = `🔥 ${streak}`;
    document.getElementById('statMeals').textContent = meals.length;

    // Donut chart
    const goal = profile.calorie_goal || log.calorie_goal || 1800;
    document.getElementById('donutCal').textContent = totalCal;
    document.getElementById('donutGoal').textContent = goal;
    drawDonut(totalCal, goal);

    // Macro bars
    const targets = { protein: 50, carbs: 250, fat: 65, fiber: 25 };
    updateMacro('Protein', log.total_protein_g || 0, targets.protein);
    updateMacro('Carbs', log.total_carbs_g || 0, targets.carbs);
    updateMacro('Fat', log.total_fat_g || 0, targets.fat);
    updateMacro('Fiber', log.total_fiber_g || 0, targets.fiber);

    // Meal list
    const mealList = document.getElementById('mealList');
    if (meals.length > 0) {
      const emojis = { breakfast: '🥣', lunch: '🍛', dinner: '🍽️', snack: '🥗' };
      mealList.innerHTML = meals.map(m => `
        <div class="meal-item">
          <span class="meal-emoji">${emojis[m.meal_type] || '🍽️'}</span>
          <div class="meal-info">
            <div class="meal-name">${m.dish_name}</div>
            <div class="meal-meta">${m.meal_type || 'Meal'} · ${Math.round(m.calories_kcal)} kcal</div>
          </div>
          <div class="meal-score">${m.health_score}</div>
        </div>
      `).join('');
    }

    // Load nudge
    loadNudge();
  } catch (e) { console.error('Dashboard load error:', e); }
}

function updateMacro(name, value, target) {
  const key = name.toLowerCase();
  const pct = Math.min(100, (value / target) * 100);
  const bar = document.getElementById(`bar${name === 'Carbs' ? 'Carbs' : name === 'Fat' ? 'Fat' : name === 'Fiber' ? 'Fiber' : 'Protein'}`);
  const val = document.getElementById(`val${name === 'Carbs' ? 'Carbs' : name === 'Fat' ? 'Fat' : name === 'Fiber' ? 'Fiber' : 'Protein'}`);
  if (bar) bar.style.width = `${pct}%`;
  if (val) val.textContent = `${Math.round(value)}g`;
}

function drawDonut(current, goal) {
  const canvas = document.getElementById('donutCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const size = 180;
  canvas.width = size * 2; canvas.height = size * 2;
  ctx.scale(2, 2);
  const cx = size / 2, cy = size / 2, r = 70, lw = 14;
  const pct = Math.min(1, current / goal);

  // Background ring
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,255,255,0.06)'; ctx.lineWidth = lw; ctx.stroke();

  // Progress ring
  const start = -Math.PI / 2;
  const end = start + pct * Math.PI * 2;
  ctx.beginPath(); ctx.arc(cx, cy, r, start, end);
  const grad = ctx.createLinearGradient(0, 0, size, size);
  if (pct > 0.9) { grad.addColorStop(0, '#FF5252'); grad.addColorStop(1, '#FF8A80'); }
  else { grad.addColorStop(0, '#00BFA5'); grad.addColorStop(1, '#1DE9B6'); }
  ctx.strokeStyle = grad; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();
}

async function loadNudge() {
  try {
    const resp = await fetch(`${API}/api/v1/coach/nudge`);
    const data = await resp.json();
    if (data.message) {
      document.getElementById('nudgeText').innerHTML = `<strong>${data.time_context}</strong> ${data.message}`;
    }
  } catch (e) { /* non-critical */ }
}

// ─── Snap & Know ───
function handleImageSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  selectedImage = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById('previewImg');
    preview.src = e.target.result;
    preview.classList.remove('hidden');
    document.getElementById('cameraIcon').classList.add('hidden');
    document.getElementById('btnAnalyze').disabled = false;
  };
  reader.readAsDataURL(file);
}

async function analyzeFood() {
  if (!selectedImage) return;
  showLoading('Analyzing your food with Gemini AI...');
  try {
    const formData = new FormData();
    formData.append('image', selectedImage);
    formData.append('user_id', currentUser?.user_id || 'demo-user-nutrilens');
    formData.append('meal_type', guessMealType());

    const resp = await fetch(`${API}/api/v1/nutrition/analyze`, { method: 'POST', body: formData });
    const result = await resp.json();
    displayResult(result);
    announce(`Analysis complete: ${result.dish_name}, Health Score ${result.health_score} out of 100`);
    // Refresh dashboard data
    loadDashboard();
  } catch (e) {
    console.error('Analysis error:', e);
    hideLoading();
  }
}

async function analyzeText() {
  const desc = document.getElementById('foodDescription').value.trim();
  if (!desc) return;
  showLoading('Analyzing with Gemini AI...');
  try {
    const resp = await fetch(`${API}/api/v1/nutrition/analyze-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: desc }),
    });
    const result = await resp.json();
    displayResult(result);
    announce(`Analysis complete: ${result.dish_name}, Health Score ${result.health_score} out of 100`);
    loadDashboard();
  } catch (e) {
    console.error('Text analysis error:', e);
    hideLoading();
  }
}

function displayResult(r) {
  hideLoading();
  const scoreClass = r.health_score >= 70 ? 'score-high' : r.health_score >= 40 ? 'score-mid' : 'score-low';
  const container = document.getElementById('analysisResult');
  container.classList.remove('hidden');
  container.innerHTML = `
    <div class="result-card">
      <div class="result-dish">${r.dish_name}</div>
      <div class="result-score-wrap">
        <div class="health-score-circle ${scoreClass}">${r.health_score}</div>
        <div>
          <div class="result-cal">${Math.round(r.calories_kcal)} kcal <span>· ${r.portion_size || '1 serving'}</span></div>
          <div style="font-size:0.75rem;color:var(--text-muted);">${r.cuisine || 'Indian'} · Confidence: ${Math.round((r.confidence || 0.85) * 100)}%</div>
        </div>
      </div>
      <div class="result-explanation">${r.explanation || ''}</div>
      <div class="macro-bars" style="margin-bottom:16px;">
        <div class="macro-row"><span class="macro-label">Protein</span><div class="macro-bar-bg"><div class="macro-bar protein" style="width:${Math.min(100, (r.macros?.protein_g || 0) / 50 * 100)}%"></div></div><span class="macro-val">${Math.round(r.macros?.protein_g || 0)}g</span></div>
        <div class="macro-row"><span class="macro-label">Carbs</span><div class="macro-bar-bg"><div class="macro-bar carbs" style="width:${Math.min(100, (r.macros?.carbohydrates_g || 0) / 250 * 100)}%"></div></div><span class="macro-val">${Math.round(r.macros?.carbohydrates_g || 0)}g</span></div>
        <div class="macro-row"><span class="macro-label">Fat</span><div class="macro-bar-bg"><div class="macro-bar fat" style="width:${Math.min(100, (r.macros?.fat_g || 0) / 65 * 100)}%"></div></div><span class="macro-val">${Math.round(r.macros?.fat_g || 0)}g</span></div>
        <div class="macro-row"><span class="macro-label">Fiber</span><div class="macro-bar-bg"><div class="macro-bar fiber" style="width:${Math.min(100, (r.macros?.fiber_g || 0) / 25 * 100)}%"></div></div><span class="macro-val">${Math.round(r.macros?.fiber_g || 0)}g</span></div>
      </div>
      ${r.micronutrient_highlights?.length ? `<div style="margin-bottom:12px;"><span style="font-size:0.8rem;color:var(--text-secondary);">Micronutrients: </span>${r.micronutrient_highlights.map(m => `<span class="alt-tag" style="background:rgba(64,196,255,0.1);border-color:rgba(64,196,255,0.2);color:var(--accent-blue);">${m}</span>`).join('')}</div>` : ''}
      ${r.healthier_alternatives?.length ? `<div class="alternatives"><span style="font-size:0.8rem;color:var(--text-secondary);">Healthier alternatives: </span>${r.healthier_alternatives.map(a => `<span class="alt-tag">${a}</span>`).join('')}</div>` : ''}
    </div>`;
}

function guessMealType() {
  const h = new Date().getHours();
  if (h < 11) return 'breakfast';
  if (h < 15) return 'lunch';
  if (h < 18) return 'snack';
  return 'dinner';
}

// ─── Coach ───
async function sendCoachMessage() {
  const input = document.getElementById('coachInput');
  const query = input.value.trim();
  if (!query) return;
  input.value = '';
  addMessage(query, 'user');
  await askCoach(query);
}

async function askCoach(query) {
  addMessage(query, 'user', true);
  const msgs = document.getElementById('coachMessages');
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'msg bot';
  loadingDiv.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;"></div>';
  msgs.appendChild(loadingDiv);
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const resp = await fetch(`${API}/api/v1/coach/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language: currentLang, include_audio: false }),
    });
    const data = await resp.json();
    loadingDiv.remove();
    addMessage(data.response_text, 'bot');

    if (data.suggestions?.length) {
      const sugDiv = document.getElementById('coachSuggestions');
      sugDiv.innerHTML = data.suggestions.map(s => `<button class="suggestion-chip" onclick="askCoach(this.textContent)">${s}</button>`).join('');
    }
  } catch (e) {
    loadingDiv.remove();
    addMessage("I'm having trouble connecting right now. Please try again!", 'bot');
  }
}

function addMessage(text, type, skipIfUser) {
  if (skipIfUser && type === 'user') {
    // Check if last message is already this text
    const msgs = document.getElementById('coachMessages');
    const last = msgs.lastElementChild;
    if (last && last.classList.contains('user') && last.textContent === text) return;
  }
  const msgs = document.getElementById('coachMessages');
  const div = document.createElement('div');
  div.className = `msg ${type}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

let mediaRecorder = null;
let audioChunks = [];

function toggleVoiceInput() {
  const btn = document.getElementById('btnMic');
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    btn.classList.remove('recording');
    return;
  }
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        addMessage('🎤 Voice message sent...', 'user');
        try {
          const resp = await fetch(`${API}/api/v1/coach/voice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio_base64: base64, language: currentLang }),
          });
          const data = await resp.json();
          addMessage(data.response_text, 'bot');
        } catch (e) { addMessage("Voice processing failed. Try typing instead!", 'bot'); }
      };
      reader.readAsDataURL(blob);
    };
    mediaRecorder.start();
    btn.classList.add('recording');
    announce('Recording started. Tap microphone again to stop.');
  }).catch(() => addMessage("Microphone access denied. Please enable it in settings.", 'bot'));
}

// ─── Explore ───
async function loadExploreData() {
  loadRestaurants();
  loadRecipes();
}

async function loadRestaurants() {
  try {
    const resp = await fetch(`${API}/api/v1/explore/restaurants`);
    const data = await resp.json();
    const list = document.getElementById('restaurantList');
    const icons = ['🥗', '🌿', '💪', '🍃', '🥑', '🍲'];
    list.innerHTML = data.map((r, i) => `
      <div class="restaurant-card">
        <div class="rest-icon">${icons[i % icons.length]}</div>
        <div class="rest-info">
          <div class="rest-name">${r.name}</div>
          <div class="rest-addr">${r.address}</div>
          <div class="rest-meta">
            <span class="rest-rating">⭐ ${r.rating}</span>
            <span class="rest-dist">📍 ${r.distance_km}km</span>
            <span class="rest-fit">🎯 ${r.nutritional_fit_score}% fit</span>
          </div>
          ${r.recommended_dish ? `<div style="font-size:0.75rem;color:var(--primary);margin-top:4px;">Try: ${r.recommended_dish}</div>` : ''}
        </div>
      </div>
    `).join('');
  } catch (e) { console.error('Restaurants error:', e); }
}

async function loadRecipes() {
  try {
    const resp = await fetch(`${API}/api/v1/explore/recipes`);
    const data = await resp.json();
    const grid = document.getElementById('recipeGrid');
    grid.innerHTML = data.map(v => `
      <div class="recipe-card" onclick="window.open('https://youtube.com/watch?v=${v.video_id}','_blank')" tabindex="0" role="link" aria-label="Watch ${v.title}">
        <img class="recipe-thumb" src="${v.thumbnail_url || ''}" alt="${v.title}" loading="lazy" onerror="this.style.background='var(--bg-card)'">
        <div class="recipe-info">
          <div class="recipe-title">${v.title}</div>
          <div class="recipe-channel">${v.channel_name}</div>
        </div>
      </div>
    `).join('');
  } catch (e) { console.error('Recipes error:', e); }
}

// ─── Profile ───
async function saveProfile() {
  const profile = {
    weight_kg: parseFloat(document.getElementById('profWeight').value),
    dietary_goal: document.getElementById('profGoal').value,
    activity_level: document.getElementById('profActivity').value,
    allergies: document.getElementById('profAllergies').value.split(',').map(s => s.trim()).filter(Boolean),
    daily_calorie_target: parseInt(document.getElementById('profCalGoal').value),
  };
  try {
    await fetch(`${API}/api/v1/profile/goals`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    announce('Profile saved successfully!');
    alert('Profile updated! ✅');
  } catch (e) { console.error('Save profile error:', e); }
}

// ─── Language Toggle ───
function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'hi' : 'en';
  document.getElementById('langToggle').textContent = currentLang === 'en' ? 'EN | हिं' : 'हिं | EN';
  announce(currentLang === 'hi' ? 'भाषा हिंदी में बदली गई' : 'Language switched to English');
}

// ─── Notifications ───
function requestNotificationPermission() {
  if ('Notification' in window) {
    Notification.requestPermission().then(p => {
      if (p === 'granted') announce('Notifications enabled! You\'ll get meal nudges.');
    });
  }
}

// ─── Utility ───
function showLoading(text) {
  document.getElementById('loadingText').textContent = text || 'Loading...';
  document.getElementById('loadingOverlay').classList.remove('hidden');
}
function hideLoading() { document.getElementById('loadingOverlay').classList.add('hidden'); }
function announce(text) {
  const el = document.getElementById('srAnnounce');
  el.textContent = text;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 3000);
}

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  // Auto sign-in for demo
  handleSignIn();
  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  }
});
