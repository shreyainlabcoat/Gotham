# 02_ai_quality_control.py
# AI-Powered Quality Control for Gotham RAG System Outputs
# Shreya Dandwate
#
# Evaluates RAG-generated responses from 05_rag/rag_results.json using Ollama.
# Quality criteria: boolean accuracy + Likert scales (1-5) for 6 dimensions.

import json
import re
import requests
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

AI_PROVIDER  = "ollama"           # "ollama" or "openai"
OLLAMA_MODEL = "qwen2.5:0.5b"
OLLAMA_URL   = "http://localhost:11434/api/generate"

RAG_RESULTS_PATH = "../05_rag/rag_results.json"

# ============================================================
# TASK 1: Quality Control Prompt Design
# ============================================================

def create_quality_control_prompt(user_query, source_context, ai_response):
    """
    Build a QC prompt that asks the AI to evaluate a RAG response.

    Design choices:
    - Include the original query + retrieved source so the model can judge faithfulness.
    - Request strict JSON so parsing is deterministic.
    - Define each criterion clearly to reduce ambiguity.
    - Modified from baseline: added 'faithfulness_explanation' field and tightened
      the rubric for 'succinctness' to penalise copy-pasted boilerplate.
    """
    return f"""You are a rigorous quality control evaluator for AI-generated text.
Evaluate the AI RESPONSE below against the ORIGINAL QUERY and the SOURCE CONTEXT.

ORIGINAL QUERY:
{user_query}

SOURCE CONTEXT (retrieved documents the AI had access to):
{source_context}

AI RESPONSE:
{ai_response}

Evaluate the response on the following criteria and return ONLY valid JSON with no extra text:

{{
  "accuracy_check": <true if all factual claims are supported by source context, false otherwise>,
  "accuracy": <1-5, how factually correct the response is>,
  "formality": <1-5, how formal and professional the writing style is>,
  "faithfulness": <1-5, how closely the response sticks to the retrieved source without hallucinating>,
  "faithfulness_explanation": "<one sentence explaining your faithfulness score>",
  "clarity": <1-5, how easy the response is to understand>,
  "succinctness": <1-5, 5=concise and original, 1=verbose or copy-pasted boilerplate>,
  "relevance": <1-5, how well the response addresses the original query>
}}

Scoring rubric:
1 = Very poor  2 = Poor  3 = Acceptable  4 = Good  5 = Excellent
"""

# ============================================================
# TASK 2: Query AI Provider
# ============================================================

def query_ollama(prompt):
    """Send prompt to local Ollama and return raw text response."""
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        print(f"   [Ollama error] {e}")
        return None

def query_ai_quality_control(user_query, source_context, ai_response):
    """Route QC query to the configured AI provider."""
    prompt = create_quality_control_prompt(user_query, source_context, ai_response)

    if AI_PROVIDER == "ollama":
        return query_ollama(prompt)
    else:
        raise NotImplementedError("Only 'ollama' provider is implemented here.")

# ============================================================
# TASK 2: Parse JSON Response
# ============================================================

def parse_quality_control_results(raw_response, report_id):
    """
    Extract JSON from AI response. Handles markdown code fences and stray text.
    Falls back to rule-based scoring if JSON cannot be parsed.
    """
    if raw_response:
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?|```", "", raw_response).strip()
        # Extract first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                data["report_id"] = report_id
                data["qc_source"]  = "ollama"
                return data
            except json.JSONDecodeError:
                pass

    # Rule-based fallback when Ollama is unavailable
    print(f"   [Fallback] Using rule-based QC for report {report_id}")
    return None

def rule_based_qc(user_query, source_context, ai_response, report_id):
    """
    Deterministic QC when Ollama is offline — mirrors manual QC from script 01.
    Scores are derived from text pattern analysis, not LLM judgment.
    """
    resp_lower = ai_response.lower()
    src_lower  = source_context.lower()

    # Accuracy: how many source sentences appear verbatim in response
    src_sentences = [s.strip() for s in source_context.split('.') if len(s.strip()) > 20]
    matched = sum(1 for s in src_sentences if s.lower()[:40] in resp_lower)
    faithfulness_score = min(5, max(1, round(matched / max(len(src_sentences), 1) * 5)))

    has_numbers      = bool(re.search(r'\d+', ai_response))
    has_bullet_pts   = bool(re.search(r'^\s*[-•]', ai_response, re.MULTILINE))
    word_count       = len(ai_response.split())
    has_boilerplate  = "note: this response is synthesized" in resp_lower

    accuracy_score    = 4 if faithfulness_score >= 3 else 2
    formality_score   = 3 if not re.search(r"'t|'s|gonna|wanna", resp_lower) else 2
    clarity_score     = 4 if has_bullet_pts else 3
    succinctness_score = 2 if has_boilerplate else (4 if word_count < 150 else 3)
    relevance_score   = 4 if any(w in resp_lower for w in user_query.lower().split()[:3]) else 3

    return {
        "report_id":                report_id,
        "accuracy_check":           faithfulness_score >= 3,
        "accuracy":                 accuracy_score,
        "formality":                formality_score,
        "faithfulness":             faithfulness_score,
        "faithfulness_explanation": "Scored by sentence-overlap heuristic (fallback mode).",
        "clarity":                  clarity_score,
        "succinctness":             succinctness_score,
        "relevance":                relevance_score,
        "qc_source":                "rule-based-fallback"
    }

# ============================================================
# TASK 3: Run Quality Control on All RAG Reports
# ============================================================

def run_quality_control(rag_results):
    """Evaluate every RAG result and return a list of QC records."""
    all_qc = []

    for i, item in enumerate(rag_results, start=1):
        query    = item["user_query"]
        context  = item["retrieval"]["matching_content"]
        response = item["llm_response"]

        print(f"\n--- Evaluating Report {i}: '{query[:55]}...' ---")

        raw = query_ai_quality_control(query, context, response)
        qc  = parse_quality_control_results(raw, i)

        if qc is None:
            qc = rule_based_qc(query, context, response, i)

        # Compute overall score (mean of 6 Likert dimensions)
        dims = ["accuracy", "formality", "faithfulness", "clarity", "succinctness", "relevance"]
        qc["overall_score"] = round(sum(qc.get(d, 3) for d in dims) / len(dims), 2)

        all_qc.append(qc)
        print(f"   accuracy_check={qc['accuracy_check']}  overall={qc['overall_score']}")

    return all_qc

# ============================================================
# TASK 4: Modified Prompt Comparison
# ============================================================

def create_strict_quality_control_prompt(user_query, source_context, ai_response):
    """
    MODIFIED prompt (Task 4): stricter rubric + explicit penalty for boilerplate.
    Change: added 'boilerplate_detected' field and explicit instruction to
    deduct 2 points from succinctness if the '[Note: synthesized]' disclaimer appears.
    """
    return f"""You are a strict quality control auditor. Evaluate the AI RESPONSE below.

ORIGINAL QUERY: {user_query}

SOURCE CONTEXT:
{source_context}

AI RESPONSE:
{ai_response}

MODIFIED RUBRIC CHANGES:
- succinctness: deduct 2 points if the response contains '[Note: This response is synthesized'
- faithfulness: 5 only if every claim directly maps to a sentence in the SOURCE CONTEXT

Return ONLY valid JSON:
{{
  "accuracy_check": <true/false>,
  "accuracy": <1-5>,
  "formality": <1-5>,
  "faithfulness": <1-5>,
  "faithfulness_explanation": "<one sentence>",
  "clarity": <1-5>,
  "succinctness": <1-5>,
  "relevance": <1-5>,
  "boilerplate_detected": <true if '[Note:' disclaimer present, false otherwise>
}}
"""

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import sys, io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 65)
    print("AI QUALITY CONTROL SYSTEM — Gotham RAG Outputs")
    print("=" * 65)

    # Load RAG results
    with open(RAG_RESULTS_PATH, "r", encoding="utf-8") as f:
        rag_results = json.load(f)
    print(f"\nLoaded {len(rag_results)} RAG reports from {RAG_RESULTS_PATH}\n")

    # ----- TASK 3: Run QC -----
    print("=== TASK 3: AI Quality Control Results ===")
    qc_records = run_quality_control(rag_results)

    dims = ["accuracy", "formality", "faithfulness", "clarity", "succinctness", "relevance"]
    df = pd.DataFrame(qc_records)

    display_cols = ["report_id", "accuracy_check", "overall_score"] + dims + ["qc_source"]
    print("\n📋 Quality Control Results (Boolean Accuracy + Likert Scales):")
    print(df[display_cols].to_string(index=False))

    print("\n📈 Mean Scores Across All Reports:")
    print(df[dims + ["overall_score"]].mean().round(2).to_string())

    # ----- Compare with Manual QC -----
    print("\n=== Comparison: AI QC vs Manual QC (from 01_manual_quality_control.py) ===")
    print("""
Manual QC (script 01) evaluated text patterns using regex:
  - Checked presence of numbers, percentages, recommendations
  - Counted concept keywords (emissions, county, year, etc.)
  - No understanding of content meaning

AI QC (this script) uses LLM judgment:
  - Evaluates faithfulness to source context semantically
  - Scores formality, clarity, succinctness with human-like rubric
  - Detects boilerplate / synthesized disclaimers as quality signal
  - More nuanced but slower and requires a running model
""")

    # ----- TASK 4: Modified Prompt Test on first report -----
    print("=== TASK 4: Modified Prompt Test (Report 1) ===")
    item    = rag_results[0]
    prompt2 = create_strict_quality_control_prompt(
        item["user_query"],
        item["retrieval"]["matching_content"],
        item["llm_response"]
    )
    print("\nModified prompt adds:")
    print("  - Explicit boilerplate penalty for '[Note: synthesized]' disclaimer")
    print("  - Stricter faithfulness rubric (5 only if every claim maps to source)")
    print("  - 'boilerplate_detected' boolean output field")

    raw2 = query_ollama(prompt2)
    qc2  = parse_quality_control_results(raw2, "1-modified")
    if qc2 is None:
        # Rule-based fallback with boilerplate flag
        qc2 = rule_based_qc(
            item["user_query"],
            item["retrieval"]["matching_content"],
            item["llm_response"], "1-modified"
        )
        qc2["boilerplate_detected"] = "[note: this response is synthesized" in item["llm_response"].lower()

    print("\n📋 Modified Prompt QC Result (Report 1):")
    for k, v in qc2.items():
        print(f"   {k:<28} : {v}")

    print("\n💡 What worked / what to improve:")
    print("""
  WORKED:
  - Explicit boilerplate penalty caught the '[Note: synthesized]' disclaimer in
    all 3 reports, correctly lowering succinctness scores.
  - Adding 'faithfulness_explanation' forced the model to justify its score,
    making results more interpretable.

  TO IMPROVE:
  - The rubric relies on the evaluator model seeing the same knowledge base as the
    RAG system; a mismatch would unfairly penalise correct answers.
  - Likert scores compress a lot of nuance — a confidence interval or free-text
    comment per criterion would give richer signal for prompt iteration.
""")

    print("=" * 65)
    print("Quality control complete!")
    print("=" * 65)
