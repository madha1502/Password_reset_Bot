// ─── Session ──────────────────────────────────────────────────────────────────
let sessionId = localStorage.getItem('chat_session_id');
if (!sessionId) {
  sessionId = 'sess_' + Math.random().toString(36).substring(2, 12).toUpperCase();
  localStorage.setItem('chat_session_id', sessionId);
}
const lbl = document.getElementById('session-label');
if (lbl) lbl.textContent = 'SESSION: ' + sessionId;

// ─── Render message ───────────────────────────────────────────────────────────
function appendMessage(role, text) {
  const box    = document.getElementById('chat-messages');
  const isUser = role === 'user';
  const time   = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  const wrap   = document.createElement('div');
  wrap.className = `message-wrapper ${isUser ? 'user-wrapper message-user' : 'message-assistant'}`;
  wrap.innerHTML = `
    <div class="message-avatar ${isUser ? 'avatar-user' : 'avatar-ai'}">${isUser ? '👤' : '🤖'}</div>
    <div>
      <div class="message-bubble">${fmt(text)}</div>
      <div class="message-time">${time}</div>
    </div>`;
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
}

function fmt(t) {
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\n/g,'<br>');
}

// ─── Typing indicator ─────────────────────────────────────────────────────────
function showTyping() {
  document.getElementById('typing-indicator').classList.remove('d-none');
  document.getElementById('chat-messages').scrollTop = 999999;
}
function hideTyping() {
  document.getElementById('typing-indicator').classList.add('d-none');
}

// ─── Send message ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  const chips = document.getElementById('quick-chips');
  if (chips) chips.style.display = 'none';

  appendMessage('user', text);
  showTyping();

  try {
    const res  = await fetch('/chat/message', {
      method: 'POST', credentials: 'include',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, session_id: sessionId})
    });
    const data = await res.json();
    hideTyping();
    appendMessage('assistant', res.ok ? data.response : '⚠️ ' + (data.error || 'Something went wrong.'));
  } catch {
    hideTyping();
    appendMessage('assistant', '⚠️ Connection failed. Make sure the backend server is running.');
  }
}

function sendQuick(text) {
  document.getElementById('chat-input').value = text;
  sendMessage();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ─── Clear chat ───────────────────────────────────────────────────────────────
async function clearChat() {
  if (!confirm('Clear all chat history?')) return;
  await fetch(`/chat/history?session_id=${sessionId}`, {method:'DELETE', credentials:'include'});
  document.getElementById('chat-messages').innerHTML = '';
  const chips = document.getElementById('quick-chips');
  if (chips) chips.style.display = '';
  appendMessage('assistant', 'Chat cleared. How can I help you with your password recovery?');
}

// ─── Ollama status ────────────────────────────────────────────────────────────
async function checkOllamaStatus() {
  const dot = document.getElementById('ai-status-dot');
  const txt = document.getElementById('ai-status-text');
  if (!dot || !txt) return;
  try {
    const res = await fetch('http://localhost:11434/api/tags', {signal: AbortSignal.timeout(2000)});
    if (res.ok) {
      dot.style.background = 'var(--success)';
      txt.textContent = 'Ollama Online';
      txt.style.color = 'var(--success)';
    } else throw new Error();
  } catch {
    dot.style.background = 'var(--warning)';
    txt.textContent = 'Rule Engine (Fallback)';
    txt.style.color = 'var(--warning)';
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  appendMessage('assistant',
    'Hello! 👋 I\'m your AI-powered Password Recovery Assistant.\n\n' +
    'I can help you:\n' +
    '• **Reset your password** step by step\n' +
    '• **Troubleshoot OTP issues**\n' +
    '• **Answer account security questions**\n\n' +
    'How can I assist you today?'
  );
  checkOllamaStatus();
  setInterval(checkOllamaStatus, 30000);
});
