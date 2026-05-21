// ─────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────
let chatLang  = 'hi';   // current chat language
let voiceLang = 'hi';   // current voice language
let isStreaming  = false;
let isListening  = false;
let recognition  = null;

// ─────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────
const BASE = '/assistant';   // prefix — matches app.include_router prefix

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escHtml(t) {
  return String(t)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}

// Minimal markdown → HTML for chat bubbles
function mdToHtml(text) {
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,     '<em>$1</em>')
    .replace(/^(\d+)\. /gm,   '<br><b>$1.</b> ')
    .replace(/^[-•] /gm,      '<br>• ')
    .replace(/\n/g,            '<br>');
}

// ─────────────────────────────────────────────────────────────
// MODE SWITCHING
// ─────────────────────────────────────────────────────────────
function switchMode(mode) {
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('chat-panel').style.display  = 'none';
  document.getElementById('voice-panel').style.display = 'none';
  if (mode === 'chat') {
    document.querySelector('.chat-tab').classList.add('active');
    document.getElementById('chat-panel').style.display = 'block';
  } else {
    document.querySelector('.voice-tab').classList.add('active');
    document.getElementById('voice-panel').style.display = 'block';
  }
}

// ─────────────────────────────────────────────────────────────
// LANGUAGE TOGGLES
// ─────────────────────────────────────────────────────────────
function setChatLang(lang) {
  chatLang = lang;
  document.getElementById('chat-lt-en').classList.toggle('active', lang === 'en');
  document.getElementById('chat-lt-hi').classList.toggle('active', lang === 'hi');
  // Reload history for new language
  loadChatHistory();
}

function setVoiceLang(lang) {
  voiceLang = lang;
  document.getElementById('voice-lt-en').classList.toggle('active', lang === 'en');
  document.getElementById('voice-lt-hi').classList.toggle('active', lang === 'hi');
  // Update the hint label
  const label = lang === 'hi' ? 'Hindi (\u0939\u093F\u0902\u0926\u0940)' : 'English';
  document.getElementById('voice-lang-label').textContent = label;
  // Update memory badge for this lang
  loadVoiceMemory();
}

// ─────────────────────────────────────────────────────────────
// CHAT — DOM helpers
// ─────────────────────────────────────────────────────────────
function chatBox() { return document.getElementById('chat-messages'); }

function addMsg(role, htmlContent, streaming = false) {
  const box   = chatBox();
  const wrap  = document.createElement('div');
  wrap.className = `msg ${role}`;
  const avatar = role === 'bot' ? '\uD83C\uDF31' : '\uD83D\uDC64';
  const bClass = streaming ? 'msg-bubble streaming' : 'msg-bubble';
  const bId    = streaming ? 'id="streaming-bubble"' : '';
  wrap.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div>
      <div class="${bClass}" ${bId}>${htmlContent}</div>
      <div class="msg-time">${getTime()}</div>
    </div>`;
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
  return wrap;
}

function showTyping() {
  const box = chatBox();
  const el  = document.createElement('div');
  el.className = 'msg bot'; el.id = 'typing-row';
  el.innerHTML = `<div class="msg-avatar">\uD83C\uDF31</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
    </div>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}
function removeTyping() { document.getElementById('typing-row')?.remove(); }

function setMemoryBadge(id, count) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = count > 0
    ? `Memory: ${count} exchange${count !== 1 ? 's' : ''} (${chatLang === 'hi' ? '\u0939\u093F' : 'EN'})`
    : 'No memory yet';
}

function setChatBusy(busy) {
  isStreaming = busy;
  document.getElementById('chat-input').disabled = busy;
  document.getElementById('send-btn').disabled   = busy;
  const dot  = document.getElementById('chat-dot');
  const txt  = document.getElementById('chat-status-text');
  dot.style.background = busy ? '#D4A843' : '';
  txt.textContent      = busy ? 'Kisan AI is thinking\u2026' : 'Kisan AI is online';
}

// ─────────────────────────────────────────────────────────────
// CHAT — load history
// ─────────────────────────────────────────────────────────────
async function loadChatHistory() {
  const box = chatBox();
  box.innerHTML = '';
  try {
    const data = await fetch(`${BASE}/api/history/chat/${chatLang}`).then(r => r.json());
    const hist = data.history || [];

    if (hist.length === 0) {
      const welcome = chatLang === 'hi'
        ? '\u0928\u092E\u0938\u094D\u0924\u0947! \u092E\u0948\u0902 Kisan AI \u0939\u0942\u0901, \u0906\u092A\u0915\u093E \u0915\u0943\u0937\u093F \u0935\u093F\u0936\u0947\u0937\u091C\u094D\u091E \u0938\u0932\u093E\u0939\u0915\u093E\u0930 \u0964 \u0905\u092A\u0928\u0940 \u092B\u0938\u0932, \u092E\u093F\u091F\u094D\u091F\u0940, \u0915\u0940\u091F \u092F\u093E \u0916\u0947\u0924\u0940 \u0915\u0947 \u092C\u093E\u0930\u0947 \u092E\u0947\u0902 \u092A\u0942\u091B\u0947\u0902!'
        : 'Namaste! I\'m Kisan AI, your farming advisor. Ask me anything about your crops, soil, pests, or farming practices!';
      addMsg('bot', escHtml(welcome));
    } else {
      const div = document.createElement('div');
      div.className = 'history-divider';
      div.textContent = `\u2191 Previous conversation restored (${data.count} exchange${data.count !== 1 ? 's' : ''})`;
      box.appendChild(div);
      hist.forEach(m => addMsg(m.role === 'user' ? 'user' : 'bot', mdToHtml(m.content)));
    }
    setMemoryBadge('chat-memory-badge', data.count);
  } catch {
    addMsg('bot', 'Namaste! Ask me anything about your crops!');
  }
}

// ─────────────────────────────────────────────────────────────
// CHAT — send + stream
// ─────────────────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
}

async function sendChat() {
  if (isStreaming) return;
  const input = document.getElementById('chat-input');
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = ''; input.style.height = 'auto';
  addMsg('user', escHtml(msg));
  showTyping();
  setChatBusy(true);

  try {
    const resp = await fetch(`${BASE}/api/chat/stream`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: msg, lang: chatLang }),
    });

    if (!resp.ok) {
      removeTyping();
      addMsg('bot', `\u26A0\uFE0F Server error ${resp.status}. Please try again.`);
      setChatBusy(false);
      return;
    }

    // Build the streaming bot bubble
    removeTyping();
    const botWrap  = document.createElement('div');
    botWrap.className = 'msg bot';
    const bubble   = document.createElement('div');
    bubble.className = 'msg-bubble streaming';
    const timeEl   = document.createElement('div');
    timeEl.className = 'msg-time';
    timeEl.textContent = getTime();
    const inner = document.createElement('div');
    inner.appendChild(bubble); inner.appendChild(timeEl);
    botWrap.innerHTML = '<div class="msg-avatar">\uD83C\uDF31</div>';
    botWrap.appendChild(inner);
    chatBox().appendChild(botWrap);

    let accum = '';
    const reader  = resp.body.getReader();
    const decoder = new TextDecoder('utf-8');  // explicit UTF-8

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (!raw) continue;
        let evt;
        try { evt = JSON.parse(raw); } catch { continue; }

        if (evt.error) {
          bubble.innerHTML = `\u26A0\uFE0F ${escHtml(evt.error)}`;
          bubble.classList.remove('streaming');
          break;
        }
        if (evt.token) {
          accum += evt.token;
          bubble.innerHTML = mdToHtml(accum);
          chatBox().scrollTop = chatBox().scrollHeight;
        }
        if (evt.done) {
          bubble.classList.remove('streaming');
          setMemoryBadge('chat-memory-badge', evt.history_count ?? 0);
        }
      }
    }
  } catch (err) {
    removeTyping();
    addMsg('bot', '\u26A0\uFE0F Could not reach the server. Make sure FastAPI is running.');
  } finally {
    setChatBusy(false);
  }
}

async function clearChat() {
  await fetch(`${BASE}/api/history/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: 'chat', lang: chatLang }),
  });
  await loadChatHistory();
}

// ─────────────────────────────────────────────────────────────
// VOICE
// ─────────────────────────────────────────────────────────────
async function loadVoiceMemory() {
  try {
    const data = await fetch(`${BASE}/api/history/voice/${voiceLang}`).then(r => r.json());
    const el = document.getElementById('voice-memory-badge');
    el.textContent = data.count > 0
      ? `Memory: ${data.count} exchange${data.count !== 1 ? 's' : ''} (${voiceLang === 'hi' ? '\u0939\u093F' : 'EN'})`
      : 'No memory yet';
  } catch {}
}

function toggleVoice() {
  if (isListening) stopListening(); else startListening();
}

function startListening() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    alert('Voice recognition requires Chrome browser.');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang            = voiceLang === 'hi' ? 'hi-IN' : 'en-US';
  recognition.interimResults  = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isListening = true;
    document.getElementById('voice-btn').classList.add('active');
    document.getElementById('voice-btn').textContent = '\uD83D\uDD34';
    document.getElementById('voice-btn-wrap').classList.add('listening');
    document.getElementById('voice-status').textContent = 'Listening\u2026';
    document.getElementById('voice-sub').textContent    = 'Speak now. I\'m listening\u2026';
  };

  recognition.onresult = async (e) => {
    const transcript = e.results[0][0].transcript;
    showVoiceTranscripts(transcript, '\u2026');
    document.getElementById('voice-status').textContent = 'Getting AI response\u2026';
    await getVoiceResponse(transcript);
  };

  recognition.onerror = () => {
    resetVoiceBtn();
    document.getElementById('voice-status').textContent = 'Error. Tap to try again.';
  };

  recognition.onend = () => resetVoiceBtn();
  recognition.start();
}

function stopListening() {
  if (recognition) recognition.stop();
  resetVoiceBtn();
}

function resetVoiceBtn() {
  isListening = false;
  const btn = document.getElementById('voice-btn');
  btn.classList.remove('active');
  btn.textContent = '\uD83C\uDF04';
  btn.textContent = '\uD83C\uDF3E'; // wheat/mic emoji fallback
  btn.textContent = '\uD83C\uDF3E';
  // use mic emoji
  btn.innerHTML = '\uD83C\uDF04';
  btn.textContent = '🎤';
  document.getElementById('voice-btn-wrap').classList.remove('listening');
  document.getElementById('voice-status').textContent = 'Tap to Speak';
  document.getElementById('voice-sub').textContent    = 'Press the mic again for another question.';
}

function showVoiceTranscripts(userText, aiText) {
  document.getElementById('voice-transcripts').style.display = 'flex';
  document.getElementById('user-transcript').textContent = userText;
  document.getElementById('ai-transcript').textContent   = aiText;
}

async function getVoiceResponse(userText) {
  try {
    const resp = await fetch(`${BASE}/api/voice`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: userText, lang: voiceLang }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      document.getElementById('ai-transcript').textContent = `\u26A0\uFE0F ${err.detail || 'Server error'}`;
      document.getElementById('voice-status').textContent  = 'Error.';
      return;
    }

    const data = await resp.json();
    document.getElementById('ai-transcript').textContent = data.reply;
    document.getElementById('voice-status').textContent  = 'Speaking\u2026';

    // Update memory badge
    const el = document.getElementById('voice-memory-badge');
    const c  = data.history_count;
    el.textContent = c > 0
      ? `Memory: ${c} exchange${c !== 1 ? 's' : ''} (${voiceLang === 'hi' ? '\u0939\u093F' : 'EN'})`
      : 'No memory yet';

    speakText(data.reply, voiceLang);
  } catch {
    document.getElementById('ai-transcript').textContent = '\u26A0\uFE0F Could not reach the server.';
    document.getElementById('voice-status').textContent  = 'Connection error.';
  }
}

function speakText(text, lang) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utt  = new SpeechSynthesisUtterance(text);
  utt.lang   = lang === 'hi' ? 'hi-IN' : 'en-US';
  utt.rate   = 0.95;
  utt.onend  = () => {
    document.getElementById('voice-status').textContent = 'Tap to Speak';
    document.getElementById('voice-sub').textContent    = 'Press the mic again for another question.';
  };
  window.speechSynthesis.speak(utt);
}

async function clearVoice() {
  await fetch(`${BASE}/api/history/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: 'voice', lang: voiceLang }),
  });
  document.getElementById('voice-transcripts').style.display = 'none';
  document.getElementById('voice-status').textContent = 'Memory cleared. Tap to Speak.';
  document.getElementById('voice-memory-badge').textContent = 'No memory yet';
}

// ─────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadChatHistory();
  loadVoiceMemory();
});
