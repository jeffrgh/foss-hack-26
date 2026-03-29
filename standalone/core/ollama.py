
import requests
import json
import re
import uuid


from few_shot_examples import FEW_SHOT_PROMPT

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
- always include a navbar, at least one hero section, and a footer
- hero sections must have a heading, subheading, and at least one button
- use real looking placeholder content relevant to the description
- apply proper colors and spacing in baseStyles — never leave baseStyles empty on visible elements


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
    res = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=1200,
    )
    res.raise_for_status()
    return res.json()["response"]


def clean_output(text):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def enhance_prompt(description):
    return (
        f"{description}. "
        "Include: a navbar with logo and nav links, a bold hero section with heading, "
        "subheading and CTA button, relevant content sections with real placeholder text, "
        "and a footer. Apply proper colors, padding and font sizes to all elements."
    )


def generate_page(description):
    prompt = (
        f"{FEW_SHOT_PROMPT}\n\nDescription: {description}\n\nJSON only, nothing else."
    )

    raw = call_ollama(prompt)
    cleaned = clean_output(raw)
    return json.loads(cleaned)

def generate_page_groq(description, api_key):
    from groq import Groq
    client = Groq(api_key=api_key)
    prompt = f"{FEW_SHOT_PROMPT}\n\nDescription: {enhance_prompt(description)}\n\nJSON only, nothing else."
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )
    raw = response.choices[0].message.content
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    return json.loads(raw.strip())

def generate_page_openai(description, api_key):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = f"{FEW_SHOT_PROMPT}\n\nDescription: {enhance_prompt(description)}\n\nJSON only, nothing else."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )
    raw = response.choices[0].message.content
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    return json.loads(raw.strip())


def generate_page_gemini(description, api_key):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"{SYSTEM_PROMPT}\n\n{FEW_SHOT_PROMPT}\n\nDescription: {enhance_prompt(description)}\n\nJSON only, nothing else."
    response = model.generate_content(prompt)
    raw = response.text
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    return json.loads(raw.strip())


def refine_page(current_json, refinement, groq_key=None):
    current_str = json.dumps(current_json, indent=2)
    prompt = (
        f"Here is an existing Frappe Builder page JSON:\n\n{current_str}\n\n"
        f"Modify it based on this instruction: {refinement}\n\n"
        "IMPORTANT: Keep ALL existing sections and content. Only change what is specifically asked. "
        "Return the complete updated JSON only, nothing else."
    )
    if groq_key:
        from groq import Groq
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=8000
        )
        raw = response.choices[0].message.content
    else:
        raw = call_ollama(prompt)
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    return json.loads(raw.strip())

if __name__ == "__main__":
    desc = "a coffee shop landing page with dark hero, tagline, and order now button"
    result = generate_page(desc)
    print(json.dumps(result, indent=2))
