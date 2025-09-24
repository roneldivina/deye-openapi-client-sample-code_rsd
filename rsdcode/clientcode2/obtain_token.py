import requests
from urllib.parse import urljoin

API_BASE = "https://eu1-developer.deyecloud.com/v1.0"  # or whatever base they use

def get_token(app_id: str, app_secret: str) -> str:
    url = urljoin(API_BASE, "/v1/oauth/token")
    payload = {
        "appId": app_id,
        "appSecret": app_secret
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    j = r.json()
    # sample structure: { "code": 0, "data": { "accessToken": "...", "expiresIn": 3600 } }
    return j["data"]["accessToken"]
