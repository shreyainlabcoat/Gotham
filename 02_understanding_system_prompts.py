"""
SYSTEM PROMPT ENGINEERING: Understanding How Prompts Shape Agent Behavior

Key Concept:
============
A system prompt defines the ROLE and BEHAVIOR of an agent.
Changing the system prompt changes HOW THE AGENT RESPONDS to the same input.

This file shows:
- What a system prompt is
- How to modify it
- How it changes agent behavior
- Examples with before/after

Reference: 03_ollama/02_ollama.py shows basic Ollama usage
"""

import requests
import json


# ============================================================================
# STAGE 1: UNDERSTAND SYSTEM PROMPTS
# ============================================================================

print("=" * 80)
print("STAGE 1: UNDERSTANDING SYSTEM PROMPTS")
print("=" * 80)

print("""
What is a System Prompt?
------------------------
A system prompt defines the ROLE and CONSTRAINTS of an agent.
It tells the LLM what character to play and how to behave.

Example 1 - No system prompt (model talks like itself):
  Input: "How is the weather?"
  Output: "I'm an AI model and cannot check weather..."

Example 2 - System prompt as weather reporter:
  System: "You are a weather reporter."
  Input: "How is the weather?"
  Output: "Good afternoon! Currently it's 72 degrees and sunny..."

Example 3 - System prompt as angry weather reporter:
  System: "You are an angry weather reporter who yells."
  Input: "How is the weather?"
  Output: "ARE YOU KIDDING ME? IT'S RAINING AGAIN! THE WEATHER IS TERRIBLE!!!"

The SYSTEM PROMPT shapes the behavior more than anything else.
""")


# ============================================================================
# STAGE 2: BASIC OLLAMA QUERY (From 02_ollama.py)
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 2: BASIC OLLAMA QUERY")
print("=" * 80)

print("""
Here's the basic structure from 02_ollama.py:

    body = {
        "model": "gemma3:latest",
        "prompt": "Is model working?",
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=body)
    output = response.json()["response"]

The "prompt" field is what you send to the model.
""")

# Basic query function
def query_ollama(prompt, model="smollm2:135m"):
    """Send a simple query to Ollama and get response."""
    url = "http://localhost:11434/api/generate"
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=body, timeout=5)
        return response.json().get("response", "[No response]")
    except Exception as e:
        return f"[Ollama unavailable: {str(e)}]"


# ============================================================================
# STAGE 3: SYSTEM PROMPTS CHANGE BEHAVIOR
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 3: HOW SYSTEM PROMPTS CHANGE BEHAVIOR")
print("=" * 80)

# The same USER INPUT...
user_question = "What should people do about air pollution in NYC?"

print(f"\nUser Question: '{user_question}'\n")

# ... but DIFFERENT SYSTEM PROMPTS create DIFFERENT outputs

# SYSTEM PROMPT 1: Technical Expert
print("-" * 80)
print("SYSTEM PROMPT 1: Technical Air Quality Expert")
print("-" * 80)

system_prompt_1 = """You are a technical air quality expert.
Provide detailed scientific explanations.
Include specific measurements, PM2.5 values, and EPA standards.
Use technical terminology."""

print(f"\nSystem Prompt:\n{system_prompt_1}\n")

# Combine system prompt + user question
full_prompt_1 = f"{system_prompt_1}\n\nQuestion: {user_question}"

response_1 = query_ollama(full_prompt_1)
print(f"Agent Response:\n{response_1}\n")

fallback_1 = """Fine particulate matter (PM2.5 < 2.5 micrometers) concentrations in NYC
exceed EPA 24-hour National Ambient Air Quality Standard (NAAQS) of 35 µg/m³.
Mitigation includes source reduction, emission controls, and real-time air quality
monitoring using optical particle counters and regulatory compliance measures."""


# ============================================================================

# SYSTEM PROMPT 2: Concerned Parent
print("-" * 80)
print("SYSTEM PROMPT 2: Concerned Parent")
print("-" * 80)

system_prompt_2 = """You are a concerned parent worried about your children's health.
Speak with emotion and urgency.
Focus on how pollution affects kids and families.
Give practical advice parents can do TODAY."""

print(f"\nSystem Prompt:\n{system_prompt_2}\n")

full_prompt_2 = f"{system_prompt_2}\n\nQuestion: {user_question}"

response_2 = query_ollama(full_prompt_2)
print(f"Agent Response:\n{response_2}\n")

fallback_2 = """I'm terrified about what air pollution is doing to our children!
My kids have been coughing more and getting more sick. We NEED to act NOW!
Here's what I do: Keep windows closed on bad air days, buy N95 masks for my kids,
use HEPA air filters at home, and check air quality apps every morning before
taking them outside. Every parent should do this - our kids' lungs are at stake!"""


# ============================================================================

# SYSTEM PROMPT 3: Government Regulator
print("-" * 80)
print("SYSTEM PROMPT 3: Government Regulator")
print("-" * 80)

system_prompt_3 = """You are a NYC government official responsible for public health.
Be professional and measured.
Focus on regulations, policies, and official actions.
Cite legal requirements and oversight mechanisms."""

print(f"\nSystem Prompt:\n{system_prompt_3}\n")

full_prompt_3 = f"{system_prompt_3}\n\nQuestion: {user_question}"

response_3 = query_ollama(full_prompt_3)
print(f"Agent Response:\n{response_3}\n")

fallback_3 = """The NYC Department of Environmental Protection enforces the Clean Air Act
and State Environmental Quality Review Act. When PM2.5 exceeds 35 µg/m³, we activate
Air Quality Alert protocols. Official actions include: emissions reduction targets for
vehicles and industry, mandatory public notification, health department advisories for
vulnerable populations, and air quality monitoring at 100+ locations citywide. We also
coordinate with EPA regarding NAAQS compliance and implementation plans."""


# ============================================================================
# STAGE 4: COMPARISON TABLE
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 4: COMPARING THE THREE RESPONSES")
print("=" * 80)

print("""
Same Question: "What should people do about air pollution in NYC?"

THREE Different System Prompts = THREE Different Agent Personalities

┌────────────────────┬──────────┬──────────┬──────────┐
│ Aspect             │ Expert   │ Parent   │ Official │
├────────────────────┼──────────┼──────────┼──────────┤
│ Tone               │ Technical│ Emotional│ Formal   │
│ Focus              │ Science  │ Family   │ Policy   │
│ Key Metrics        │ PM2.5 µg │ Kids     │ Legal    │
│ Recommendations    │ Technical│ Action   │ Official │
│ Language Level     │ Expert   │ Plain    │ Formal   │
│ Urgency            │ Neutral  │ High     │ Measured │
└────────────────────┴──────────┴──────────┴──────────┘

KEY INSIGHT:
The SYSTEM PROMPT determines the agent's personality and response style.
Same input, different prompt = completely different output!
""")


# ============================================================================
# STAGE 5: HOW TO MODIFY PROMPTS (Practical Guide)
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 5: HOW TO MODIFY SYSTEM PROMPTS")
print("=" * 80)

print("""
Three ways to change agent behavior:

1. CHANGE THE ROLE
   ❌ Bad:  "You are an expert."
   ✅ Good: "You are a pediatrician worried about children's lung health."

   This changes WHAT the agent knows and cares about.

2. ADD CONSTRAINTS
   ❌ Bad:  "Give advice about air quality."
   ✅ Good: "Give advice that a 10-year-old can understand. Use only 3 sentences."

   This changes HOW the agent responds (format, complexity, length).

3. SPECIFY TONE
   ❌ Bad:  "Discuss air pollution."
   ✅ Good: "Discuss air pollution with urgency and emotion, like you're trying
            to convince someone to care RIGHT NOW."

   This changes the STYLE and EMOTIONAL TONE.

4. ADD EXAMPLES
   ❌ Bad:  "Summarize this."
   ✅ Good: "Summarize this in the style of a news headline. Examples:
            - 'NYC Air Quality Hits Crisis Level'
            - 'Vulnerable Groups Face Health Risks'"

   This shows the agent what you want by example.
""")


# ============================================================================
# STAGE 6: PRACTICE - MODIFY YOUR OWN PROMPT
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 6: PRACTICE - MODIFY YOUR OWN SYSTEM PROMPT")
print("=" * 80)

print("""
Exercise: Create your own system prompt and test it

Here's a template:

    my_system_prompt = '''You are a [ROLE].

    Your job is to [RESPONSIBILITY].

    When responding:
    - Use [TONE] tone
    - Format as [FORMAT]
    - Focus on [FOCUS AREA]
    - Include [SPECIFIC DETAILS]

    Example of good response:
    [SHOW EXAMPLE]
    '''

Then test it:

    my_prompt = my_system_prompt + "\\n\\nQuestion: " + user_question
    response = query_ollama(my_prompt)
    print(response)

Try these variations:
1. Make it funny (comedian role)
2. Make it formal (lawyer role)
3. Make it simple (5-year-old role)
4. Make it urgent (emergency responder role)
""")


# ============================================================================
# STAGE 7: KEY LEARNINGS
# ============================================================================

print("\n" + "=" * 80)
print("STAGE 7: KEY LEARNINGS")
print("=" * 80)

learnings = [
    "1. SYSTEM PROMPT = AGENT PERSONALITY",
    "   The system prompt defines how the agent thinks and responds.",
    "",
    "2. SAME INPUT, DIFFERENT PROMPTS = DIFFERENT OUTPUTS",
    "   Change the prompt, change the behavior.",
    "",
    "3. PROMPT ENGINEERING IS ITERATIVE",
    "   Write a prompt → test it → refine it → test again",
    "",
    "4. BE SPECIFIC, NOT VAGUE",
    "   \"Be helpful\" < \"Explain like I'm a 10-year-old in 2 sentences\"",
    "",
    "5. TONE MATTERS",
    "   Technical, emotional, formal, funny - prompts shape tone.",
    "",
    "6. EXAMPLES HELP",
    "   Showing what you want is better than describing it.",
    "",
    "7. CONSTRAINTS ARE YOUR FRIEND",
    "   \"Use only 3 bullet points\" makes better outputs than open-ended requests."
]

for learning in learnings:
    print(learning)


# ============================================================================
# FINAL CHALLENGE
# ============================================================================

print("\n" + "=" * 80)
print("FINAL CHALLENGE: CREATE YOUR OWN AGENT")
print("=" * 80)

print("""
Your assignment:
1. Pick a role (chef, teacher, comedian, detective, etc.)
2. Write a system prompt that defines that role clearly
3. Create a question about air quality
4. Test the prompt with query_ollama()
5. Screenshot the result

Example template:

    chef_prompt = '''You are a celebrity chef at a Michelin-starred restaurant.
    You speak with passion about your craft.
    You relate everything to food and cooking.
    You're known for being dramatic and expressive.
    '''

    question = "What should people do about air pollution in NYC?"

    full_prompt = chef_prompt + "\\n\\nQuestion: " + question
    response = query_ollama(full_prompt)
    print(response)

Submit:
- Your system prompt
- The question you asked
- Screenshot of agent's response showing the role was adopted
""")

print("\n" + "=" * 80)
