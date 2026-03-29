import requests
import json
import os

FRAPPE_URL = "http://localhost:8000"
FRAPPE_USER = os.getenv("FRAPPE_USER", "Administrator")
FRAPPE_PASS = os.getenv("FRAPPE_PASS", "admin")


def get_session():
    s = requests.Session()
    s.post(f"{FRAPPE_URL}/api/method/login", data={"usr": FRAPPE_USER, "pwd": FRAPPE_PASS}).raise_for_status()
    return s


def import_page(page_data, session=None):
    if session is None:
        session = get_session()
    blocks = page_data.get("blocks", [])
    payload = {
        "doctype": "Builder Page",
        "page_title": page_data.get("page_title", "Generated Page"),
        "published": 1,
        "blocks": json.dumps(blocks) if isinstance(blocks, list) else blocks
    }
    res = session.post(f"{FRAPPE_URL}/api/resource/Builder Page", json=payload)
    res.raise_for_status()
    name = res.json().get("data", {}).get("name", "")
    return {"name": name, "url": f"{FRAPPE_URL}/builder/page/{name}"} 


def is_running():
    try:
        return requests.get(f"{FRAPPE_URL}/api/method/ping", timeout=3).status_code == 200
    except:
        return False

def update_page(page_name, page_data, session=None):
    if session is None:
        session = get_session()
    blocks = page_data.get("blocks", [])
    payload = {
        "blocks": json.dumps(blocks) if isinstance(blocks, list) else blocks,
        "page_title": page_data.get("page_title", "Generated Page")
    }
    res = session.put(f"{FRAPPE_URL}/api/resource/Builder Page/{page_name}", json=payload)
    res.raise_for_status()
    return {"name": page_name, "url": f"{FRAPPE_URL}/builder/page/{page_name}"}