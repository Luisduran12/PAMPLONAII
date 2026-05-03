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
// IMPORTANTE: No usar "history" — es window.history, variable reservada del navegador.
let msgHistory = [];
let isBusy = false;
let currentTheme = 'light';

// Carga segura del estado persistido
try {
    const saved = localStorage.getItem('campus_history');
    if (saved) msgHistory = JSON.parse(saved);
    currentTheme = localStorage.getItem('campus_theme') || 'light';
} catch { /* si localStorage falla, usamos defaults */ }

// ── Tarjetas de bienvenida ──────────────────────────────────────────────
const CARDS = [
    { icon: '📅', title: 'Fechas importantes', q: '¿Cuáles son las fechas de inscripción?' },
    { icon: '📋', title: 'Inscripción de materias', q: '¿Cómo me inscribo a una asignatura?' },
    { icon: '📰', title: 'Últimas noticias', q: '¿Qué noticias hay hoy en la Unipamplona?' },
    { icon: '📞', title: 'Soporte académico', q: '¿Cómo contacto a secretaría académica?' },
];

// ── Inicialización ──────────────────────────────────────────────────────
applyTheme(currentTheme);
loadSuggestions();
if (msgHistory.length > 0) renderHistory(); else renderWelcome();
userInput.focus();

// ── Tema ────────────────────────────────────────────────────────────────
function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    if (themeIcon) themeIcon.className = (t === 'dark') ? 'fas fa-sun' : 'fas fa-moon';
}
if (btnTheme) {
    btnTheme.addEventListener('click', () => {
        currentTheme = (currentTheme === 'light') ? 'dark' : 'light';
        localStorage.setItem('campus_theme', currentTheme);
        applyTheme(currentTheme);
    });
}

// ── Nuevo chat ──────────────────────────────────────────────────────────
if (btnClear) {
    btnClear.addEventListener('click', () => {
        if (!confirm('¿Empezamos de cero? Se borrará la conversación actual.')) return;
        msgHistory = [];
        try { localStorage.removeItem('campus_history'); } catch { }
        chatWindow.innerHTML = '';
        renderWelcome();
        loadSuggestions();
        userInput.focus();
    });
}

// ── Saludo según hora ───────────────────────────────────────────────────
function getGreeting() {
    const h = new Date().getHours();
    if (h >= 6 && h < 12) return '¡Buenos días! ☀️';
    if (h >= 12 && h < 19) return '¡Buenas tardes! 🌤';
    return '¡Buenas noches! 🌙';
}

// ── Pantalla de bienvenida ──────────────────────────────────────────────
function renderWelcome() {
    const sec = document.createElement('div');
    sec.className = 'welcome-section';

    const greeting = document.createElement('div');
    greeting.className = 'welcome-greeting';
    greeting.innerHTML = '<span>👋</span>';
    const greetText = document.createElement('span');
    greetText.textContent = getGreeting() + ' Soy ';
    const strong = document.createElement('strong');
    strong.textContent = 'Pamplon-AI';
    greetText.appendChild(strong);
    greeting.appendChild(greetText);

    const sub = document.createElement('p');
    sub.className = 'welcome-sub';
    sub.innerHTML = 'Tu asistente académico de la <strong>Universidad de Pamplona</strong>.<br>Pregúntame sobre inscripciones, horarios, reglamento, noticias y más.';

    const grid = document.createElement('div');
    grid.className = 'example-cards';

    CARDS.forEach(c => {
        const card = document.createElement('button');
        card.className = 'example-card';
        card.innerHTML = '<span class="icon">' + c.icon + '</span>' +
            '<span class="title">' + c.title + '</span>' +
            '<span class="desc">' + c.q + '</span>';
        card.addEventListener('click', () => {
            userInput.value = c.q;
            sendMessage();
        });
        grid.appendChild(card);
    });

    sec.appendChild(greeting);
    sec.appendChild(sub);
    sec.appendChild(grid);
    chatWindow.appendChild(sec);
}

// ── Persistencia ────────────────────────────────────────────────────────
function saveMsg(role, text, source) {
    msgHistory.push({ role, text, source: source || null });
    if (msgHistory.length > 30) msgHistory.shift();
    try { localStorage.setItem('campus_history', JSON.stringify(msgHistory)); } catch { }
}

function renderHistory() {
    msgHistory.forEach(m => drawBubble(m.role === 'user', m.text, m.source, false));
    scrollBottom();
}

// ── Sugerencias ─────────────────────────────────────────────────────────
async function loadSuggestions() {
    try {
        const res = await fetch(`${API_URL}/api/faqs`);
        if (!res.ok) return;
        const faqs = await res.json();
        const pick = [...faqs].sort(() => Math.random() - .5).slice(0, 5);
        suggestionsC.innerHTML = '';
        const frag = document.createDocumentFragment();
        pick.forEach(f => {
            const chip = document.createElement('button');
            chip.className = 'chip';
            chip.textContent = f.pregunta;
            chip.addEventListener('click', () => { userInput.value = f.pregunta; sendMessage(); });
            frag.appendChild(chip);
        });
        suggestionsC.appendChild(frag);
    } catch { /* silencioso */ }
}

// ── Envío principal ─────────────────────────────────────────────────────
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isBusy) return;

    // Eliminar pantalla de bienvenida si existe
    const welcome = chatWindow.querySelector('.welcome-section');
    if (welcome) welcome.remove();

    isBusy = true;
    userInput.value = '';
    userInput.focus();

    drawBubble(true, text, null, true);
    saveMsg('user', text, null);

    if (avatarEmoji) avatarEmoji.textContent = '🤔';
    if (statusText) statusText.textContent = 'PamplonAI está escribiendo…';

    // Indicador de escritura
    const typingRow = addTypingRow();
    let typingRemoved = false;

    const removeTyping = () => {
        if (!typingRemoved && typingRow.parentNode) {
            typingRow.remove();
            typingRemoved = true;
        }
    };

    let fullAnswer = '';
    let msgSource = 'ai';

    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: msgHistory.map(m => ({ role: m.role, content: m.text }))
            })
        });

        if (!res.ok) throw new Error('HTTP ' + res.status);

        removeTyping();

        // Crear burbuja de respuesta con referencias directas — sin querySelector en el loop
        const botRow = document.createElement('div');
        botRow.className = 'message-row bot';

        const botAvatar = document.createElement('div');
        botAvatar.className = 'msg-avatar';
        botAvatar.textContent = '🎓';

        const msgContent = document.createElement('div');
        msgContent.className = 'msg-content';

        const tagEl = document.createElement('span');
        tagEl.className = 'source-tag';
        tagEl.style.display = 'none';

        const bubbleEl = document.createElement('div');
        bubbleEl.className = 'bubble';

        msgContent.appendChild(tagEl);
        msgContent.appendChild(bubbleEl);
        botRow.appendChild(botAvatar);
        botRow.appendChild(msgContent);
        chatWindow.appendChild(botRow);

        // ── Leer stream ──
        // Usamos UN solo TextDecoder y UN solo buffer acumulativo.
        // NUNCA decodificamos el mismo `value` dos veces.
        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8', { fatal: false });
        let buffer = '';
        let headerDone = false;

        let scrollPending = false;
        const schedScroll = () => {
            if (scrollPending) return;
            scrollPending = true;
            requestAnimationFrame(() => { scrollBottom(); scrollPending = false; });
        };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // Decodificar UNA sola vez por chunk
            const chunk = decoder.decode(value, { stream: !done });
            buffer += chunk;

            if (!headerDone) {
                if (buffer.includes('||SPLIT||')) {
                    // Protocolo IA: {"source":"ai"}||SPLIT||<texto>
                    const splitIdx = buffer.indexOf('||SPLIT||');
                    fullAnswer = buffer.slice(splitIdx + '||SPLIT||'.length);
                    msgSource = 'ai';
                    tagEl.className = 'source-tag tag-ai';
                    tagEl.textContent = '🤖 Asistente IA';
                    tagEl.style.display = '';
                    bubbleEl.textContent = fullAnswer;
                    buffer = '';
                    headerDone = true;
                } else if (buffer.trimStart().startsWith('{')) {
                    // Protocolo FAQ: JSON completo
                    try {
                        const data = JSON.parse(buffer);
                        msgSource = 'faq';
                        fullAnswer = data.answer || '';
                        tagEl.className = 'source-tag tag-faq';
                        tagEl.textContent = '✅ Respuesta oficial';
                        tagEl.style.display = '';
                        bubbleEl.textContent = fullAnswer;
                        buffer = '';
                        break; // FAQ es una sola respuesta, salimos
                    } catch { /* JSON incompleto, seguir acumulando */ }
                }
            } else {
                // Streaming normal: buffer vacío, acumulamos en fullAnswer directamente
                fullAnswer += chunk;
                bubbleEl.textContent = fullAnswer;
            }

            schedScroll();
        }

        // Feedback
        addFeedbackBtns(msgContent, text, fullAnswer, msgSource);
        saveMsg('assistant', fullAnswer, msgSource);

    } catch (err) {
        console.error('[PamplonAI] Error:', err);
        removeTyping();
        const errMsgs = [
            'Uy, tuve un problema. ¿Puedes reformular tu pregunta? 😅',
            'Algo salió mal. Intenta de nuevo en unos segundos.',
        ];
        drawBubble(false, errMsgs[Math.floor(Math.random() * errMsgs.length)], null, true);
    } finally {
        // SIEMPRE se ejecuta, sin importar lo que ocurra arriba
        isBusy = false;
        if (avatarEmoji) avatarEmoji.textContent = '🎓';
        if (statusText) statusText.textContent = 'En línea · PamplonAI';
        scrollBottom();
    }
}

// ── Helpers ─────────────────────────────────────────────────────────────
function drawBubble(isUser, text, source, animate) {
    const row = document.createElement('div');
    row.className = 'message-row ' + (isUser ? 'user' : 'bot');
    if (!animate) row.style.animation = 'none';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = isUser ? '👤' : '🎓';

    const content = document.createElement('div');
    content.className = 'msg-content';

    if (!isUser && source) {
        const tag = document.createElement('span');
        if (source === 'faq') {
            tag.className = 'source-tag tag-faq';
            tag.textContent = '✅ Respuesta oficial';
        } else {
            tag.className = 'source-tag tag-ai';
            tag.textContent = '🤖 Asistente IA';
        }
        content.appendChild(tag);
    }

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text; // textContent para prevenir XSS
    content.appendChild(bubble);

    row.appendChild(avatar);
    row.appendChild(content);
    chatWindow.appendChild(row);
    scrollBottom();
    return row;
}

function addTypingRow() {
    const row = document.createElement('div');
    row.className = 'message-row bot';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = '🤔';

    const content = document.createElement('div');
    content.className = 'msg-content';

    const inner = document.createElement('div');
    inner.style.cssText = 'display:flex;align-items:center;gap:.5rem;padding:.5rem 0;color:var(--text-muted);font-size:.8rem';

    const dots = document.createElement('div');
    dots.className = 'dots';
    dots.innerHTML = '<span></span><span></span><span></span>';

    const label = document.createElement('span');
    label.textContent = 'PamplonAI está pensando...';

    inner.appendChild(dots);
    inner.appendChild(label);
    content.appendChild(inner);
    row.appendChild(avatar);
    row.appendChild(content);
    chatWindow.appendChild(row);
    scrollBottom();
    return row;
}

function addFeedbackBtns(container, question, answer, source) {
    const feedRow = document.createElement('div');
    feedRow.className = 'feedback-row';

    let voted = false;

    ['👍 Útil', '👎 No útil'].forEach((label, i) => {
        const btn = document.createElement('button');
        btn.className = 'feedback-btn';
        btn.textContent = label;
        btn.addEventListener('click', async () => {
            if (voted) return;
            voted = true;
            feedRow.querySelectorAll('.feedback-btn').forEach(b => { b.disabled = true; });
            btn.classList.add(i === 0 ? 'active-good' : 'active-bad');
            try {
                await fetch(`${API_URL}/api/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, answer, rating: i === 0 ? 1 : 0, source })
                });
            } catch { /* silencioso */ }
        });
        feedRow.appendChild(btn);
    });

    container.appendChild(feedRow);
}

function scrollBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ── Eventos ─────────────────────────────────────────────────────────────
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
