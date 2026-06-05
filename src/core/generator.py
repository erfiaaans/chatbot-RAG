import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from google import genai

from src.config.config import settings
from src.config.prompts import load_prompt

PROMPT_TEMPLATE = load_prompt("prompts.md")


class ContextAssembler:
    def format_chunk(self, c: dict) -> str:
        source = c.get("meta", {}).get("source", "Umum")
        text = c.get("text", "").strip()

        return f"[{source}]\n{text}"

    def assemble(self, chunks: list[dict], question: str, history: list = []) -> str:
        try:
            context = "\n\n---\n\n".join(self.format_chunk(c) for c in chunks)

            if history:
                history_text = "\n".join(
                    f"Mahasiswa: {h['question']}\nAsisten: {h['answer']}"
                    for h in history
                )
            else:
                history_text = (
                    "Belum ada riwayat percakapan. Mahasiswa baru memulai chat."
                )

            history_section = history_text

            return PROMPT_TEMPLATE.format(
                history_section=history_section,
                context=context,
                question=question,
            )

        except Exception as e:
            raise ValueError(f"Gagal menyusun prompt: {e}") from e


class GeminiGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.llm_model
        print(f"Using Gemini model: {self.model}")

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": settings.temperature,
                    "max_output_tokens": settings.max_output_tokens,
                },
            )
            return response.text or ""
        except Exception as e:
            error_msg = str(e)
        if (
            "429" in error_msg
            or "RESOURCE_EXHAUSTED" in error_msg
            or "quota" in error_msg.lower()
        ):
            raise RuntimeError(
                "Sistem sedang sibuk atau batas penggunaan harian telah tercapai. Mohon tunggu beberapa saat dan coba lagi."
            )
        raise RuntimeError(f"Gagal generate jawaban: {e}") from e


# Testing
if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    try:
        from src.core.retriever import Retriever

        print("=" * 60, flush=True)
        print("PENGUJIAN MODUL GENERATION", flush=True)
        print("=" * 60, flush=True)

        print("\nPengujian Context Assembler", flush=True)
        print("-" * 40, flush=True)

        retriever = Retriever()
        assembler = ContextAssembler()

        question = "Apa saja isi dari Kajian Teoritis?"
        chunks = retriever.retrieve(question)

        print(f"Query         : {question}", flush=True)
        print(f"Jumlah chunk  : {len(chunks)}", flush=True)

        prompt = assembler.assemble(chunks, question)
        print(prompt[:500] + " ...", flush=True)
        print("[OK] Context Assembler berhasil.", flush=True)

        print("\nPengujian LLM Generator", flush=True)
        print("-" * 40, flush=True)

        generator = GeminiGenerator()
        answer = generator.generate(prompt)

        print(f"Pertanyaan    : {question}", flush=True)
        print(f"Jawaban LLM   :\n{answer}", flush=True)

        print("\n" + "=" * 60, flush=True)
        print("Pengujian selesai.", flush=True)

    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback

        traceback.print_exc()
