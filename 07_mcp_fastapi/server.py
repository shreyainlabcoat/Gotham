# server.py
# Stateless MCP Server — Gotham Environmental Health Dashboard
# FastAPI + Model Context Protocol
#
# Tools:
#   get_air_quality_summary   — returns PM2.5, NO2, O3 readings for NYC boroughs
#   get_health_risk_assessment — returns risk level and advice for a pollutant value
#
# How to run locally:
#   python runme.py
#   or: uvicorn server:app --port 8000 --reload   (from this folder)
#
# Packages:
#   pip install fastapi uvicorn pandas

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import pandas as pd
import json

app = FastAPI()

# ── Static NYC air quality data (simulated sensor readings) ──────────────────
# In a production Gotham deployment these would come from the NYC Open Data API.

_AQ_DATA = pd.DataFrame([
    {"borough": "Manhattan", "pollutant": "PM2.5", "value": 45.2, "unit": "µg/m³"},
    {"borough": "Brooklyn",  "pollutant": "PM2.5", "value": 38.5, "unit": "µg/m³"},
    {"borough": "Queens",    "pollutant": "PM2.5", "value": 52.1, "unit": "µg/m³"},
    {"borough": "Bronx",     "pollutant": "PM2.5", "value": 41.8, "unit": "µg/m³"},
    {"borough": "Manhattan", "pollutant": "NO2",   "value": 31.4, "unit": "ppb"},
    {"borough": "Brooklyn",  "pollutant": "NO2",   "value": 28.9, "unit": "ppb"},
    {"borough": "Queens",    "pollutant": "NO2",   "value": 35.2, "unit": "ppb"},
    {"borough": "Bronx",     "pollutant": "NO2",   "value": 33.1, "unit": "ppb"},
    {"borough": "Manhattan", "pollutant": "O3",    "value": 62.0, "unit": "ppb"},
    {"borough": "Brooklyn",  "pollutant": "O3",    "value": 58.5, "unit": "ppb"},
    {"borough": "Queens",    "pollutant": "O3",    "value": 65.3, "unit": "ppb"},
    {"borough": "Bronx",     "pollutant": "O3",    "value": 60.1, "unit": "ppb"},
])

# EPA 24-hour health thresholds
_EPA_THRESHOLDS = {
    "PM2.5": 35.4,   # µg/m³
    "NO2":   53.0,   # ppb (annual standard; used here as a daily proxy)
    "O3":    70.0,   # ppb (8-hour standard)
}

# Risk bands per pollutant
_RISK_BANDS = {
    "PM2.5": [(0, 12, "Good"), (12, 35.4, "Moderate"), (35.4, 55.4, "Unhealthy for Sensitive Groups"),
              (55.4, 150.4, "Unhealthy"), (150.4, float("inf"), "Very Unhealthy")],
    "NO2":   [(0, 53, "Good"), (53, 100, "Moderate"), (100, 360, "Unhealthy"), (360, float("inf"), "Very Unhealthy")],
    "O3":    [(0, 54, "Good"), (54, 70, "Moderate"), (70, 85, "Unhealthy for Sensitive Groups"),
              (85, 105, "Unhealthy"), (105, float("inf"), "Very Unhealthy")],
}

_PROTECTIVE_ACTIONS = {
    "Good":                              ["Enjoy outdoor activities normally."],
    "Moderate":                          ["Sensitive individuals should consider limiting prolonged outdoor exertion."],
    "Unhealthy for Sensitive Groups":    ["Children, elderly, and people with asthma should limit outdoor activity.",
                                          "Wear an N95 mask if you must go outside."],
    "Unhealthy":                         ["Everyone should limit outdoor exertion.",
                                          "Wear an N95/KN95 mask outdoors.",
                                          "Use indoor air purifiers."],
    "Very Unhealthy":                    ["Avoid all outdoor activity.",
                                          "Keep windows closed and run HEPA air purifiers.",
                                          "Contact 311 or a healthcare provider if experiencing symptoms."],
}

_VULNERABLE_GROUPS = {
    "Good":                              [],
    "Moderate":                          ["People with respiratory conditions"],
    "Unhealthy for Sensitive Groups":    ["Children", "Elderly", "People with asthma or COPD"],
    "Unhealthy":                         ["Children", "Elderly", "People with asthma or COPD", "Pregnant women"],
    "Very Unhealthy":                    ["Everyone — all residents at risk"],
}


def _risk_level(pollutant: str, value: float) -> str:
    for lo, hi, label in _RISK_BANDS.get(pollutant, []):
        if lo <= value < hi:
            return label
    return "Unknown"


# ── Tool definitions (what the LLM sees) ────────────────────────────────────

TOOLS = [
    {
        "name": "get_air_quality_summary",
        "description": (
            "Returns current PM2.5, NO2, and O3 readings for NYC boroughs. "
            "Optionally filter by borough or pollutant. Flags readings that exceed EPA thresholds."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "borough": {
                    "type": "string",
                    "description": "NYC borough to filter by. Options: 'Manhattan', 'Brooklyn', 'Queens', 'Bronx', or 'all' (default).",
                },
                "pollutant": {
                    "type": "string",
                    "description": "Pollutant to filter by. Options: 'PM2.5', 'NO2', 'O3', or 'all' (default).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_health_risk_assessment",
        "description": (
            "Given a pollutant name and a measured value, returns the EPA risk level, "
            "affected vulnerable groups, and protective actions for NYC residents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pollutant": {
                    "type": "string",
                    "description": "Pollutant name: 'PM2.5', 'NO2', or 'O3'.",
                },
                "value": {
                    "type": "number",
                    "description": "Measured concentration of the pollutant.",
                },
            },
            "required": ["pollutant", "value"],
        },
    },
]


# ── Tool logic ───────────────────────────────────────────────────────────────

def run_tool(name: str, args: dict) -> str:
    if name == "get_air_quality_summary":
        df = _AQ_DATA.copy()

        borough = args.get("borough", "all")
        pollutant = args.get("pollutant", "all")

        if borough and borough.lower() != "all":
            df = df[df["borough"].str.lower() == borough.lower()]
        if pollutant and pollutant.lower() != "all":
            df = df[df["pollutant"].str.upper() == pollutant.upper()]

        if df.empty:
            return json.dumps({"error": "No data found for the given filters."})

        # Add EPA threshold and exceedance flag
        df = df.copy()
        df["epa_threshold"] = df["pollutant"].map(_EPA_THRESHOLDS)
        df["exceeds_epa"] = df["value"] > df["epa_threshold"]
        df["risk_level"] = df.apply(lambda r: _risk_level(r["pollutant"], r["value"]), axis=1)

        return df.to_json(orient="records", indent=2)

    if name == "get_health_risk_assessment":
        pollutant = args.get("pollutant", "").upper().replace("PM25", "PM2.5")
        value = float(args.get("value", 0))

        if pollutant not in _RISK_BANDS:
            return json.dumps({"error": f"Unknown pollutant '{pollutant}'. Choose PM2.5, NO2, or O3."})

        risk = _risk_level(pollutant, value)
        threshold = _EPA_THRESHOLDS[pollutant]

        result = {
            "pollutant": pollutant,
            "value": value,
            "risk_level": risk,
            "exceeds_epa_threshold": value > threshold,
            "epa_threshold": threshold,
            "vulnerable_groups": _VULNERABLE_GROUPS.get(risk, []),
            "protective_actions": _PROTECTIVE_ACTIONS.get(risk, []),
        }
        return json.dumps(result, indent=2)

    raise ValueError(f"Unknown tool: {name}")


# ── MCP JSON-RPC router ──────────────────────────────────────────────────────

@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()
    method = body.get("method")
    id_ = body.get("id")

    if isinstance(method, str) and method.startswith("notifications/"):
        return Response(status_code=202)

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "gotham-aq-server", "version": "1.0.0"},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            tool_result = run_tool(
                body["params"]["name"],
                body["params"]["arguments"],
            )
            result = {
                "content": [{"type": "text", "text": tool_result}],
                "isError": False,
            }
        else:
            raise ValueError(f"Method not found: {method}")

    except Exception as e:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": str(e)}}
        )

    return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result})


@app.options("/mcp")
async def mcp_options():
    return Response(status_code=204, headers={"Allow": "GET, POST, OPTIONS"})


@app.get("/mcp")
async def mcp_get():
    return Response(
        content=json.dumps({"error": "This MCP server uses stateless HTTP. Use POST."}),
        status_code=405,
        headers={"Allow": "GET, POST, OPTIONS"},
        media_type="application/json",
    )
