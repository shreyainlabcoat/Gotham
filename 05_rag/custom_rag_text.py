# custom_rag_text.py
# Complete RAG workflow with text file retrieval
# Author: Custom Implementation

import os
import requests
import json
import time

# ============================================================================
# 0. CONFIGURATION
# ============================================================================

# Model and API configuration
MODEL = "gemma3:latest"  # Use the available model
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
OLLAMA_API_URL = f"{OLLAMA_HOST}/api/generate"

# Document configuration
DOCUMENT_PATH = "data/sample.txt"

# System prompt - instructs the LLM how to process retrieved data
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
    Search a text file for keywords from the query.
    
    Parameters:
    -----------
    query : str
        The search query
    document_path : str
        Path to the text file to search
    
    Returns:
    --------
    dict
        Dictionary containing the search results and metadata
    """
    
    # Read the text file
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
    
    # Extract keywords from query (split by common words, remove short words)
    import re
    # Remove common stop words and extract meaningful keywords
    stop_words = {'what', 'is', 'how', 'does', 'by', 'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'up', 'about', 'as', 'can', 'do', 'have', 'has', 'its', 'of', 'that', 'this', 'work', 'works', 'do', 'your', 'you', 'me', 'my', 'it'}
    keywords = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', query) if w.lower() not in stop_words and len(w) > 2]
    
    # If no keywords found, use original query
    if not keywords:
        keywords = [query.lower()]
    
    # Score lines based on matches
    scored_lines = []
    for line in lines:
        line_lower = line.lower()
        # Count how many keywords match in this line
        match_count = sum(1 for kw in keywords if kw in line_lower)
        if match_count > 0:
            scored_lines.append((match_count, line))
    
    # Sort by match count (highest first)
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    
    # Get top matches
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
# 2. LLM QUERY FUNCTION - Send context to Ollama
# ============================================================================

def query_ollama(prompt, model=MODEL, system_prompt=SYSTEM_PROMPT):
    """
    Send a prompt to Ollama and get a response.
    
    Parameters:
    -----------
    prompt : str
        The user prompt to send to the model
    model : str
        The model name to use
    system_prompt : str
        System instructions for the model
    
    Returns:
    --------
    str
        The model's response text
    """
    
    # Build the request body
    request_body = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True  # Use streaming to reduce memory footprint
    }
    
    try:
        print(f"[*] Querying {model}...")
        response = requests.post(OLLAMA_API_URL, json=request_body, timeout=120, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        full_response += chunk["response"]
                except json.JSONDecodeError:
                    continue
        
        return full_response.strip() if full_response else "No response received from model"
            
    except requests.exceptions.ConnectionError:
        return "❌ ERROR: Could not connect to Ollama. Make sure Ollama is running on http://localhost:11434"
    except requests.exceptions.Timeout:
        return "❌ ERROR: Request timed out. The model may be taking too long to respond."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# ============================================================================
# 3. COMPLETE RAG WORKFLOW
# ============================================================================

def run_rag_query(user_query):
    """
    Execute the complete RAG workflow:
    1. Retrieve relevant documents
    2. Build context from retrieved documents
    3. Generate response using LLM
    
    Parameters:
    -----------
    user_query : str
        The user's question
    
    Returns:
    --------
    dict
        Complete RAG workflow results
    """
    
    print("\n" + "="*70)
    print(f"USER QUERY: {user_query}")
    print("="*70)
    
    # Step 1: Retrieve relevant documents
    print("\n[RETRIEVAL] Searching documents...")
    retrieval_result = search_text(user_query, DOCUMENT_PATH)
    print(f"   Found {retrieval_result['num_results']} relevant sections")
    
    if retrieval_result['num_results'] > 0:
        print(f"   Content preview: {retrieval_result['matching_content'][:200]}...")
    
    # Step 2: Build the prompt for the LLM with retrieved context
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
        context_prompt = f"""User Question: {user_query}

I could not find relevant information in the knowledge base about this topic.
Please provide a helpful response based on your general knowledge."""
    
    # Step 3: Query the LLM
    print("\n[LLM] Querying language model for response...")
    llm_response = query_ollama(context_prompt)
    
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
    # Configure stdout to handle Unicode on Windows
    import sys
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[*] Starting Custom RAG Query System")
    print("="*70)
    
    # Test queries to demonstrate the RAG workflow
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
        
        # Add delay between queries to be respectful to the model
        if query != test_queries[-1]:
            time.sleep(1)
    
    # Save all results to a JSON file for review
    output_file = "rag_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] RAG workflow complete!")
    print(f"[FILE] Results saved to: {output_file}")
    print("="*70)
