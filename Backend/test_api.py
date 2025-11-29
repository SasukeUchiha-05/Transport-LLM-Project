import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Start Session
    uid = str(uuid.uuid4())
    print(f"Starting session for UID: {uid}")
    try:
        resp = requests.post(f"{BASE_URL}/start_session", json={"UID": uid})
        resp.raise_for_status()
        data = resp.json()
        session_id = data.get("session_id")
        print(f"Session ID: {session_id}")
    except Exception as e:
        print(f"Failed to start session: {e}")
        return

    # 1.5 Login (Optional but good to test)
    print("Testing Login...")
    try:
        resp = requests.post(f"{BASE_URL}/login", json={"name": "Customer2", "password": "asdfgh9"})
        if resp.status_code == 200:
            print("Login Successful")
            print(resp.json())
        else:
            print(f"Login Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Login Error: {e}")

    # 2. Query
    query = "What transport services do you offer?"
    print(f"Sending query: {query}")
    try:
        resp = requests.post(f"{BASE_URL}/query", json={"query": query, "session_id": session_id})
        resp.raise_for_status()
        data = resp.json()
        print(f"Response: {data}")
    except Exception as e:
        print(f"Failed to query: {e}")

if __name__ == "__main__":
    test_flow()
