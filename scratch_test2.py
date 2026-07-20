import urllib.request
import urllib.error

try:
    req = urllib.request.Request('http://127.0.0.1:8000/communities/123')
    resp = urllib.request.urlopen(req)
    print("Response:", resp.read())
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
