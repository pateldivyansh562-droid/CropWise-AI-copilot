// lands.js — list page modal + CRUD
const BASE = '/manage-lands';

// ── Modal ──────────────────────────────────────────────────────────────────────
function openAddModal() {
  document.getElementById('modal-title').textContent      = 'Naya Khet Joḍen';
  document.getElementById('modal-save-btn').textContent   = 'Khet Bachao';
  document.getElementById('edit-land-id').value           = '';
  clearForm();
  showModal();
}

async function openEditModal(landId) {
  try {
    const data = await fetch(`${BASE}/api/lands`).then(r => r.json());
    const land = data.lands.find(l => l.id === landId);
    if (!land) return alert('Khet nahi mila');
    document.getElementById('modal-title').textContent    = 'Khet Badlen';
    document.getElementById('modal-save-btn').textContent = 'Badlao Bachao';
    document.getElementById('edit-land-id').value         = landId;
    fillForm(land);
    showModal();
  } catch (e) {
    alert('Data load nahi ho saka: ' + e.message);
  }
}

function showModal() {
  document.getElementById('modal-overlay').classList.add('open');
  document.getElementById('land-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.getElementById('land-modal').classList.remove('open');
  document.body.style.overflow = '';
}

// ── Form ───────────────────────────────────────────────────────────────────────
function clearForm() {
  ['f-name','f-crop-name','f-sowing-date','f-last-watered','f-notes']
    .forEach(id => { const el = document.getElementById(id); if(el) el.value = ''; });
  document.getElementById('f-watering-freq').value = '';
  document.querySelectorAll('.freq-btn').forEach(b => b.classList.remove('selected'));
  document.querySelector('input[name="f-lang"][value="hi"]').checked = true;
}

function fillForm(land) {
  const set = (id, v) => { const el = document.getElementById(id); if(el) el.value = v || ''; };
  set('f-name',          land.name);
  set('f-crop-name',     land.crop_name);
  set('f-sowing-date',   land.sowing_date);
  set('f-last-watered',  land.last_watered);
  set('f-notes',         land.notes);
  set('f-watering-freq', land.watering_freq);
  // Highlight the matching freq button
  document.querySelectorAll('.freq-btn').forEach(b => {
    b.classList.toggle('selected', b.textContent.trim() === land.watering_freq);
  });
  const lang = land.lang || 'hi';
  const r = document.querySelector(`input[name="f-lang"][value="${lang}"]`);
  if (r) r.checked = true;
}

function selectFreq(btn, val) {
  document.querySelectorAll('.freq-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('f-watering-freq').value = val;
}

function readForm() {
  const g    = id => (document.getElementById(id)?.value || '').trim();
  const lang = document.querySelector('input[name="f-lang"]:checked')?.value || 'hi';
  return {
    name:          g('f-name'),
    crop_name:     g('f-crop-name'),
    sowing_date:   g('f-sowing-date'),
    last_watered:  g('f-last-watered'),
    watering_freq: g('f-watering-freq'),
    notes:         g('f-notes'),
    lang,
  };
}

// ── Save ───────────────────────────────────────────────────────────────────────
async function saveLand() {
  const data   = readForm();
  const landId = document.getElementById('edit-land-id').value;

  if (!data.name)      return alert('Khet ka naam likhna zaroori hai।');
  if (!data.crop_name) return alert('Fasal ka naam likhna zaroori hai।');

  const btn = document.getElementById('modal-save-btn');
  btn.disabled = true; btn.textContent = 'Saving…';

  try {
    const url    = landId ? `${BASE}/api/lands/${landId}` : `${BASE}/api/lands`;
    const method = landId ? 'PUT' : 'POST';
    const resp   = await fetch(url, {
      method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    closeModal();
    window.location.reload();
  } catch (e) {
    alert('Save nahi ho saka: ' + e.message);
    btn.disabled = false;
    btn.textContent = landId ? 'Badlao Bachao' : 'Khet Bachao';
  }
}

// ── Delete ─────────────────────────────────────────────────────────────────────
async function deleteLand(landId) {
  if (!confirm('Kya aap is khet ko hataना chahte hain? Yeh wapas nahi aayega।')) return;
  try {
    const resp = await fetch(`${BASE}/api/lands/${landId}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const card = document.getElementById(`card-${landId}`);
    if (card) { card.style.transition = '0.25s'; card.style.opacity = '0'; card.style.transform = 'scale(0.95)'; setTimeout(() => card.remove(), 250); }
  } catch (e) {
    alert('Delete nahi ho saka: ' + e.message);
  }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
