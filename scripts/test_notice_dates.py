#!/usr/bin/env python3
"""
Test Notice Date/Time Display
Run: python test_notice_dates.py
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

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


def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_section(title: str):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{title:^70}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")


def make_request(method: str, path: str, token: Optional[str] = None, body: Optional[Dict] = None) -> tuple[int, Any]:
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


def login(email: str, password: str = "Test@1234") -> Optional[Dict]:
    status, data = make_request("POST", "/auth/login", body={
        "email_or_phone": email,
        "password": password
    })
    if status == 200:
        print_success(f"Logged in as {email}")
        return data
    else:
        print_error(f"Login failed for {email}: {data.get('detail', 'Unknown error')}")
        return None


def create_test_notice(token: str, hostel_id: str = None) -> Optional[str]:
    """Create a test notice with specific date/time"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    future_date = now + timedelta(days=7)
    
    notice_data = {
        "title": f"Test Notice - Date Test {now.strftime('%Y-%m-%d %H:%M:%S')}",
        "content": "This is a test notice to verify date/time display.\nCreated at: " + now.isoformat(),
        "notice_type": "general",
        "priority": "medium",
        "is_published": True,
        "publish_at": now.isoformat(),
        "expires_at": future_date.isoformat()
    }
    
    if hostel_id:
        notice_data["hostel_id"] = hostel_id
    
    path = f"/admin/hostels/{hostel_id}/notices" if hostel_id else "/admin/notices/platform"
    
    status, data = make_request("POST", path, token=token, body=notice_data)
    
    if status == 201:
        notice_id = data.get("id")
        print_success(f"Created test notice: {notice_id[:8]}...")
        print_info(f"  Title: {data.get('title')}")
        print_info(f"  Created at: {data.get('created_at')}")
        return notice_id
    else:
        print_error(f"Failed to create notice: {status}")
        return None


def test_student_notice_dates():
    """Test student notice date/time display"""
    print_section("STUDENT NOTICE DATE/TIME DISPLAY TEST")
    print_info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"API URL: {BASE_URL}")
    
    # Login as Student
    print_info("\nStep 1: Login as Student...")
    student_data = login("hemant.pawade.lev044@levitica.in")
    
    if not student_data:
        print_error("Cannot proceed without student login")
        return
    
    student_token = student_data.get("access_token")
    
    # Get student's notices
    print_info("\nStep 2: Fetch student notices...")
    status, data = make_request("GET", "/student/notices/paginated?page=1&per_page=10", token=student_token)
    
    if status != 200:
        print_error(f"Failed to fetch notices: {status}")
        return
    
    items = data.get("items", [])
    total = data.get("total", 0)
    
    print_success(f"Fetched {len(items)} of {total} notices")
    
    if not items:
        print_warning("No notices found. Creating a test notice...")
        
        # Login as Admin to create a notice
        admin_data = login("admin1@stayease.com")
        if admin_data:
            admin_token = admin_data.get("access_token")
            hostel_ids = admin_data.get("hostel_ids", [])
            
            if hostel_ids:
                notice_id = create_test_notice(admin_token, hostel_ids[0])
                if notice_id:
                    # Wait a moment then retry
                    import time
                    time.sleep(1)
                    
                    # Fetch notices again
                    status, data = make_request("GET", "/student/notices/paginated?page=1&per_page=10", token=student_token)
                    if status == 200:
                        items = data.get("items", [])
                        total = data.get("total", 0)
                        print_success(f"Now have {len(items)} notices")
    
    print_section("NOTICE DATE/TIME DISPLAY CHECK")
    
    # Test 1: Check date format in response
    print_info("\nTest 1: Check if date fields are present and properly formatted")
    
    date_fields = ["created_at", "updated_at", "publish_at", "expires_at"]
    
    if items:
        sample = items[0]
        print_info(f"Sample notice: {sample.get('title', 'N/A')[:50]}")
        
        for field in date_fields:
            value = sample.get(field)
            if value:
                print_success(f"  {field}: {value}")
                # Check if format looks like ISO (has 'T')
                if 'T' in str(value):
                    print_success(f"    ✓ Format: ISO format (contains 'T')")
                else:
                    print_warning(f"    ⚠ Format may not be ISO (no 'T'): {value}")
            else:
                print_warning(f"  {field}: {RED}MISSING or NULL{RESET}")
    else:
        print_warning("No notices to test")
    
    # Test 2: Check if dates are readable/displayable
    print_info("\nTest 2: Check date readability for frontend display")
    
    if items:
        for i, notice in enumerate(items[:3]):
            print_info(f"\n  Notice {i+1}: {notice.get('title', 'N/A')[:40]}")
            created = notice.get('created_at')
            if created:
                # Try to parse as datetime
                try:
                    # Check if it's ISO format
                    if isinstance(created, str):
                        if 'T' in created:
                            # Parse ISO format
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            print_success(f"    Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            print_warning(f"    Created: {created} (non-ISO format)")
                    else:
                        print_info(f"    Created: {created}")
                except Exception as e:
                    print_error(f"    Failed to parse date: {e}")
            else:
                print_warning("    Created date: NOT AVAILABLE")
    
    # Test 3: Check read status dates (if any)
    print_info("\nTest 3: Check read status for notices")
    
    if items:
        notice_id = items[0].get("id")
        if notice_id:
            # Mark as read
            status, data = make_request("POST", f"/student/notices/{notice_id}/read", token=student_token)
            if status == 200:
                print_success(f"Marked notice {notice_id[:8]}... as read")
            
            # Check read status list
            status, data = make_request("GET", "/student/notices/read-status", token=student_token)
            if status == 200:
                read_ids = data if isinstance(data, list) else []
                print_success(f"User has read {len(read_ids)} notices")
    
    # Summary
    print_section("TEST SUMMARY")
    
    issues_found = []
    
    if items:
        sample = items[0]
        for field in date_fields:
            if not sample.get(field):
                issues_found.append(f"{field} missing")
    
    if issues_found:
        print_error(f"Date issues found: {', '.join(issues_found)}")
        print(f"\n{RED}{BOLD}❌ Some date fields are missing or not properly formatted{RESET}")
    else:
        print(f"{GREEN}{BOLD}✅ Date fields are present and properly formatted!{RESET}")
    
    # Test 4: Verify admin notice creation dates
    print_info("\nTest 4: Verify admin notice creation dates")
    
    admin_data = login("admin1@stayease.com")
    if admin_data:
        admin_token = admin_data.get("access_token")
        hostel_ids = admin_data.get("hostel_ids", [])
        
        if hostel_ids:
            status, data = make_request("GET", f"/admin/hostels/{hostel_ids[0]}/notices/paginated?page=1&per_page=5", token=admin_token)
            
            if status == 200:
                admin_items = data.get("items", [])
                if admin_items:
                    sample_admin = admin_items[0]
                    print_info("\n  Admin notice sample:")
                    created = sample_admin.get("created_at")
                    print_success(f"    Created: {created}")
                    print_success(f"    Updated: {sample_admin.get('updated_at')}")
                    
                    # Check if dates are ISO format
                    if isinstance(created, str) and 'T' in created:
                        print_success("    ✓ Using ISO date format")
                    else:
                        print_warning("    ⚠ Date format may not be ISO")
    
    print(f"\n{CYAN}Expected date format: ISO 8601 (e.g., 2026-05-07T10:30:00+00:00){RESET}")
    print(f"\n{GREEN}To fix: Ensure NoticeResponse uses datetime fields with proper serialization{RESET}")


def test_create_notice_with_dates():
    """Test creating a notice with explicit dates"""
    print_section("CREATE NOTICE WITH DATE FIELDS TEST")
    
    # Login as Admin
    admin_data = login("admin1@stayease.com")
    if not admin_data:
        print_error("Admin login failed")
        return
    
    admin_token = admin_data.get("access_token")
    hostel_ids = admin_data.get("hostel_ids", [])
    
    if not hostel_ids:
        print_error("No hostels assigned")
        return
    
    from datetime import datetime, timedelta
    
    now = datetime.now()
    future = now + timedelta(days=30)
    
    notice_data = {
        "title": f"Date Format Test {now.strftime('%Y-%m-%d %H:%M:%S')}",
        "content": f"This notice tests date format display.\n\nCreated: {now.isoformat()}\nExpires: {future.isoformat()}",
        "notice_type": "general",
        "priority": "medium",
        "is_published": True,
        "publish_at": now.isoformat(),
        "expires_at": future.isoformat(),
        "hostel_id": hostel_ids[0]
    }
    
    print_info("Creating notice with explicit dates...")
    status, data = make_request("POST", f"/admin/hostels/{hostel_ids[0]}/notices", token=admin_token, body=notice_data)
    
    if status == 201:
        print_success("Notice created successfully!")
        print_info(f"  ID: {data.get('id')}")
        print_info(f"  Title: {data.get('title')}")
        print_info(f"  Created at: {data.get('created_at')}")
        print_info(f"  Publish at: {data.get('publish_at')}")
        print_info(f"  Expires at: {data.get('expires_at')}")
        
        # Verify date format
        if data.get('created_at') and 'T' in str(data.get('created_at')):
            print_success("  ✓ Created at uses ISO format with time")
        else:
            print_warning("  ⚠ Created at may not include time component")
            
        return data.get('id')
    else:
        print_error(f"Failed to create notice: {status}")
        return None


if __name__ == "__main__":
    test_create_notice_with_dates()
    test_student_notice_dates()