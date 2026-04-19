from google import genai
from config import settings


class ContextAssembler:
    def assemble(self, chunks: list[dict], question: str, history: list = []) -> str:
        context = "\n\n".join(f"[Sumber: {c['filename']}]\n{c['text']}" for c in chunks)
        history_text = ""
        if history:
            history_text = "\n".join(
                f"Mahasiswa: {h['question']}\nAsisten: {h['answer']}" for h in history
            )
        if history_text:
            history_section = f"Riwayat Percakapan:\n{history_text}\n\n"
        else:
            history_section = ""

        prompt = f"""Kamu adalah asisten akademik Prodi TIF UNIPMA.
Jawab pertanyaan HANYA berdasarkan konteks dokumen berikut.
Jika informasi tidak tersedia dalam konteks, sampaikan bahwa
informasi tidak ditemukan dan sarankan menghubungi prodi.
{history_section}

Konteks dokumen:
{context}

Pertanyaan: {question}
Jawaban:"""
        return prompt


class GeminiGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.llm_model

    def generate(self, prompt: str, chunks: list) -> dict:
        response = self.client.model.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_output_tokens,
            },
        )

        sources = list({c["filename"] for c in chunks})
        return {"answer": response.text, "sources": sources}
