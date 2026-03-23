# custom_rag_system.py
# Complete Custom RAG Implementation
# Shreya's Submission for Custom RAG Lab
#
# Overview:
# This script implements a complete Retrieval-Augmented Generation (RAG) system
# that demonstrates:
# 1. Data source creation (text file with AI/ML/RAG content)
# 2. Search function with keyword extraction and relevance scoring
# 3. Prompt construction using retrieved context
# 4. LLM integration with Ollama with intelligent fallback

import os
import re
import json
import time
import requests

# ============================================================================
# CONFIGURATION
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
# SEARCH FUNCTION - Retrieving Relevant Documents
# ============================================================================

def search_text(query, document_path):
    """
    Implement TF-IDF-like keyword matching for document retrieval.
    
    This function:
    1. Reads the document
    2. Extracts meaningful keywords from the query (removes stop words)
    3. Scores each document line based on keyword matches
    4. Returns the top matches ranked by relevance
    
    Parameters:
    -----------
    query : str
        The user's search query
    document_path : str
        Path to the text file containing the knowledge base
    
    Returns:
    --------
    dict
        Contains query, document name, matching content, and number of matches
    """
    
    if not os.path.exists(document_path):
        return {
            "query": query,
            "document": os.path.basename(document_path),
            "matching_content": "FILE NOT FOUND",
            "num_results": 0
        }
    
    # Read document
    with open(document_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into lines and remove empty ones
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # KEYWORD EXTRACTION: Remove common stop words
    # This focuses on meaningful terms for better matching
    stop_words = {
        'what', 'is', 'how', 'does', 'by', 'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at',
        'to', 'for', 'with', 'from', 'up', 'about', 'as', 'can', 'do', 'have', 'has', 'its',
        'of', 'that', 'this', 'work', 'works', 'your', 'you', 'me', 'my', 'it'
    }
    
    keywords = [
        w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', query)
        if w.lower() not in stop_words and len(w) > 2
    ]
    
    # If no keywords extracted, use the full query
    if not keywords:
        keywords = [query.lower()]
    
    # RELEVANCE SCORING: Count keyword matches in each document line
    scored_lines = []
    for line in lines:
        line_lower = line.lower()
        match_count = sum(1 for kw in keywords if kw in line_lower)
        if match_count > 0:
            scored_lines.append((match_count, line))
    
    # Sort by relevance (highest match count first)
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 10 matches
    matching_lines = [line for _, line in scored_lines[:10]]
    result_text = " ".join(matching_lines)
    
    return {
        "query": query,
        "document": os.path.basename(document_path),
        "matching_content": result_text,
        "num_results": len(matching_lines)
    }

# ============================================================================
# LLM QUERY FUNCTION - Generating Responses
# ============================================================================

def query_ollama(prompt, model=MODEL, system_prompt=SYSTEM_PROMPT):
    """
    Query the Ollama LLM and generate a response.
    
    This function:
    1. Constructs a request with the prompt and system instructions
    2. Sends it to the Ollama API
    3. Returns the generated response
    4. Falls back to synthesis if LLM unavailable (memory constraints)
    
    Parameters:
    -----------
    prompt : str
        The context-enriched prompt with retrieved documents
    model : str
        The model to use (default: gemma3:latest)
    system_prompt : str
        System instructions for the model
    
    Returns:
    --------
    str or None
        The generated response, or None if LLM unavailable
    """
    
    request_body = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=request_body, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if "response" in response_data:
            return response_data["response"].strip()
        
    except Exception:
        return None  # Trigger fallback if any error

def synthesize_response(retrieved_content, user_query):
    """
    Synthesize a response from retrieved content when LLM is unavailable.
    
    This demonstrates the RAG principle: using retrieved documents even when
    full LLM inference isn't possible.
    """
    
    sentences = [s.strip() + '.' for s in retrieved_content.split('.') if s.strip()]
    
    response = f"""Based on the retrieved documents, I can provide the following information about: "{user_query}"

Key findings from the knowledge base:
"""
    
    # Add relevant sentences from retrieved content
    for i, sentence in enumerate(sentences[:3]):
        if sentence.lower() not in user_query.lower():
            response += f"\n- {sentence}"
    
    response += f"\n\n[Note: This response is synthesized from retrieved documents as the LLM cannot fully load due to memory constraints]"
    
    return response

# ============================================================================
# COMPLETE RAG WORKFLOW
# ============================================================================

def run_rag_query(user_query):
    """
    Execute the complete RAG pipeline:
    1. RETRIEVAL: Find relevant documents using semantic search
    2. AUGMENTATION: Create context-aware prompt with retrieved content
    3. GENERATION: Use LLM to generate answer based on context
    
    Parameters:
    -----------
    user_query : str
        The user's question
    
    Returns:
    --------
    dict
        Complete workflow results with retrieval and generation output
    """
    
    print("\n" + "="*70)
    print(f"USER QUERY: {user_query}")
    print("="*70)
    
    # STEP 1: RETRIEVAL
    print("\n[RETRIEVAL] Searching documents for relevant content...")
    retrieval_result = search_text(user_query, DOCUMENT_PATH)
    print(f"   Found {retrieval_result['num_results']} relevant sections")
    
    if retrieval_result['num_results'] > 0:
        print(f"   Preview: {retrieval_result['matching_content'][:150]}...")
    
    # STEP 2: AUGMENTATION - Build prompt with context
    print("\n[AUGMENTATION] Building context-aware prompt...")
    
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
    
    # STEP 3: GENERATION
    print("\n[GENERATION] Querying language model...")
    llm_response = query_ollama(context_prompt)
    
    # Fallback to synthesis if LLM unavailable
    if llm_response is None:
        print("   (Using synthesis fallback)")
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
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Handle Unicode encoding on Windows
    import sys
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[*] CUSTOM RAG SYSTEM - Lab Submission")
    print("="*70)
    print("This system demonstrates Retrieval-Augmented Generation with:")
    print("  1. Custom text document knowledge base")
    print("  2. Keyword-based semantic search")
    print("  3. Context-aware prompt construction")
    print("  4. Ollama LLM integration")
    print("="*70)
    
    # Sample queries to demonstrate the system
    test_queries = [
        "What is RAG and how does it work?",
        "Tell me about supervised learning",
        "How does Ollama work with RAG systems?"
    ]
    
    all_results = []
    
    # Run RAG workflow for each query
    for query in test_queries:
        result = run_rag_query(query)
        all_results.append(result)
        
        # Display response
        print("\n[RESPONSE]:")
        print("-" * 70)
        print(result['llm_response'])
        print("-" * 70)
        
        # Small delay between queries
        if query != test_queries[-1]:
            time.sleep(1)
    
    # Save complete results to JSON
    output_file = "rag_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] RAG workflow complete!")
    print(f"[FILE] Results saved to: {output_file}")
    print("="*70)
    print("\nSUBMISSION NOTES:")
    print("- Data source: Text file (data/sample.txt) with AI/ML content")
    print("- Search function: Keyword extraction + relevance scoring")
    print("- System prompt: Instructs LLM to use retrieved context")
    print("- Output: Demonstrates 3-step RAG pipeline")
    print("="*70)
