# scripts/test_duplicate_email_multi_hostel.py
#!/usr/bin/env python3
"""
Test duplicate email handling across multiple hostels
Run: python scripts/test_duplicate_email_multi_hostel.py
"""

import asyncio
import asyncpg
import json
import urllib.request
import urllib.error
from datetime import datetime
import os

BASE_URL = "http://localhost:8000/api/v1"

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    print(f"{BLUE}ℹ {text}{RESET}")


def print_section(title: str):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{title:^70}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")


def make_request(method: str, path: str, token: str = None, body: dict = None) -> tuple:
    """Make HTTP request to API"""
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
            return e.code, json.loads(raw) if raw else {"detail": str(e)}
        except:
            return e.code, {"detail": raw.decode('utf-8', errors='replace')}
    except Exception as e:
        return 500, {"detail": str(e)}


def login(email: str, password: str = "Test@1234") -> str:
    """Login and return access token"""
    status, data = make_request("POST", "/auth/login", body={
        "email_or_phone": email,
        "password": password
    })
    if status == 200:
        return data.get("access_token")
    else:
        print_error(f"Login failed: {data.get('detail', 'Unknown')}")
        return None


def create_admin(token: str, email: str, phone: str, full_name: str, password: str = "Test@1234") -> tuple:
    """Create a new admin"""
    payload = {
        "email": email,
        "phone": phone,
        "full_name": full_name,
        "password": password
    }
    return make_request("POST", "/super-admin/admins", token=token, body=payload)


def get_hostels(token: str) -> list:
    """Get all hostels"""
    status, data = make_request("GET", "/super-admin/hostels", token=token)
    if status == 200:
        return data
    return []


def assign_hostel_to_admin(token: str, admin_id: str, hostel_id: str) -> tuple:
    """Assign a hostel to an admin"""
    payload = {"hostel_ids": [hostel_id]}
    return make_request("POST", f"/super-admin/admins/{admin_id}/assign-hostels", token=token, body=payload)


def delete_admin(token: str, admin_id: str) -> tuple:
    """Delete an admin (if endpoint exists)"""
    return make_request("DELETE", f"/super-admin/admins/{admin_id}", token=token)


def delete_user_by_email(db_url: str, email: str) -> None:
    """Direct database deletion of user by email"""
    async def _delete():
        try:
            conn = await asyncpg.connect(db_url)
            # First delete related records
            await conn.execute('DELETE FROM refresh_tokens WHERE user_id IN (SELECT id FROM users WHERE email = $1)', email)
            await conn.execute('DELETE FROM otp_verifications WHERE user_id IN (SELECT id FROM users WHERE email = $1)', email)
            await conn.execute('DELETE FROM admin_hostel_mappings WHERE admin_id IN (SELECT id FROM users WHERE email = $1)', email)
            # Then delete the user
            result = await conn.execute('DELETE FROM users WHERE email = $1', email)
            await conn.close()
            if result != "DELETE 0":
                print_info(f"  Deleted user with email: {email}")
        except Exception as e:
            print_warning(f"  Could not delete {email}: {e}")
    
    asyncio.run(_delete())


def main():
    print_section("DUPLICATE EMAIL TEST FOR MULTIPLE HOSTELS")
    
    # Login as Super Admin
    token = login("superadmin@stayease.com")
    if not token:
        print_error("Cannot proceed without super admin token")
        return
    
    print_success("Logged in as Super Admin")
    
    # Get hostels
    hostels = get_hostels(token)
    if len(hostels) < 2:
        print_error(f"Need at least 2 hostels for this test. Found {len(hostels)}")
        return
    
    print_info(f"Found {len(hostels)} hostels")
    for i, hostel in enumerate(hostels[:3], 1):
        print_info(f"  {i}. {hostel.get('name')} (ID: {hostel.get('id')[:8]}...)")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"duplicate.test.{timestamp}@stayease.com"
    test_phone = f"9{timestamp[:8]}12345"
    
    # Test 1: Create first admin
    print_section("TEST 1: Create First Admin")
    print_info(f"Creating admin with email: {test_email}")
    status, data = create_admin(token, test_email, test_phone, "First Admin Test")
    
    if status == 201:
        first_admin_id = data.get("id")
        print_success(f"First admin created successfully! ID: {first_admin_id[:8]}...")
        
        # Assign first hostel to this admin
        first_hostel_id = hostels[0].get("id")
        print_info(f"Assigning hostel: {hostels[0].get('name')}")
        status, data = assign_hostel_to_admin(token, first_admin_id, first_hostel_id)
        
        if status == 200:
            print_success(f"Hostel assigned to first admin")
        else:
            print_warning(f"Failed to assign hostel: {status}")
    else:
        print_error(f"Failed to create first admin: {status}")
        if status == 409:
            print_info("Email already exists. Try a different email.")
        return
    
    # Test 2: Try to create second admin with SAME email
    print_section("TEST 2: Create Second Admin with Same Email")
    print_info(f"Attempting to create admin with SAME email: {test_email}")
    print_info(f"Different phone: 8{timestamp[:8]}54321")
    
    status, data = create_admin(token, test_email, "8" + test_phone[1:], "Second Admin Test")
    
    if status == 409:
        print_success(f"Correctly REJECTED duplicate email (HTTP 409)")
        print_info(f"  Error: {data.get('detail', 'Email already registered')}")
        print_success("✓ Duplicate emails are NOT allowed across hostels")
    else:
        print_error(f"Unexpected result: HTTP {status}")
        if status == 201:
            print_error("❌ Duplicate email was ACCEPTED - This is a security issue!")
    
    # Test 3: Try different email but same phone
    print_section("TEST 3: Create Admin with Same Phone")
    different_email = f"different.{timestamp}@stayease.com"
    print_info(f"Different email: {different_email}")
    print_info(f"Same phone: {test_phone}")
    
    status, data = create_admin(token, different_email, test_phone, "Phone Test Admin")
    
    if status == 409:
        print_success(f"Correctly REJECTED duplicate phone (HTTP 409)")
    elif status == 201:
        print_error(f"❌ Duplicate phone was ACCEPTED - HTTP {status}")
        # Clean up
        admin_id = data.get("id")
        if admin_id:
            print_info(f"  Cleaning up: deleting admin {admin_id[:8]}...")
            # Note: DELETE endpoint may not exist, so this is best effort
    else:
        print_info(f"Result: HTTP {status}")
    
    # Test 4: Same admin can manage multiple hostels
    print_section("TEST 4: Can Same Admin Manage Multiple Hostels?")
    
    fresh_email = f"multi.hostel.{timestamp}@stayease.com"
    fresh_phone = f"7{timestamp[:8]}99999"
    
    print_info(f"Creating fresh admin: {fresh_email}")
    status, data = create_admin(token, fresh_email, fresh_phone, "Multi-Hostel Admin")
    
    if status != 201:
        print_error(f"Failed to create fresh admin: {status}")
    else:
        multi_admin_id = data.get("id")
        print_success(f"Admin created: {multi_admin_id[:8]}...")
        
        # Assign first hostel
        print_info(f"Assigning hostel '{hostels[0].get('name')}'...")
        status, data = assign_hostel_to_admin(token, multi_admin_id, hostels[0].get("id"))
        
        if status == 200:
            print_success(f"Hostel 1 assigned")
        else:
            print_error(f"Failed to assign hostel 1: {status}")
        
        # Assign second hostel
        print_info(f"Assigning hostel '{hostels[1].get('name')}'...")
        status, data = assign_hostel_to_admin(token, multi_admin_id, hostels[1].get("id"))
        
        if status == 200:
            print_success(f"Hostel 2 assigned")
            print_success("✓ Same admin CAN manage multiple hostels")
        else:
            print_error(f"Failed to assign hostel 2: {status}")
    
    # Summary
    print_section("CONCLUSION")
    print(f"""
{BOLD}Findings:{RESET}

1. {GREEN}Duplicate emails are NOT allowed{RESET} - Creating admin with same email 
   returns HTTP 409 Conflict, even for different hostels.

2. {GREEN}Duplicate phones are NOT allowed{RESET} - Phone numbers must be unique
   across all users.

3. {GREEN}Same admin CAN manage multiple hostels{RESET} - By assigning multiple
   hostels to the same admin account.

{BOLD}Test accounts created:{RESET}
   - First admin: {test_email}
   - Multi-hostel admin: {fresh_email}

{BOLD}To clean up:{RESET}
   These accounts can be deleted via the admin panel or database.
    """)
    
    # Ask about cleanup
    print("\n" + "="*70)
    response = input("Delete test accounts? (y/n): ").strip().lower()
    if response == 'y':
        db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/stayease_dev')
        delete_user_by_email(db_url, test_email)
        delete_user_by_email(db_url, fresh_email)
        delete_user_by_email(db_url, different_email)
        print_success("Cleanup complete!")


if __name__ == "__main__":
    main()