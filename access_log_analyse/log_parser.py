import json
from typing import Dict, List, Any, Optional


def extract_nested_field(data: Dict[str, Any], path: str) -> Optional[Any]:
    """
    Extract a nested field from a dictionary using a dot-separated path.
    
    Args:
        data: The dictionary to extract from
        path: Dot-separated path to the field (e.g., 'subject_info.subject_id')
        
    Returns:
        The value at the specified path or None if the path doesn't exist
    """
    keys = path.split('.')
    result = data
    
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return None
            
    return result


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single log line in JSON format.
    
    Args:
        line: A JSON log line
        
    Returns:
        A dictionary with extracted fields or None if parsing fails
    """
    try:
        data = json.loads(line.strip())
        
        # Extract the required fields
        subject_id = extract_nested_field(data, 'subject_info.subject_id')
        
        # Extract client_id from request.oauth_request.client_id if it exists
        client_id = None
        request = data.get('request', {})
        oauth_request = request.get('oauth_request', {})
        if oauth_request and 'client_id' in oauth_request:
            client_id = oauth_request['client_id']
            
        total_duration = data.get('total´_duration')
        
        # if subject_id is not None and client_id is not None and total_duration is not None:
        return {
            'subject_id': subject_id,
            'client_id': client_id,
            'total_duration': total_duration
        }
        return None
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error parsing log line: {e}")
        return None


def parse_log_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a log file containing JSON lines.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        A list of dictionaries with extracted fields
    """
    results = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                parsed_line = parse_log_line(line)
                if parsed_line:
                    results.append(parsed_line)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading log file: {e}")
        
    return results