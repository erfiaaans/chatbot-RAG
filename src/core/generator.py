from google import genai
from src.config.config import settings


class ContextAssembler:
    def assemble(self, chunks: list[dict], question: str, history: list = []) -> str:
        try:
            context = "\n\n".join(
                f"[Sumber: {c.get('meta', {}).get('source', '-')}]\n{c.get('text', '')}"
                for c in chunks
            )

            history_text = ""
            if history:
                history_text = "\n".join(
                    f"Mahasiswa: {h['question']}\nAsisten: {h['answer']}"
                    for h in history
                )

            history_section = (
                f"Riwayat Percakapan:\n{history_text}\n\n" if history_text else ""
            )

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

        except Exception as e:
            raise ValueError(f"Gagal menyusun prompt: {e}") from e


class GeminiGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.llm_model

    def generate(self, prompt: str, chunks: list, sources: list) -> dict:
        response = self.client.model.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_output_tokens,
            },
        )
        return {"answer": response.text, "sources": sources}
