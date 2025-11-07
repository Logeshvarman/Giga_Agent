import os
import textwrap
from pathlib import Path
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate

# ---------------------- CONFIG -------------------------
PROJECT_PATH = "./sample_project"     
APPLY_FIX = True                     # True = overwrite files with fixes
EXTENSIONS = [".js", ".ts", ".py", ".java", ".cs"]   # File types to scan
OLLAMA_MODEL = "phi3:mini"            # Local model (must exist in Ollama)
# -------------------------------------------------------


def get_source_files(folder):
    """Recursively find all matching source files."""
    for root, _, files in os.walk(folder):
        for file in files:
            if any(file.endswith(ext) for ext in EXTENSIONS):
                yield Path(root) / file


# def create_prompt(file_path, content):
#     """Generate the AI prompt for syntax checking and fixing."""
#     prompt = f"""
# You are a strict Python code compiler and repair assistant.

# Your task:
# 1. Identify and correct ALL syntax errors, indentation problems, and unsafe patterns.
# 2. Ensure the corrected code runs without syntax errors.
# 3. Always output the corrected full code between triple backticks.

# File: {file_path}

# Original code:
# {content}

# If the code is already good, re-output it unchanged inside triple backticks.
# If you cannot fix it, return:
# """
#     return textwrap.dedent(prompt)

def create_prompt(file_path, content):
    """Generate the AI prompt for syntax checking and fixing for multiple languages."""
    prompt = f"""
You are a strict multi-language code compiler and repair assistant.

Supported languages: Python, Java, C#, JavaScript, TypeScript.

Your task:
1. Detect and correct ALL syntax errors, indentation issues, and structural problems.
2. For each language, ensure the corrected code would compile or run successfully.
3. Do not rewrite the code unnecessarily — preserve formatting and logic.
4. Always output the corrected full code between triple backticks (```) only.
5. If the file is already correct, re-output it unchanged.
6. If the code cannot be fixed safely, return an explanation instead.

File path: {file_path}

Original code:
{content}
"""
    return textwrap.dedent(prompt)

def analyze_and_fix(llm, file_path):
    """Analyze a file and return AI-suggested corrected code."""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[Error] Failed to read {file_path}: {e}")
        return None

    prompt_text = create_prompt(file_path, content)
    prompt = PromptTemplate.from_template("{input_text}")
    chain = prompt | llm

    print(f"\n[Analyzing] {file_path}...")
    result = chain.invoke({"input_text": prompt_text})

    result_text = result if isinstance(result, str) else result.content
    if not result_text:
        return None

    # Extract corrected code between triple backticks
    code = None
    if "```" in result_text:
        parts = result_text.split("```")
        for p in parts:
            p = p.strip()
            # Skip code block language identifiers
            if p and not p.startswith(("diff", "bash", "json", "python")):
                code = p
                break

    # Fallback: use the entire response if no code block was found
    if not code:
        code = result_text.strip()

    return code


def save_fix(file_path, new_content):
    """Overwrite the file with the new content."""
    Path(file_path).write_text(new_content, encoding="utf-8")
    print(f"[Fixed] Applied fix to {file_path}")


def main():
    print("Code AI Fixer")

    llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.0, max_tokens=2048)
    files = list(get_source_files(PROJECT_PATH))

    if not files:
        print(f"[Warning] No source files found in {PROJECT_PATH}")
        return

    for file_path in files:
        new_code = analyze_and_fix(llm, file_path)
        if not new_code:
            print(f"[Error] No output for {file_path}")
            continue

        original = Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()
        if new_code.strip() == original.strip():
            print(f"[OK] {file_path} looks clean — no changes needed.")
        else:
            print(f"Fix suggestion for {file_path}:")
            print(new_code[:1000])
            if len(new_code) > 1000:
                print("...output truncated...")

            if APPLY_FIX:
                save_fix(file_path, new_code)

    print("Scan complete")


if __name__ == "__main__":
    main()
