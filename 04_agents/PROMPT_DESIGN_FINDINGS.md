# Multi-Agent Prompt Design: Iteration Findings & Lessons Learned

## Executive Summary

After running 2 iterations of the multi-agent system, significant issues were identified in how agents interpret and follow system prompts. **Key finding**: The current fallback mechanism in `functions.py` returns hardcoded responses that don't follow the new comprehensive system prompts we designed.

---

## Iteration 1 & 2 Results

### Problem Observed
All three agents returned identical or near-identical output across both iterations, indicating they were using the fallback responses rather than actually executing with the system prompts.

**Iteration 1 Agent 1 Output** (Expected: Structured data format):
```
| Location | PM2.5 (µg/m³) | Status |
|----------|---|--------|
| Manhattan | 45.2 | Moderate |
| Brooklyn | 38.5 | Moderate |
| Queens | 52.1 | Unhealthy for Sensitive Groups |

**Analysis:** Current air quality in NYC shows moderate to elevated PM2.5 levels...
```

**Issue**: This is a markdown table (Agent 2's format), not the pipe-delimited text format Agent 1 should produce.

---

## Root Cause Analysis

### Why Agents Aren't Following Prompts

1. **Ollama Not Running**: The `agent_run()` function in `functions.py` falls back to hardcoded responses when Ollama is unavailable
2. **Fallback Logic Too Simple**: The fallback detection (`if "data_analysis" in role.lower()`) is too simplistic - it can't distinguish between the three agents properly
3. **System Prompts Not Being Used**: The comprehensive system prompts we created are passed to `agent_run()` but never actually used since fallback kicks in immediately

### How It Should Work vs. How It Actually Works

**Intended Flow**:
```
system_prompt (from system_prompts.yaml)
    +
task (previous agent output or user request)
    ↓
Ollama/LLM processes
    ↓
Formatted output
```

**Actual Flow** (when Ollama not available):
```
agent_run(role=system_prompt, task=task)
    ↓
Ollama unavailable → Exception caught
    ↓
Simple regex check: "data_analysis" in role?
    ↓
Return hardcoded response (ignores actual prompt)
```

---

## What Worked: Design Phase

1. ✅ **System Design Document**: Clear architecture with explicit data contracts between agents
2. ✅ **Detailed System Prompts**: Each agent has 150+ words of specific instruction covering role, input/output format, constraints, and examples
3. ✅ **Evaluation Framework**: Automated metrics can correctly identify when agents fail to follow format specifications
4. ✅ **Test Infrastructure**: The iteration loop and comparison system works smoothly

---

## What Didn't Work: Execution Phase

1. ❌ **Fallback Responses**: Hardcoded fallback doesn't follow the real system prompts - creates confusion about what "good" output looks like
2. ❌ **Format Mismatch**: Fallback assumes all agents should return markdown, but Agent 1 should return pipe-delimited text
3. ❌ **Agent Confusion**: System can't distinguish between agents' expected output formats
4. ❌ **Prompt Following**: With an actual LLM available, unknown if it would follow the detailed prompts

---

## Key Insights from Prompt Engineering Attempt

### Insight 1: Output Format Specification Matters
**When**: Designing Agent 1 prompt
**Discovery**: Simply saying "return structured data" is vague. Must specify:
- Exact format (pipe-delimiters vs markdown vs JSON)
- Example of valid output
- What fields are required (Location, Value, Unit, etc.)
- What to do if data is missing

**Result**: System prompts include detailed format examples, but execution revealed they're not being followed.

### Insight 2: Agent Chaining Is Hard
**When**: Designing data flow between agents
**Discovery**: Output format of Agent N must exactly match input expectations of Agent N+1:
- If Agent 1 outputs pipe-delimited text, Agent 2 must be trained to parse pipe-delimited text
- If Agent 2 outputs markdown table, Agent 3 must know how to extract values from markdown

**Result**: Our system prompts assume this handoff works, but without actual LLM execution, we can't verify.

### Insight 3: Fallback Responses Are Training Data
**Discovery**: If your fallback responses don't follow your system prompts, they become anti-training-data. The evaluation framework will learn that fallbacks aren't what you actually want.

**Better approach**: Fallback responses should perfectly exemplify what the system prompts describe.

### Insight 4: Format Compliance is Testable, Behavior Isn't
**Success**: Our evaluation framework can automatically detect:
- ✅ Is output markdown table or plain text?
- ✅ Are required fields present?
- ✅ Are values within reasonable ranges?
- ❌ Is reasoning sound?
- ❌ Is the alert actually helpful?

**Implication**: For multi-agent systems, focus prompts on format/structure first, then on content quality.

---

## Recommendations for Prompt Iteration (Next Steps)

### Short Term: Fix Fallback Responses
**Problem**: Fallback responses don't match system prompts
**Solution**:
1. Create proper Agent 1 fallback that returns pipe-delimited text
2. Create proper Agent 2 fallback that returns markdown table
3. Create proper Agent 3 fallback that returns markdown alert
4. Update `functions.py` fallback logic to distinguish agent roles

**Code Change Needed in `functions.py`**:
```python
if "Data Collector" in role or "Agent 1" in role:
    return """Location: Manhattan | Pollutant: PM2.5 | Value: 45.2 | Unit: µg/m³ | LastUpdated: 2026-03-16T14:30:00Z | DataQuality: Good
..."""
elif "Environmental Analyst" in role or "Agent 2" in role:
    return """| Location | PM2.5 (µg/m³) | Health Status | ...
|----------|---|--------|..."""
else:
    return """# Air Quality Alert..."""
```

### Medium Term: Test With Real LLM
**When**: Ollama is set up and running
**Process**:
1. Run `iterate_prompts.py again with actual LLM
2. Evaluate if outputs match system prompts
3. If not, iteratively refine system prompts based on actual LLM behavior

### Long Term: System Prompt Optimization

**For Agent 1 (Data Collector)**:
- Current prompt: Too generic about "handling failures"
- Improvement: Add specific error codes and how to handle each
- Add: Instructions for rate limiting, retry logic

**For Agent 2 (Environmental Analyst)**:
- Current prompt: Good EPA categorization guidance
- Improvement: Add example input→output transformation
- Add: Instructions for handling partial data (some locations missing)

**For Agent 3 (Public Alert Writer)**:
- Current prompt: Very detailed (good!)
- Improvement: Add style guide (reading level, punctuation rules)
- Add: Tone calibration examples (when to write urgent vs. neutral)

---

## Lessons for Future Multi-Agent Systems

### 1. Design Your System Prompts Around Constraints, Not Capabilities
❌ Bad: "Analyze this data intelligently"
✅ Good: "Return a markdown table with these 5 columns in this order, sorted by highest value first"

### 2. Test Prompts Incrementally
- Test Agent 1 alone before chaining Agent 2
- Verify output format at each step
- Don't assume Agent 2 can parse Agent 1 output correctly

### 3. Make Fallback Responses "Gold Standard"
- Fallback responses should be perfect examples of what you want
- Use them as test cases for evaluation
- When real LLM output differs, that's a prompt refinement signal

### 4. Evaluation Framework Should Be Strict
- Our eval framework correctly identified all failures
- It checks format, not just "is the output reasonable"
- This is correct for multi-agent systems where format matters most

### 5. Role-Based Prompting Is Powerful But Requires Specificity
- Telling an agent its "role" helps, but isn't enough
- Must specify: Input format, Output format, Success criteria, Examples
- Without these, quality is unpredictable

---

## System Prompts Quality Assessment

### Agent 1: Data Collector - Score: 8/10
**Strengths**:
- Clear role definition and responsibility
- Precise output format specification with example
- Explicit data quality flags defined
- Good error handling guidance

**Needs Work**:
- Could specify timeout behavior for slow APIs
- Could add instructions for handling partial data (some locations, no others)
- Could specify pagination handling for large datasets

### Agent 2: Environmental Analyst - Score: 9/10
**Strengths**:
- Excellent EPA threshold table for reference
- Exact markdown table format specified
- Clear sorting requirement (highest first)
- Good conditional health recommendations

**Needs Work**:
- Could add examples of incorrect EPA categorizations (for training)
- Could specify how to handle conflicting data
- Could add tone guidance (clinical vs. accessible language)

### Agent 3: Public Alert Writer - Score: 8.5/10
**Strengths**:
- Very detailed structure (headline, summary, at-risk, recommendations, resources)
- Excellent action verb specification (Limit, Wear, Use, Check, Seek)
- Good tone calibration (urgent but not alarming)
- Specific examples of Good vs. Bad recommendations

**Needs Work**:
- Could add reading level guidance (8th grade English target)
- Could specify content length limits (alert in <2 min read)
- Could add instructions for multilocal alerts (how to prioritize which areas to mention)

---

## Verification: Do Prompts Match System Design?

| Aspect | Design Doc | System Prompt | Match? |
|--------|-----------|---------------|--------|
| Output format | Pipe-delimited text | Pipe-delimited text | ✅ Yes |
| Required fields | Location, Value, Unit, LastUpdated, QualityFlag | All specified | ✅ Yes |
| EPA categories | 5 categories defined | All 5 in table | ✅ Yes |
| Table sorting | Highest pollution first | Explicitly: "HIGHEST to LOWEST" | ✅ Yes |
| Action verbs | Not specified in design | "Limit, Wear, Use, Check, Seek" | ✅ Added |
| Example outputs | Provided | Provided | ✅ Yes |
| Error handling | Graceful fallback | "Transparent about data source" | ✅ Yes |

**Conclusion**: System prompts accurately translate system design into executable instructions.

---

## Next Iteration Plan

### When Ollama is Available:
1. Run `iterate_prompts.py` with Ollama running
2. Compare actual LLM outputs against system prompts
3. If outputs don't match:
   - Identify which prompt section failed
   - Refine that section with more specificity or examples
   - Re-run iteration
4. Repeat until all agents pass evaluation 3 times in a row

### What to Look For:
- **Format deviation**: Does output match specified format?
- **Content accuracy**: Are facts/numbers correct?
- **Completeness**: Are all required sections present?
- **Tone accuracy**: Is urgency level appropriate?

### How to Refine:
- Add more examples if output deviates from format
- Specify constraints more precisely if violations occur
- Use "MUST" not "should" for non-negotiable requirements
- Add output length limits if outputs are too long/short

---

## Conclusion

The **system design and prompt engineering effort was successful**, but **execution was blocked by lack of running LLM**. The evaluation framework correctly identified all deviations from requirements. When an LLM is available:

1. Run the full iteration loop with real agent
2. Refine system prompts based on actual LLM behavior
3. Document which prompt changes led to improvements
4. Validate that final system reliably produces compliant outputs

**Deliverables Completed**:
- ✅ System Design Document (system_design.md) - Comprehensive architecture
- ✅ System Prompts (system_prompts.yaml) - Detailed agent instructions
- ✅ Evaluation Framework (eval_framework.py) - Automated quality testing
- ✅ Iteration Infrastructure (iterate_prompts.py) - Multi-iteration runner
- ✅ This Report (PROMPT_DESIGN_FINDINGS.md) - Full analysis and lessons
- ⏳ Real-world Iteration (pending Ollama availability) - Will complete when LLM available
