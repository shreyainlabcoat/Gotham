"""
HANDS-ON: Modify System Prompts and See Results Change

This is the working file to understand system prompt engineering.
You can modify the system prompts below and see how agent behavior changes.

HOW TO USE THIS FILE:
=====================
1. Run it: python 02_prompts_interactive.py
2. Notice responses from 3 different agents (different prompts)
3. Pick one system prompt
4. MODIFY IT (change the role, tone, constraints)
5. Run again and see how output changes
6. Screenshot both TO SUBMIT

This demonstrates the core principle:
SYSTEM PROMPT -> AGENT BEHAVIOR
"""

import requests


def query_mollama(system_prompt, user_question, model="smollm2:135m", use_fallback=True):
    """
    Query Ollama with a system prompt and user question.

    Args:
        system_prompt: The role/instructions for the agent
        user_question: The question to ask
        model: Which LLM to use
        use_fallback: Use fallback if Ollama unavailable

    Returns:
        Agent's response
    """
    url = "http://localhost:11434/api/generate"

    # Combine system prompt and user question
    full_prompt = f"{system_prompt}\n\nQuestion: {user_question}"

    body = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=body, timeout=5)
        return response.json().get("response", "[No response]")
    except Exception as e:
        if use_fallback:
            return "[Ollama unavailable - using fallback response]"
        else:
            return f"[Error: {str(e)}]"


# ============================================================================
# THE QUESTION (Same for all agents)
# ============================================================================

USER_QUESTION = "What should I do about air pollution in NYC?"

print("=" * 80)
print("SYSTEM PROMPT ENGINEERING EXERCISE")
print("=" * 80)
print(f"\nQuestion asked to all agents:\n'{USER_QUESTION}'\n")


# ============================================================================
# AGENT 1: SYSTEM PROMPT VERSION A - Technical Expert
# ============================================================================

print("\n" + "=" * 80)
print("AGENT 1: TECHNICAL EXPERT (Version A - ORIGINAL)")
print("=" * 80)

SYSTEM_PROMPT_A = """You are an environmental scientist and air quality expert.
You understand EPA standards, PM2.5 measurements, and pollution mechanics.
Provide technical, detailed explanations.
Include specific measurements and scientific reasoning."""

print(f"\nSystem Prompt:\n{SYSTEM_PROMPT_A}\n")
print("Expected output: Technical, scientific, detailed")

response_a = query_mollama(SYSTEM_PROMPT_A, USER_QUESTION)
print(f"\nAgent Response:\n{response_a}\n")


# ============================================================================
# AGENT 2: SYSTEM PROMPT VERSION B - Concerned Parent
# ============================================================================

print("\n" + "=" * 80)
print("AGENT 2: CONCERNED PARENT (Version B - EMOTIONAL)")
print("=" * 80)

SYSTEM_PROMPT_B = """You are a parent with young children.
You are deeply concerned about their health and safety.
Respond with emotion and urgency.
Give practical, actionable advice that a parent can do TODAY.
Focus on protecting your family."""

print(f"\nSystem Prompt:\n{SYSTEM_PROMPT_B}\n")
print("Expected output: Emotional, urgent, family-focused, actionable")

response_b = query_mollama(SYSTEM_PROMPT_B, USER_QUESTION)
print(f"\nAgent Response:\n{response_b}\n")


# ============================================================================
# AGENT 3: SYSTEM PROMPT VERSION C - Government Official
# ============================================================================

print("\n" + "=" * 80)
print("AGENT 3: GOVERNMENT OFFICIAL (Version C - FORMAL/OFFICIAL)")
print("=" * 80)

SYSTEM_PROMPT_C = """You are a New York City government official.
You speak in an official, measured, professional manner.
Focus on regulations, policies, and government programs.
Cite legal requirements and official agencies (EPA, DEP, etc.).
Sound authoritative and trustworthy."""

print(f"\nSystem Prompt:\n{SYSTEM_PROMPT_C}\n")
print("Expected output: Formal, official, policy-focused, authoritative")

response_c = query_mollama(SYSTEM_PROMPT_C, USER_QUESTION)
print(f"\nAgent Response:\n{response_c}\n")


# ============================================================================
# COMPARISON: SAME INPUT, DIFFERENT OUTPUTS
# ============================================================================

print("\n" + "=" * 80)
print("KEY OBSERVATION")
print("=" * 80)

print("""
SAME QUESTION was asked to all three agents.
DIFFERENT SYSTEM PROMPTS were given.
DIFFERENT RESPONSES were produced.

This proves: SYSTEM PROMPT DETERMINES AGENT BEHAVIOR

Agent 1 (Technical): Detailed, scientific, numbers-focused
Agent 2 (Parent): Emotional, urgent, family-focused
Agent 3 (Official): Formal, policy-focused, authoritative

The SYSTEM PROMPT is the primary control for agent personality.
""")


# ============================================================================
# NOW YOU TRY: MODIFY A SYSTEM PROMPT
# ============================================================================

print("\n" + "=" * 80)
print("YOUR TURN: MODIFY A SYSTEM PROMPT")
print("=" * 80)

print("""
EXERCISE: Modify one of the system prompts above and see results change.

Pick one and modify it:

Option 1: Make Agent 1 (TECHNICAL EXPERT) more funny
  OLD:  "You are an environmental scientist..."
  NEW:  "You are an environmental scientist who explains things using
         food metaphors. Be funny and keep people engaged."

Option 2: Make Agent 2 (PARENT) more hopeful
  OLD:  "You are a parent...respond with emotion and urgency..."
  NEW:  "You are an optimistic parent who believes in solutions.
         Share what you're doing and inspire others with hope."

Option 3: Make Agent 3 (OFFICIAL) more approachable
  OLD:  "You are a government official. Speak officially..."
  NEW:  "You are a friendly NYC government worker who genuinely cares.
         Explain policy but in a warm, human way."

THEN:
1. Copy the system prompt you want to modify (A, B, or C)
2. Change it with your modification
3. Run the script again: python 02_prompts_interactive.py
4. Notice how the response changed!
5. Screenshot both the prompt AND the response
6. Submit with explanation of what you changed and why
""")


# ============================================================================
# TEMPLATE FOR YOUR MODIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("TEMPLATE: CREATE YOUR OWN SYSTEM PROMPT")
print("=" * 80)

print("""
Here's a template you can use to create completely new agents:

    MY_SYSTEM_PROMPT = '''You are a [ROLE].

    Key traits:
    - [Trait 1]
    - [Trait 2]
    - [Trait 3]

    When responding:
    - Tone: [Describe tone]
    - Format: [How to structure answer]
    - Focus on: [What to emphasize]
    - Avoid: [What NOT to say]

    Example of a good response from you:
    "[Show example of what you want]"
    '''

Example filled in:

    COMEDIAN_PROMPT = '''You are a stand-up comedian.

    Key traits:
    - You find humor in everyday problems
    - You're self-deprecating and relatable
    - You make observations about life

    When responding:
    - Tone: Funny, lighthearted, witty
    - Format: Joke setup -> punchline
    - Focus on: Finding the humor
    - Avoid: Mean-spirited jokes

    Example of a good response:
    "Air pollution? Yeah, I tried calling my mom.
    She said, 'Why? At least you can't see the condition
    of my apartment through the smog!' Classic mom."
    '''

Then test it:
    response = query_mollama(COMEDIAN_PROMPT, USER_QUESTION)
    print(response)
""")


# ============================================================================
# SUBMISSION REQUIREMENTS
# ============================================================================

print("\n" + "=" * 80)
print("WHAT TO SUBMIT")
print("=" * 80)

print("""
1. ORIGINAL SYSTEM PROMPT
   Show the system prompt before modification

2. YOUR MODIFICATION
   Show what you changed and why

3. AGENT RESPONSE - BEFORE
   Screenshot of agent response with original prompt

4. AGENT RESPONSE - AFTER
   Screenshot of agent response with modified prompt

5. EXPLANATION (2-3 sentences)
   Describe:
   - What you changed
   - How the response changed
   - Why the system prompt matters

Example submission:

   Original Prompt: "You are a technical expert"

   Modified Prompt: "You are a comedian who makes jokes about everything"

   Before: Technical explanation of PM2.5 standards...

   After: "Air quality? Yeah, my lungs are like a air filter that's
           been running since 2010. Overdue for a replacement!"

   Explanation: By changing the role from "technical expert" to
   "comedian," the agent completely changed its response style from
   detailed/scientific to humorous/observational. This shows that the
   system prompt is the primary control for agent personality.
""")

print("\n" + "=" * 80)
