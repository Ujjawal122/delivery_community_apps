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

def join_community(token, community_id):
    req = urllib.request.Request(f'{base_url}/communities/{community_id}/join', method='POST', headers={'Authorization': f'Bearer {token}'})
    try:
        resp = urllib.request.urlopen(req, data=b'')
        print("Join:", resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print("Join Error:", e.read().decode('utf-8'))

def check_membership(token, community_id):
    req = urllib.request.Request(f'{base_url}/communities/{community_id}/membership', headers={'Authorization': f'Bearer {token}'})
    try:
        resp = urllib.request.urlopen(req)
        print("Membership:", resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print("Membership Error:", e.code, e.read().decode('utf-8'))

email = register()
if email:
    token = login(email)
    community_id = '6a939fe6-21c6-49a5-8be1-65f7f6b32b78'
    join_community(token, community_id)
    check_membership(token, community_id)
