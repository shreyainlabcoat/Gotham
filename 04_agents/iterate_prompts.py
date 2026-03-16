"""
Iteration Script for Multi-Agent Prompt Refinement

This script manages multiple iterations of the multi-agent system,
tracking improvements and issues across iterations.
"""

import json
import sys
import importlib.util
from datetime import datetime
from eval_framework import EvaluationMetrics

# Import run_workflow from 04_rules.py using importlib
spec = importlib.util.spec_from_file_location("rules_04", "04_rules.py")
rules_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules_module)
run_workflow = rules_module.run_workflow

class IterationTracker:
    """Tracks results and improvements across iterations"""

    def __init__(self):
        self.iterations = {}

    def add_iteration(self, iteration_num: int, results: dict):
        """Record results for an iteration"""
        self.iterations[iteration_num] = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

    def get_improvement(self, iteration_a: int, iteration_b: int) -> dict:
        """Compare two iterations to see improvements"""
        if iteration_a not in self.iterations or iteration_b not in self.iterations:
            return None

        improvements = {"agents": {}}

        # Compare each agent
        for agent_idx, agent_key in enumerate([0, 1, 2]):
            agent_name = [
                "Agent 1: Data Collector",
                "Agent 2: Environmental Analyst",
                "Agent 3: Public Health Officer",
            ][agent_idx]

            old_passed = self.iterations[iteration_a]["results"][agent_key].get("passed", False)
            new_passed = self.iterations[iteration_b]["results"][agent_key].get("passed", False)

            old_issues = len(self.iterations[iteration_a]["results"][agent_key].get("issues", []))
            new_issues = len(self.iterations[iteration_b]["results"][agent_key].get("issues", []))

            improvements["agents"][agent_name] = {
                "passed_before": old_passed,
                "passed_now": new_passed,
                "issues_before": old_issues,
                "issues_now": new_issues,
                "improvement": new_passed and not old_passed,
                "issues_reduced": new_issues < old_issues,
            }

        return improvements


def run_iterations(num_iterations: int = 2):
    """Run multiple iterations of the workflow and track improvements"""

    tracker = IterationTracker()
    all_results = []

    for i in range(1, num_iterations + 1):
        print(f"\n\n{'#'*80}")
        print(f"# STARTING ITERATION {i} OF {num_iterations}")
        print(f"{'#'*80}\n")

        result1, result2, result3, passed = run_workflow(iteration=i, show_eval=True)

        # Store evaluation results for comparison
        metrics = EvaluationMetrics()
        eval_results = [
            metrics.evaluate_agent1_output(result1),
            metrics.evaluate_agent2_output(result2),
            metrics.evaluate_agent3_output(result3),
        ]

        tracker.add_iteration(i, eval_results)
        all_results.append({"iteration": i, "results": eval_results})

    # Print summary comparison
    print_iterations_summary(tracker, num_iterations)

    return all_results


def print_iterations_summary(tracker: IterationTracker, num_iterations: int):
    """Print summary comparing all iterations"""

    print(f"\n\n{'='*80}")
    print("ITERATION COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    if num_iterations < 2:
        print("Need at least 2 iterations to compare. Run with num_iterations >= 2")
        return

    for i in range(2, num_iterations + 1):
        improvements = tracker.get_improvement(i - 1, i)

        print(f"\nComparison: Iteration {i-1} -> Iteration {i}")
        print("-" * 60)

        for agent_name, stats in improvements["agents"].items():
            print(f"\n{agent_name}:")
            print(f"  Passed: {stats['passed_before']} -> {stats['passed_now']}")
            print(f"  Issues: {stats['issues_before']} -> {stats['issues_now']}")

            if stats["improvement"]:
                print(f"  [OK] IMPROVEMENT: Now passing!")
            elif stats["issues_reduced"]:
                print(f"  [WARN] Still failing but issues reduced")
            elif not stats["passed_before"] and not stats["passed_now"]:
                print(f"  [X] No improvement yet")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # Run 2 iterations and compare
    print("Starting iteration loop...")
    print("This will run the full workflow twice and compare results.\n")

    results = run_iterations(num_iterations=2)

    print("\n" + "="*80)
    print("ITERATION LOOP COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the evaluation reports above")
    print("2. If all agents passed: System is ready for deployment")
    print("3. If some agents failed: Review PROMPT_DESIGN_FINDINGS.md for guidance")
    print("4. Edit system_prompts.yaml to fix failing agents")
    print("5. Re-run this script to validate improvements\n")
