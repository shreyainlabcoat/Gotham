# Custom RAG System - Lab Submission Explanation

## Overview
This submission implements a complete Retrieval-Augmented Generation (RAG) system that combines document retrieval with LLM inference to answer user questions based on a custom knowledge base.

---

## 1. DATA SOURCE

**What was created:** A text file (`data/sample.txt`) containing 20 sentences about AI, Machine Learning, and RAG technologies.

**Why this data source:**
- **Relevance**: The knowledge base focuses on RAG concepts, which are directly related to the lab exercise
- **Simplicity**: A text file is the easiest data format to implement and demonstrates the core RAG concepts
- **Quality**: Contains diverse information about RAG, supervised/unsupervised learning, LLMs, Ollama, embeddings, and related techniques
- **Size**: Approximately 20 sentences provide enough content for meaningful retrieval without overwhelming the system

**Sample content includes:**
- Definition and core concepts of RAG
- How RAG works technically
- Components (retrieval, ranking, generation)
- Integration with Ollama
- Related concepts (embeddings, prompt engineering, fine-tuning)

---

## 2. SEARCH FUNCTION

**Implementation:** Keyword-based semantic search with relevance scoring (similar to TF-IDF)

**How it works:**
1. **Keyword Extraction**: Extract meaningful keywords from the user query
   - Remove 50+ common stop words (the, is, how, what, etc.)
   - Only consider words longer than 2 characters
   - Focus on domain-specific terms

2. **Relevance Scoring**: Score each document line based on keyword matches
   - Count how many keywords appear in each line
   - Higher match count = more relevant
   - Sort results by relevance

3. **Result Ranking**: Return top 10 most relevant sentences
   - Ordered by match count (most relevant first)
   - Joined into a single context string

**Example:**
```
Query: "What is RAG and how does it work?"
Extracted Keywords: ['rag']
Top Match: "Retrieval-Augmented Generation (RAG) is a powerful technique that combines information retrieval with generative language models." (1 keyword match)
```

**Advantages:**
- Fast and efficient (no ML model required for search)
- Easy to understand and debug
- Works well for keyword-focused queries
- Scalable to larger document collections

---

## 3. SYSTEM PROMPT

**Purpose:** Instruct the LLM how to process and utilize the retrieved information

**System Prompt Used:**
```
You are a helpful AI assistant specialized in Retrieval-Augmented Generation (RAG).
Your role is to answer user questions based on the provided context/documents.
Always use the retrieved information to support your answers.
If the retrieved information doesn't contain the answer, say so clearly.
Be concise and factual.
```

**What it instructs the LLM to do:**
1. **Role Definition**: Establishes the LLM as a RAG-specific assistant
2. **Context-Based Answering**: Ensures responses are grounded in retrieved documents
3. **Citation**: Instructs the model to use retrieved information as the knowledge base
4. **Transparency**: If information isn't available, the LLM should say so (hallucination prevention)
5. **Tone**: Keep responses concise and fact-based (not creative or verbose)

---

## 4. COMPLETE RAG PIPELINE

The system executes three key steps:

### Step 1: RETRIEVAL
- User query: "What is RAG and how does it work?"
- Search function extracts keyword "rag" 
- Returns 10 relevant sentences from knowledge base

### Step 2: AUGMENTATION  
- Combines user query with retrieved context
- Creates a structured prompt that tells the LLM to answer based on the context
- Passes this context-enriched prompt to the LLM

### Step 3: GENERATION
- LLM reads the prompt with context
- Generates answer grounded in the retrieved information
- Returns response to user

---

## 5. KEY FILES

- **`custom_rag_system.py`**: Main RAG implementation (ready for submission)
- **`data/sample.txt`**: Knowledge base with AI/ML/RAG content
- **`rag_results.json`**: Output from running the system

---

## 6. HOW TO RUN

```bash
cd 05_rag
python custom_rag_system.py
```

The script will:  
1. Execute 3 sample queries  
2. Display retrieval, augmentation, and generation steps  
3. Show the LLM responses  
4. Save complete results to `rag_results.json`  

---

## 7. TECHNICAL NOTES

**Memory Constraint Handling:**
- The system is designed to work even if the LLM model cannot fully load due to memory constraints
- Falls back to document synthesis if LLM is unavailable
- Still demonstrates the complete RAG pipeline even with synthesis

**Search Algorithm:**
- Stop words removed: 50+ common English words
- Keyword minimum length: 3 characters
- Relevance based on: count of matching keywords
- Time complexity: O(n*m) where n=documents, m=keywords

**Scalability:**
- The search function can scale to 1000s of documents
- For millions of documents, would recommend vector embeddings (as mentioned in the knowledge base)
- Current implementation prioritizes interpretability over performance

---

## 8. FUTURE IMPROVEMENTS

Potential enhancements mentioned in the knowledge base:
1. **Vector Embeddings**: Use semantic similarity instead of keyword matching
2. **Multi-hop Reasoning**: Retrieve and reason over multiple documents
3. **Reranking**: Use a cross-encoder to rerank retrieved results
4. **Document Chunking**: Split large documents into smaller, more relevant chunks
5. **Query Expansion**: Generate multiple query variations for better retrieval

---

**Submission Date:** March 22, 2026  
**System Status:** Complete and functional ✓
