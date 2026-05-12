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

    if (role === 'user') {

        div.className =
            'flex gap-3 max-w-[85%] self-end flex-row-reverse';

        div.innerHTML = `
            <div
                class="bg-brand-600 p-3.5 rounded-2xl rounded-tr-none shadow-sm text-sm text-white leading-relaxed"
            >
                ${text}
            </div>
        `;

    }

    // ===== BOT =====
    else {

        div.className = 'flex gap-3 max-w-[85%]';

        div.innerHTML = `
            <div
                class="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center text-brand-600 mt-1"
            >
                <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    ></path>
                </svg>
            </div>

            <div
                class="bubble bg-white p-3.5 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 text-sm text-slate-700 leading-relaxed"
            >
                ${text}
            </div>
        `;
    }

    div.id = id;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    return id;
}

// ===== TYPING =====
function appendTyping() {
    const messages = document.getElementById('messages');
    const id = 'typing-' + Date.now();

    const div = document.createElement('div');

    div.className = 'flex gap-3 max-w-[85%]';

    div.innerHTML = `
        <div
            class="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center text-brand-600 mt-1"
        >
            🤖
        </div>

        <div
            class="bg-white p-3.5 rounded-2xl rounded-tl-none shadow-sm border border-slate-100"
        >
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    div.id = id;
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
    el.querySelector('.bubble').appendChild(div);
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
        const res = await fetch('/api/chat', {
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

                    const messages = document.getElementById('messages');
                    messages.scrollTop = messages.scrollHeight;
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

function setLoading(state) {
    isLoading = state;
    document.getElementById('sendBtn').disabled = state;
    document.getElementById('questionInput').disabled = state;
}

document.addEventListener("DOMContentLoaded", function () {
    const hamburger = document.getElementById("hamburger");
    const navMenu = document.getElementById("navMenu");

    if (hamburger && navMenu) {
        hamburger.addEventListener("click", function () {
            navMenu.classList.toggle("hidden");
        });
    }
});

const chatPopup = document.getElementById("chat-popup");
const chatArea = document.getElementById("chat-area");

const iconDefault = document.getElementById("chat-icon-default");
const iconClose = document.getElementById("chat-icon-close");

const iconMaximize = document.getElementById("chat-icon-maximize");
const iconRestore = document.getElementById("chat-icon-restore");

let isChatOpen = false;
let isMaximized = false;

function toggleChat() {
    isChatOpen = !isChatOpen;

    if (isChatOpen) {

        chatPopup.classList.remove(
            "opacity-0",
            "scale-90",
            "pointer-events-none"
        );

        chatPopup.classList.add(
            "opacity-100",
            "scale-100",
            "pointer-events-auto"
        );

        iconDefault.classList.add(
            "opacity-0",
            "scale-50",
            "rotate-90"
        );

        iconClose.classList.remove(
            "opacity-0",
            "scale-50"
        );

        iconClose.classList.add(
            "opacity-100",
            "scale-100",
            "rotate-90"
        );

    } else {

        if (isMaximized) {
            toggleMaximize();
        }

        chatPopup.classList.remove(
            "opacity-100",
            "scale-100",
            "pointer-events-auto"
        );

        chatPopup.classList.add(
            "opacity-0",
            "scale-90",
            "pointer-events-none"
        );

        iconDefault.classList.remove(
            "opacity-0",
            "scale-50",
            "rotate-90"
        );

        iconClose.classList.remove(
            "opacity-100",
            "scale-100",
            "rotate-90"
        );

        iconClose.classList.add(
            "opacity-0",
            "scale-50"
        );
    }
}

function toggleMaximize() {

    isMaximized = !isMaximized;

    if (isMaximized) {

        chatPopup.classList.remove(
            "bottom-24",
            "right-6",
            "lg:bottom-28",
            "lg:right-8",
            "w-[calc(100vw-3rem)]",
            "sm:w-[380px]",
            "rounded-2xl",
            "h-[600px]",
            "max-h-[80vh]"
        );

        chatPopup.classList.add(
            "bottom-0",
            "right-0",
            "w-full",
            "h-[100dvh]",
            "rounded-none"
        );

        iconMaximize.classList.add("hidden");
        iconRestore.classList.remove("hidden");

        document.body.style.overflow = "hidden";

    } else {

        chatPopup.classList.add(
            "bottom-24",
            "right-6",
            "lg:bottom-28",
            "lg:right-8",
            "w-[calc(100vw-3rem)]",
            "sm:w-[380px]",
            "rounded-2xl",
            "h-[600px]",
            "max-h-[80vh]"
        );

        chatPopup.classList.remove(
            "bottom-0",
            "right-0",
            "w-full",
            "h-[100dvh]",
            "rounded-none"
        );

        iconMaximize.classList.remove("hidden");
        iconRestore.classList.add("hidden");

        document.body.style.overflow = "";
    }
}

function goToChat(topic) {
    const input = document.getElementById("questionInput");

    if (!input) return;
    const chatPopup = document.getElementById("chat-popup");

    chatPopup.classList.remove(
        "opacity-0",
        "scale-90",
        "pointer-events-none"
    );

    chatPopup.classList.add(
        "opacity-100",
        "scale-100"
    );
    document
        .getElementById("chat-icon-default")
        ?.classList.add("opacity-0", "scale-50");

    document
        .getElementById("chat-icon-close")
        ?.classList.remove("opacity-0", "scale-50");

    input.value = topic;
    autoResize(input);
    sendMessage();
}