"""
Stage 2: Simple 2-Agent Chain
============================

This is a minimal example showing how 2 agents work together:
- Agent 1: Summarizer (takes raw data, creates summary)
- Agent 2: Formatter (takes summary, creates pretty output)

This is the simplest multi-agent pattern - good for learning.
"""

import requests


def agent_run(role, task, model="smollm2:135m", fallback_response=None):
    """Simple agent execution with optional fallback."""
    url = "http://localhost:11434/api/generate"

    full_prompt = f"{role}\n\nInput:\n{task}"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json().get("response", "No response generated.")
    except Exception as e:
        if fallback_response:
            return fallback_response
        return f"[Error: {str(e)}]"


# ============================================================================
# DEFINE THE TWO AGENTS
# ============================================================================

AGENT_1_SUMMARIZER = """You are a Summarizer.
Take raw text input and create a concise 2-3 sentence summary.
Focus on the main points only."""

AGENT_2_FORMATTER = """You are a Formatter.
Take the summary provided and format it as a nice headline + bullet points.
Make it visually appealing and easy to scan."""


# ============================================================================
# SAMPLE DATA
# ============================================================================

raw_data = """
The environmental crisis in New York City is intensifying. Air quality has
deteriorated significantly over the past week due to increased traffic,
industrial emissions, and unfavorable weather patterns. PM2.5 levels in
Manhattan have reached 52 µg/m³, exceeding EPA health standards. Brooklyn
shows 38.5 µg/m³, and Queens is at 52.1 µg/m³. Vulnerable populations
including children, elderly, and those with respiratory conditions are
advised to limit outdoor activities. The Department of Environmental
Protection recommends wearing N95 masks when outdoors and using air
filtration systems indoors.
"""


# ============================================================================
# RUN THE 2-AGENT CHAIN
# ============================================================================

print("="*70)
print("STAGE 2: SIMPLE 2-AGENT CHAIN")
print("="*70)

print("\n[RAW DATA INPUT]")
print("-" * 70)
print(raw_data)

print("\n" + "="*70)
print("AGENT 1: SUMMARIZER")
print("="*70)

# Agent 1: Summarize the raw data
summary = agent_run(
    AGENT_1_SUMMARIZER,
    raw_data,
    fallback_response="""NYC air quality has deteriorated significantly with PM2.5 levels
exceeding EPA standards in Manhattan (52 µg/m³) and Queens (52.1 µg/m³).
Vulnerable populations are advised to limit outdoor activities and wear N95 masks.
Air filtration systems are recommended indoors."""
)

print("\n[AGENT 1 OUTPUT - Summary]")
print("-" * 70)
print(summary)

print("\n" + "="*70)
print("AGENT 2: FORMATTER")
print("="*70)

# Agent 2: Takes Agent 1's output and formats it
formatted_output = agent_run(
    AGENT_2_FORMATTER,
    summary,
    fallback_response="""
NYC AIR QUALITY ALERT - ELEVATED PM2.5 LEVELS

• Manhattan: 52 µg/m³ (Exceeds EPA Standards)
• Queens: 52.1 µg/m³ (Exceeds EPA Standards)
• Brooklyn: 38.5 µg/m³ (Elevated)

ACTION REQUIRED:
• Vulnerable populations: Limit outdoor activities
• All residents: Wear N95 masks when outside
• Use indoor air filtration when possible
"""
)

print("\n[AGENT 2 OUTPUT - Formatted Report]")
print("-" * 70)
print(formatted_output)

print("\n" + "="*70)
print("DATA FLOW SUMMARY")
print("="*70)
print("""
Raw Data (unstructured, long)
        |
   AGENT 1: Summarizer
   (Extracts key points)
        |
   Summary (concise, 2-3 sentences)
        |
   AGENT 2: Formatter
   (Makes it pretty and scannable)
        |
   Final Report (structured, visual)
""")

print("\n" + "="*70)
print("HOW TO MODIFY THIS EXAMPLE")
print("="*70)
print("""
1. Change AGENT_1_SUMMARIZER role to create a different summary style
2. Change AGENT_2_FORMATTER role to format differently (e.g., HTML, markdown)
3. Add a third agent: Agent 3 could translate to another language
4. Use different raw_data for different domains (news, emails, documents)
5. Run with Ollama for real agent responses instead of fallbacks
""")

print("\n" + "="*70)
