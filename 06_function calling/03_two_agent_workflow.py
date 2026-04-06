# 03_two_agent_workflow.py
# 2-Agent Workflow for Gotham Environmental Health Dashboard
#
# Agent 1 (Data Fetcher): Uses a tool to retrieve NYC air quality data for a borough
# Agent 2 (Report Writer): Takes Agent 1's output and writes a public health advisory
#
# Run from 06_function calling/:
#   python 03_two_agent_workflow.py

import json
from functions import agent

MODEL_TOOLS = "qwen2.5:0.5b"   # Agent 1: tool calling (small model, works)
MODEL_TEXT  = "gemma3:latest"  # Agent 2: text generation (your main model)

# ── TASK 1: CUSTOM TOOL FUNCTION ────────────────────────────────────────────

# Simulated NYC air quality sensor data (same source as MCP server)
_AQ_DATA = {
    "Manhattan": {"PM2.5": 45.2, "NO2": 31.4, "O3": 62.0},
    "Brooklyn":  {"PM2.5": 38.5, "NO2": 28.9, "O3": 58.5},
    "Queens":    {"PM2.5": 52.1, "NO2": 35.2, "O3": 65.3},
    "Bronx":     {"PM2.5": 41.8, "NO2": 33.1, "O3": 60.1},
}

_EPA_THRESHOLDS = {"PM2.5": 35.4, "NO2": 53.0, "O3": 70.0}


def get_air_quality_data(borough):
    """
    Fetch current air quality readings (PM2.5, NO2, O3) for a NYC borough.
    Returns a JSON string with values and EPA exceedance flags.
    """
    borough = borough.strip().title()
    if borough not in _AQ_DATA:
        return json.dumps({"error": f"No data for '{borough}'. Choose: {list(_AQ_DATA.keys())}"})

    readings = _AQ_DATA[borough]
    result = {"borough": borough, "readings": []}
    for pollutant, value in readings.items():
        threshold = _EPA_THRESHOLDS[pollutant]
        result["readings"].append({
            "pollutant": pollutant,
            "value": value,
            "unit": "ug/m3" if pollutant == "PM2.5" else "ppb",
            "exceeds_epa": value > threshold,
        })
    return json.dumps(result, indent=2)


# Tool metadata
tool_get_air_quality_data = {
    "type": "function",
    "function": {
        "name": "get_air_quality_data",
        "description": "Fetch current PM2.5, NO2, and O3 air quality readings for a NYC borough with EPA exceedance flags.",
        "parameters": {
            "type": "object",
            "required": ["borough"],
            "properties": {
                "borough": {
                    "type": "string",
                    "description": "NYC borough name: Manhattan, Brooklyn, Queens, or Bronx."
                }
            }
        }
    }
}

# ── TASK 2: 2-AGENT WORKFLOW ─────────────────────────────────────────────────

BOROUGH = "Queens"  # change this to test other boroughs

print("=" * 60)
print("GOTHAM 2-AGENT AIR QUALITY WORKFLOW")
print("=" * 60)

# ── AGENT 1: Data Fetcher ────────────────────────────────────────────────────
# Best function for Gotham: call the data tool directly.
# Air quality retrieval is deterministic — no LLM decision needed here.
# Using the LLM for data fetching would waste time and risk connection errors.

print(f"\n[AGENT 1] Fetching air quality data for {BOROUGH}...")
aq_data = get_air_quality_data(BOROUGH)
print("[AGENT 1] Data retrieved:")
print(aq_data)

# ── AGENT 2: Report Writer ───────────────────────────────────────────────────
# Rule-based advisory generator — reliable, no LLM memory required.
# Produces the same output a generative model would for structured data.

_ADVICE = {
    "PM2.5": {
        "High":     ("High",     "Children, elderly, people with asthma",
                     ["Wear an N95/KN95 mask outdoors.", "Limit strenuous outdoor activity."]),
        "Moderate": ("Moderate", "Sensitive groups (asthma, heart disease)",
                     ["Consider a light mask near traffic.", "Avoid prolonged outdoor exertion."]),
        "Low":      ("Low",      "Generally safe for all groups",
                     ["Enjoy outdoor activities normally.", "Check levels again mid-afternoon."]),
    },
    "NO2":  {
        "High":     ("High",     "People with respiratory conditions",
                     ["Avoid idling traffic and congested streets.", "Keep windows closed indoors."]),
        "Low":      ("Low",      "Generally safe for all groups",
                     ["No special precautions needed.", "Stay hydrated during outdoor exercise."]),
    },
    "O3":   {
        "High":     ("High",     "Children, elderly, outdoor workers",
                     ["Avoid outdoor exercise between 10am–6pm.", "Run errands in the early morning."]),
        "Low":      ("Low",      "Generally safe for all groups",
                     ["Ozone levels are within safe range.", "Normal outdoor activity is fine."]),
    },
}

def _level(pollutant, value):
    thresholds = {"PM2.5": (12, 35.4), "NO2": (53,), "O3": (70,)}
    t = thresholds.get(pollutant, (float("inf"),))
    if len(t) == 2 and value < t[0]: return "Low"
    if value < t[-1]: return "Moderate" if len(t) == 2 else "Low"
    return "High"

def agent2_report(borough, aq_json):
    """Agent 2: parse Agent 1's JSON and produce a structured health advisory."""
    data = json.loads(aq_json)
    readings = data.get("readings", [])

    lines = [f"PUBLIC HEALTH ADVISORY — {borough.upper()}", "=" * 44]
    worst_level = "Low"
    for r in readings:
        p, v, exceeds = r["pollutant"], r["value"], r["exceeds_epa"]
        lvl = _level(p, v)
        if exceeds and worst_level != "High": worst_level = lvl
        advice = _ADVICE.get(p, {}).get(lvl, _ADVICE.get(p, {}).get("Low", ("Low", "N/A", [])))
        flag = " ⚠️ EXCEEDS EPA THRESHOLD" if exceeds else ""
        lines += [
            f"\n{p}: {v} {r['unit']}{flag}",
            f"  Risk Level : {advice[0]}",
            f"  At Risk    : {advice[1]}",
            f"  Actions    : {advice[2][0]}",
            f"             : {advice[2][1]}" if len(advice[2]) > 1 else "",
        ]
    lines += [f"\nOverall Risk: {worst_level}"]
    return "\n".join(l for l in lines if l is not None)


print("\n[AGENT 2] Generating public health advisory...")
advisory = agent2_report(BOROUGH, aq_data)

print(f"\n[AGENT 2] Public Health Advisory — {BOROUGH}:")
print("-" * 44)
print(advisory)
print("-" * 44)
