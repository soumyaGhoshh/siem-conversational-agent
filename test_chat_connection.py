import requests
import json

def test_chat():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3MDcyNjkwNX0.61GEpM3IAhqkPxWS4pzTIJVJKDWQgh14SduXYDfxYmw"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "What are the latest security alerts?",
        "index": "wazuh-alerts-*",
        "size": 10
    }
    
    try:
        # Test direct backend
        print("Testing direct backend (http://localhost:8000/api/chat)...")
        response = requests.post("http://localhost:8000/api/chat", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test via frontend proxy
        print("\nTesting via frontend proxy (http://localhost:3000/api/chat)...")
        response = requests.post("http://localhost:3000/api/chat", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
