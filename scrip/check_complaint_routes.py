"""Check complaint routes in the codebase"""
import os
import re

def check_complaint_files():
    print("\n" + "="*60)
    print("Checking Complaint Implementation")
    print("="*60)
    
    # Check admin routes for complaint delete
    admin_file = "app/api/v1/admin/routes.py"
    if os.path.exists(admin_file):
        with open(admin_file, 'r') as f:
            content = f.read()
        
        # Search for complaint delete routes
        if 'complaint' in content.lower():
            matches = re.findall(r'@router\.(delete|patch).*complaint.*\n.*def.*', content, re.IGNORECASE)
            print(f"\n✓ Admin routes found with complaint endpoints")
            for m in matches[:5]:
                print(f"  - {m.strip()}")
        else:
            print("\n✗ No complaint delete routes found in admin routes")
    
    # Check complaint service for delete method
    service_file = "app/services/complaint_service.py"
    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()
        
        if 'async def delete' in content.lower():
            print(f"\n✓ Complaint service has delete method")
        else:
            print(f"\n✗ Complaint service has NO delete method")
    
    # Check supervisor routes
    supervisor_file = "app/api/v1/supervisor/routes.py"
    if os.path.exists(supervisor_file):
        with open(supervisor_file, 'r') as f:
            content = f.read()
        
        if 'complaint' in content.lower():
            print(f"\n✓ Supervisor routes have complaint endpoints")
        else:
            print(f"\n✗ No complaint endpoints in supervisor routes")

if __name__ == "__main__":
    check_complaint_files()