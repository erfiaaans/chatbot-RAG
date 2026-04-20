const docList = [];
let isLoading = false;

// ===== AUTO RESIZE =====
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ===== ENTER =====
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ===== SUGGESTION =====
function sendSuggestion(text) {
    document.getElementById('questionInput').value = text;
    sendMessage();
}

// ===== MESSAGE UI =====
function appendMessage(role, text) {
    const messages = document.getElementById('messages');
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7);

    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.id = id;

    const avatar = role === 'user' ? '👤' : '🤖';

    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div class="bubble-wrapper">
            <div class="bubble">${text}</div>
        </div>
    `;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    return id;
}

// ===== TYPING =====
function appendTyping() {
    const messages = document.getElementById('messages');
    const id = 'typing-' + Date.now();

    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = id;

    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <div class="typing"><span></span><span></span><span></span></div>
        </div>
    `;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    return id;
}

function removeTyping(id) {
    document.getElementById(id)?.remove();
}

// ===== TIME (ONLY ONCE) =====
function renderMeta(el, time, latency) {
    const div = document.createElement("div");
    div.className = "time";

    const seconds = latency / 1000;

    const formatted =
        seconds < 1
            ? `${latency} ms`
            : `${seconds.toFixed(1)}s`;

    div.innerText = `${time} • ${formatted}`;
    el.querySelector('.bubble-wrapper').appendChild(div);
}

// ===== SEND MESSAGE =====
async function sendMessage() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question || isLoading) return;

    appendMessage('user', question);

    input.value = '';
    input.style.height = 'auto';

    const botId = appendMessage('bot', '');
    const botEl = document.getElementById(botId);
    const botBubble = botEl.querySelector('.bubble');

    const typingId = appendTyping();

    setLoading(true);

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        let fullText = '';
        let sourcesRendered = false;
        let botTime = null;
        let botLatency = null;
        let metaRendered = false;
        let latencyRendered = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");

            for (let line of lines) {
                if (!line.startsWith("data: ")) continue;

                const data = JSON.parse(line.replace("data: ", ""));

                // ===== TIME =====
                if (data.meta?.time) {
                    botTime = data.meta.time;
                }

                // ===== LATENCY =====
                if (data.meta?.latency_ms) {
                    botLatency = data.meta.latency_ms;
                }
                // render ONLY ONCE
                if (!metaRendered && botTime && botLatency) {
                    metaRendered = true;
                    renderMeta(botEl, botTime, botLatency);
                }
                // ===== STOP TYPING =====
                if (data.token && typingId) {
                    removeTyping(typingId);
                }

                // ===== STREAM TEXT =====
                if (data.token) {
                    fullText += data.token;
                    botBubble.innerHTML = fullText;
                }

                // ===== SOURCES =====
                if (data.sources && !sourcesRendered) {
                    sourcesRendered = true;

                    const sourcesHtml = `
                        <div class="sources">
                            ${data.sources.map(s =>
                        `<span class="source-tag">📄 ${s}</span>`
                    ).join('')}
                        </div>
                    `;

                    botBubble.innerHTML = fullText + sourcesHtml;
                }
            }
        }

    } catch (err) {
        appendMessage('bot', '⚠️ Gagal streaming dari server.');
    } finally {
        setLoading(false);
    }
}

// ===== LOADING =====
function setLoading(state) {
    isLoading = state;
    document.getElementById('sendBtn').disabled = state;
    document.getElementById('questionInput').disabled = state;
}