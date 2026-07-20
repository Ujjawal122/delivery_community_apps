import urllib.request
import urllib.error
import json
import uuid

base_url = 'http://127.0.0.1:8000'

def register():
    req = urllib.request.Request(f'{base_url}/auth/register', method='POST', headers={'Content-Type': 'application/json'})
    email = f"test_{uuid.uuid4()}@test.com"
    data = json.dumps({
        "full_name": "Test User",
        "email": email,
        "password": "password123"
    }).encode('utf-8')
    try:
        resp = urllib.request.urlopen(req, data=data)
        return email
    except urllib.error.HTTPError as e:
        return None

def login(email):
    req = urllib.request.Request(f'{base_url}/auth/login', method='POST', headers={'Content-Type': 'application/json'})
    data = json.dumps({
        "email": email,
        "password": "password123"
    }).encode('utf-8')
    resp = urllib.request.urlopen(req, data=data)
    return json.loads(resp.read().decode('utf-8'))['data']['access_token']

def list_communities():
    req = urllib.request.Request(f'{base_url}/communities?limit=100')
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode('utf-8'))
        return data['data']  # it is a list
    except urllib.error.HTTPError as e:
        print("List error:", e.code)
        return []

def test_community(token, comm_id):
    # get community
    req1 = urllib.request.Request(f'{base_url}/communities/{comm_id}')
    try:
        urllib.request.urlopen(req1)
    except urllib.error.HTTPError as e:
        print(f"Community {comm_id} GET error: {e.code}, {e.read().decode('utf-8')}")

    # check membership
    req2 = urllib.request.Request(f'{base_url}/communities/{comm_id}/membership', headers={'Authorization': f'Bearer {token}'})
    try:
        urllib.request.urlopen(req2)
    except urllib.error.HTTPError as e:
        print(f"Community {comm_id} Membership error: {e.code}, {e.read().decode('utf-8')}")

    # get posts
    req3 = urllib.request.Request(f'{base_url}/posts?community_id={comm_id}', headers={'Authorization': f'Bearer {token}'})
    try:
        urllib.request.urlopen(req3)
    except urllib.error.HTTPError as e:
        print(f"Community {comm_id} Posts error: {e.code}, {e.read().decode('utf-8')}")

email = register()
if email:
    token = login(email)
    comms = list_communities()
    print(f"Found {len(comms)} communities.")
    for c in comms:
        test_community(token, c['id'])
    print("Testing completed.")
