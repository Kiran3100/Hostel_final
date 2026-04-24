import urllib.request, json, urllib.error

BASE = "http://localhost:8000/api/v1"

def post(path, body):
    data = json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data,
                               headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

credentials = [
    ("superadmin@stayease.com", "Test@1234"),
    ("admin1@stayease.com", "Test@1234"),
    ("supervisor1@stayease.com", "Test@1234"),
    ("rahul.sharma@student.com", "Test@1234"),
    ("arun.kapoor@gmail.com", "Test@1234"),
]

print("\nLogin test results:")
print("-" * 60)
for email, pwd in credentials:
    status, data = post("/auth/login", {"email_or_phone": email, "password": pwd})
    if status == 200:
        print(f"  PASS  {email} → role={data.get('role')}, hostel_ids={data.get('hostel_ids')}")
    else:
        print(f"  FAIL  {email} → {status}: {data.get('detail', data)}")
