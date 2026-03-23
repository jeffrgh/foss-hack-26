from core.frappe_api import import_page, get_session
import streamlit as st
import requests
import json
import sys
import os

FRAPPE_URL = "http://localhost:8000"
FRAPPE_USER = "Administrator"
FRAPPE_PASS = "admin"
OLLAMA_URL = "http://localhost:11434"



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


def generate(description, provider="Local Ollama", api_key=None):
    from core.ollama import generate_page, generate_page_groq, generate_page_openai, generate_page_gemini
    from core.validator import process

    if provider == "Groq" and api_key:
        result = generate_page_groq(description, api_key)
    elif provider == "OpenAI" and api_key:
        result = generate_page_openai(description, api_key)
    elif provider == "Gemini" and api_key:
        result = generate_page_gemini(description, api_key)
    else:
        result = generate_page(description)

    if isinstance(result, dict):
        return result
    fixed, _, err = process(str(result))
    if err:
        raise ValueError(err)
    return fixed

st.set_page_config(page_title="AI Page Builder", layout="wide")
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
    with st.expander("Tips for better results"):
        st.markdown("""
    **Structure** — mention the sections you want:
    `hero`, `navbar`, `footer`, `pricing section`, `contact form`, `features grid`

    **Hero** — describe it specifically:
    `dark hero with bold heading`, `full-width hero with background image`, `centered hero with CTA button`

    **Content** — give real context:
    `coffee shop`, `SaaS product`, `car dealership`, `personal portfolio`

    **Buttons & Links** — mention them explicitly:
    `Order Now button`, `Get Started CTA`, `nav links to Home About Pricing`

    **Style** — mention colors and feel:
    `dark theme`, `minimal white`, `bold typography`, `card grid layout`

    **Example prompt:**
    `A dark themed car dealership homepage with a navbar, bold hero saying Find Your Dream Car, 
    a red CTA button, a 3-card inventory grid showing car name price and View Details button, and a footer`
    """)
    llm_provider = st.selectbox(
        "LLM Provider",
        ["Local Ollama", "Groq", "OpenAI", "Gemini"],
        index=0
    )
    if llm_provider != "Local Ollama":
        api_key = st.text_input("API Key", type="password", placeholder="Paste your API key here")
    else:
        api_key = None
    

    if "desc" in st.session_state:
        typed = st.text_area("", value=st.session_state.desc, height=150, label_visibility="collapsed")
    else:
        typed = st.text_area("", placeholder="A dark landing page for a coffee shop with a hero, tagline, and order button.", height=150, label_visibility="collapsed")

    st.caption("Examples:")
    for ex in [
        "Restaurant homepage with hero, menu section, contact form",
        "SaaS product page with pricing table",
        "Personal portfolio with about and projects"
    ]:
        if st.button(ex, key=ex):
            st.session_state.desc = ex
            st.rerun()

    desc = typed
    go = st.button("Generate", type="primary", disabled=not desc)

with right:
    st.subheader("Output")

    if "result" in st.session_state:
        with st.expander("View Generated JSON", expanded=False):
            st.json(st.session_state.result)

        if "imported_page" in st.session_state:
            st.success("Imported!")
            st.markdown(f"[Open in Builder](http://127.0.0.1:8000/builder/page/{st.session_state.imported_page})")

            st.divider()
            refinement = st.text_input("Refine your page", placeholder="make the hero red, add a testimonials section...")
            refine_btn = st.button("Apply Refinement", disabled=not refinement)

            if refine_btn and refinement:
                with st.spinner("Refining..."):
                    try:
                        from core.ollama import refine_page
                        from core.validator import validate
                        from core.frappe_api import update_page
                        updated = refine_page(st.session_state.result, refinement, api_key if llm_provider != "Local Ollama" else None)
                        updated, _ = validate(updated)
                        update_page(st.session_state.imported_page, updated)
                        st.session_state.result = updated
                        st.success("Page updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            if st.button("Import to Frappe"):
                with st.spinner("Importing..."):
                    try:
                        res = import_page(st.session_state.result)
                        st.session_state.imported_page = res["name"]
                        st.success("Imported!")
                        st.markdown(f"[Open in Builder](http://127.0.0.1:8000/builder/page/{res['name']})")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.info("Output appears here after generation.")

if go and desc:
    with st.spinner("Generating..."):
        try:
            st.session_state.result = generate(desc, provider=llm_provider, api_key=api_key)
            st.rerun()
        except Exception as e:
            st.error(str(e))
