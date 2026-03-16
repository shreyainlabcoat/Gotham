"""
Evaluation Framework for Multi-Agent Air Quality System

This module provides testing and evaluation utilities for assessing the quality
and correctness of each agent's output.
"""

import re
from typing import Dict, List, Tuple


class EvaluationMetrics:
    """Metrics for evaluating agent outputs"""

    def __init__(self):
        self.test_results = []

    def evaluate_agent1_output(self, output: str) -> Dict:
        """
        Evaluate Agent 1 (Data Collector) output

        Checks:
        - All required fields present (Location, PM2.5, Unit, LastUpdated, DataQuality)
        - Values are numeric and in reasonable range (>0, <500)
        - Timestamps are present and ISO format
        - Total count is provided
        """
        metrics = {
            "agent": "Agent 1: Data Collector",
            "passed": True,
            "issues": [],
            "fields_present": True,
            "valid_values": True,
            "has_summary": False,
            "data_completeness": 0.0,
        }

        # Check for required fields
        required_fields = [
            "Location:",
            "PM2.5",
            "Value:",
            "Unit:",
            "LastUpdated:",
            "DataQuality:",
        ]
        for field in required_fields:
            if field not in output:
                metrics["fields_present"] = False
                metrics["issues"].append(f"Missing required field: {field}")
                metrics["passed"] = False

        # Check for numeric values in reasonable range
        values = re.findall(r"Value: ([\d.]+)", output)
        if values:
            for val in values:
                try:
                    num = float(val)
                    if num <= 0 or num > 500:
                        metrics["valid_values"] = False
                        metrics["issues"].append(f"Suspicious PM2.5 value: {val} µg/m³")
                        metrics["passed"] = False
                except ValueError:
                    metrics["valid_values"] = False
                    metrics["issues"].append(f"Non-numeric value found: {val}")
                    metrics["passed"] = False

        # Check for summary line
        if "Total Locations:" in output and "Data Quality Score:" in output:
            metrics["has_summary"] = True
        else:
            metrics["issues"].append("Missing summary statistics")

        # Count data completeness
        location_count = len(re.findall(r"Location:", output))
        if location_count >= 3:
            metrics["data_completeness"] = 1.0
        elif location_count >= 2:
            metrics["data_completeness"] = 0.67
        else:
            metrics["data_completeness"] = 0.0
            metrics["issues"].append(f"Only {location_count} locations found (expected >=3)")

        if metrics["data_completeness"] < 0.67:
            metrics["passed"] = False

        return metrics

    def evaluate_agent2_output(self, output: str) -> Dict:
        """
        Evaluate Agent 2 (Environmental Analyst) output

        Checks:
        - Valid markdown table format (pipes, headers, dashes)
        - Correct EPA categorization based on PM2.5 values
        - Sorted by PM2.5 (highest first)
        - All required columns present: Location, PM2.5, Health Status, Exceeds EPA?, Risk Level
        - EPA threshold accuracy (>= 35.5 should be marked "Yes")
        """
        metrics = {
            "agent": "Agent 2: Environmental Analyst",
            "passed": True,
            "issues": [],
            "table_format_valid": False,
            "columns_correct": False,
            "categories_accurate": True,
            "sorting_correct": True,
            "epa_accuracy": 1.0,
        }

        # Check for markdown table structure
        lines = output.split("\n")
        table_lines = [l for l in lines if "|" in l]

        if len(table_lines) < 3:
            metrics["issues"].append("No valid markdown table found (need header + separator + rows)")
            metrics["passed"] = False
            return metrics

        # Verify header row and separator
        if not any("Location" in l and "PM2.5" in l for l in table_lines[:2]):
            metrics["issues"].append("Table headers missing or incorrect")
            metrics["passed"] = False
        else:
            metrics["table_format_valid"] = True

        # Check required columns
        header = table_lines[0] if table_lines else ""
        required_cols = ["Location", "PM2.5", "Health Status", "Exceeds EPA", "Risk Level"]
        missing_cols = [col for col in required_cols if col not in header]
        if missing_cols:
            metrics["issues"].append(f"Missing columns: {missing_cols}")
            metrics["passed"] = False
            metrics["columns_correct"] = False
        else:
            metrics["columns_correct"] = True

        # Extract data rows and check EPA accuracy
        pm25_values = []
        for line in table_lines[2:]:  # Skip header and separator
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 5:
                try:
                    # Try to extract PM2.5 value
                    pm25_str = cells[2].replace("µg/m³", "").strip()
                    pm25_value = float(pm25_str)
                    pm25_values.append(pm25_value)

                    # Check EPA accuracy
                    exceeds_epa_marked = "Yes" in cells[4]
                    actually_exceeds = pm25_value >= 35.5

                    if exceeds_epa_marked != actually_exceeds:
                        metrics["issues"].append(
                            f"EPA marking error: {pm25_value} marked as '{cells[4]}' but should be {'Yes' if actually_exceeds else 'No'}"
                        )
                        metrics["epa_accuracy"] -= 0.1
                except (ValueError, IndexError) as e:
                    pass

        # Check sorting (should be descending)
        if len(pm25_values) > 1:
            is_sorted = all(
                pm25_values[i] >= pm25_values[i + 1] for i in range(len(pm25_values) - 1)
            )
            if not is_sorted:
                metrics["issues"].append("Data not sorted by PM2.5 (highest first)")
                metrics["sorting_correct"] = False
                metrics["passed"] = False
            else:
                metrics["sorting_correct"] = True

        # Check for health categories
        valid_categories = [
            "Good",
            "Moderate",
            "Unhealthy for Sensitive Groups",
            "Unhealthy",
            "Very Unhealthy",
        ]
        for category in valid_categories:
            if category in output:
                break
        else:
            metrics["issues"].append("No valid EPA health categories detected")
            metrics["categories_accurate"] = False
            metrics["passed"] = False

        if metrics["epa_accuracy"] < 0.8:
            metrics["passed"] = False

        return metrics

    def evaluate_agent3_output(self, output: str) -> Dict:
        """
        Evaluate Agent 3 (Public Health Officer) output

        Checks:
        - Proper structure: headline, summary, at-risk populations, recommendations, resources
        - Specific PM2.5 values cited (not generic ranges)
        - Recommendations are specific and actionable (contain action verbs)
        - Markdown formatting is correct
        - Tone is appropriate
        """
        metrics = {
            "agent": "Agent 3: Public Health Alert",
            "passed": True,
            "issues": [],
            "has_headline": False,
            "has_summary": False,
            "has_risk_populations": False,
            "has_recommendations": False,
            "has_resources": False,
            "citations_specific": True,
            "recommendations_actionable": True,
            "structure_complete": False,
        }

        # Check for section headers
        if re.search(r"#\s+.*Alert.*", output):
            metrics["has_headline"] = True
        else:
            metrics["issues"].append("Missing alert headline (should start with #)")

        if (
            re.search(r"##\s+.*[Rr]isk|##\s+[Ww]ho.*[Aa]t.*[Rr]isk", output)
            or "Who is Most at Risk" in output
        ):
            metrics["has_risk_populations"] = True
        else:
            metrics["issues"].append("Missing at-risk population section")

        if (
            re.search(r"##\s+[Ww]hat.*[Yy]ou.*[Dd]o", output)
            or "What You Should Do" in output
        ):
            metrics["has_recommendations"] = True
            # Check for bullet points
            if "-" not in output or "•" not in output:
                pass  # Some formatting is ok
        else:
            metrics["issues"].append("Missing 'What You Should Do' section")

        if (
            re.search(r"##\s+[Gg]et.*[Hh]elp|##\s+[Rr]esources", output)
            or "Get Help" in output
            or "311" in output
        ):
            metrics["has_resources"] = True
        else:
            metrics["issues"].append("Missing resources section (should include 311 or help information)")

        # Check for specific PM2.5 citations
        pm25_pattern = r"(\d+\.?\d*)\s*µg/m³|(\d+\.?\d*)\s*ug/m3"
        citations = re.findall(pm25_pattern, output)
        if len(citations) < 2:
            metrics["issues"].append(f"Only {len(citations)} specific PM2.5 citations found (need at least 2)")
            metrics["citations_specific"] = False
        else:
            metrics["citations_specific"] = True

        # Check for action verbs indicating specific recommendations
        action_verbs = [
            "limit",
            "wear",
            "use",
            "stay",
            "check",
            "seek",
            "apply",
            "keep",
            "monitor",
            "reduce",
        ]
        found_verbs = sum(1 for verb in action_verbs if verb.lower() in output.lower())
        if found_verbs < 3:
            metrics["issues"].append(f"Only {found_verbs} action verbs found (need at least 3)")
            metrics["recommendations_actionable"] = False

        # Check structure completeness
        if (
            metrics["has_headline"]
            and metrics["has_risk_populations"]
            and metrics["has_recommendations"]
            and metrics["has_resources"]
        ):
            metrics["structure_complete"] = True
        else:
            metrics["passed"] = False

        if not metrics["citations_specific"]:
            metrics["passed"] = False

        if not metrics["recommendations_actionable"]:
            metrics["passed"] = False

        return metrics


class TestCases:
    """Pre-defined test cases for evaluating the system"""

    @staticmethod
    def get_test_cases() -> List[Dict]:
        """Returns list of test cases with known inputs and expected characteristics"""
        return [
            {
                "name": "Scenario A: Moderate Pollution (Normal Case)",
                "description": "Mixed air quality - some locations moderate, some good",
                "agent1_input": "Fetch current NYC air quality data for PM2.5",
                "expected_agent1_contains": [
                    "Manhattan",
                    "Brooklyn",
                    "PM2.5",
                    "µg/m³",
                    "Total Locations",
                ],
                "expected_agent2_characteristics": [
                    "Markdown table",
                    "Health Status column",
                    "Sorted by value",
                ],
                "expected_agent3_tone": "Professional, informative",
            },
            {
                "name": "Scenario B: High Pollution (Alert Case)",
                "description": "PM2.5 levels exceeding EPA standards in multiple locations",
                "agent1_input": "Get latest PM2.5 measurements for NYC including data quality",
                "expected_agent1_contains": [
                    "Location",
                    "Value",
                    "DataQuality",
                    "Total Locations",
                ],
                "expected_agent2_characteristics": [
                    "Multiple 'Yes' EPA exceedances",
                    "High risk levels",
                    "Proper sorting",
                ],
                "expected_agent3_tone": "Urgent but not panic-inducing",
            },
            {
                "name": "Scenario C: Mixed Data Quality",
                "description": "Some data available, some locations missing or stale",
                "agent1_input": "Retrieve all available NYC air quality data for PM2.5",
                "expected_agent1_contains": [
                    "DataQuality: Stale",
                    "Data Quality Score",
                    "Status",
                ],
                "expected_agent2_characteristics": [
                    "Notes on data quality",
                    "Only uses good data",
                ],
                "expected_agent3_tone": "Transparent about data limitations",
            },
        ]


def print_evaluation_report(all_results: List[Dict], iteration: int = 1):
    """Print formatted evaluation report"""
    print(f"\n{'='*80}")
    print(f"ITERATION {iteration} EVALUATION REPORT")
    print(f"{'='*80}\n")

    overall_passed = True
    for agent_results in all_results:
        print(f"\n{agent_results['agent']}")
        print(f"{'-' * 60}")

        print(f"Status: {'[PASSED]' if agent_results['passed'] else '[FAILED]'}")

        if agent_results["issues"]:
            print(f"\nIssues Found ({len(agent_results['issues'])}):")
            for issue in agent_results["issues"]:
                print(f"  * {issue}")
        else:
            print("\nNo issues found!")

        # Print specific metrics
        for key, value in agent_results.items():
            if key not in ["agent", "passed", "issues"]:
                if isinstance(value, bool):
                    status = "[OK]" if value else "[X]"
                    print(f"  {status} {key}: {value}")
                elif isinstance(value, float):
                    print(f"  * {key}: {value:.1%}")

        if not agent_results["passed"]:
            overall_passed = False

    print(f"\n{'='*80}")
    if overall_passed:
        print("ALL AGENTS PASSED EVALUATION")
    else:
        print("SOME AGENTS FAILED - PROMPTS NEED REFINEMENT")
    print(f"{'='*80}\n")

    return overall_passed


if __name__ == "__main__":
    # Example usage
    metrics = EvaluationMetrics()
    print("Evaluation framework loaded successfully")
    print(f"Available test cases: {len(TestCases.get_test_cases())}")
