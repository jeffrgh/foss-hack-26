import frappe
import json
import re
import requests
import uuid

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

EXAMPLE_JSON = {
    "page_title": "Coffee Shop",
    "blocks": [{
        "blockId": "root", "element": "div", "originalElement": "body", "draggable": False,
        "children": [
            {
                "blockId": "nav1a2b3c", "element": "header", "blockName": "navbar",
                "children": [
                    {
                        "blockId": "logo1234a", "element": "p", "children": [],
                        "innerHTML": "<p>Brand</p>", "baseStyles": {"fontSize": "20px", "fontWeight": "bold"},
                        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {}, "attributes": {}, "classes": [],
                        "dataKey": None, "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    }
                ],
                "baseStyles": {"alignItems": "center", "display": "flex", "justifyContent": "space-between", "padding": "16px 40px", "width": "100%"},
                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {}, "attributes": {}, "classes": [],
                "dataKey": None, "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                "props": {}, "customAttributes": {}, "activeState": None
            },
            {
                "blockId": "hero1a2b3", "element": "section", "blockName": "hero",
                "children": [
                    {
                        "blockId": "h1abc1234", "element": "h1", "children": [],
                        "innerHTML": "Best Coffee in Town",
                        "baseStyles": {"color": "#ffffff", "fontSize": "48px", "fontWeight": "bold", "textAlign": "center"},
                        "mobileStyles": {"fontSize": "32px"}, "tabletStyles": {}, "rawStyles": {}, "attributes": {}, "classes": [],
                        "dataKey": None, "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    }
                ],
                "baseStyles": {"alignItems": "center", "display": "flex", "flexDirection": "column", "justifyContent": "center", "paddingBottom": "120px", "paddingTop": "120px", "width": "100%", "backgroundColor": "#111111"},
                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {}, "attributes": {}, "classes": [],
                "dataKey": None, "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                "props": {}, "customAttributes": {}, "activeState": None
            }
        ],
        "baseStyles": {"alignItems": "center", "backgroundColor": "#f8f8f8", "display": "flex", "flexDirection": "column", "flexShrink": 0, "position": "relative"},
        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {}, "attributes": {}, "classes": [],
        "dataKey": None, "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
        "props": {}, "customAttributes": {}, "activeState": None
    }]
}

MINIFIED_EXAMPLE = json.dumps(EXAMPLE_JSON, separators=(',', ':'))

SYSTEM_PROMPT = f"""You generate Frappe Builder page JSON from a text description.

CRITICAL RULES:
1. Output VALID JSON ONLY. No markdown fences, no explanations.
2. Use the exact keys, baseStyles format, and nesting shown in this example:
{MINIFIED_EXAMPLE}
3. Add all sections requested by the user as sibling blocks inside the root "children" array.
4. Every block must have a unique 9-char alphanumeric blockId.
5. Apply proper colors, padding, and layout in baseStyles. Never leave baseStyles empty for visible elements."""

DEFAULT_BLOCK = {
    "blockId": "", "element": "div", "children": [], "innerHTML": "",
    "baseStyles": {}, "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
    "attributes": {}, "classes": [], "dataKey": None, "dynamicValues": [],
    "blockClientScript": "", "blockDataScript": "",
    "props": {}, "customAttributes": {}, "activeState": None
}

ROOT_STYLES = {
    "alignItems": "center", "display": "flex", "flexDirection": "column",
    "flexShrink": 0, "position": "relative"
}


def random_id():
    return uuid.uuid4().hex[:9]


def clean(text):
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text.strip()


def fix_block(block, seen):
    result = dict(DEFAULT_BLOCK)
    result.update(block)
    if not result["blockId"] or result["blockId"] in seen:
        result["blockId"] = random_id()
    seen.add(result["blockId"])
    if isinstance(result.get("children"), list):
        result["children"] = [fix_block(c, seen) for c in result["children"] if isinstance(c, dict)]
    else:
        result["children"] = []
    return result


def validate(page_data):
    if "page_title" not in page_data:
        page_data["page_title"] = "Generated Page"

    if "root" in page_data and isinstance(page_data["root"], dict):
        page_data["blocks"] = [page_data["root"]]
    elif page_data.get("blockId") == "root" and page_data.get("children"):
        page_data["blocks"] = [page_data]

    blocks = page_data.get("blocks", [])
    if isinstance(blocks, str):
        try:
            blocks = json.loads(blocks)
        except:
            blocks = []

    if not blocks:
        blocks = [{"blockId": "root", "element": "div", "children": []}]

    if blocks[0].get("blockId") != "root":
        blocks = [{
            "blockId": "root", "element": "div", "originalElement": "body",
            "draggable": False, "children": blocks,
            "baseStyles": ROOT_STYLES.copy(),
            "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
            "attributes": {}, "classes": [], "dataKey": None, "dynamicValues": [],
            "blockClientScript": "", "blockDataScript": "",
            "props": {}, "customAttributes": {}, "activeState": None
        }]

    seen = set()
    page_data["blocks"] = [fix_block(b, seen) for b in blocks]
    return page_data


def call_ollama(prompt):
    res = requests.post(OLLAMA_URL, json={
        "model": MODEL, "prompt": prompt, "system": SYSTEM_PROMPT,
        "format": "json", "stream": False, "options": {"temperature": 0.3}
    }, timeout=120)
    res.raise_for_status()
    return res.json()["response"]


def call_groq(prompt, api_key):
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=8000,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content


def call_openai(prompt, api_key):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3, max_tokens=8000
    )
    return response.choices[0].message.content


def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}
    }
    res = requests.post(url, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def run_llm(prompt, provider, api_key):
    if provider == "Groq" and api_key:
        return call_groq(prompt, api_key)
    elif provider == "OpenAI" and api_key:
        return call_openai(prompt, api_key)
    elif provider == "Gemini" and api_key:
        return call_gemini(prompt, api_key)
    else:
        return call_ollama(prompt)


@frappe.whitelist(allow_guest=True)
def generate_page(description: str, provider: str = "Local Ollama", api_key: str | None = None):
    try:
        prompt = f"Description: {description}. Include proper sections, colors, and layout."
        raw = run_llm(prompt, provider, api_key)
        data = json.loads(clean(raw))
        return {"ok": True, "page": validate(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def import_page(page_data: str):
    try:
        data = json.loads(page_data)
        blocks = data.get("blocks", [])
        raw_title = data.get("page_title", "Generated Page")
        safe_route = re.sub(r'[\W_]+', '-', raw_title.lower()).strip('-') + "-" + uuid.uuid4().hex[:6]
        doc = frappe.get_doc({
            "doctype": "Builder Page",
            "title": raw_title,
            "page_title": raw_title,
            "route": safe_route,
            "published": 1,
            "blocks": json.dumps(blocks) if isinstance(blocks, list) else blocks
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"ok": True, "name": doc.name}
    except Exception as e:
        frappe.log_error(title="AI Builder Import Error", message=frappe.get_traceback())
        return {"ok": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def refine_page(page_name: str, page_data: str, refinement: str, provider: str = "Local Ollama", api_key: str | None = None):
    try:
        current = json.loads(page_data)
        minified_json = json.dumps(current, separators=(',', ':'))
        prompt = (
            f"Existing JSON:\n{minified_json}\n\n"
            f"Instruction: {refinement}\n"
            "Keep ALL existing sections intact. Only change what is asked. "
            "Return the complete updated JSON only."
        )
        raw = run_llm(prompt, provider, api_key)
        updated = json.loads(clean(raw))
        updated = validate(updated)
        doc = frappe.get_doc("Builder Page", page_name)
        blocks = updated.get("blocks", [])
        doc.blocks = json.dumps(blocks) if isinstance(blocks, list) else blocks
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"ok": True, "page": updated}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_status():
    ollama_ok = False
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except:
        pass
    return {"ollama": ollama_ok, "frappe": True}