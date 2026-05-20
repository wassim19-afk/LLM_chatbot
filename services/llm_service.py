# services/llm_service.py
# This module interfaces with the Ollama API to interact with the local Mistral model.
# It sends prompts and receives responses for tasks like SQL generation and insights.

from typing import List, Dict, Any
from config.settings import settings
from services.model_router import generate_response

def call_ollama(prompt: str, model: str = None, timeout: int = 15) -> str:
    """
    Sends a prompt to the Ollama API and returns the generated response.

    Args:
        prompt (str): The input prompt for the model.
        model (str, optional): The model name, defaults to settings.OLLAMA_MODEL.
        timeout (int): Request timeout in seconds, defaults to 15.

    Returns:
        str: The generated text response from the model.
    
    Raises:
        requests.Timeout: If the request times out.
        requests.RequestException: For other request failures.
    """
    selected_model = model or settings.OLLAMA_MODEL
    return generate_response(
        prompt=prompt,
        model_name=selected_model,
        timeout=timeout,
        use_fallback=True,
    )


def reformulate_question_with_context(
    current_question: str,
    last_question: str
) -> str:
    """
    Reformulate ambiguous short questions by combining with previous question context.
    
    Example:
        last_question: "CA 2024"
        current_question: "2023?"
        returns: "CA 2023?"
    
    Args:
        current_question: The user's current short/ambiguous question
        last_question: The previous question for context
    
    Returns:
        Reformulated question combining both contexts
    """
    current_lower = current_question.lower().strip()
    last_lower = last_question.lower().strip()
    
    # Extract metric name from last question by filtering numbers/dates and stop words
    last_words = last_lower.split()
    
    # Extract metric: skip numbers, years, and stop words
    metric_words = []
    for word in last_words:
        word_clean = word.rstrip('?,.!:;')  # Remove punctuation
        
        # Skip stop words and numeric values
        if word_clean.lower() not in ["by", "in", "for", "of", "the", "a", "and", "or", "et", "du", "de", "?", ""]:
            try:
                float(word_clean)  # Skip if it's a number
                continue
            except ValueError:
                pass
            
            # If word contains letters, it's likely part of metric
            if any(c.isalpha() for c in word_clean):
                metric_words.append(word_clean)
    
    if metric_words:
        # Take up to 3 words representing the metric (e.g., "CA", "chiffre affaires")
        metric = " ".join(metric_words[:3])
        reformulated = f"{metric} {current_question}"
        return reformulated.strip()
    
    return current_question


def rewrite_question_for_clarity(question: str) -> str:
    """
    Normalize and improve questions for better SQL generation.
    
    Fixes common issues:
    - Explicit metric names (e.g., "montant" → "total amount")
    - Clear dimensions (e.g., "par" → "grouped by")
    - Aggregation hints (e.g., "beaucoup" → "highest/top")
    
    Args:
        question: Original question from user
    
    Returns:
        Improved/normalized question
    """
    q = question.lower().strip()
    
    # Replace vague French terms with clear English equivalents
    replacements = {
        r'\bbeaucoup\b': 'highest',  # "beaucoup" → "highest"
        r'\bpar client\b': 'by customer',
        r'\bpar mois\b': 'by month',
        r'\bpar\s+an\b': 'by year',
        r'\bpar\s+annee\b': 'by year',
        r'\bpar\s+année\b': 'by year',
        r'\bmontant\b': 'amount',
        r'\bchiffre\s+d[\'u]affaires\b': 'revenue',  # CA
        r'\bca\b': 'revenue',
        r'\ben\s+retard\b': 'overdue',
        r'\bimpaye\b': 'unpaid',
        r'\bfiděle\b': 'loyal',
        r'\bmeilleur\b': 'top',
        r'\bclient\s+qui\s+fait\s+': 'customer who has ',
        r'\bclient\s+qui\b': 'which customer ',
        r'\bqui\s+fait\s+beaucoup\b': 'with highest ',
    }
    
    import re
    rewritten = q
    for pattern, replacement in replacements.items():
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
    
    return rewritten.strip()


def inject_conversation_context(
    current_question: str,
    conversation_history: List[Dict[str, Any]]
) -> str:
    """
    Inject previous conversation context into the prompt for better follow-ups.
    
    Args:
        current_question: The user's current question
        conversation_history: List of previous interactions from memory service
    
    Returns:
        Enriched prompt with conversation context
    """
    if not conversation_history:
        return current_question
    
    context_lines = ["Previous conversation context:\n"]
    
    # Add last 3-5 interactions for context
    relevant_history = conversation_history[-6:]  # Last 3 Q&A pairs
    
    for i, interaction in enumerate(relevant_history, 1):
        q = interaction.get("question", "")[:80]
        a = interaction.get("response", "")[:80]
        context_lines.append(f"Q{i}: {q}\nA{i}: {a}\n")
    
    context_str = "".join(context_lines)
    
    enriched_prompt = f"""{context_str}
---
Current question: {current_question}

Based on the conversation history above, answer this question. Remember the context from previous questions."""
    
    return enriched_prompt