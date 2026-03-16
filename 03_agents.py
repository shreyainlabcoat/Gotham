"""
Stage 1: Understanding Multi-Agent Workflows
============================================

This script demonstrates how three agents work together in sequence:
1. Agent 1: Fetches and validates data
2. Agent 2: Analyzes the data
3. Agent 3: Formats the analysis into a report

Key concept: Each agent's OUTPUT becomes the next agent's INPUT
"""

import requests
import json


# ============================================================================
# HELPER FUNCTION: Core Agent Execution
# ============================================================================

def agent_run(role, task, model="smollm2:135m"):
    """
    Execute an agent by sending a prompt to a local Ollama instance.

    Args:
        role: System prompt describing the agent's role
        task: Input data/question for the agent
        model: Which LLM model to use (default: smollm2:135m)

    Returns:
        Agent's response text
    """
    url = "http://localhost:11434/api/generate"

    full_prompt = f"{role}\n\nTask:\n{task}"

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
        # Fallback when Ollama is not running
        return f"[FALLBACK RESPONSE - Ollama unavailable: {str(e)}]"


# ============================================================================
# STAGE 1: UNDERSTAND THE THREE-AGENT WORKFLOW
# ============================================================================

print("="*80)
print("STAGE 1: SIMPLE THREE-AGENT WORKFLOW")
print("="*80)
print()

# Define the three agents with their specific roles
AGENT_1_ROLE = """You are a Data Fetcher & Validator.
Your job is to retrieve or describe air quality data for New York City.
Format your output as a simple text report with:
- Location names
- PM2.5 values
- Data timestamps
Keep it concise and organized."""

AGENT_2_ROLE = """You are an Environmental Analyst.
Your job is to analyze air quality data and identify health risks.
Provide:
- Which locations have unhealthy air
- Health impact assessment
- Risk level (Low/Medium/High)
Keep analysis clear and actionable."""

AGENT_3_ROLE = """You are a Report Writer.
Your job is to take analysis and write a professional summary.
Create a 3-sentence executive summary suitable for stakeholders.
Include:
- Current situation
- Key risks
- Recommended actions"""


# ============================================================================
# WORKFLOW EXECUTION: Data flows through agents in sequence
# ============================================================================

print("\n>> AGENT 1: Data Fetcher")
print("-" * 60)

# Agent 1 Input: User request for data
agent_1_input = "Provide current PM2.5 air quality data for NYC (Manhattan, Brooklyn, Queens)"

print(f"Input: {agent_1_input}\n")

# Agent 1 Output: Raw data
agent_1_output = agent_run(AGENT_1_ROLE, agent_1_input)
print(f"Output:\n{agent_1_output}\n")

# Save Agent 1's output for visualization
data_report = agent_1_output


# ============================================================================

print("\n>> AGENT 2: Environmental Analyst")
print("-" * 60)

# Agent 2 Input: Agent 1's output! (This is the key pattern)
agent_2_input = f"""Analyze this air quality data:

{agent_1_output}"""

print(f"Input: [Agent 1's output above]\n")

# Agent 2 Output: Analysis
agent_2_output = agent_run(AGENT_2_ROLE, agent_2_input)
print(f"Output:\n{agent_2_output}\n")

# Save Agent 2's output for visualization
analysis_report = agent_2_output


# ============================================================================

print("\n>> AGENT 3: Report Writer")
print("-" * 60)

# Agent 3 Input: Agent 2's output! (Chaining continues)
agent_3_input = f"""Based on this environmental analysis:

{agent_2_output}

Write an executive summary."""

print(f"Input: [Agent 2's output above]\n")

# Agent 3 Output: Final report
agent_3_output = agent_run(AGENT_3_ROLE, agent_3_input)
print(f"Output:\n{agent_3_output}\n")

# Save Agent 3's output
final_report = agent_3_output


# ============================================================================
# VISUALIZE THE DATA FLOW
# ============================================================================

print("\n" + "="*80)
print("DATA FLOW VISUALIZATION")
print("="*80)

print("""
User Request
     |
     v
[AGENT 1: Data Fetcher]  <- Gets raw data
     |
     v (outputs data report)
[AGENT 2: Analyst]       <- Analyzes Agent 1 output
     |
     v (outputs analysis)
[AGENT 3: Report Writer] <- Summarizes Agent 2 output
     |
     v
Final Executive Summary
""")


# ============================================================================
# KEY LEARNINGS
# ============================================================================

print("\n" + "="*80)
print("KEY LEARNINGS FOR MULTI-AGENT WORKFLOWS")
print("="*80)

lessons = [
    "1. SEQUENTIAL EXECUTION: Agents run one after another, not in parallel",
    "2. DATA CONTRACTS: Agent N's output format must match Agent N+1's input expectations",
    "3. ROLE CLARITY: Each agent has a specific, well-defined role",
    "4. ERROR PROPAGATION: If Agent 1 fails, Agent 2 works with garbage input",
    "5. FALLBACK IMPORTANT: Define fallback behavior when LLM is unavailable",
    "6. TRANSPARENCY: Log each agent's input/output for debugging"
]

for lesson in lessons:
    print(f"\n{lesson}")


# ============================================================================
# NEXT STEPS
# ============================================================================

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)

next_steps = """
1. Review how each agent's ROLE was defined
2. Notice how Agent 1's OUTPUT became Agent 2's INPUT
3. See how Agent 2's OUTPUT became Agent 3's INPUT
4. Modify this script: Create your own 2-agent chain (Stage 2)
5. Explore advanced patterns: VLMs, ALMs, parallel queries (Stage 3)

To run this script with a real LLM:
  1. Start Ollama: ollama serve
  2. Run: python 03_agents.py
  3. Watch agents work together in sequence!
"""

print(next_steps)

print("\n" + "="*80)
