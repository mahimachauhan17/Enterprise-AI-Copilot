import json
from backend.rag.llm_provider import get_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def parse_analytics_intent(query: str, columns: list[str]) -> dict:
    llm = get_llm(temperature=0.0)
    prompt = f"""
    You are an intent classification engine for a data analytics system.
    The user has a dataset with the following columns: {columns}
    
    Classify the user's query into one of the following intents:
    - EXECUTIVE_SUMMARY: General overview, dashboard, summary.
    - TREND_ANALYSIS: Showing data over time (needs a date column and a numeric column).
    - TOP_CATEGORIES: Showing top items, highest selling, etc (needs a categorical column and numeric column).
    - DISTRIBUTION: Showing spread of data.
    - CORRELATION: Comparing two numeric columns.
    - UNKNOWN: Not related to dataset analytics, or unable to determine.
    
    You MUST respond with ONLY a valid JSON object in this exact format, with no other text or markdown blocks:
    {{
        "intent": "EXECUTIVE_SUMMARY",
        "x_col": "Name of column for X axis (if applicable, else null)",
        "y_col": "Name of column for Y axis (if applicable, else null)"
    }}
    
    Query: "{query}"
    """
    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        
        data = json.loads(text)
        return data
    except Exception as e:
        logger.error(f"Intent parsing error: {e}")
        return {"intent": "UNKNOWN", "x_col": None, "y_col": None}
