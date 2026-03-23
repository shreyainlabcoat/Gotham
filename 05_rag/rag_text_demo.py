# rag_text_demo.py
# Complete RAG workflow demonstration with mock LLM responses
# This version works around memory constraints while showing the complete RAG system

import os
import requests
import json
import time
import re

# ============================================================================
# 0. CONFIGURATION
# ============================================================================

MODEL = "gemma3:latest"
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
OLLAMA_API_URL = f"{OLLAMA_HOST}/api/generate"

DOCUMENT_PATH = "data/sample.txt"

SYSTEM_PROMPT = """You are a helpful AI assistant specialized in Retrieval-Augmented Generation (RAG).
Your role is to answer user questions based on the provided context/documents.
Always use the retrieved information to support your answers.
If the retrieved information doesn't contain the answer, say so clearly.
Be concise and factual."""

# ============================================================================
# 1. SEARCH FUNCTION - Retrieve relevant documents
# ============================================================================

def search_text(query, document_path):
    """
    Search a text file for keywords from the query using TF-IDF-like scoring.
    """
    
    if not os.path.exists(document_path):
        return {
            "query": query,
            "document": os.path.basename(document_path),
            "matching_content": "FILE NOT FOUND",
            "num_results": 0
        }
    
    with open(document_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split by lines and filter empty ones
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Extract keywords from query (remove stop words)
    stop_words = {'what', 'is', 'how', 'does', 'by', 'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'up', 'about', 'as', 'can', 'do', 'have', 'has', 'its', 'of', 'that', 'this', 'work', 'works', 'your', 'you', 'me', 'my', 'it'}
    keywords = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', query) if w.lower() not in stop_words and len(w) > 2]
    
    if not keywords:
        keywords = [query.lower()]
    
    # Score lines based on keyword matches
    scored_lines = []
    for line in lines:
        line_lower = line.lower()
        match_count = sum(1 for kw in keywords if kw in line_lower)
        if match_count > 0:
            scored_lines.append((match_count, line))
    
    # Sort by match count (highest first)
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    matching_lines = [line for _, line in scored_lines[:10]]
    
    # Combine matching content
    result_text = " ".join(matching_lines)
    
    return {
        "query": query,
        "document": os.path.basename(document_path),
        "matching_content": result_text,
        "num_results": len(matching_lines)
    }

# ============================================================================
# 2. LLM QUERY FUNCTION - With fallback to synthesis
# ============================================================================

def query_ollama(prompt, model=MODEL, system_prompt=SYSTEM_PROMPT):
    """
    Try to query Ollama, with intelligent fallback if memory insufficient.
    """
    
    request_body = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        print("[*] Attempting to query Ollama...")
        response = requests.post(OLLAMA_API_URL, json=request_body, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if "response" in response_data:
            return response_data["response"].strip()
        else:
            return f"Unexpected response: {response_data}"
            
    except requests.exceptions.ConnectionError:
        return None  # Signal for fallback
    except json.JSONDecodeError:
        return None  # Signal for fallback
    except Exception as e:
        if "requires more system memory" in str(e) or "500" in str(e):
            return None  # Signal for fallback
        return f"Error: {str(e)}"

def synthesize_response(retrieved_content, user_query):
    """
    Synthesize a response using the retrieved content when LLM is unavailable.
    This demonstrates RAG without requiring full model inference.
    """
    
    # Extract key concepts from retrieved content
    sentences = [s.strip() + '.' for s in retrieved_content.split('.') if s.strip()]
    
    # Build response by acknowledging the query and citing retrieved content
    response = f"""Based on the retrieved documents, I can provide the following information about your question: "{user_query}"

Key findings from the knowledge base:
"""
    
    # Add up to 3 key sentences
    for i, sentence in enumerate(sentences[:3]):
        if sentence.lower() not in user_query.lower():
            response += f"\n- {sentence}"
    
    response += f"\n\nNote: This response is synthesized from the retrieved documents as the local LLM model cannot run due to memory constraints (requires 4GB, system has ~3.5GB available). In production, the Ollama LLM would generate a more comprehensive answer using these retrieved materials."
    
    return response

# ============================================================================
# 3. COMPLETE RAG WORKFLOW
# ============================================================================

def run_rag_query(user_query):
    """
    Execute the complete RAG workflow with fallback synthesis
    """
    
    print("\n" + "="*70)
    print(f"USER QUERY: {user_query}")
    print("="*70)
    
    # Step 1: Retrieve relevant documents
    print("\n[RETRIEVAL] Searching documents...")
    retrieval_result = search_text(user_query, DOCUMENT_PATH)
    print(f"   Found {retrieval_result['num_results']} relevant sections")
    
    if retrieval_result['num_results'] > 0:
        print(f"   Preview: {retrieval_result['matching_content'][:150]}...")
    
    # Step 2: Build the prompt for the LLM
    print("\n[PROMPT] Building context-aware prompt...")
    
    if retrieval_result['num_results'] > 0:
        context_prompt = f"""Based on the following retrieved information, answer the user's question:

RETRIEVED INFORMATION:
---------------------
{retrieval_result['matching_content']}
---------------------

USER QUESTION: {user_query}

ANSWER:"""
    else:
        context_prompt = f"Answer this question: {user_query}"
    
    # Step 3: Query the LLM (with fallback)
    print("\n[LLM] Querying language model...")
    llm_response = query_ollama(context_prompt)
    
    # If LLM fails, synthesize response
    if llm_response is None:
        print("   (Ollama unavailable, using synthesis)")
        llm_response = synthesize_response(retrieval_result['matching_content'], user_query)
    
    # Compile results
    results = {
        "user_query": user_query,
        "retrieval": retrieval_result,
        "llm_response": llm_response,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return results

# ============================================================================
# 4. MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[*] Starting Custom RAG Query System")
    print("="*70)
    
    # Test queries
    test_queries = [
        "What is RAG and how does it work?",
        "Tell me about supervised learning",
        "How does Ollama work with RAG systems?"
    ]
    
    all_results = []
    
    for query in test_queries:
        result = run_rag_query(query)
        all_results.append(result)
        
        # Display results
        print("\n[RESPONSE]:")
        print("-" * 70)
        print(result['llm_response'])
        print("-" * 70)
        
        if query != test_queries[-1]:
            time.sleep(1)
    
    # Save results
    output_file = "rag_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] RAG workflow complete!")
    print(f"[FILE] Results saved to: {output_file}")
    print("="*70)
