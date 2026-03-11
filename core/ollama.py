

import requests
import json
import re
import uuid


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

SYSTEM_PROMPT = """You generate Frappe Builder page JSON from a text description.

Rules:
- respond with JSON only, no explanations, no markdown fences
- every block needs: blockId, element, children, innerHTML, baseStyles, mobileStyles, tabletStyles, rawStyles, attributes, classes, dataKey, dynamicValues, blockClientScript, blockDataScript, props, customAttributes, activeState
- blockId must be a unique 9-char alphanumeric string for every block
- root block always has blockId "root" and element "div"
- leaf nodes still need "children": []
- wrap text in innerHTML as <p> tags

Output format:
{
  "page_title": "...",
  "blocks": [
    {
      "blockId": "root",
      "element": "div",
      "originalElement": "body",
      "draggable": false,
      "children": [...],
      "baseStyles": {"alignItems": "center", "display": "flex", "flexDirection": "column", "flexShrink": 0, "position": "relative"},
      "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
      "attributes": {}, "classes": [], "dataKey": null,
      "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
      "props": {}, "customAttributes": {}, "activeState": null
    }
  ]
}"""


def random_id():
    return uuid.uuid4().hex[:9]


def call_ollama(prompt):
    res = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.3}
    }, timeout=120)
    res.raise_for_status()
    return res.json()["response"]


def clean_output(text):
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def generate_page(description):
    prompt = f"Generate a Frappe Builder page JSON for: {description}\n\nJSON only, nothing else."
    raw = call_ollama(prompt)
    cleaned = clean_output(raw)
    return json.loads(cleaned)


if __name__ == "__main__":
    desc = "a coffee shop landing page with dark hero, tagline, and order now button"
    result = generate_page(desc)
    print(json.dumps(result, indent=2))
