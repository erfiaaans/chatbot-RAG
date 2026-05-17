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
        div.className = 'flex gap-3 max-w-[85%] self-end flex-row-reverse';
        div.innerHTML = `
            <div class="bg-brand-600 p-3.5 rounded-2xl rounded-tr-none shadow-sm text-sm text-white leading-relaxed">
                ${text}
            </div>
        `;
    }
    // ===== BOT =====
    else {
        div.className = 'flex gap-3 max-w-[85%]';
        div.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center text-brand-600 mt-1 shadow-sm">
                <!-- Ikon AI Sparkle -->
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"></path>
                </svg>
            </div>

            <div class="bubble bg-white p-3.5 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 text-sm text-slate-700 leading-relaxed">
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
            <svg
                class="w-4 h-4 animate-pulse"
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
            class="bg-white px-4 py-4 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 flex items-center gap-1.5 h-[44px]"
        >
            <div class="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style="animation-delay: 0ms;"></div>
            <div class="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style="animation-delay: 150ms;"></div>
            <div class="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style="animation-delay: 300ms;"></div>
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

    // Tampilkan pesan user
    appendMessage('user', question);

    input.value = '';
    input.style.height = 'auto';

    // 1. Tampilkan animasi typing SAJA (jangan buat pesan bot kosong dulu)
    let typingId = appendTyping();

    // Siapkan variabel untuk menampung elemen chat bot nanti
    let botId = null;
    let botEl = null;
    let botBubble = null;

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

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");

            for (let line of lines) {
                if (!line.startsWith("data: ")) continue;

                try {
                    const data = JSON.parse(line.replace("data: ", ""));

                    // 1. Simpan META terlebih dahulu jika server mengirimkannya duluan
                    if (data.meta?.time) {
                        botTime = data.meta.time;
                    }
                    if (data.meta?.latency_ms) {
                        botLatency = data.meta.latency_ms;
                    }

                    // 2. HAPUS ANIMASI LOADING HANYA JIKA menerima Teks (token) ATAU Error
                    if (data.token !== undefined || data.error !== undefined) {
                        if (!botId) {
                            // Hapus animasi loading
                            if (typingId) {
                                removeTyping(typingId);
                                typingId = null;
                            }

                            // Baru buat bubble aslinya di sini
                            botId = appendMessage('bot', '');
                            botEl = document.getElementById(botId);
                            botBubble = botEl.querySelector('.bubble');

                            // Render time & latency jika tadi metanya dikirim duluan
                            if (!metaRendered && botTime && botLatency) {
                                metaRendered = true;
                                renderMeta(botEl, botTime, botLatency);
                            }
                        }
                    }

                    // ==========================================
                    // PENANGANAN ERROR API / SERVER
                    // ==========================================
                    if (data.error) {
                        let errorMsg = data.error;
                        if (errorMsg.includes('429') || errorMsg.includes('RESOURCE_EXHAUSTED')) {
                            errorMsg = "Sistem sedang sibuk atau batas penggunaan harian telah tercapai. Mohon tunggu beberapa detik dan coba lagi.";
                        }

                        botBubble.innerHTML = `
                            <div class="flex flex-col gap-1 text-red-500">
                                <span class="font-semibold text-sm flex items-center gap-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    Gagal Memuat Jawaban
                                </span>
                                <span class="text-xs text-red-400 mt-1">${errorMsg}</span>
                            </div>
                        `;

                        const messages = document.getElementById('messages');
                        messages.scrollTop = messages.scrollHeight;
                        continue;
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
                            <div class="sources mt-2 border-t border-slate-100 pt-2">
                                <span class="text-xs font-semibold text-slate-400 block mb-1">Sumber:</span>
                                ${data.sources.map(s =>
                            `<span class="inline-block bg-slate-100 text-slate-600 text-[10px] px-2 py-1 rounded-md mr-1 mb-1">📄 ${s}</span>`
                        ).join('')}
                            </div>
                        `;

                        botBubble.innerHTML = fullText + sourcesHtml;
                        const messages = document.getElementById('messages');
                        messages.scrollTop = messages.scrollHeight;
                    }
                } catch (e) {
                    console.error("Error parsing JSON chunk", e);
                }
            }
        }

    } catch (err) {
        // Jika server terputus/mati total saat di awal permintaan
        if (typingId) {
            removeTyping(typingId);
            typingId = null;
        }
        if (!botId) {
            botId = appendMessage('bot', '');
            botEl = document.getElementById(botId);
            botBubble = botEl.querySelector('.bubble');
        }

        botBubble.innerHTML = `
            <div class="text-red-500 text-sm font-medium flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Gagal terhubung ke server.
            </div>
        `;
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
async function resetChat() {
    try {
        await fetch("/api/reset", {
            method: "POST",
        });
        const messages = document.getElementById("messages");

        messages.innerHTML = `
      <div class="text-center">
        <span
          class="text-[10px] uppercase font-semibold text-slate-400 bg-white px-2 py-1 rounded-full shadow-sm"
        >
          Hari Ini
        </span>
      </div>

      <div class="flex gap-3 max-w-[85%]">
        <div
          class="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center text-brand-600 mt-1"
        >
          🤖
        </div>

        <div
          class="bg-white p-3.5 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 text-sm text-slate-700 leading-relaxed"
        >
          Halo, saya siap membantu. Silahkan ajukan pertanyaan akademik program studi Teknik Informatika.
        </div>
      </div>
    `;
    } catch (error) {
        console.error("Reset gagal:", error);
    }
}