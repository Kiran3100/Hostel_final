#!/usr/bin/env python3
"""
Test the failing endpoints individually.
"""

import json
import urllib.request
import urllib.error
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, path, token=None, body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw) if raw else {}
        except:
            return e.code, {"detail": raw.decode('utf-8', errors='replace')}
    except Exception as e:
        return 500, {"detail": str(e)}

def login(email, password="Test@1234"):
    status, data = make_request("POST", "/auth/login", body={
        "email_or_phone": email,
        "password": password
    })
    if status == 200:
        return data.get("access_token")
    return None

def test_compare_favorites():
    print("\n" + "="*60)
    print("Testing Compare Favorites")
    print("="*60)
    
    token = login("arun.kapoor@gmail.com")
    if not token:
        print("❌ Login failed")
        return
    
    status, data = make_request("POST", "/visitor/favorites/compare", token=token)
    print(f"Status: {status}")
    if status == 200:
        print(f"✅ Success: Found {len(data)} favorites to compare")
        if data:
            print(f"   First: {data[0].get('name')} - ₹{data[0].get('starting_price')}")
    else:
        print(f"❌ Failed: {data.get('detail', 'Unknown error')}")

def test_read_status():
    print("\n" + "="*60)
    print("Testing Read Status")
    print("="*60)
    
    token = login("arun.kapoor@gmail.com")
    if not token:
        print("❌ Login failed")
        return
    
    status, data = make_request("GET", "/visitor/notices/read-status", token=token)
    print(f"Status: {status}")
    if status == 200:
        print(f"✅ Success: Read {len(data)} notices")
    else:
        print(f"❌ Failed: {data.get('detail', 'Unknown error')}")

def test_join_waitlist():
    print("\n" + "="*60)
    print("Testing Join Waitlist")
    print("="*60)
    
    token = login("arun.kapoor@gmail.com")
    if not token:
        print("❌ Login failed")
        return
    
    # First get a valid room ID
    status, hostels = make_request("GET", "/public/hostels?per_page=1")
    if status != 200 or not hostels.get("items"):
        print("❌ Could not get hostel")
        return
    
    hostel_id = hostels["items"][0].get("id")
    
    # Get rooms for this hostel
    status, rooms = make_request("GET", f"/public/hostels/{hostel_id}/rooms")
    if status != 200 or not rooms:
        print("❌ Could not get rooms")
        return
    
    room_id = rooms[0].get("id")
    print(f"Using hostel: {hostels['items'][0].get('name')}")
    print(f"Using room: {rooms[0].get('room_number')}")
    
    # Join waitlist
    future_start = (date.today() + timedelta(days=60)).isoformat()
    future_end = (date.today() + timedelta(days=90)).isoformat()
    
    payload = {
        "hostel_id": hostel_id,
        "room_id": room_id,
        "booking_mode": "monthly",
        "check_in_date": future_start,
        "check_out_date": future_end
    }
    
    status, data = make_request("POST", "/visitor/waitlist/join", token=token, body=payload)
    print(f"Status: {status}")
    if status in [200, 201]:
        print(f"✅ Success: Position {data.get('position', 'N/A')}")
    else:
        print(f"❌ Failed: {data.get('detail', 'Unknown error')}")

if __name__ == "__main__":
    test_compare_favorites()
    test_read_status()
    test_join_waitlist()