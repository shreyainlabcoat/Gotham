# Multi-Agent System Design: NYC Environmental Dashboard

## System Overview

This document describes a 3-agent sequential pipeline system for analyzing environmental air quality data and generating public health alerts for NYC residents.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MULTI-AGENT WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐     ┌──────────────────┐   ┌──────────────┐ │
│  │   AGENT 1        │     │   AGENT 2        │   │   AGENT 3    │ │
│  │  Data Fetch &    │────▶│  Environmental   │──▶│  Alert       │ │
│  │  Validation      │     │  Analysis        │   │  Generation  │ │
│  └──────────────────┘     └──────────────────┘   └──────────────┘ │
│         │                        │                       │         │
│      Input:                   Input:                 Input:         │
│    User Request          Raw Data from          Analyzed Data      │
│                          Agent 1                 from Agent 2      │
│                                                                     │
│      Output:                Output:               Output:           │
│   Validated Data          Markdown Table      Formatted Alert      │
│    with Quality           with Health         with Specific         │
│    Indicators            Rankings            Recommendations       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Specification

**Agent 1 Output → Agent 2 Input**:
- Format: Plain text, newline-separated records
- Contract: Each line contains: Location | Pollutant | Value | Unit | LastUpdated

**Agent 2 Output → Agent 3 Input**:
- Format: Markdown table with headers
- Contract: Contains Location, PM2.5 values, Health Status classifications

**Agent 3 Output**:
- Format: Markdown-formatted alert text
- Contract: Contains headline, summary, affected populations, specific recommendations

---

## Agent Specifications

### Agent 1: Data Collector & Validator

**Role**: Fetch real-time air quality data from OpenAQ and validate data quality before passing to analysis.

**Responsibility**: Ensure downstream agents receive only high-quality, complete data with clear quality indicators.

#### Input Specification

**Format**: User request for NYC air quality data

**Required Elements**:
- Time window: "current/latest"
- Geographic scope: NYC (all boroughs)
- Pollutant focus: PM2.5
- Source: OpenAQ API (primary), fallback to recent historical data

**Example Input**:
```
Fetch the latest air quality data for New York City, specifically PM2.5 measurements from all monitoring stations. Include the most recent reading for each location. If real-time data is unavailable, provide the most recent available data with a clear timestamp.
```

#### Output Specification

**Format**: Structured text, one data point per line

**Required Columns**:
1. Location (neighborhood/borough)
2. Pollutant (should be PM2.5)
3. Value (numeric)
4. Unit (µg/m³)
5. LastUpdated (ISO timestamp)
6. DataQualityFlag (empty if good, or alert: "Stale" / "Missing" / "Unusual")

**Constraints**:
- Must include all available NYC locations
- Must indicate if data is >1 hour old
- Flag any suspicious values (outliers, negative numbers)
- Include count of valid data points

**Example Output**:
```
Location: Manhattan | Pollutant: PM2.5 | Value: 45.2 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:30:00Z | DataQuality: Good
Location: Brooklyn | Pollutant: PM2.5 | Value: 38.5 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:25:00Z | DataQuality: Good
Location: Queens | Pollutant: PM2.5 | Value: 52.1 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:20:00Z | DataQuality: Good
Total Locations: 3 | Data Quality: 100% valid readings | Status: Ready for analysis
```

**Success Criteria**:
- ✅ All NYC locations included
- ✅ All required fields present (no missing columns)
- ✅ Values are numeric and reasonable (>0, <500 µg/m³)
- ✅ Timestamps are recent (<4 hours old)
- ✅ Data quality flags are accurate
- ✅ Summary statistics provided

---

### Agent 2: Environmental Data Analysis

**Role**: Analyze raw air quality data and produce a structured health assessment ranking locations by pollution severity.

**Responsibility**: Translate raw measurements into actionable health categories for downstream alert generation.

#### Input Specification

**Source**: Agent 1 output (validated air quality data)

**Expected Format**: Structured text with Location, PM2.5 Value, Unit, Timestamp, Quality Flag

**Example Input**:
```
Location: Manhattan | Pollutant: PM2.5 | Value: 45.2 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:30:00Z | DataQuality: Good
Location: Brooklyn | Pollutant: PM2.5 | Value: 38.5 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:25:00Z | DataQuality: Good
Location: Queens | Pollutant: PM2.5 | Value: 52.1 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:20:00Z | DataQuality: Good
```

#### Output Specification

**Format**: Markdown-formatted table with analysis results

**Required Columns**:
1. Location
2. PM2.5 Value (µg/m³)
3. Health Status (Good / Moderate / Unhealthy for Sensitive Groups / Unhealthy / Very Unhealthy)
4. Exceeds EPA? (Yes / No)
5. Health Risk Level (Low / Moderate / High / Critical)

**EPA PM2.5 Thresholds** (24-hour standard):
- < 12.0: Good (Green)
- 12.1-35.4: Moderate (Yellow)
- 35.5-55.4: Unhealthy for Sensitive Groups (Orange)
- 55.5-150.4: Unhealthy (Red)
- > 150.4: Very Unhealthy (Purple)

**Styling Rules**:
- Sort rows by PM2.5 value HIGHEST to LOWEST (worst air quality first)
- Mark any exceeding 35.5 with ⚠️ notation
- Add summary statistics below table
- Include recommendation: "Sensitive populations should limit outdoor activity" if any location exceeds 35.4

**Example Output**:
```
| Location | PM2.5 (µg/m³) | Health Status | Exceeds EPA? | Risk Level |
|----------|---|--------|---|---|
| Queens | 52.1 | Unhealthy for Sensitive Groups | ⚠️ Yes | High |
| Manhattan | 45.2 | Unknown for Sensitive Groups | ⚠️ Yes | High |
| Brooklyn | 38.5 | Moderate | ⚠️ Yes | Moderate |

**Summary**: 3 locations monitored. 2 locations (Queens, Manhattan) exceed EPA healthy thresholds. Average PM2.5: 45.3 µg/m³.

**Overall Assessment**: Moderate to elevated pollution levels. Sensitive populations should limit outdoor activity.
```

**Success Criteria**:
- ✅ Markdown table with correct format
- ✅ All locations from Agent 1 included
- ✅ Health status categories are correct for each PM2.5 value
- ✅ EPA exceedances marked accurately
- ✅ Sorted by PM2.5 value (highest first)
- ✅ Summary statistics provided
- ✅ No formatting errors (pipes, dashes aligned)

---

### Agent 3: Public Health Alert Generator

**Role**: Transform air quality analysis into urgent, actionable public health alerts with specific recommendations for NYC residents.

**Responsibility**: Communicate health risks and protective measures in clear, compelling language that motivates action.

#### Input Specification

**Source**: Agent 2 output (analyzed data as markdown table)

**Expected Format**: Markdown table with health status and PM2.5 values per location, plus summary assessment

**Example Input**:
```
| Location | PM2.5 (µg/m³) | Health Status | Exceeds EPA? | Risk Level |
|----------|---|--------|---|---|
| Queens | 52.1 | Unhealthy for Sensitive Groups | Yes | High |
| Manhattan | 45.2 | Unhealthy for Sensitive Groups | Yes | High |
| Brooklyn | 38.5 | Moderate | Yes | Moderate |

Summary: 3 locations monitored. 2 locations exceed EPA thresholds. Average PM2.5: 45.3 µg/m³.
Overall Assessment: Moderate to elevated pollution. Sensitive populations should limit outdoor activity.
```

#### Output Specification

**Format**: Markdown-formatted alert with structured sections

**Required Sections**:
1. **Headline** (1 line): Location-specific alert status
   - Format: "Air Quality Alert: [Primary Affected Area] - [Severity Level]"
   - Example: "Air Quality Alert: Queens & Manhattan - Elevated PM2.5"

2. **Summary** (1-2 sentences): Current conditions and primary concern
   - Must cite specific PM2.5 value
   - Must mention affected location(s)
   - Example: "Queens is experiencing elevated PM2.5 at 52.1 µg/m³, exceeding EPA health standards."

3. **At-Risk Populations** (1 sentence): Who is most vulnerable
   - Include: children, elderly, people with lung/heart conditions
   - Specific: "Particularly those with asthma, heart disease, or COPD"

4. **Specific Recommendations** (3-5 bullet points): What people should DO
   - Must be specific, not generic (e.g., "Avoid jogging in Central Park" not "Exercise less")
   - Use clear actions people can understand
   - Include both preventive (masks, air filters) and behavioral (limit outdoor time)
   - Format: "- Action verb: Specific recommendation"

5. **Resources** (1 sentence): Where to get help
   - NYC Department of Environmental Protection hotline
   - Air quality website for updates

**Tone & Style**:
- Professional but urgent (not alarmist)
- Use active voice
- Cite the actual PM2.5 values (not generic ranges)
- Keep paragraphs to 1-2 sentences max
- Use bullet points for recommendations

**Example Output**:
```
# Air Quality Alert: Queens & Manhattan - Elevated PM2.5

Queens is experiencing significantly elevated air pollution, with PM2.5 levels at 52.1 µg/m³—directly exceeding EPA health standards. Manhattan also shows elevated levels at 45.2 µg/m³.

## Who is most at risk?
Children, elderly residents, and people with asthma, heart disease, or chronic lung conditions are particularly vulnerable to elevated PM2.5.

## What you should do:
- **Limit outdoor activities**: Reduce time spent outside, especially vigorous exercise like running or outdoor sports
- **Wear an N95 mask**: If you must go outside, wear a properly fitted N95 or KN95 mask
- **Use air filters**: Ensure home and workplace HVAC systems have high-efficiency filters; consider a portable HEPA filter
- **Check air quality**: Monitor NYC Air Quality forecasts regularly at www.dec.ny.gov/airquality
- **Seek cleaner air**: If possible, spend time in air-conditioned spaces; consider visiting indoor venues

## Get help:
For more information on air quality and health impacts, contact NYC Department of Environmental Protection: 311 or visit www.dec.ny.gov.
```

**Success Criteria**:
- ✅ Alert headline clearly identifies affected areas
- ✅ Specific PM2.5 values cited (not generic ranges)
- ✅ Actionable recommendations (specific, not generic)
- ✅ At-risk populations clearly identified
- ✅ Recommendations are realistic and achievable
- ✅ Tone is appropriate (urgent but not panic-inducing)
- ✅ No formatting errors; uses markdown properly
- ✅ Readers know exactly what to do

---

## Workflow Execution Specification

### Sequential Pipeline
1. **Agent 1 executes**: Fetch and validate data
2. **Agent 2 executes**: Analyze data from Agent 1
3. **Agent 3 executes**: Generate alert from Agent 2 analysis
4. **Output**: Final alert is ready for dashboard display

### Error Handling
- If Agent 1 fails: Use simulated data with clear "SIMULATED" label
- If Agent 2 fails: Use basic health categorization fallback
- If Agent 3 fails: Use template alert with citations from Agent 2

### Data Contracts
- Each agent MUST verify input matches expected format
- Each agent MUST produce valid output before passing to next agent
- Missing data should trigger quality flags, not silent failures

---

## Success Metrics for System

| Aspect | Agent 1 | Agent 2 | Agent 3 |
|--------|---------|---------|---------|
| **Input Validation** | Recognizes API failures | Parses text correctly | Extracts data from tables |
| **Format Compliance** | All fields populated | Valid markdown table | Proper markdown structure |
| **Accuracy** | Values match source | Categories correct | Citations accurate |
| **Actionability** | Data is complete | Rankings are sensible | Recommendations are specific |
| **Usability** | Easy to parse | Clear formatting | Clear, urgent tone |

---

## Example: End-to-End Workflow

**User Request**: "What's the air quality situation in NYC today?"

**Agent 1 Output**:
```
Location: Manhattan | PM2.5: 45.2 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:30:00Z | Status: Good
Location: Queens | PM2.5: 52.1 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:20:00Z | Status: Good
```

**Agent 2 Output**:
```
| Location | PM2.5 | Health Status | Risk |
|----------|-------|------------------|------|
| Queens | 52.1 | Unhealthy for Sensitive | High |
| Manhattan | 45.2 | Unhealthy for Sensitive | High |
```

**Agent 3 Output**:
```
# Air Quality Alert: Queens & Manhattan - Elevated PM2.5
Queens reports PM2.5 at 52.1 µg/m³, exceeding EPA standards.
Sensitive populations should limit outdoor activities and wear N95 masks if outside.
```

---

## Design Decisions

1. **Sequential Pipeline**: Chosen because each step builds on the previous, and decision-making improves with structured intermediate results
2. **Explicit Format Specs**: Ensures agents produce predictable outputs that work well together
3. **Health Categories**: EPA standards used as authoritative reference for PM2.5 interpretation
4. **Markdown Output**: Human-readable, renders well in dashboards, supports bold/emphasis for urgency
5. **Specific Recommendations**: Replaces generic advice with actionable steps people can actually take

