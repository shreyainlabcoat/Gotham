import pandas as pd
import requests

def get_shortages(category="Psychiatry", limit=500):
    """Mocks the drug shortage data so the script has something to analyze."""
    # Creating a dummy dataframe that matches the filtering logic in 04_rules.py
    data = {
        "generic_name": ["Amphetamine Mixed Salts", "Methylphenidate", "Lisdexamfetamine", "Fluoxetine"],
        "update_date": ["2024-03-01", "2024-03-02", "2024-03-03", "2024-03-01"],
        "availability": ["Unavailable", "Unavailable", "Unavailable", "Available"],
        "category": [category] * 4
    }
    return pd.DataFrame(data)

def df_as_text(df):
    """Converts the pandas dataframe to a markdown table string."""
    if df.empty:
        return "No data available."
    return df.to_markdown(index=False)

def agent_run(role, task, model="smollm2:135m", output="text"):
    """Sends the prompt to your local Ollama instance, with fallback simulated responses."""
    url = "http://localhost:11434/api/generate"

    # Combine the system rules and the data task into one prompt
    full_prompt = f"{role}\n\nHere is the data:\n{task}"

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
        # Fallback to simulated response when Ollama is not available
        # Distinguish between agents by checking the role content

        role_lower = role.lower()
        first_line = role.split('\n')[0].lower() if role else ""

        if "data collector" in role_lower or "agent 1" in first_line:
            # Agent 1: Return pipe-delimited data format
            return """Location: Manhattan | Pollutant: PM2.5 | Value: 45.2 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:30:00Z | DataQuality: Good
Location: Brooklyn | Pollutant: PM2.5 | Value: 38.5 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:25:00Z | DataQuality: Good
Location: Queens | Pollutant: PM2.5 | Value: 52.1 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:20:00Z | DataQuality: Good
Total Locations: 3 | Valid Readings: 3 | Data Quality Score: 100% | Status: Ready"""

        elif "environmental" in role_lower and "analyst" in role_lower:
            # Agent 2: Return markdown table format
            return """| Location | PM2.5 (µg/m³) | Health Status | Exceeds EPA? | Risk Level |
|----------|---|--------|---|---|
| Queens | 52.1 | Unhealthy for Sensitive Groups | Yes | High |
| Manhattan | 45.2 | Unhealthy for Sensitive Groups | Yes | High |
| Brooklyn | 38.5 | Unhealthy for Sensitive Groups | Yes | Moderate |

**Analysis Summary:**
- Total Locations: 3
- Locations Exceeding EPA Standards: 3 (Queens, Manhattan, Brooklyn)
- Highest PM2.5: 52.1 µg/m³ at Queens
- Average PM2.5: 45.3 µg/m³
- Overall Assessment: Moderate to elevated pollution affecting all monitored areas. Multiple locations exceed EPA health thresholds.

[Alert] When levels exceed 35.4 µg/m³, sensitive populations (children, elderly, people with asthma) should limit outdoor activities."""

        else:
            # Agent 3: Return markdown alert format
            return """# Air Quality Alert for Queens and Manhattan - Elevated PM2.5

Queens is experiencing elevated air pollution at 52.1 µg/m³, exceeding EPA health standards.
Manhattan is also affected at 45.2 µg/m³. These levels pose health risks for vulnerable populations.

## Who is Most at Risk?
Children, elderly residents, and people with asthma, COPD, or heart disease are most vulnerable to elevated PM2.5 and should take extra precautions.

## What You Should Do:
- Limit outdoor activities: Avoid vigorous outdoor exercise like running or sports. Stay indoors when possible or use air-conditioned spaces.
- Wear an N95 mask: If you must go outside, wear a properly fitted N95 or KN95 mask for respiratory protection.
- Use air filters: Ensure your home has good air filtration. Consider running a portable HEPA air purifier in main living areas.
- Stay in air-conditioned spaces: Use libraries, malls, or indoor gyms which typically have better air systems.
- Monitor updates: Check NYC air quality forecasts at www.dec.ny.gov/airquality before outdoor activities.

## Get Help & Updates:
For questions about air quality and health impacts, contact NYC Department of Environmental Protection at 311 or visit www.dec.ny.gov/airquality."""