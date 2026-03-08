import json
import re
import uuid


DEFAULT_BLOCK = {
    "blockId": "",
    "element": "div",
    "children": [],
    "innerHTML": "",
    "baseStyles": {},
    "mobileStyles": {},
    "tabletStyles": {},
    "rawStyles": {},
    "attributes": {},
    "classes": [],
    "dataKey": None,
    "dynamicValues": [],
    "blockClientScript": "",
    "blockDataScript": "",
    "props": {},
    "customAttributes": {},
    "activeState": None
}


def random_id():
    return uuid.uuid4().hex[:9]


def strip_fences(text):
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
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
    warnings = []

    if "blocks" not in page_data:
        warnings.append("missing blocks field")
        page_data["blocks"] = [{"blockId": "root", "element": "div", "children": []}]

    if "page_title" not in page_data:
        page_data["page_title"] = "Generated Page"

    blocks = page_data["blocks"]
    if isinstance(blocks, str):
        try:
            blocks = json.loads(blocks)
        except json.JSONDecodeError:
            warnings.append("blocks is invalid JSON string, resetting")
            blocks = [{"blockId": "root", "element": "div", "children": []}]

    if not blocks:
        blocks = [{"blockId": "root", "element": "div", "children": []}]

    if blocks[0].get("blockId") != "root":
        warnings.append("wrapping blocks in root")
        blocks = [{
            "blockId": "root",
            "element": "div",
            "originalElement": "body",
            "draggable": False,
            "children": blocks,
            "baseStyles": {"alignItems": "center", "display": "flex", "flexDirection": "column", "flexShrink": 0, "position": "relative"}
        }]

    seen = set()
    page_data["blocks"] = [fix_block(b, seen) for b in blocks]
    return page_data, warnings


def process(raw_output):
    cleaned = strip_fences(raw_output)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except:
                return None, [], "could not parse JSON from output"
        else:
            return None, [], "no JSON found in output"

    fixed, warnings = validate(data)
    return fixed, warnings, None


if __name__ == "__main__":
    test = '''```json
{
  "page_title": "Coffee Shop",
  "blocks": [
    {
      "blockId": "root",
      "element": "div",
      "children": [
        {
          "blockId": "hero1",
          "element": "section",
          "children": [
            {
              "blockId": "title1",
              "element": "h1",
              "innerHTML": "Best Coffee in Town",
              "children": [],
              "baseStyles": {"color": "#fff", "fontSize": "48px"}
            }
          ],
          "baseStyles": {"backgroundColor": "#1a1a1a", "padding": "100px", "textAlign": "center"}
        }
      ],
      "baseStyles": {"display": "flex", "flexDirection": "column"}
    }
  ]
}
```'''

    result, warnings, err = process(test)
    if err:
        print("error:", err)
    else:
        if warnings:
            print("warnings:", warnings)
        print(json.dumps(result, indent=2))
