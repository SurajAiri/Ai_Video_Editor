import json
import re

def llm_json_parser(data: str | dict) -> dict:
    """
    Parse JSON content from LLM response, handling both direct JSON and markdown-formatted JSON.
    
    Args:
        data: Input that could be dict or string containing JSON
    
    Returns:
        dict: Parsed JSON object
    
    Raises:
        ValueError: If JSON parsing fails
    """
    # If already a dict, return as is
    if isinstance(data, dict):
        return data
    
    # First try direct JSON parsing
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        # Try extracting JSON from triple backticks
        match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', data)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format within backticks')
        raise ValueError('Invalid JSON format')
    

