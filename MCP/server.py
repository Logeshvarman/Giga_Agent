from fastmcp import FastMCP
import requests
import os
import base64
import yaml
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("LLM-Server")

REPO = "Logeshvarman/vc-server"         # GitHub repo (owner/repo)
BRANCH = "bonk-demo"                         # Branch to read
OLLAMA_URL = "http://127.0.0.1:11435/api/generate"

GITHUB_PAT = os.getenv("GITHUB_PAT")

HEADERS = {
    "Authorization": f"token {GITHUB_PAT}",
    "Accept": "application/vnd.github+json"
}


@mcp.tool()
def ask_llm(prompt: str) -> str:
    """Send prompt to local LLM (llama3.2)."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return resp.json().get("response", "No response")
    except Exception as e:
        return f"LLM Error: {str(e)}"

@mcp.tool()
def read_github_file(path: str) -> str:
    """
    Reads a GitHub file online using PAT authenticated API.
    Works for public & private repos.
    """
    url = f"https://api.github.com/repos/{REPO}/contents/{path}?ref={BRANCH}"

    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        return f"Error {resp.status_code}: {resp.text}"

    data = resp.json()

    if "content" not in data:
        return "File has no content"

    try:
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    except Exception:
        return "Error decoding file content"


@mcp.tool()
def list_github_files() -> list:
    """List every file in the GitHub repo via recursive tree API."""
    url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        return [f"Error {resp.status_code}: {resp.text}"]

    tree = resp.json().get("tree", [])
    files = [item["path"] for item in tree if item["type"] == "blob"]
    return files


@mcp.tool()
def analyze_repo() -> str:
    """Fetches all repo files from GitHub and analyzes them using LLM."""

    # Step 1 — Get file list
    files = list_github_files()

    if not isinstance(files, list):
        return "Failed to list repo files."

    # Step 2 — Read contents
    file_contents = {}

    for path in files:
        content = read_github_file(path)
        file_contents[path] = content

    # Step 3 — LLM prompt
    prompt = f"""
You are an expert AI code reviewer.

Analyze the following GitHub repo files and identify:
- bugs
- vulnerabilities
- missing error handling
- performance issues
- required improvements
- code smells
- missing tests

Return a clean, structured report.

FILES:
{file_contents}
"""

    # Step 4 — Ask Ollama
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        return resp.json().get("response", "No response from LLM")
    except Exception as e:
        return f"LLM Error: {str(e)}"


@mcp.tool()
def whoami() -> str:
    """Checks if PAT loaded correctly."""
    return f"GITHUB_PAT Loaded: {'Yes' if GITHUB_PAT else 'No'}"


if __name__ == "__main__":
    print("🚀 Starting LLM-Server MCP with Online GitHub Access...")
    mcp.run()
