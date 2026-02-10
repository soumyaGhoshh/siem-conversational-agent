import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_flow():
    # 1. Login
    print("Testing Login...")
    resp = requests.post(f"{BASE_URL}/login", json={"username": "analyst1", "password": "changeme"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json().get("token")
    print("Login successful.")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Stats
    print("\nTesting Stats...")
    resp = requests.get(f"{BASE_URL}/stats", headers=headers)
    print(f"Stats Status: {resp.status_code}")
    if resp.status_code == 200:
        stats = resp.json()
        print(f"Total Alerts: {stats.get('totalAlerts')}")
        print(f"Risk Scoring Count: {len(stats.get('riskScoring', []))}")
    else:
        print(f"Stats failed: {resp.text}")

    # 3. Test Chat (LLM)
    print("\nTesting Chat (LLM)...")
    chat_payload = {
        "prompt": "Show me recent login failures",
        "index": "wazuh-alerts-*",
        "size": 5
    }
    resp = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_payload)
    print(f"Chat Status: {resp.status_code}")
    if resp.status_code == 200:
        chat_data = resp.json()
        print("Chat successful.")
        if chat_data.get('analysis'):
            print(f"Analysis: {chat_data.get('analysis')[:100]}...")
        else:
            print("Analysis missing in response!")
            print(json.dumps(chat_data, indent=2))
        
        if chat_data.get('story'):
            print(f"Story: {chat_data.get('story')[:100]}...")
        else:
            print("Story missing in response!")
    else:
        print(f"Chat failed: {resp.text}")

if __name__ == "__main__":
    test_flow()
