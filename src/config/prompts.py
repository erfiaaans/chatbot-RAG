from pathlib import Path


def load_prompt(filename: str) -> str:
    path = Path(__file__).parent / filename
    return path.read_text(encoding="utf-8").strip()
#Testing
if __name__ == "__main__":

    print("\nPengujian Load Prompt Template")
    print("-" * 40)

    prompt = load_prompt("prompts.md")

    print(f"Status        : Berhasil dimuat")
    print(f"Panjang prompt: {len(prompt)} karakter")
    print(f"Jumlah baris  : {prompt.count(chr(10)) + 1} baris")
    print(f"\n--- Cuplikan Prompt (100 karakter pertama) ---")
    print(prompt[:100] + " ...")

    print("\n" + "=" * 60)
    print("Pengujian Modul Prompt Engineering selesai.")
    print("=" * 60)