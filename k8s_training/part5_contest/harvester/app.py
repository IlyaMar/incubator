import urllib.request
import urllib.parse
import json

def put_request_with_urllib(url, data=None, headers=None):
    """
    Make a PUT request using urllib (no external dependencies)
    """
    try:
        # Prepare the data
        if data is not None:
            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
            else:
                data = str(data).encode('utf-8')
        else:
            data = b''
        
        # Default headers
        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Python PUT Script'
            }
        
        # Create request
        request = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        
        # Make the request
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            status_code = response.getcode()
            
            print(f"Status Code: {status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response_body}")
            
            return response_body, status_code
            
    except urllib.error.URLError as e:
        print(f"Error making PUT request: {e}")
        return None, None

# Example usage
if __name__ == "__main__":
    url = "http://resource-silo:8080/deliver?clan=atreides"
    data = {"title": "Updated via urllib", "body": "Content", "userId": 1}
    
    put_request_with_urllib(url, data)
