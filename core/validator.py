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

ROOT_BASE_STYLES = {
    "alignItems": "center",
    "display": "flex",
    "flexDirection": "column",
    "flexShrink": 0,
    "position": "relative"
}

# Fields that must exist on every block (missing ones get defaulted + warned)
REQUIRED_FIELDS = set(DEFAULT_BLOCK.keys())

# Fields that are non-string scalars and must not be coerced
ARRAY_FIELDS = {"children", "classes", "dynamicValues"}
DICT_FIELDS = {"baseStyles", "mobileStyles", "tabletStyles", "rawStyles", "attributes", "props", "customAttributes"}


def random_id():
    return uuid.uuid4().hex[:9]


def strip_fences(text):
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def fix_block(block, seen, warnings):
    result = dict(DEFAULT_BLOCK)
    result.update(block)

    # FIX 1: missing innerHTML on container blocks — warn so we know it happened
    if "innerHTML" not in block:
        warnings.append(f"block '{block.get('blockId', '?')}' missing innerHTML, defaulting to ''")

    # FIX 2: dict/array fields that arrived as wrong type
    for field in DICT_FIELDS:
        if not isinstance(result.get(field), dict):
            warnings.append(f"block '{result.get('blockId','?')}'.{field} is not a dict, resetting")
            result[field] = {}
    for field in ARRAY_FIELDS - {"children"}:
        if not isinstance(result.get(field), list):
            warnings.append(f"block '{result.get('blockId','?')}'.{field} is not a list, resetting")
            result[field] = []

    # FIX 3: duplicate or missing blockId
    if not result["blockId"] or result["blockId"] in seen:
        old_id = result["blockId"]
        result["blockId"] = random_id()
        warnings.append(f"duplicate/missing blockId '{old_id}' replaced with '{result['blockId']}'")
    seen.add(result["blockId"])

    # FIX 4: children must be a list of dicts
    if isinstance(result.get("children"), list):
        result["children"] = [
            fix_block(c, seen, warnings)
            for c in result["children"]
            if isinstance(c, dict)
        ]
    else:
        if result.get("children") is not None:
            warnings.append(f"block '{result['blockId']}' children is not a list, resetting")
        result["children"] = []

    return result


def validate(page_data):
    warnings = []

    # FIX 5: missing blocks field entirely
    if "blocks" not in page_data:
        warnings.append("missing blocks field")
        page_data["blocks"] = [{"blockId": "root", "element": "div", "children": []}]

    if "page_title" not in page_data:
        page_data["page_title"] = "Generated Page"

    blocks = page_data["blocks"]

    # FIX 6: blocks is a JSON string instead of a list
    if isinstance(blocks, str):
        try:
            blocks = json.loads(blocks)
        except json.JSONDecodeError:
            warnings.append("blocks is invalid JSON string, resetting")
            blocks = [{"blockId": "root", "element": "div", "children": []}]

    if not blocks:
        blocks = [{"blockId": "root", "element": "div", "children": []}]

    # FIX 7: root block missing required style fields (e.g. pricing_page pattern)
    first = blocks[0] if isinstance(blocks[0], dict) else {}
    if first.get("blockId") == "root":
        patched = False
        if not isinstance(first.get("baseStyles"), dict) or not first.get("baseStyles"):
            first["baseStyles"] = ROOT_BASE_STYLES.copy()
            patched = True
        for field in ("mobileStyles", "tabletStyles", "rawStyles"):
            if not isinstance(first.get(field), dict):
                first[field] = {}
                patched = True
        for field in ("classes", "dynamicValues"):
            if not isinstance(first.get(field), list):
                first[field] = []
                patched = True
        if patched:
            warnings.append("root block missing style/meta fields, patched with defaults")

    # FIX 8: no root wrapper — wrap all blocks under a new root
    if blocks[0].get("blockId") != "root":
        warnings.append("wrapping blocks in root")
        blocks = [{
            "blockId": "root",
            "element": "div",
            "originalElement": "body",
            "draggable": False,
            "children": blocks,
            "baseStyles": ROOT_BASE_STYLES.copy(),
            "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
            "classes": [], "dataKey": None, "dynamicValues": [],
            "blockClientScript": "", "blockDataScript": "",
            "props": {}, "customAttributes": {}, "activeState": None
        }]

    seen = set()
    page_data["blocks"] = [fix_block(b, seen, warnings) for b in blocks]
    print("no errors discovered,validation succesfull!!!!!")
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
            except Exception:
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
