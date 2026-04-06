"""
functions.py
Helper functions for agent orchestration with Ollama function calling.
"""

import requests
import json

PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
CHAT_URL = f"{OLLAMA_HOST}/api/chat"


def agent(messages, model, output="text", tools=None):
    """
    Send a chat request to Ollama, optionally with tools.

    Parameters
    ----------
    messages : list of dict
        Chat history in Ollama message format.
    model : str
        Ollama model name (must support tools when output="tools").
    output : str
        "text"  — return the assistant's text reply as a string.
        "tools" — execute any tool calls and return a list of tool-call
                  dicts, each with an added "output" key holding the result.
    tools : list of dict or None
        Tool metadata schemas to pass to the model.

    Returns
    -------
    str | list
        Text response (output="text") or list of executed tool calls (output="tools").
    """
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if tools:
        body["tools"] = tools

    response = requests.post(CHAT_URL, json=body)
    response.raise_for_status()
    result = response.json()

    message = result.get("message", {})

    # ── Tool-call mode ──────────────────────────────────────────────────────
    if output == "tools":
        tool_calls = message.get("tool_calls", [])
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            raw_args = tool_call["function"].get("arguments", {})
            func_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            # Look up the function by name in the caller's global scope.
            # We import the caller's globals by walking up the call stack.
            import inspect
            caller_globals = inspect.stack()[1].frame.f_globals
            func = caller_globals.get(func_name)
            if func:
                tool_call["output"] = func(**func_args)
        return tool_calls

    # ── Text mode ───────────────────────────────────────────────────────────
    return message.get("content", "")


def agent_run(role, task, model="qwen2.5:0.5b"):
    """
    Simple text-generation agent using Ollama's /api/generate endpoint.
    No tool calling — just sends a prompt and returns the text response.

    Parameters
    ----------
    role : str
        System prompt describing the agent's persona and job.
    task : str
        The data or question the agent should process.
    model : str
        Ollama model name.

    Returns
    -------
    str
        The model's text response.
    """
    url = f"http://localhost:{PORT}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user",   "content": task},
        ],
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        if not response.ok:
            return f"[agent_run error {response.status_code}: {response.text}]"
        return response.json().get("message", {}).get("content", "No response generated.")
    except Exception as e:
        return f"[agent_run error: {e}]"
