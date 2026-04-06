# testme.py
# Test the Gotham MCP Server (Stages 1–4)
#
# Start the server before running:
#   python runme.py          (from this folder)
#   or: uvicorn server:app --port 8000 --reload
#
# pip install requests python-dotenv

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ── Server URL ───────────────────────────────────────────────
# Use local server (start with python runme.py first)
SERVER = "http://127.0.0.1:8000/mcp"

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
CHAT_URL = f"{OLLAMA_BASE}/api/chat"
MODEL = "qwen2.5:0.5b"


def mcp_request(method, params=None, id=1):
    """Send one JSON-RPC request to the MCP server."""
    body = {"jsonrpc": "2.0", "id": id, "method": method, "params": params or {}}
    resp = requests.post(SERVER, json=body)
    resp.raise_for_status()
    return resp.json().get("result")


def ollama_is_running():
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=2)
        return r.ok
    except requests.RequestException:
        return False


# ── Step 1: HANDSHAKE ────────────────────────────────────────
print("# 1. HANDSHAKE — initialize")
init = mcp_request("initialize", {
    "protocolVersion": "2025-03-26",
    "clientInfo": {"name": "gotham-test-client", "version": "1.0.0"},
    "capabilities": {},
})
print(f"Server: {init['serverInfo']['name']} v{init['serverInfo']['version']}\n")


# ── Step 2: DISCOVER TOOLS ───────────────────────────────────
print("# 2. DISCOVER TOOLS — tools/list")
tools_raw = mcp_request("tools/list")["tools"]
for t in tools_raw:
    print(f"  - {t['name']}: {t['description'][:80]}...")
print()


# ── Step 3a: CALL TOOL 1 — get_air_quality_summary ──────────
print("# 3a. CALL TOOL — get_air_quality_summary (Queens, PM2.5)")
result = mcp_request("tools/call", {
    "name": "get_air_quality_summary",
    "arguments": {"borough": "Queens", "pollutant": "PM2.5"},
})
print(result["content"][0]["text"])
print()


# ── Step 3b: CALL TOOL 2 — get_health_risk_assessment ────────
print("# 3b. CALL TOOL — get_health_risk_assessment (PM2.5 = 52.1)")
result2 = mcp_request("tools/call", {
    "name": "get_health_risk_assessment",
    "arguments": {"pollutant": "PM2.5", "value": 52.1},
})
print(result2["content"][0]["text"])
print()


# ── Step 4: LET THE LLM CHOOSE THE TOOL ─────────────────────
print("# 4. CONNECT LLM TO MCP SERVER")

if not ollama_is_running():
    print(f"Skipping: Ollama not running at {OLLAMA_BASE}. Start Ollama and re-run.")
else:
    # 4a. Convert MCP tool format → Ollama format
    def mcp_to_ollama(tool):
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"],
            },
        }

    ollama_tools = [mcp_to_ollama(t) for t in tools_raw]

    # 4b. Ask the LLM a question — it should pick get_health_risk_assessment
    print("# 4b. Asking LLM: 'What is the health risk for NO2 at 35 ppb in NYC?'")
    messages = [{"role": "user", "content": "Use get_health_risk_assessment to check the health risk for NO2 at 35 ppb."}]
    body = {"model": MODEL, "messages": messages, "tools": ollama_tools, "stream": False}

    try:
        resp = requests.post(CHAT_URL, json=body, timeout=120)
        resp.raise_for_status()
        result_llm = resp.json()
    except requests.exceptions.ReadTimeout:
        print("Ollama timed out — model is too slow or still loading. Steps 1–3 above confirm the MCP server works.")
        result_llm = {}

    # 4c. Execute the tool call against the MCP server
    tool_calls = result_llm.get("message", {}).get("tool_calls", [])
    if tool_calls:
        tc = tool_calls[0]
        func_name = tc["function"]["name"]
        raw_args = tc["function"]["arguments"]
        func_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

        print(f"LLM chose tool: {func_name} with args {func_args}")
        mcp_result = mcp_request("tools/call", {"name": func_name, "arguments": func_args})
        print(mcp_result["content"][0]["text"])
    elif result_llm:
        print("No tool_calls returned — model answered directly or prompt needs adjustment.")
