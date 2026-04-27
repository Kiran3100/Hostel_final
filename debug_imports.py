#!/usr/bin/env python3
import sys
import os

print("Python path:", sys.path)
print("Current directory:", os.getcwd())

try:
    print("\nChecking directory structure...")
    for root, dirs, files in os.walk("app/api/v1"):
        level = root.replace("app/api/v1", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
except Exception as e:
    print(f"Error listing files: {e}")

try:
    print("\nAttempting to import...")
    from app.api.v1.public.routes import router
    print("✓ Successfully imported public.routes")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()