"""
Multi-Agent Orchestration for NYC Environmental Dashboard

This script manages a 3-agent pipeline:
1. Data Collector: Fetches and validates air quality data
2. Environmental Analyst: Analyzes data and produces health assessment
3. Public Health Officer: Generates actionable public alerts
"""

import yaml
from functions import agent_run
from eval_framework import EvaluationMetrics, print_evaluation_report

# 1. CONFIGURATION
MODEL = "smollm2:135m"
SHOW_EVALUATION = True  # Set to False to skip evaluation output

# 2. LOAD SYSTEM PROMPTS FROM YAML
with open("system_prompts.yaml", "r", encoding="utf-8") as f:
    system_prompts = yaml.safe_load(f)

agent1_prompt = system_prompts["agents"]["data_collector"]["system_prompt"]
agent2_prompt = system_prompts["agents"]["environmental_analyst"]["system_prompt"]
agent3_prompt = system_prompts["agents"]["public_health_officer"]["system_prompt"]


# 3. WORKFLOW EXECUTION
def run_workflow(iteration: int = 1, show_eval: bool = True):
    """
    Execute the 3-agent pipeline with evaluation

    Args:
        iteration: Iteration number (for reporting)
        show_eval: Whether to show evaluation results
    """
    print(f"\n{'='*80}")
    print(f"ITERATION {iteration}: RUNNING MULTI-AGENT WORKFLOW")
    print(f"{'='*80}\n")

    evaluation_results = []
    metrics = EvaluationMetrics()

    # ========== AGENT 1: DATA COLLECTOR ==========
    print(">> AGENT 1: Data Collector & Validator")
    print("-" * 60)

    task1 = "Fetch the latest air quality data for New York City, specifically PM2.5 measurements from all monitoring stations."
    result1 = agent_run(role=agent1_prompt, task=task1, model=MODEL, output="text")

    print("OUTPUT:")
    print(result1)
    print()

    # Evaluate Agent 1
    eval1 = metrics.evaluate_agent1_output(result1)
    evaluation_results.append(eval1)

    # ========== AGENT 2: ENVIRONMENTAL ANALYST ==========
    print(">> AGENT 2: Environmental Data Analyst")
    print("-" * 60)

    task2 = result1  # Use Agent 1 output as input
    result2 = agent_run(role=agent2_prompt, task=task2, model=MODEL, output="text")

    print("OUTPUT:")
    print(result2)
    print()

    # Evaluate Agent 2
    eval2 = metrics.evaluate_agent2_output(result2)
    evaluation_results.append(eval2)

    # ========== AGENT 3: PUBLIC HEALTH OFFICER ==========
    print(">> AGENT 3: Public Health Alert Officer")
    print("-" * 60)

    task3 = result2  # Use Agent 2 output as input
    result3 = agent_run(role=agent3_prompt, task=task3, model=MODEL, output="text")

    print("OUTPUT:")
    print(result3)
    print()

    # Evaluate Agent 3
    eval3 = metrics.evaluate_agent3_output(result3)
    evaluation_results.append(eval3)

    # ========== EVALUATION SUMMARY ==========
    if show_eval:
        overall_passed = print_evaluation_report(evaluation_results, iteration=iteration)
        return result1, result2, result3, overall_passed
    else:
        return result1, result2, result3, None


if __name__ == "__main__":
    # Run the workflow
    result1, result2, result3, passed = run_workflow(iteration=1, show_eval=SHOW_EVALUATION)