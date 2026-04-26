import requests

print("start")
print("pypi...")
print(requests.get("https://pypi.org", timeout=10).status_code)

print("telegram...")
response = requests.get("https://api.telegram.org", timeout=10)
print(response.status_code)

print("done")