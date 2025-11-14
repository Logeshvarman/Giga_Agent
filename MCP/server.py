from fastmcp import FastMCP
import requests
import os
import yaml

REPO_PATH = "vc-server"   # <--- your local cloned repo

mcp = FastMCP("LLM-Server")

@mcp.tool()
def ask_llm(prompt: str) -> str:
    resp = requests.post(
        "http://127.0.0.1:11435/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        },
        timeout=30
    )
    return resp.json().get("response", "no response")

@mcp.tool()
def get_repo_files_from_build() -> dict:
    """
    Reads vc-server/.github/workflows/build.yml
    Extracts 'paths' section and returns file contents.
    """

    build_path = os.path.join(REPO_PATH, ".github", "workflows", "build.yml")

    if not os.path.exists(build_path):
        return {"error": f"{build_path} not found"}


    with open(build_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    paths = []

    if "on" in config:
        for event in ["push", "pull_request"]:
            if event in config["on"]:
                if "paths" in config["on"][event]:
                    paths += config["on"][event]["paths"]

    paths = list(set(paths))  # unique

    results = {}

    for p in paths:
        clean_path = p.replace("/**", "").replace("**", "")
        abs_path = os.path.join(REPO_PATH, clean_path)

        if not os.path.exists(abs_path):
            results[p] = "NOT FOUND"
            continue

        if os.path.isfile(abs_path):
            results[p] = open(abs_path, "r", encoding="utf-8").read()

        else:
            folder_map = {}
            for root, _, files in os.walk(abs_path):
                for file in files:
                    full = os.path.join(root, file)
                    try:
                        folder_map[full] = open(full, "r", encoding="utf-8").read()
                    except:
                        folder_map[full] = "CANNOT READ FILE"
            results[p] = folder_map

    return results


@mcp.tool()
def analyze_repo() -> str:
    """Reads repo files based on build.yml and sends them to LLM for analysis."""

    files = get_repo_files_from_build()

    prompt = f"""
You are an expert AI code reviewer.
Analyze the following files, find issues, bugs, and improvements:

{files}

Return a detailed analysis.
"""

    resp = requests.post(
        "http://127.0.0.1:11435/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )

    return resp.json().get("response", "no response")

if __name__ == "__main__":
    print("Starting LLM-Server MCP server...")
    mcp.run()
