import json
import logging
from typing import Optional

# Third-party imports
import json_repair

logger = logging.getLogger(__name__)


def repair_json_output(content: str) -> str:
    """
    Repair and normalize JSON output from various formats.
    
    This function handles JSON content that may be wrapped in markdown code blocks,
    malformed, or contain syntax errors. It attempts to repair the JSON and return
    a properly formatted JSON string.

    Args:
        content (str): String content that may contain JSON data. Can be wrapped
                      in markdown code blocks (```json or ```ts) or raw JSON.

    Returns:
        str: Repaired and formatted JSON string if successful, otherwise returns
             the original content unchanged.
             
    Raises:
        None: All exceptions are caught and logged, function never raises.
    """
    # Handle null or empty input
    if not content:
        logger.warning("Empty or None content provided to repair_json_output")
        return content or ""
    
    content = content.strip()
    
    # Check if content appears to be JSON-like
    is_json_like = (
        content.startswith(("{", "[")) or 
        "```json" in content or 
        "```ts" in content
    )
    
    if is_json_like:
        try:
            # Extract JSON from markdown code blocks
            cleaned_content = _extract_json_from_codeblock(content)
            
            # Attempt to repair and parse JSON
            repaired_json_object = json_repair.loads(cleaned_content)
            
            # Return formatted JSON string
            return json.dumps(repaired_json_object, ensure_ascii=False, indent=None)
            
        except (json.JSONDecodeError, ValueError) as json_error:
            logger.warning(f"JSON parsing/repair failed: {json_error}")
        except Exception as unexpected_error:
            logger.error(f"Unexpected error during JSON repair: {unexpected_error}")
    
    return content


def _extract_json_from_codeblock(content: str) -> str:
    """
    Extract JSON content from markdown code blocks.
    
    Removes ```json, ```ts, and closing ``` markers from the content.
    
    Args:
        content (str): Content that may contain markdown code block markers.
        
    Returns:
        str: Content with code block markers removed.
    """
    # Remove opening code block markers
    if content.startswith("```json"):
        content = content.removeprefix("```json")
    elif content.startswith("```ts"):
        content = content.removeprefix("```ts")
    
    # Remove closing code block marker
    if content.endswith("```"):
        content = content.removesuffix("```")
    
    return content.strip()
