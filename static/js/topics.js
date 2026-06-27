// Definisi data
const popularTopics = [
  {
    title: "Apa saja layanan surat untuk mahasiswa?",
    iconPath: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
  },
  {
    title: "Kapan mata kuliah AI Lanjut kelas 6B dilaksanakan?",
    iconPath: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
  },
  {
    title: "Ruang Lab TIF digunakan untuk mata kuliah apa?",
    iconPath: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
  },
  {
    title: "Kapan ujian skripsi dilaksanakan?",
    iconPath: "M12 14l9-5-9-5-9 5 9 5z M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"
  },
  {
    title: "Mata kuliah semester 5 Teknik Informatika apa saja?",
    iconPath: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
  },
  {
    title: "Apa saja ketentuan umum pelaksanaan magang?",
    iconPath: "M21 13.255A23.93 23.93 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
  },
  {
    title: "Bagaimana cara registrasi dan pengisian KRS bagi mahasiswa baru?",
    iconPath: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012-2m-6 9l2 2 4-4"
  },
  {
    title: "Bagaimana struktur penulisan skripsi?",
    iconPath: "M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
  }
];

// Fungsi untuk render
function renderTopics() {
  const container = document.getElementById('topics-container');
  if (!container) return;

  container.innerHTML = popularTopics.map(topic => `
    <div
      onclick="goToChat('${topic.title}')"
      class="flex items-center gap-3 p-3 rounded-xl border border-slate-100 bg-slate-50 hover:bg-brand-50 hover:border-brand-200 transition-colors cursor-pointer group"
    >
      <div class="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-brand-500 shadow-sm group-hover:text-brand-600">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${topic.iconPath}"></path>
        </svg>
      </div>
      <span class="text-sm font-medium text-slate-700">${topic.title}</span>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', renderTopics);