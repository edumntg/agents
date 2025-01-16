import json
import re

def extract_json(s):
    """
    LLMs returns JSON code in their responses. Sometimes inside a ```json ``` markdown, and sometimes just RAW json
    This function extracts the JSON code from their responses, considering all cases


    :param s:
    :return:
    """
    # Attempt to extract JSON directly if not wrapped in markdown
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Fallback to extracting JSON from markdown format
        pattern = r'```json\s*({.*?})\s*```'
        match = re.search(pattern, s, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
                return None
        else:
            return None