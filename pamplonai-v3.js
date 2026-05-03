// ── Configuración ───────────────────────────────────────────────────────
const API_URL = "https://pamplonaii.onrender.com";

// ── DOM refs ────────────────────────────────────────────────────────────
const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const suggestionsC = document.getElementById('suggestions-container');
const btnClear = document.getElementById('btn-clear');
const btnTheme = document.getElementById('btn-theme');
const themeIcon = document.getElementById('theme-icon');
const avatarEmoji = document.getElementById('avatar-emoji');
const statusText = document.getElementById('status-text');

// ── Mobile Menu Logic ───────────────────────────────────────────────────
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');

function toggleMenu() {
    sidebar.classList.toggle('active');
    sidebarOverlay.classList.toggle('active');
}

if (menuToggle) menuToggle.addEventListener('click', toggleMenu);
if (sidebarOverlay) sidebarOverlay.addEventListener('click', toggleMenu);

// ── Estado ──────────────────────────────────────────────────────────────
let msgHistory = [];
let isBusy = false;
let currentTheme = 'light';

try {
    const saved = localStorage.getItem('campus_history');
    if (saved) msgHistory = JSON.parse(saved);
    currentTheme = localStorage.getItem('campus_theme') || 'light';
} catch { }

const CARDS = [
    { icon: '📅', title: 'Fechas importantes', q: '¿Cuáles son las fechas de inscripción?' },
    { icon: '📋', title: 'Inscripción de materias', q: '¿Cómo me inscribo a una asignatura?' },
    { icon: '📰', title: 'Últimas noticias', q: '¿Qué noticias hay hoy en la Unipamplona?' },
    { icon: '📞', title: 'Soporte académico', q: '¿Cómo contacto a secretaría académica?' },
];

function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    if (themeIcon) themeIcon.className = (t === 'dark') ? 'fas fa-sun' : 'fas fa-moon';
}

applyTheme(currentTheme);
if (btnTheme) btnTheme.addEventListener('click', () => {
    currentTheme = (currentTheme === 'light') ? 'dark' : 'light';
    localStorage.setItem('campus_theme', currentTheme);
    applyTheme(currentTheme);
});

if (btnClear) {
    btnClear.addEventListener('click', () => {
        if (!confirm('¿Empezamos de cero?')) return;
        msgHistory = [];
        localStorage.removeItem('campus_history');
        chatWindow.innerHTML = '';
        renderWelcome();
        userInput.focus();
    });
}

function getGreeting() {
    const h = new Date().getHours();
    if (h >= 6 && h < 12) return '¡Buenos días! ☀️';
    if (h >= 12 && h < 19) return '¡Buenas tardes! 🌤';
    return '¡Buenas noches! 🌙';
}

function renderWelcome() {
    const sec = document.createElement('div');
    sec.className = 'welcome-section';
    sec.innerHTML = `
        <div class="welcome-greeting"><span>👋</span> ${getGreeting()} Soy <strong>Pamplon-AI</strong></div>
        <p class="welcome-sub">Tu asistente académico de la <strong>Universidad de Pamplona</strong>.</p>
        <div class="example-cards"></div>
    `;
    const grid = sec.querySelector('.example-cards');
    CARDS.forEach(c => {
        const card = document.createElement('button');
        card.className = 'example-card';
        card.innerHTML = `<span class="icon">${c.icon}</span><span class="title">${c.title}</span><span class="desc">${c.q}</span>`;
        card.addEventListener('click', () => { userInput.value = c.q; sendMessage(); });
        grid.appendChild(card);
    });
    chatWindow.appendChild(sec);
}

if (msgHistory.length > 0) {
    msgHistory.forEach(m => drawBubble(m.role === 'user', m.text, m.source));
} else {
    renderWelcome();
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isBusy) return;

    // DIAGNÓSTICO: Alerta de conexión
    console.log("Conectando a: " + API_URL);

    const welcome = chatWindow.querySelector('.welcome-section');
    if (welcome) welcome.remove();

    isBusy = true;
    userInput.value = '';
    drawBubble(true, text);

    const typingRow = addTypingRow();

    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: msgHistory.map(m => ({ role: m.role, content: m.text }))
            })
        });

        typingRow.remove();

        if (!res.ok) throw new Error('Status: ' + res.status);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullAnswer = '';

        const botRow = drawBubble(false, '', 'ai');
        const bubble = botRow.querySelector('.bubble');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            if (chunk.includes('||SPLIT||')) {
                fullAnswer = chunk.split('||SPLIT||')[1];
            } else {
                fullAnswer += chunk;
            }
            bubble.textContent = fullAnswer;
            scrollBottom();
        }

        msgHistory.push({ role: 'user', text });
        msgHistory.push({ role: 'assistant', text: fullAnswer });
        localStorage.setItem('campus_history', JSON.stringify(msgHistory));

    } catch (err) {
        console.error("DEBUG_ERROR:", err);
        if (typingRow) typingRow.remove();
        drawBubble(false, "🔴 ERROR_CRITICO: " + err.message + ". ¿Agregaste la llave GROQ_API_KEY en Render?");
    } finally {
        isBusy = false;
        scrollBottom();
    }
}

function drawBubble(isUser, text, source) {
    const row = document.createElement('div');
    row.className = 'message-row ' + (isUser ? 'user' : 'bot');
    row.innerHTML = `
        <div class="msg-avatar">${isUser ? '👤' : '🎓'}</div>
        <div class="msg-content">
            ${(!isUser && source) ? `<span class="source-tag ${source === 'faq' ? 'tag-faq' : 'tag-ai'}">${source === 'faq' ? '✅ Oficial' : '🤖 IA'}</span>` : ''}
            <div class="bubble">${text}</div>
        </div>
    `;
    chatWindow.appendChild(row);
    scrollBottom();
    return row;
}

function addTypingRow() {
    const row = document.createElement('div');
    row.className = 'message-row bot';
    row.innerHTML = `<div class="msg-avatar">🤔</div><div class="msg-content"><div class="bubble">Pensando...</div></div>`;
    chatWindow.appendChild(row);
    scrollBottom();
    return row;
}

function scrollBottom() { chatWindow.scrollTop = chatWindow.scrollHeight; }

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
