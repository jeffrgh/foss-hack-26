import streamlit as st
import requests
import json
import sys
import os

FRAPPE_URL = "http://localhost:8000"
FRAPPE_USER = "Administrator"
FRAPPE_PASS = "admin"
OLLAMA_URL = "http://localhost:11434"


def frappe_session():
    s = requests.Session()
    s.post(f"{FRAPPE_URL}/api/method/login", data={"usr": FRAPPE_USER, "pwd": FRAPPE_PASS}).raise_for_status()
    return s


def import_page(page_data, session):
    blocks = page_data.get("blocks", [])
    payload = {
        "doctype": "Builder Page",
        "page_title": page_data.get("page_title", "Generated Page"),
        "published": 1,
        "blocks": json.dumps(blocks) if isinstance(blocks, list) else blocks
    }
    res = session.post(f"{FRAPPE_URL}/api/resource/Builder Page", json=payload)
    res.raise_for_status()
    return res.json()


def ollama_up():
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=3).status_code == 200
    except:
        return False


def frappe_up():
    try:
        return requests.get(f"{FRAPPE_URL}/api/method/ping", timeout=3).status_code == 200
    except:
        return False


def generate(description):
    from core.ollama import generate_page
    from core.validator import process

    result = generate_page(description)
    if isinstance(result, dict):
        return result
    fixed, _, err = process(str(result))
    if err:
        raise ValueError(err)
    return fixed

st.set_page_config(page_title="AI Page Builder", page_icon="🧠", layout="wide")
st.title("AI Page Builder for Frappe")
st.caption("Describe a page, get Frappe Builder JSON, import in one click.")
st.divider()

c1, c2, _ = st.columns([1, 1, 4])
if ollama_up():
    c1.success("Ollama running")
else:
    c1.error("Ollama offline")

if frappe_up():
    c2.success("Frappe running")
else:
    c2.error("Frappe offline")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Describe your page")
    desc = st.text_area("", placeholder="A dark landing page for a coffee shop with a hero, tagline, and order button.", height=150, label_visibility="collapsed")

    st.caption("Examples:")
    for ex in [
        "Restaurant homepage with hero, menu section, contact form",
        "SaaS product page with pricing table",
        "Personal portfolio with about and projects"
    ]:
        if st.button(ex, key=ex):
            st.session_state.desc = ex

    if "desc" in st.session_state:
        desc = st.session_state.desc

    go = st.button("Generate", type="primary", disabled=not desc)

with right:
    st.subheader("Generated JSON")

    if "result" in st.session_state:
        st.json(st.session_state.result)
        if st.button("Import to Frappe"):
            with st.spinner("Importing..."):
                try:
                    s = frappe_session()
                    res = import_page(st.session_state.result, s)
                    name = res.get("data", {}).get("name", "")
                    st.success("Imported!")
                    st.markdown(f"[Open in Builder]({FRAPPE_URL}/builder/{name})")
                except Exception as e:
                    st.error(str(e))
    else:
        st.info("JSON will appear here after generation.")

if go and desc:
    with st.spinner("Generating..."):
        try:
            st.session_state.result = generate(desc)
            st.rerun()
        except Exception as e:
            st.error(str(e))
