# RAG SUBMISSION MATERIALS

## PROJECT 1: Custom RAG System Lab (05_rag)

### 📋 SUBMISSION CHECKLIST

**File 1: Complete RAG Workflow Script**
- Location: `05_rag/custom_rag_system.py`
- Size: ~11 KB
- Status: ✓ Ready to submit

**File 2: Screenshot Evidence**
- Run: `python custom_rag_system.py`
- Shows: 3 complete queries with retrieval, augmentation, generation
- (See terminal output below)

**File 3: Brief Explanation (3-4 Sentences)**

---

## SUBMISSION TEXT FOR LAB 1

### Data Source Created and Why:
I created a text file (`data/sample.txt`) containing 20 sentences about Retrieval-Augmented Generation, machine learning concepts, and LLMs because it provides domain-relevant content for demonstrating RAG principles while being simple to implement and allowing meaningful document retrieval.

### Search Function Implementation:
The search function extracts meaningful keywords from user queries (removing 50+ stop words), scores each document line by counting keyword matches, and returns the top 10 ranked results—implementing a keyword-based semantic search algorithm similar to TF-IDF that prioritizes relevance.

### System Prompt Instructions:
The system prompt instructs the LLM to act as a RAG specialist that answers questions based exclusively on retrieved documents, be concise and factual, and transparently acknowledge when information is unavailable in the knowledge base to prevent hallucination.

---

## PROJECT 2: Gotham Air Quality RAG Integration (03_ollama)

### 📋 SUBMISSION CHECKLIST

**File 1: Complete RAG Workflow Script**
- Location: `03_ollama/rag_health_insights.py`
- Size: ~7.8 KB
- Status: ✓ Ready to submit
- Additional: `03_ollama/gotham_ai_report.py` (modified with RAG integration)

**File 2: Screenshot Evidence**
- Run: `streamlit run 03_ollama/gotham_ai_report.py`
- Steps: Select "RAG + Ollama (Knowledge Base)" → Click 🧬 RAG Analysis tab
- Shows: Knowledge-enhanced health recommendations with retrieval context

**File 3: Brief Explanation (3-4 Sentences)**

---

## SUBMISSION TEXT FOR GOTHAM RAG

### Data Source Created and Why:
I created `air_quality_knowledge_base.txt` with 20 health-specific facts about air pollution, PM2.5, ozone, vulnerable populations, and protective measures because it provides domain expertise on health impacts that complements real-time air quality data for better commuter guidance.

### Search Function Implementation:
The search function extracts health-relevant keywords from the current pollution type (PM2.5 or Ozone), searches the knowledge base for matching facts, and ranks results by keyword frequency—ensuring retrieved health information is specific to the actual pollutant the user is concerned about.

### System Prompt Instructions:
The system prompt instructs the LLM to act as an environmental health specialist that synthesizes retrieved health facts with current pollution levels to generate structured recommendations including risk assessment, health impacts, vulnerable groups, protective actions, and safer alternatives.

---

## HOW TO GENERATE SCREENSHOTS

### For Lab RAG (05_rag):
```bash
cd c:\Users\Shreya\Desktop\Gotham\05_rag
python custom_rag_system.py
```
**Screenshot shows:**
- ✓ [RETRIEVAL] Finding relevant sections
- ✓ [AUGMENTATION] Building context prompts
- ✓ [GENERATION] Responses from 3 queries
- ✓ Proof both scripts work

---

### For Gotham RAG (03_ollama):
```bash
cd c:\Users\Shreya\Desktop\Gotham\03_ollama
streamlit run gotham_ai_report.py
```
**Then in UI:**
1. Keep default NYC location
2. Select pollutant (PM2.5)
3. Select AI: "RAG + Ollama (Knowledge Base)"
4. Click 🧬 RAG Analysis tab
5. Take screenshot showing recommendations

**Screenshot shows:**
- ✓ New RAG tab in action
- ✓ Knowledge-enhanced recommendations
- ✓ Retrieved health context
- ✓ Structured response format

---

## COMPLETE FILE SUMMARY

### Lab RAG Files (05_rag):
```
05_rag/
├── custom_rag_system.py          ← Main script (11 KB)
├── data/
│   └── sample.txt                ← Knowledge base
├── rag_results.json              ← Output example
├── SUBMISSION_EXPLANATION.md     ← Documentation
└── README_SUBMISSION.md          ← Checklist
```

### Gotham RAG Files (03_ollama):
```
03_ollama/
├── rag_health_insights.py        ← RAG module (7.8 KB)
├── air_quality_knowledge_base.txt ← Health KB
├── gotham_ai_report.py           ← Modified (with RAG tab)
└── RAG_INTEGRATION_GUIDE.md      ← Documentation
```

---

## QUICK COPY-PASTE FOR SUBMISSIONS

### Lab RAG Explanation (Copy This):
```
I created a text file containing 20 sentences about RAG and machine learning 
because it provides meaningful content for retrieval. My search function 
extracts keywords from queries, scores documents by match count, and returns 
top results—like TF-IDF scoring. The system prompt instructs the LLM to answer 
based only on retrieved documents and acknowledge missing information.
```

### Gotham RAG Explanation (Copy This):
```
I created an air quality health knowledge base with 20 facts about PM2.5, 
ozone, and protective measures because it provides expertise on health impacts 
that complement real pollution data. The search function extracts health-relevant 
keywords and retrieves matching facts ranked by keyword frequency. The system 
prompt instructs the LLM to combine health facts with pollution levels to 
generate structured recommendations with risk assessment and protective actions.
```

---

## SUBMISSION TIPS

✓ Submit **scripts** (Python files)
✓ Include **screenshots** (PNG/JPG of console and UI)
✓ Add **explanations** (copy-paste the text above)
✓ Reference **knowledge bases** (mention file names)
✓ Show **RAG pipeline** (retrieval → augmentation → generation)

Both projects demonstrate complete RAG systems with:
- Custom knowledge bases
- Semantic search functions
- Context-augmented prompts
- LLM integration
- Structured responses

---

## 🚀 NEXT STEPS

1. **Take LAB RAG screenshot:**
   ```bash
   python 05_rag/custom_rag_system.py > lab_rag_output.txt
   # Screenshot the output
   ```

2. **Take GOTHAM RAG screenshot:**
   ```bash
   streamlit run 03_ollama/gotham_ai_report.py
   # Select RAG option → Click RAG tab → Screenshot
   ```

3. **Prepare submission with:**
   - Scripts (Python files)
   - Screenshots
   - Explanations (use text above)

4. **Submit to course platform**

Everything is ready! Just take the screenshots and submit. ✓
