import requests

BASE_URL = "http://127.0.0.1:7860/api"

print("1. Signing up/Logging in...")
login_res = requests.post(f"{BASE_URL}/login", json={"email": "test@example.com", "password": "password123"})
if login_res.status_code != 200:
    print("Login failed, trying signup...")
    signup_res = requests.post(f"{BASE_URL}/signup", json={"username": "testuser", "email": "test@example.com", "password": "password123"})
    if signup_res.status_code != 201:
        print(f"Signup failed: {signup_res.text}")
        exit(1)
    login_res = requests.post(f"{BASE_URL}/login", json={"email": "test@example.com", "password": "password123"})
    if login_res.status_code != 200:
        print(f"Login after signup failed: {login_res.text}")
        exit(1)
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful.")

print("2. Uploading document...")
files = {"files": ("sample_policy.txt", open("sample_policy.txt", "rb"), "text/plain")}
upload_res = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
if upload_res.status_code != 200:
    print(f"Upload failed: {upload_res.text}")
    exit(1)
print("Upload response:", upload_res.json())

print("3. Querying document...")
chat_res = requests.post(f"{BASE_URL}/chat", json={"query": "How many days of paid time off do employees get?"}, headers=headers, stream=True)
if chat_res.status_code != 200:
    print(f"Chat failed: {chat_res.text}")
    exit(1)

print("Chat response:")
for line in chat_res.iter_lines():
    if line:
        print(line.decode('utf-8'))
print("\nDone.")
