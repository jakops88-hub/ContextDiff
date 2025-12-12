"""
System prompts for LLM-powered semantic analysis.

These prompts are the "brain" of ContextDiff - they instruct the LLM
on how to perform semantic difference analysis with precision.
"""

from typing import Dict


def get_system_prompt(sensitivity: str) -> str:
    """
    Generate the system prompt for semantic analysis based on sensitivity level.
    
    Args:
        sensitivity: The sensitivity level ('low', 'medium', or 'high').
        
    Returns:
        A detailed system prompt instructing the LLM on analysis behavior.
    """
    
    base_prompt = """Compare texts. JSON only.

CRITICAL CONSTRAINTS:
1. NEVER include original_text/generated_text in response
2. type field MUST be UPPERCASE: FACTUAL, TONE, OMISSION, ADDITION, FORMATTING
3. severity MUST be exactly: "info", "warning", or "critical" (NOT minor/moderate/fatal)
4. Positions must be EXACT (never use [0,0] - omit if unknown)
5. Reasoning: MAX 5 WORDS
6. Description: MAX 10 WORDS

LEVELS: NONE (0-10), MINOR (11-30), MODERATE (31-55), CRITICAL (56-80), FATAL (81-100)
is_safe: score≤40 + no critical"""

    sensitivity_instructions = {
        "low": "\nLOW: Critical only. 0-3 changes.",
        "medium": "\nMED: Factual+tone shifts. 2-8 changes.",
        "high": "\nHIGH: All differences. 5-15+ changes."
    }
    
    json_schema = """
JSON:
{"summary":{"is_safe":bool,"risk_score":int,"semantic_change_level":str},"changes":[{"type":str,"severity":str,"description":str,"original_span":{"text":str,"context_before":str,"context_after":str,"start":int,"end":int},"generated_span":{"text":str,"context_before":str,"context_after":str,"start":int,"end":int},"reasoning":str}]}

STRICT LIMITS:
- Context: 30 chars before/after
- Description: MAX 10 words
- Reasoning: MAX 5 words
- NO text echo

Identical: {"summary":{"is_safe":true,"risk_score":0,"semantic_change_level":"NONE"},"changes":[]}
"""
    
    sensitivity_instruction = sensitivity_instructions.get(sensitivity, sensitivity_instructions["medium"])
    
    return f"{base_prompt}\n\n{sensitivity_instruction}\n\n{json_schema}"


def get_user_prompt(original_text: str, generated_text: str) -> str:
    """
    Generate the user prompt with the actual texts to compare.
    
    Args:
        original_text: The original/reference text.
        generated_text: The generated text to analyze.
        
    Returns:
        A formatted user prompt containing both texts.
    """
    return f"""ORIGINAL:
{original_text}

GENERATED:
{generated_text}

Analyze. Return JSON."""


# Pre-built sensitivity mappings for quick reference
SENSITIVITY_DESCRIPTIONS: Dict[str, str] = {
    "low": "Only critical issues that could cause real-world consequences",
    "medium": "Balanced analysis flagging significant semantic changes",
    "high": "Maximum scrutiny capturing all semantic differences"
}
