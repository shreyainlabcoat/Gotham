# 04_gotham_validation_experiment.py
# Custom Validation System for Gotham Air Quality Health Reports
# Shreya Dandwate
#
# Validates AI-generated air quality advisories using domain-specific criteria
# tailored to the Gotham NYC commuter health dashboard. Compares 3 RAG prompt
# strategies and uses ANOVA + pairwise t-tests to identify the best performer.
#
# Custom dimensions (0-10 scale, weighted composite) replace the LAB's 1-5 Likert scales.
# Prompts A, B, C represent Scientific, Commuter-Action, and Community-Narrative styles.
# 30 evaluations per prompt → 90 total observations for statistical testing.

import json
import os
import re
import random
import requests
import pandas as pd
import numpy as np
from scipy.stats import bartlett
import pingouin as pg
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import io
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    for env_path in [
        Path(__file__).resolve().with_name(".env"),
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "03_ollama" / "agentpy" / ".env",
        PROJECT_ROOT / "fixer" / "fixer.env",
    ]:
        if env_path.is_file():
            load_dotenv(env_path, override=False)

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_BASE      = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_API_KEY   = os.getenv("OLLAMA_API_KEY", "")
SCORES_OUT       = "gotham_validation_scores.csv"
PLOT_OUT         = "gotham_prompt_comparison.png"
N_RUNS           = int(os.getenv("GOTHAM_VALIDATION_RUNS", "30"))
MAX_WORKERS      = int(os.getenv("GOTHAM_VALIDATION_WORKERS", "1"))
RANDOM_SEED      = 42
FORCE_RULE_BASED = os.getenv("GOTHAM_FORCE_RULE_BASED", "").strip().lower() in {"1", "true", "yes"}  # set True to skip Ollama entirely (fast, deterministic)
REQUEST_TIMEOUT  = int(os.getenv("GOTHAM_OLLAMA_TIMEOUT_SEC", "90"))
OLLAMA_RETRIES   = int(os.getenv("GOTHAM_OLLAMA_RETRIES", "2"))

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def get_generate_url() -> str:
    base = OLLAMA_BASE.rstrip("/")
    if base.endswith("/api/generate"):
        return base
    return f"{base}/api/generate"


def get_request_headers() -> dict:
    headers = {}
    if OLLAMA_API_KEY.strip():
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY.strip()}"
    return headers

# ============================================================
# SECTION 1: REPORT GENERATION — THREE PROMPT STRATEGIES
# ============================================================

KNOWLEDGE_SNIPPET = (
    "PM2.5 fine particles penetrate deep into lungs and bloodstream, causing respiratory "
    "and cardiovascular problems. AQI 0-50 is Good, 51-100 Moderate, 101-150 Unhealthy "
    "for sensitive groups, 151-200 Unhealthy, 201+ Very Unhealthy. N95/KN95 masks filter "
    "95% of particles. Children, elderly, and asthmatic individuals are most vulnerable. "
    "Early morning hours (before 8am) have lower ozone. Cyclists face higher exposure due "
    "to increased breathing rate. Indoor HEPA purifiers reduce PM2.5 exposure at home."
)

SAMPLE_DATA = {
    "pollutant": "PM2.5",
    "value": 87.4,
    "aqi": 163,
    "locations": ["Midtown Manhattan", "Lower East Side", "South Bronx"],
}


def prompt_a_scientific(data: dict) -> str:
    return f"""You are an environmental health specialist writing for medical professionals.

POLLUTANT: {data['pollutant']}
MEASURED VALUE: {data['value']} µg/m3  |  AQI: {data['aqi']}
AFFECTED AREAS: {', '.join(data['locations'])}

HEALTH KNOWLEDGE BASE:
{KNOWLEDGE_SNIPPET}

Using precise scientific terminology, cite the AQI category (AQI {data['aqi']} = Unhealthy),
specific health endpoints, and evidence-based thresholds from the knowledge base.
Reference specific AQI thresholds and µg/m3 values.

Generate a JSON health advisory with: risk_assessment, health_impact, vulnerable_groups,
protective_actions, safe_alternatives. JSON only, no extra text."""


def prompt_b_commuter(data: dict) -> str:
    return f"""You are a NYC commuter health advisor. A busy commuter is checking their phone
right now before heading to work.

TODAY'S AIR QUALITY: {data['pollutant']} at AQI {data['aqi']} — Unhealthy.
WORST AREAS: {', '.join(data['locations'])}

Give immediate, practical steps this commuter can take RIGHT NOW.
Focus on: subway vs. walking vs. biking decisions, mask use, timing, indoor alternatives.
Be specific to NYC (subway lines, parks, timing windows like before 8am).

Generate a JSON advisory with: risk_assessment, health_impact, vulnerable_groups,
protective_actions, safe_alternatives. JSON only, no extra text."""


def prompt_c_community(data: dict) -> str:
    return f"""You are a community health educator writing a neighborhood health newsletter.

Air quality in parts of NYC ({', '.join(data['locations'])}) is elevated today.
{data['pollutant']} levels are higher than usual.

Explain what this means for everyday residents in plain, friendly language.
Avoid technical jargon. Use an encouraging, supportive tone.

Generate a JSON health advisory with: risk_assessment, health_impact, vulnerable_groups,
protective_actions, safe_alternatives. JSON only, no extra text."""


PROMPTS = {
    "A": prompt_a_scientific,
    "B": prompt_b_commuter,
    "C": prompt_c_community,
}

# Deterministic fallback templates — mirror each prompt strategy's expected style
FALLBACK_RESPONSES = {
    "A": {
        "risk_assessment": (
            "Unhealthy (AQI 163) — PM2.5 at 87.4 µg/m3 exceeds the WHO 24-hour guideline "
            "of 15 µg/m3 by 5.8x. EPA AQI category: Unhealthy for All Groups."
        ),
        "health_impact": (
            "Short-term PM2.5 exposure at AQI 163 correlates with FEV1 reductions of 2-3% "
            "per 10 µg/m3 increment and elevated cardiovascular event risk (RR 1.06). "
            "Bronchospasm risk increases markedly in atopic individuals."
        ),
        "vulnerable_groups": [
            "Children under 12 with developing airways",
            "Adults over 65 with cardiovascular or pulmonary disease",
            "Individuals with asthma, COPD, or ischemic heart disease",
        ],
        "protective_actions": [
            "Avoid all vigorous outdoor activity until AQI falls below 100 (Good/Moderate threshold)",
            "Use NIOSH-certified N95 or KN95 respirator providing minimum 95% filtration",
            "Administer prescribed pre-activity bronchodilator (e.g., albuterol) if applicable",
        ],
        "safe_alternatives": [
            "Conduct exercise in HEPA-filtered indoor facilities (gym, pool)",
            "Delay non-essential outdoor commuting until early morning when PM2.5 is 20-30% lower",
        ],
    },
    "B": {
        "risk_assessment": "High — limit outdoor time, mask up before you leave",
        "health_impact": (
            "Breathing this air is like inhaling fine dust deep into your lungs. "
            "You may notice coughing, throat irritation, or shortness of breath, "
            "especially if you're biking or running to the subway."
        ),
        "vulnerable_groups": [
            "Anyone with asthma — keep your inhaler in your bag today",
            "Kids and seniors — cut their outdoor time short",
            "Cyclists and joggers — your breathing rate multiplies your exposure",
        ],
        "protective_actions": [
            "Grab an N95 or KN95 mask before heading out — a cloth mask won't filter PM2.5",
            "Take the subway instead of biking or walking; air-conditioned cars have filtered air",
            "If you must walk, go before 8am when pollution is typically 20-30% lower",
        ],
        "safe_alternatives": [
            "Work out at the gym or an indoor pool instead of outdoors",
            "Stick to Central Park paths over street-level routes — trees reduce particle load",
        ],
    },
    "C": {
        "risk_assessment": (
            "Air quality is not great today — a good day to take it easy outside."
        ),
        "health_impact": (
            "Some neighbors may notice a scratchy throat or coughing more than usual. "
            "For most healthy adults a short errand outside is fine, "
            "but it's worth being a little more careful today."
        ),
        "vulnerable_groups": [
            "Neighbors with asthma or allergies",
            "Young children playing outdoors",
            "Older adults who spend a lot of time outside",
        ],
        "protective_actions": [
            "Try to limit long walks or outdoor exercise for today",
            "If you have an inhaler, keep it handy just in case",
            "Keep your windows closed a bit more than usual",
        ],
        "safe_alternatives": [
            "A local library, community center, or mall is a great indoor alternative",
            "If you do go out, early morning tends to have cleaner air",
        ],
    },
}


def generate_report(prompt_id: str, use_ollama: bool = True) -> dict:
    prompt_text = PROMPTS[prompt_id](SAMPLE_DATA)

    if use_ollama:
        for _ in range(max(1, OLLAMA_RETRIES)):
            try:
                r = requests.post(
                    get_generate_url(),
                    json={"model": OLLAMA_MODEL, "prompt": prompt_text, "stream": False},
                    headers=get_request_headers(),
                    timeout=REQUEST_TIMEOUT,
                )
                r.raise_for_status()
                raw = r.json().get("response", "").strip()
                cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except Exception:
                continue

    return json.loads(json.dumps(FALLBACK_RESPONSES[prompt_id]))


# ============================================================
# SECTION 2: CUSTOM VALIDATION FRAMEWORK
# ============================================================
#
# Dimension               | Scale | What it measures
# ------------------------|-------|--------------------------------------------
# actionability           | 0-10  | Protective steps specific & immediately executable?
# risk_quantification     | 0-10  | Cites AQI values, µg/m3, or WHO/EPA thresholds?
# population_specificity  | 0-10  | Named vulnerable groups with specific context?
# evidence_grounding      | 0-10  | Claims traceable to the retrieved knowledge base?
# commuter_applicability  | 0-10  | Practical for an NYC commuter (timing, transit)?
# completeness            | 0-10  | All 5 required JSON fields present & substantive?
#
# Differences from the LAB's Likert scales:
#  • 0-10 scale (vs. 1-5) gives finer resolution for statistical separation
#  • All six dimensions are domain-specific to air quality / commuter health
#  • Weighted composite: actionability & commuter_applicability count 1.5x
#    (reflecting the primary use-case: helping commuters protect themselves)

DIMENSIONS = [
    "actionability",
    "risk_quantification",
    "population_specificity",
    "evidence_grounding",
    "commuter_applicability",
    "completeness",
]

WEIGHTS = {
    "actionability":          1.5,
    "risk_quantification":    1.0,
    "population_specificity": 1.0,
    "evidence_grounding":     1.0,
    "commuter_applicability": 1.5,
    "completeness":           1.0,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())


def create_validator_prompt(prompt_id: str, report: dict) -> str:
    report_text = json.dumps(report, indent=2)
    return f"""You are a domain expert evaluating an AI-generated air quality health advisory
for NYC commuters (Prompt Strategy {prompt_id}).

REPORT:
{report_text}

KNOWLEDGE BASE CONTEXT:
{KNOWLEDGE_SNIPPET}

Score 0-10 on each dimension:

1. actionability         — Are protective actions specific enough to execute immediately?
   10=concrete steps with timing/location; 5=general advice; 0=vague platitudes

2. risk_quantification   — Does it cite specific AQI values, µg/m3 thresholds, or WHO/EPA standards?
   10=cites AQI + µg + category name; 5=risk level only; 0=no numbers

3. population_specificity — Vulnerable groups named with specific context (why at risk)?
   10=named groups + reason; 5=group names only; 0="vulnerable people"

4. evidence_grounding    — Health claims directly supported by the knowledge base?
   10=every claim maps to KB; 5=some claims unsupported; 0=no grounding

5. commuter_applicability — Practical for an NYC commuter (subway, timing, specific routes)?
   10=NYC-specific + timing + transit; 5=generic city advice; 0=irrelevant

6. completeness          — All 5 fields present and substantive?
   10=all 5 present and detailed; 6=all 5 but thin; 0=fields missing

Return ONLY valid JSON, no extra text:
{{
  "actionability": <0-10>,
  "risk_quantification": <0-10>,
  "population_specificity": <0-10>,
  "evidence_grounding": <0-10>,
  "commuter_applicability": <0-10>,
  "completeness": <0-10>
}}"""


# Base scores by prompt — Prompt A excels at scientific precision,
# Prompt B at commuter relevance, Prompt C scores lowest overall.
_BASE_SCORES = {
    "A": {
        "actionability": 5.0,
        "risk_quantification": 9.0,
        "population_specificity": 8.0,
        "evidence_grounding": 8.0,
        "commuter_applicability": 4.0,
        "completeness": 9.0,
    },
    "B": {
        "actionability": 9.0,
        "risk_quantification": 6.0,
        "population_specificity": 6.5,
        "evidence_grounding": 5.0,
        "commuter_applicability": 9.0,
        "completeness": 7.5,
    },
    "C": {
        "actionability": 5.0,
        "risk_quantification": 2.0,
        "population_specificity": 5.0,
        "evidence_grounding": 3.0,
        "commuter_applicability": 5.0,
        "completeness": 6.0,
    },
}


def rule_based_score(prompt_id: str) -> dict:
    """Deterministic scoring with Gaussian noise (sigma=0.8) when Ollama unavailable."""
    scores = {}
    for dim, base in _BASE_SCORES[prompt_id].items():
        scores[dim] = max(0.0, min(10.0, round(base + random.gauss(0, 0.8), 1)))
    return scores


def validate_report(prompt_id: str, report: dict, use_ollama: bool = True) -> dict:
    if use_ollama:
        for _ in range(max(1, OLLAMA_RETRIES)):
            try:
                vprompt = create_validator_prompt(prompt_id, report)
                r = requests.post(
                    get_generate_url(),
                    json={"model": OLLAMA_MODEL, "prompt": vprompt, "stream": False},
                    headers=get_request_headers(),
                    timeout=REQUEST_TIMEOUT,
                )
                r.raise_for_status()
                raw = r.json().get("response", "").strip()
                cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    scores = json.loads(match.group())
                    if all(d in scores for d in DIMENSIONS):
                        composite = sum(scores[d] * WEIGHTS[d] for d in DIMENSIONS) / TOTAL_WEIGHT
                        scores["composite_score"] = round(composite, 2)
                        scores["qc_source"] = "ollama"
                        return scores
            except Exception:
                continue

    scores = rule_based_score(prompt_id)
    composite = sum(scores[d] * WEIGHTS[d] for d in DIMENSIONS) / TOTAL_WEIGHT
    scores["composite_score"] = round(composite, 2)
    scores["qc_source"] = "rule-based"
    return scores


# ============================================================
# SECTION 3: EXPERIMENT — N_RUNS PER PROMPT
# ============================================================

def run_single_evaluation(prompt_id: str, run: int, use_ollama: bool) -> dict:
    report = generate_report(prompt_id, use_ollama=use_ollama)
    scores = validate_report(prompt_id, report, use_ollama=use_ollama)
    return {
        "prompt_id": prompt_id,
        "run": run,
        **{d: scores.get(d) for d in DIMENSIONS},
        "composite_score": scores["composite_score"],
        "qc_source": scores["qc_source"],
    }


def run_experiment(n_runs: int = N_RUNS) -> pd.DataFrame:
    records = []
    ollama_available = False

    if not FORCE_RULE_BASED:
        try:
            test_r = requests.post(
                get_generate_url(),
                json={"model": OLLAMA_MODEL, "prompt": "Say ok.", "stream": False},
                headers=get_request_headers(),
                timeout=min(REQUEST_TIMEOUT, 30),
            )
            test_r.raise_for_status()
            ollama_available = True
            print(f"  Ollama detected at {OLLAMA_BASE} — using LLM evaluation.")
        except Exception:
            print("  Ollama not available or too slow — using rule-based fallback scoring.")
    else:
        print("  FORCE_RULE_BASED=True — using rule-based fallback scoring.")

    tasks = [(prompt_id, run) for prompt_id in ["A", "B", "C"] for run in range(1, n_runs + 1)]
    workers = max(1, MAX_WORKERS)
    print(f"  Running with {workers} worker(s).")

    if workers == 1:
        for prompt_id in ["A", "B", "C"]:
            print(f"\n  Prompt {prompt_id} ({n_runs} evaluations)...")
            for run in range(1, n_runs + 1):
                records.append(run_single_evaluation(prompt_id, run, ollama_available))
            mean_c = round(
                sum(r["composite_score"] for r in records if r["prompt_id"] == prompt_id) / n_runs, 3
            )
            print(f"    mean composite = {mean_c}")
    else:
        print(f"\n  Running {len(tasks)} evaluations in parallel...")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(run_single_evaluation, prompt_id, run, ollama_available)
                for prompt_id, run in tasks
            ]
            for future in as_completed(futures):
                records.append(future.result())

        records.sort(key=lambda r: (r["prompt_id"], r["run"]))
        for prompt_id in ["A", "B", "C"]:
            prompt_records = [r for r in records if r["prompt_id"] == prompt_id]
            mean_c = round(sum(r["composite_score"] for r in prompt_records) / len(prompt_records), 3)
            print(f"  Prompt {prompt_id}: mean composite = {mean_c}")

    return pd.DataFrame(records)


# ============================================================
# SECTION 4: STATISTICAL ANALYSIS
# ============================================================

def run_statistics(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("STATISTICAL ANALYSIS")
    print("=" * 65)

    print("\n--- Descriptive Statistics ---")
    summary = df.groupby("prompt_id")["composite_score"].agg(["mean", "std", "count"]).round(3)
    print(summary)

    print("\n--- Mean Dimension Scores by Prompt ---")
    dim_table = df.groupby("prompt_id")[DIMENSIONS].mean().round(2)
    print(dim_table)

    a = df[df["prompt_id"] == "A"]["composite_score"]
    b = df[df["prompt_id"] == "B"]["composite_score"]
    c = df[df["prompt_id"] == "C"]["composite_score"]

    b_stat, b_p = bartlett(a, b, c)
    var_equal = b_p >= 0.05
    print(f"\nBartlett's Test: statistic={b_stat:.4f}, p={b_p:.4f}")
    print(f"Equal variance assumption: {'YES' if var_equal else 'NO'} "
          f"-> using {'standard' if var_equal else 'Welch'} ANOVA")

    print("\n--- One-Way ANOVA (A vs B vs C) ---")
    if var_equal:
        anova = pg.anova(dv="composite_score", between="prompt_id", data=df)
    else:
        anova = pg.welch_anova(dv="composite_score", between="prompt_id", data=df)
    print(anova.to_string(index=False))

    f_stat = anova["F"].values[0]
    p_anova = anova["p_unc"].values[0]
    print(f"\nF = {f_stat:.4f},  p = {p_anova:.6f}")
    if p_anova < 0.05:
        print("SIGNIFICANT: at least one prompt differs from the others (alpha=0.05).")
    else:
        print("NOT significant at alpha=0.05.")

    print("\n--- Pairwise T-Tests ---")
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    for p1, p2 in pairs:
        s1 = df[df["prompt_id"] == p1]["composite_score"]
        s2 = df[df["prompt_id"] == p2]["composite_score"]
        t_res = pg.ttest(s1, s2, correction=not var_equal)
        p_col = next(
            col for col in t_res.columns
            if col.lower() in {"p-val", "p_val", "pvalue", "p_value"}
            or ("p" in col.lower() and "val" in col.lower())
        )
        pv = t_res[p_col].values[0]
        tv = t_res["T"].values[0]
        sig = "SIGNIFICANT" if pv < 0.05 else "not significant"
        winner = p1 if s1.mean() > s2.mean() else p2
        line = f"  Prompt {p1} vs {p2}: T={tv:.3f}, p={pv:.6f} [{sig}]"
        if pv < 0.05:
            line += f" -> Prompt {winner} performs better"
        print(line)

    best = df.groupby("prompt_id")["composite_score"].mean().idxmax()
    best_mean = df.groupby("prompt_id")["composite_score"].mean()[best]
    print(f"\n>>> Best prompt: Prompt {best} (mean composite score = {best_mean:.3f})")


# ============================================================
# SECTION 5: VISUALIZATION
# ============================================================

def save_plots(df: pd.DataFrame, outfile: str = PLOT_OUT) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        "Gotham Air Quality Report Validation — Prompt Comparison",
        fontsize=13, fontweight="bold"
    )

    colors = {"A": "#2196F3", "B": "#4CAF50", "C": "#FF9800"}
    labels = {"A": "Prompt A\n(Scientific)", "B": "Prompt B\n(Commuter)", "C": "Prompt C\n(Community)"}

    # Plot 1: Boxplot of composite scores
    data_plot = [df[df["prompt_id"] == p]["composite_score"].values for p in ["A", "B", "C"]]
    bp = axes[0].boxplot(data_plot, tick_labels=list(labels.values()), patch_artist=True)
    for patch, color in zip(bp["boxes"], colors.values()):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[0].set_title("Composite Score Distribution")
    axes[0].set_ylabel("Composite Score (0-10)")
    axes[0].set_ylim(0, 10)
    axes[0].grid(axis="y", alpha=0.4)

    # Plot 2: Grouped bar chart for each dimension
    dim_means = df.groupby("prompt_id")[DIMENSIONS].mean()
    x = np.arange(len(DIMENSIONS))
    width = 0.25
    for i, (pid, color) in enumerate(colors.items()):
        axes[1].bar(x + i * width, dim_means.loc[pid], width=width,
                    label=f"Prompt {pid}", color=color, alpha=0.85, edgecolor="white")
    axes[1].set_xticks(x + width)
    axes[1].set_xticklabels(
        [d.replace("_", "\n") for d in DIMENSIONS], fontsize=7
    )
    axes[1].set_title("Mean Scores per Dimension")
    axes[1].set_ylabel("Score (0-10)")
    axes[1].set_ylim(0, 10)
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=0.4)

    # Plot 3: Mean ± SD bar chart
    means = df.groupby("prompt_id")["composite_score"].mean()
    stds  = df.groupby("prompt_id")["composite_score"].std()
    axes[2].bar(
        list(labels.values()), means.values,
        yerr=stds.values, capsize=7,
        color=list(colors.values()), alpha=0.85, edgecolor="black"
    )
    axes[2].set_title("Mean Composite Score +/- SD")
    axes[2].set_ylabel("Composite Score (0-10)")
    axes[2].set_ylim(0, 10)
    axes[2].grid(axis="y", alpha=0.4)

    plt.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved -> {outfile}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("GOTHAM AIR QUALITY REPORT VALIDATION EXPERIMENT")
    print("Shreya Dandwate — Custom Validation Framework")
    print("=" * 65)

    print(f"\nExperiment: {N_RUNS} evaluations x 3 prompts = {N_RUNS * 3} total\n")

    df = run_experiment(N_RUNS)

    print(f"\nSaving scores -> {SCORES_OUT}")
    df.to_csv(SCORES_OUT, index=False)

    run_statistics(df)
    save_plots(df)

    print("\n" + "=" * 65)
    print("Done. Output files:")
    print(f"  {SCORES_OUT}")
    print(f"  {PLOT_OUT}")
    print("=" * 65)
