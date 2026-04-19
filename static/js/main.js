const docList = [];
let isLoading = false;

// ===== AUTO RESIZE TEXTAREA =====
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ===== HANDLE ENTER KEY =====
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ===== SUGGESTION CHIPS =====
function sendSuggestion(text) {
    document.getElementById('questionInput').value = text;
    sendMessage();
}

// ===== SEND MESSAGE =====
async function sendMessage() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question || isLoading) return;

    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    appendMessage('user', question);
    input.value = '';
    input.style.height = 'auto';

    const typingId = appendTyping();
    setLoading(true);

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        removeTyping(typingId);
        if (data.error) {
            appendMessage('bot', '⚠️ ' + data.error);
        } else {
            appendMessage('bot', data.answer, data.sources || []);
        }
    } catch (err) {
        removeTyping(typingId);
        appendMessage('bot', '⚠️ Gagal terhubung ke server. Pastikan aplikasi berjalan.');
    } finally {
        setLoading(false);
    }
}

// ===== APPEND MESSAGE =====
function appendMessage(role, text, sources = []) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    let sourcesHtml = '';
    if (sources.length > 0) {
        sourcesHtml = `<div class="sources">
      ${sources.map(s => `<span class="source-tag">📄 ${s}</span>`).join('')}
    </div>`;
    }

    div.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="bubble">
      ${escapeHtml(text).replace(/\n/g, '<br>')}
      ${sourcesHtml}
    </div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

// ===== TYPING INDICATOR =====
function appendTyping() {
    const messages = document.getElementById('messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = id;
    div.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <div class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ===== LOADING STATE =====
function setLoading(state) {
    isLoading = state;
    document.getElementById('sendBtn').disabled = state;
    document.getElementById('questionInput').disabled = state;
}

// ===== UPLOAD FILE =====
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (!files.length) {
        showToast('Pilih file terlebih dahulu.', 'error');
        return;
    }

    const btn = document.getElementById('uploadBtn');
    const progress = document.getElementById('uploadProgress');
    const bar = document.getElementById('uploadBar');
    btn.disabled = true;
    btn.textContent = 'Mengindeks...';
    progress.classList.add('active');

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        bar.style.width = ((i / files.length) * 80) + '%';
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'berhasil') {
                addDocToList(data.filename, data.chunks);
                showToast(`✓ ${data.filename} berhasil diindeks (${data.chunks} chunk)`, 'success');
            } else {
                showToast(`✗ Gagal: ${data.error}`, 'error');
            }
        } catch {
            showToast('Gagal terhubung ke server.', 'error');
        }
    }

    bar.style.width = '100%';
    setTimeout(() => {
        progress.classList.remove('active');
        bar.style.width = '0%';
    }, 600);

    btn.disabled = false;
    btn.innerHTML = '⬆ Indeks Dokumen';
    fileInput.value = '';
}

// ===== ADD DOC TO LIST =====
function addDocToList(filename, chunks) {
    if (docList.includes(filename)) return;
    docList.push(filename);

    const list = document.getElementById('docList');
    const empty = list.querySelector('.doc-empty');
    if (empty) empty.remove();

    const ext = filename.split('.').pop().toUpperCase();
    const icon = ext === 'PDF' ? '📕' : ext === 'DOCX' ? '📘' : '📝';
    const item = document.createElement('div');
    item.className = 'doc-item';
    item.innerHTML = `
    <span class="doc-icon">${icon}</span>
    <span class="doc-name" title="${filename}">${filename}</span>
    <span class="doc-badge">${chunks} chunk</span>`;
    list.appendChild(item);
}

// ===== RESET CHAT =====
async function resetChat() {
    try { await fetch('/reset', { method: 'POST' }); } catch { }
    document.getElementById('messages').innerHTML = `
    <div class="welcome" id="welcome">
      <div class="welcome-icon">🤖</div>
      <h2>Halo, Mahasiswa TIF!</h2>
      <p>Tanyakan informasi akademik Prodi TIF UNIPMA. Saya akan menjawab berdasarkan dokumen resmi yang telah diindeks.</p>
      <div class="suggestions">
        <button class="suggestion-chip" onclick="sendSuggestion(this.textContent)">Jadwal kuliah semester ini?</button>
        <button class="suggestion-chip" onclick="sendSuggestion(this.textContent)">Syarat sidang skripsi?</button>
        <button class="suggestion-chip" onclick="sendSuggestion(this.textContent)">Prosedur pengisian KRS?</button>
        <button class="suggestion-chip" onclick="sendSuggestion(this.textContent)">Informasi beasiswa KIP?</button>
      </div>
    </div>`;
    showToast('Riwayat percakapan direset.', 'success');
}

// ===== TOAST =====
function showToast(msg, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ===== ESCAPE HTML =====
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ===== DRAG & DROP =====
const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    document.getElementById('fileInput').files = e.dataTransfer.files;
});