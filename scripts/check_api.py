import urllib.request, json

r = urllib.request.urlopen("http://localhost:8000/api/v1/public/hostels")
d = json.loads(r.read())
print(f"API OK — {len(d)} hostels")
for h in d[:2]:
    print(f"  {h['name']} ({h['city']}) — rating: {h['rating']}, price: {h['starting_price']}")

r2 = urllib.request.urlopen("http://localhost:8000/health")
print(f"Health: {json.loads(r2.read())}")
