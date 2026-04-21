from google import genai
from src.config.config import settings
from src.config.prompts import load_prompt

PROMPT_TEMPLATE = load_prompt("prompts.md")


class ContextAssembler:
    def format_chunk(self, c: dict) -> str:
        source = c.get("meta", {}).get("source", "-")
        text = c.get("text", "").strip()

        return f"""[Sumber: {source}]\n{text}"""

    def assemble(self, chunks: list[dict], question: str, history: list = []) -> str:
        try:
            context = "\n\n=== CHUNK ===\n\n".join(self.format_chunk(c) for c in chunks)

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

    def generate(self, prompt: str) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": settings.temperature,
                    "max_output_tokens": settings.max_output_tokens,
                },
            )
            return response.text  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Gagal generate jawaban: {e}") from e
