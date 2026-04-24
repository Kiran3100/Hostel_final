# scripts/debug_waitlist.py
import json
import urllib.request
import urllib.error
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login(email, password="Test@1234"):
    data = json.dumps({"email_or_phone": email, "password": password}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Login error: {e}")
        return None

# Login as visitor
visitor = login("arun.kapoor@gmail.com")
if not visitor:
    print("Login failed")
    exit(1)

token = visitor.get("access_token")
print(f"Token: {token[:50]}...")

# Get a valid hostel and room
print("\nGetting valid hostel and room...")
req = urllib.request.Request(f"{BASE_URL}/public/hostels?per_page=1", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    hostels = json.loads(resp.read())
    hostel_id = hostels["items"][0]["id"]
    print(f"Hostel ID: {hostel_id}")

# Get rooms for this hostel
req = urllib.request.Request(f"{BASE_URL}/public/hostels/{hostel_id}/rooms", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    rooms = json.loads(resp.read())
    if rooms:
        room_id = rooms[0]["id"]
        print(f"Room ID: {room_id}")
    else:
        print("No rooms found")
        exit(1)

# Test waitlist join
future_date = (date.today() + timedelta(days=60)).isoformat()
future_end = (date.today() + timedelta(days=90)).isoformat()

waitlist_data = {
    "hostel_id": hostel_id,
    "room_id": room_id,
    "booking_mode": "monthly",
    "check_in_date": future_date,
    "check_out_date": future_end
}

print(f"\nWaitlist data: {json.dumps(waitlist_data, indent=2)}")

req = urllib.request.Request(
    f"{BASE_URL}/visitor/waitlist/join",
    data=json.dumps(waitlist_data).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"\nSuccess: {result}")
except urllib.error.HTTPError as e:
    print(f"\nError {e.code}: {e.read().decode()}")