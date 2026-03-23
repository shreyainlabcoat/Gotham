# rag_health_insights.py
# RAG module for health-specific air quality analysis
# Retrieves relevant health information and generates informed recommendations

import re
import os
from typing import Dict, Tuple

def load_knowledge_base(kb_path: str) -> list:
    """Load the air quality health knowledge base."""
    if not os.path.exists(kb_path):
        return []
    
    with open(kb_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into sentences
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    return sentences

def search_health_knowledge(query: str, knowledge_base: list) -> str:
    """
    RAG RETRIEVAL: Search knowledge base for relevant health information.
    Uses keyword extraction and relevance scoring.
    """
    
    if not knowledge_base:
        return ""
    
    # Extract keywords from query
    stop_words = {
        'what', 'is', 'how', 'does', 'by', 'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at',
        'to', 'for', 'with', 'from', 'up', 'about', 'as', 'can', 'do', 'have', 'has', 'its',
        'of', 'that', 'this', 'should', 'i', 'my', 'me', 'it', 'pm', 'o', 'are'
    }
    
    keywords = [
        w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', query)
        if w.lower() not in stop_words and len(w) > 2
    ]
    
    if not keywords:
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
    
    # Score knowledge base sentences
    scored_sentences = []
    for sentence in knowledge_base:
        sentence_lower = sentence.lower()
        match_count = sum(1 for kw in keywords if kw in sentence_lower)
        if match_count > 0:
            scored_sentences.append((match_count, sentence))
    
    # Sort by relevance
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 3 relevant sentences
    relevant_info = ". ".join([s for _, s in scored_sentences[:3]])
    return relevant_info if relevant_info else ""

def build_health_prompt(pollutant_key: str, value: float, locations: list, retrieved_info: str) -> str:
    """
    RAG AUGMENTATION: Build context-aware prompt with retrieved health information.
    """
    
    location_summary = ", ".join(locations[:3]) if locations else "multiple areas"
    
    prompt = f"""You are an environmental health specialist analyzing air quality for commuters in NYC.

POLLUTANT: {pollutant_key}
CURRENT LEVEL: {value:.1f}
AFFECTED AREAS: {location_summary}

HEALTH KNOWLEDGE CONTEXT:
{retrieved_info}

Based on the current pollution level and the health knowledge provided, generate a JSON response with:
- risk_assessment: Current health risk level (Low, Moderate, High, Severe)
- health_impact: Specific health impacts expected at this level (2 sentences)
- vulnerable_groups: Who is most at risk (list 2-3 groups)
- protective_actions: What people should do right now (2-3 specific recommendations)
- safe_alternatives: Indoor or safer outdoor alternatives to suggest

Format as JSON only. No additional text."""
    
    return prompt

def get_rag_health_insights(df, pollutant_key: str, kb_path: str, ai_choice: str = "Ollama") -> Dict:
    """
    Complete RAG pipeline for health insights.
    1. RETRIEVAL - Find relevant health information
    2. AUGMENTATION - Build context prompt
    3. GENERATION - Query LLM with context
    """
    
    import requests
    import json
    
    if df.empty:
        return {"error": "No air quality data available for analysis"}
    
    # STEP 1: RETRIEVAL
    knowledge_base = load_knowledge_base(kb_path)
    if not knowledge_base:
        return {"error": "Knowledge base not found"}
    
    query = f"Health impacts of {pollutant_key} exposure for commuters"
    retrieved_info = search_health_knowledge(query, knowledge_base)
    
    if not retrieved_info:
        retrieved_info = "General information about air quality and health precautions."
    
    # STEP 2: AUGMENTATION
    locations = df["Location"].head(3).tolist() if "Location" in df.columns else []
    prompt = build_health_prompt(
        pollutant_key, 
        df["Value"].mean(), 
        locations,
        retrieved_info
    )
    
    # STEP 3: GENERATION
    if ai_choice == "Ollama (gemma3)":
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "gemma3:latest",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json().get("response", "")
            # Try to extract JSON from response
            try:
                json_obj = json.loads(result)
                json_obj["retrieved_context"] = retrieved_info
                return json_obj
            except:
                return {
                    "error": "Could not parse response",
                    "raw_response": result,
                    "retrieved_context": retrieved_info
                }
        except Exception as e:
            return {
                "error": f"Ollama Error: {str(e)}",
                "retrieved_context": retrieved_info
            }
    
    # Fallback: synthesized response
    return {
        "risk_assessment": "Moderate to High",
        "health_impact": f"At {df['Value'].mean():.1f} level, {pollutant_key} poses respiratory concerns. Vulnerable populations should limit outdoor exposure.",
        "vulnerable_groups": ["Children", "Elderly", "People with asthma"],
        "protective_actions": [
            "Wear N95/KN95 mask for outdoor activities",
            "Limit strenuous outdoor exercise",
            "Stay hydrated and monitor symptoms"
        ],
        "safe_alternatives": [
            "Move activities indoors (gym, swimming pool, covered facilities)",
            "Exercise in early morning hours (lower pollution)",
            "Use air purifiers in home and office"
        ],
        "retrieved_context": retrieved_info,
        "note": "Synthesized response (Ollama unavailable)"
    }

def format_rag_response(rag_result: Dict) -> str:
    """Format RAG response for Streamlit display."""
    
    if "error" in rag_result:
        return f"⚠️ {rag_result['error']}"
    
    output = ""
    
    if "risk_assessment" in rag_result:
        output += f"**Risk Level**: {rag_result['risk_assessment']}\n\n"
    
    if "health_impact" in rag_result:
        output += f"**Health Impact**: {rag_result['health_impact']}\n\n"
    
    if "vulnerable_groups" in rag_result:
        groups = rag_result['vulnerable_groups']
        if isinstance(groups, list):
            output += f"**At-Risk Groups**: {', '.join(groups)}\n\n"
        else:
            output += f"**At-Risk Groups**: {groups}\n\n"
    
    if "protective_actions" in rag_result:
        actions = rag_result['protective_actions']
        if isinstance(actions, list):
            output += "**What You Should Do**:\n"
            for action in actions:
                output += f"• {action}\n"
        else:
            output += f"**What You Should Do**: {actions}\n"
        output += "\n"
    
    if "safe_alternatives" in rag_result:
        alternatives = rag_result['safe_alternatives']
        if isinstance(alternatives, list):
            output += "**Safer Alternatives**:\n"
            for alt in alternatives:
                output += f"• {alt}\n"
        else:
            output += f"**Safer Alternatives**: {alternatives}\n"
    
    if "retrieved_context" in rag_result and rag_result["retrieved_context"]:
        output += f"\n---\n**Knowledge Base Retrieved**:\n*{rag_result['retrieved_context'][:200]}...*"
    
    return output
