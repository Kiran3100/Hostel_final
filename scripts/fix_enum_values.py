# scripts/fix_enum_values.py
import re

# Read the seed_data.py file
with open('scripts/seed_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix hostel_type values (uppercase enum)
content = re.sub(r'"hostel_type":\s*"boys"', '"hostel_type": "BOYS"', content)
content = re.sub(r'"hostel_type":\s*"girls"', '"hostel_type": "GIRLS"', content)
content = re.sub(r'"hostel_type":\s*"coed"', '"hostel_type": "COED"', content)

# Also fix room_type values if needed
content = re.sub(r'"type":\s*"single"', '"type": "SINGLE"', content)
content = re.sub(r'"type":\s*"double"', '"type": "DOUBLE"', content)
content = re.sub(r'"type":\s*"triple"', '"type": "TRIPLE"', content)
content = re.sub(r'"type":\s*"dormitory"', '"type": "DORMITORY"', content)

# Write back
with open('scripts/seed_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed enum values in seed_data.py")
print("   - hostel_type: boys → BOYS, girls → GIRLS, coed → COED")
print("   - room_type: single → SINGLE, double → DOUBLE, triple → TRIPLE, dormitory → DORMITORY")