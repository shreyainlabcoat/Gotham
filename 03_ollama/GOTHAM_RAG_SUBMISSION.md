# GOTHAM RAG SUBMISSION

## 📋 WHAT TO SUBMIT

### 1️⃣ **Complete RAG Workflow Script**
File: `rag_health_insights.py` (in 03_ollama folder)
Size: 7.8 KB
Status: ✓ Ready

This script contains:
- Search function (RETRIEVAL)
- Prompt builder (AUGMENTATION)
- LLM integration (GENERATION)
- Response formatter

---

### 2️⃣ **Screenshot of Output**

To generate your screenshot:

```bash
cd c:\Users\Shreya\Desktop\Gotham\03_ollama
streamlit run gotham_ai_report.py
```

**In the Streamlit app:**
1. Keep default NYC location (or customize)
2. Select pollutant: **PM2.5**
3. Select AI Engine: **"RAG + Ollama (Knowledge Base)"**
4. Click the 🧬 **RAG Analysis** tab
5. Take screenshot showing the knowledge-enhanced recommendations

**Your screenshot will show:**
- Risk assessment
- Health impacts
- Vulnerable groups
- Protective actions
- Safer alternatives
- Retrieved knowledge base context

---

### 3️⃣ **Brief Explanation (3-4 Sentences)**

**Copy this explanation:**

```
I created an air quality health knowledge base (air_quality_knowledge_base.txt) 
with 20 facts about PM2.5, ozone, vulnerable populations, and protective measures 
because it provides domain expertise on health impacts that complements real-time 
pollution data for better commuter guidance. The search function extracts 
health-relevant keywords from the current pollution type and retrieves matching 
facts ranked by keyword frequency, ensuring results are specific to the user's 
concern. The system prompt instructs the LLM to act as an environmental health 
specialist that combines retrieved health facts with current pollution levels 
to generate structured recommendations including risk assessment, health impacts, 
at-risk groups, protective actions, and safer alternatives.
```

---

## 📂 FILES TO SUBMIT

You need to submit:

### Main Script:
- **`rag_health_insights.py`** ← The RAG workflow script

### Supporting Files (reference only):
- `air_quality_knowledge_base.txt` ← Knowledge base
- `gotham_ai_report.py` ← Modified with RAG tab (optional to include)
- `RAG_INTEGRATION_GUIDE.md` ← Documentation (optional)

---

## 🎬 HOW TO TAKE THE SCREENSHOT

### Step 1: Start the app
```bash
cd c:\Users\Shreya\Desktop\Gotham\03_ollama
streamlit run gotham_ai_report.py
```

### Step 2: Configure in Streamlit UI
- **Latitude**: 40.7128 (default)
- **Longitude**: -74.0060 (default)
- **Radius**: 10 km
- **Pollutant**: PM2.5
- **AI Engine**: Select "RAG + Ollama (Knowledge Base)"

### Step 3: View RAG Output
- Click the 🧬 **RAG Analysis** tab
- Wait for the analysis to complete (5-10 seconds)
- You'll see:
  ```
  💡 Knowledge-Based Recommendations
  
  Risk Level: Moderate to High
  Health Impact: [Generated response]
  At-Risk Groups: Children, Elderly, People with asthma
  What You Should Do:
  • Wear N95/KN95 mask
  • Limit strenuous outdoor exercise
  • Stay hydrated
  
  Safer Alternatives:
  • Move activities indoors
  • Exercise in early morning
  • Use air purifiers
  ```

### Step 4: Screenshot
- Take a screenshot of the entire app showing the RAG tab results
- Save as PNG or JPG

---

## 📝 SUBMISSION CHECKLIST

- [ ] File: `rag_health_insights.py` (the main RAG script)
- [ ] Screenshot: RAG Analysis tab showing recommendations
- [ ] Explanation: 3-4 sentences (copy from above)
- [ ] Knowledge base file: `air_quality_knowledge_base.txt` (if required)

---

## ✅ YOUR RAG SYSTEM DOES

**RETRIEVAL**: Searches air_quality_knowledge_base.txt for health facts relevant to PM2.5

**AUGMENTATION**: Combines retrieved health facts with real-time pollution data and location info

**GENERATION**: Sends augmented prompt to Ollama to generate health recommendations

**OUTPUT**: Structured JSON with risk level, health impacts, at-risk groups, actions, alternatives

---

## 🚀 READY TO SUBMIT!

All files are in: `c:\Users\Shreya\Desktop\Gotham\03_ollama\`

Just:
1. Run the app
2. Take screenshot
3. Copy explanation
4. Submit script + screenshot + explanation

That's it! ✓
