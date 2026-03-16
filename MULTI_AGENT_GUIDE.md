# Multi-Agent Workflow Learning Path
## Complete Guide to Building Agent Chains

---

## 📚 Directory of Files

### **Stage 1: Understanding the Basics**
**File**: `03_agents.py`
- **What it teaches**: How 3 agents work together sequentially
- **Pattern**: Agent 1 output → Agent 2 input → Agent 3 output
- **Key concept**: Data flowing through a pipeline
- **Complexity**: ⭐☆☆☆☆ (Very basic)
- **Run it**: `python 03_agents.py`

### **Stage 2: Simple 2-Agent Chain**
**File**: `03_agents_stage2.py`
- **What it teaches**: Minimal working example of agent chaining
- **Pattern**: Raw Data → Summarizer Agent → Formatter Agent
- **Key concept**: Data transformation at each step
- **Complexity**: ⭐⭐☆☆☆ (Very simple, easy to modify)
- **Run it**: `python 03_agents_stage2.py`
- **Modification ideas**:
  - Add a 3rd agent for translation
  - Change roles to handle different data types
  - Test with your own input data

### **Stage 3: Vision-Language Models (VLMs)**
**File**: `03_agents_vlm.py`
- **What it teaches**: Multimodal agents that understand images
- **Pattern**: Image + Text → VLM Analysis → LLM Report
- **Key concept**: Different agent types for different modalities
- **Complexity**: ⭐⭐⭐☆☆ (More advanced, requires image processing)
- **Run it**: `python 03_agents_vlm.py`
- **Requirements**:
  - Ollama with `llava` model (vision)
  - Ollama with `smollm2:135m` model (text)

### **Stage 3 Extended: Parallel Agents & Audio**
**File**: `03_agents_advanced.py`
- **What it teaches**:
  - Running multiple agents in parallel
  - Audio-Language Model (ALM) agents
  - Synthesizing results from multiple sources
- **Pattern**: Input → [Agent A, Agent B, Agent C] (parallel) → Synthesizer
- **Key concepts**:
  - Concurrent execution
  - Multi-perspective analysis
  - Result synthesis
- **Complexity**: ⭐⭐⭐⭐☆ (Advanced, uses multithreading)
- **Run it**: `python 03_agents_advanced.py`

---

## 🔄 Learning Path Progression

```
START
  ↓
[03_agents.py]
Understand basic sequential pipeline
  ↓
[03_agents_stage2.py]
Practice with simple 2-agent chain
  ↓
[03_agents_vlm.py]
Learn about multimodal agents
  ↓
[03_agents_advanced.py]
Master parallel execution & synthesis
  ↓
END (Ready to build your own!)
```

---

## 🎯 Key Concepts Taught

### 1. **Data Pipeline**
- Agent N outputs structured data
- This becomes Agent N+1's input
- Format must be compatible
- Example: Agent 1 summarizes → Agent 2 formats summary

### 2. **Agent Roles**
- Each agent has a specific responsibility
- Clear role definition improves output quality
- Roles should complement each other
- Example: Analyzer doesn't need to know how to format

### 3. **Multimodal Processing**
- VLMs: Process images + text together
- ALMs: Process audio + text together
- LLMs: Process text only
- Chain different types for comprehensive analysis

### 4. **Parallel Processing**
- Multiple agents can analyze same input simultaneously
- Saves time vs sequential processing
- Enables multi-perspective analysis
- Requires synthesis step to combine results

### 5. **Error Handling & Fallbacks**
- Always define fallback responses
- Agents may be unavailable (Ollama down, API limits)
- Fallbacks should be reasonable (ideally exemplify what real output should be)
- Without fallbacks, pipeline fails completely

### 6. **Orchestration Patterns**

```
SEQUENTIAL (Simple):
Input → Agent1 → Agent2 → Agent3 → Output

PARALLEL (Comprehensive):
         ┌→ Agent A ┐
Input → ┤→ Agent B ├→ Synthesizer → Output
         └→ Agent C ┘

HIERARCHICAL (Complex):
Input → Manager Agent → (directs multiple workers) → Output

BRANCHING (Conditional):
Input → Decision Agent → (routes to different agents based on content) → Output
```

---

## 📝 Common Modifications

### **To Add a New Agent**:
1. Define its role (system prompt)
2. Identify its input (what data does it process?)
3. Specify its output format
4. Chain it into the workflow

### **To Use Different Models**:
```python
# Use different base model
agent_run(role, task, model="neural-chat:latest")

# Or mix models in single workflow
agent_run(AGENT_1_ROLE, task, model="smollm2:135m")      # Fast text model
vlm_agent_run(VLM_ROLE, task, model="llava")             # Vision model
alm_agent_run(ALM_ROLE, task, model="openhermes")        # Audio-capable model
```

### **To Process Your Own Data**:
```python
# Read from file
with open("data.txt", "r") as f:
    raw_data = f.read()

# Or from API
response = requests.get("https://api.example.com/data")
raw_data = response.json()

# Pass to first agent
agent1_output = agent_run(AGENT_1_ROLE, raw_data)
```

### **To Save Outputs**:
```python
# Save each agent's output
with open("agent1_output.txt", "w") as f:
    f.write(agent1_output)

# Or store as JSON for later processing
import json
results = {
    "agent1": agent1_output,
    "agent2": agent2_output,
    "agent3": agent3_output
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## ⚙️ Technical Requirements

### **Minimum Setup**:
- Python 3.8+
- `requests` library (for API calls)
- Ollama installed and running
- At least one Ollama model

### **Full Setup**:
```bash
# Install Ollama from https://ollama.ai

# Pull models
ollama pull smollm2:135m    # Fast text model
ollama pull llava           # Vision-Language Model
ollama pull openhermes      # Audio-capable model

# Start Ollama
ollama serve

# In another terminal, run our scripts
python 03_agents.py
python 03_agents_stage2.py
# ... etc
```

### **For VLM Features**:
```bash
pip install pillow          # Image processing
pip install torch           # Deep learning
ollama pull llava           # Vision model
```

### **For ALM Features**:
```bash
pip install librosa         # Audio features
pip install pydub           # Audio processing
pip install speech-recognition  # Audio transcription
```

---

## 🧪 Testing & Validation

### **Checklist for Each Agent**:
- [ ] Agent receives expected input format
- [ ] Agent produces expected output format
- [ ] Output quality is reasonable
- [ ] Agent handles errors gracefully
- [ ] Fallback response works when model unavailable

### **Checklist for Agent Chain**:
- [ ] Agent 1 output matches Agent 2 input expectations
- [ ] Information flows correctly through chain
- [ ] Final output answers original question
- [ ] Quality improves with each step (ideally)
- [ ] Entire chain works offline (with fallbacks)

---

## 💡 Real-World Applications

### **Environmental Monitoring** (Our Example):
```
Raw Data (API/Sensors)
    ↓
[VLM] Satellite imagery analysis
    ↓
[LLM] Environmental assessment
    ↓
[Parallel] Health/Economic/Policy analysis
    ↓
[Synthesizer] Comprehensive action plan
```

### **News Processing**:
```
News Article Text
    ↓
[LLM] Summarization
    ↓
[Parallel] Fact-checking / Sentiment analysis / Topic extraction
    ↓
[Synthesizer] Structured news summary
```

### **Code Review**:
```
Source Code
    ↓
[LLM] Quality analysis
    ↓
[Parallel] Security issues / Performance / Style
    ↓
[Synthesizer] Review report
```

### **Customer Feedback Analysis**:
```
Customer Audio Interview
    ↓
[ALM] Transcription + sentiment
    ↓
[Parallel] Intent analysis / Urgency assessment / Topic extraction
    ↓
[Synthesizer] Action items
```

---

## 📚 Further Learning

### **From These Files, You'll Learn**:
1. How to define agent roles
2. How to chain agents sequentially
3. How to hand off data between agents
4. How to use different agent types (LLM, VLM, ALM)
5. How to run agents in parallel
6. How to synthesize multiple perspectives
7. How to add fallback responses
8. How to customize for your domain

### **Next Topics to Explore**:
- Tool-using agents (agents that call external APIs)
- Hierarchical multi-agent (manager + workers)
- Agent memory (maintaining context across calls)
- Dynamic agent creation (generating agents based on input)
- Multi-turn conversations (agents talking to each other)

---

## 🎬 Quick Start: Run One Now

**Simplest to start**: `03_agents_stage2.py`

```bash
# Make sure Ollama is running:
ollama serve

# In another terminal:
python 03_agents_stage2.py
```

You'll see:
1. Raw data input
2. Agent 1 summarizing it
3. Agent 2 formatting the summary
4. Final pretty output

**No modifications needed** - it works with fallbacks if Ollama isn't available!

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Make sure `ollama serve` is running |
| Models not found | Run `ollama pull smollm2:135m` etc |
| Slow responses | Your machine might be weak, use faster model: `neural-chat:latest` |
| Weird outputs | Try with real Ollama (not fallback), or improve agent role definition |
| ImportError for requests | `pip install requests` |

---

## 🎓 Recommended Study Order

1. **Read** `03_agents.py` (understand the pattern)
2. **Run** `03_agents_stage2.py` (see it work)
3. **Modify** `03_agents_stage2.py` (change roles, try your own data)
4. **Review** `03_agents_vlm.py` (understand multimodal)
5. **Explore** `03_agents_advanced.py` (master advanced patterns)
6. **Build** your own workflow (apply learning)

---

## 📞 Questions to Ask Yourself

- What data do I have? (text, images, audio, structured?)
- What do I want to accomplish? (analysis? formatting? decision-making?)
- How many perspectives do I need? (single or multiple agents?)
- What's the time constraint? (sequential or parallel?)
- How important is quality? (fallback OK or need real LLM?)

Happy agent chaining! 🚀

---

**Created**: March 16, 2026
**Files**: `03_agents.py`, `03_agents_stage2.py`, `03_agents_vlm.py`, `03_agents_advanced.py`
**Related**: `04_agents/` (full multi-agent prompt engineering lab)
