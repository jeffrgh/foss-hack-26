

import json
import re
import uuid
import jsonschema


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

BLOCK_SCHEMA = {
    "type": "object",
    "required": ["blockId", "element", "children"],
    "properties": {
        "blockId":            {"type": "string", "minLength": 1},
        "element":            {"type": "string", "minLength": 1},
        "children":           {"type": "array"},
        "innerHTML":          {"type": "string"},
        "blockName":          {"type": "string"},
        "baseStyles":         {"type": "object"},
        "mobileStyles":       {"type": "object"},
        "tabletStyles":       {"type": "object"},
        "rawStyles":          {"type": "object"},
        "attributes":         {"type": "object"},
        "classes":            {"type": "array"},
        "dataKey":            {},
        "dynamicValues":      {"type": "array"},
        "blockClientScript":  {"type": "string"},
        "blockDataScript":    {"type": "string"},
        "props":              {"type": "object"},
        "customAttributes":   {"type": "object"},
        "activeState":        {},
    }
}

PAGE_SCHEMA = {
    "type": "object",
    "required": ["page_title", "blocks"],
    "properties": {
        "page_title": {"type": "string", "minLength": 1},
        "route":      {"type": "string"},
        "published":  {"type": "integer"},
        "blocks": {
            "type": "array",
            "minItems": 1,
            "items": BLOCK_SCHEMA
        }
    }
}


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_BLOCK = {
    "blockId":           "",
    "element":           "div",
    "children":          [],
    "innerHTML":         "",
    "baseStyles":        {},
    "mobileStyles":      {},
    "tabletStyles":      {},
    "rawStyles":         {},
    "attributes":        {},
    "classes":           [],
    "dataKey":           None,
    "dynamicValues":     [],
    "blockClientScript": "",
    "blockDataScript":   "",
    "props":             {},
    "customAttributes":  {},
    "activeState":       None,
}

ROOT_STYLES = {
    "alignItems":    "center",
    "display":       "flex",
    "flexDirection": "column",
    "flexShrink":    0,
    "position":      "relative",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_id() -> str:
    return uuid.uuid4().hex[:9]


def strip_fences(text: str) -> str:
    """Remove markdown code fences and any surrounding prose."""
    text = text.strip()

    # If there's a ```json ... ``` block, extract just that
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Otherwise strip leading/trailing fences
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def extract_json(text: str):
    """
    Try multiple strategies to get a parseable JSON string from raw LLM output.
    Returns (parsed_object, strategy_used) or raises ValueError.
    """
    # 1. Direct parse after fence stripping
    cleaned = strip_fences(text)
    try:
        return json.loads(cleaned), "direct"
    except json.JSONDecodeError:
        pass

    # 2. Find first {...} blob (handles preamble prose)
    obj_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group()), "extracted_object"
        except json.JSONDecodeError:
            pass

    # 3. Find first [...] array (LLM returned bare array)
    arr_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group()), "extracted_array"
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON found in LLM output")


# ---------------------------------------------------------------------------
# Block repair
# ---------------------------------------------------------------------------

def coerce_styles(val) -> dict:
    """If styles is a string or None, return {}. Otherwise return as-is if dict."""
    if isinstance(val, dict):
        return val
    return {}


def fix_block(block: dict, seen: set) -> dict:
    """Recursively repair a single block dict."""
    result = dict(DEFAULT_BLOCK)
    result.update(block)

    # Rename "styles" → "baseStyles" (common LLM mistake)
    if "styles" in result and "baseStyles" not in block:
        result["baseStyles"] = result.pop("styles")

    # Ensure element is a non-empty string
    if not isinstance(result.get("element"), str) or not result["element"]:
        result["element"] = "div"

    # Ensure innerHTML is a string
    if not isinstance(result.get("innerHTML"), str):
        result["innerHTML"] = ""

    # Ensure all style fields are dicts
    for style_key in ("baseStyles", "mobileStyles", "tabletStyles", "rawStyles"):
        result[style_key] = coerce_styles(result.get(style_key))

    # Ensure list fields are lists
    for list_key in ("classes", "dynamicValues"):
        if not isinstance(result.get(list_key), list):
            result[list_key] = []

    # Ensure string fields are strings
    for str_key in ("blockClientScript", "blockDataScript"):
        if not isinstance(result.get(str_key), str):
            result[str_key] = ""

    # Ensure dict fields are dicts
    for dict_key in ("attributes", "props", "customAttributes"):
        if not isinstance(result.get(dict_key), dict):
            result[dict_key] = {}

    # Fix blockId: missing, empty, or duplicate → new random id
    bid = result.get("blockId")
    if not bid or not isinstance(bid, str) or bid in seen:
        result["blockId"] = random_id()
    seen.add(result["blockId"])

    # Recurse children, skip non-dict items
    if isinstance(result.get("children"), list):
        result["children"] = [
            fix_block(c, seen)
            for c in result["children"]
            if isinstance(c, dict)
        ]
    else:
        result["children"] = []

    return result


# ---------------------------------------------------------------------------
# Page repair
# ---------------------------------------------------------------------------

def repair(page_data, warnings: list) -> dict:
    """
    Repair a parsed (but potentially invalid) page dict in-place.
    Appends human-readable warnings for each fix applied.
    Returns repaired page_data.
    """
    # Handle bare array: LLM returned [...] instead of {"blocks": [...]}
    if isinstance(page_data, list):
        warnings.append("LLM returned bare array — wrapping as blocks")
        page_data = {"page_title": "Generated Page", "blocks": page_data}

    # Rename "name" → "page_title"
    if "name" in page_data and "page_title" not in page_data:
        warnings.append('renamed "name" → "page_title"')
        page_data["page_title"] = page_data.pop("name")

    # Ensure page_title exists and is a non-empty string
    if not isinstance(page_data.get("page_title"), str) or not page_data["page_title"]:
        warnings.append("missing or invalid page_title — using default")
        page_data["page_title"] = "Generated Page"

    # Ensure blocks exists
    if "blocks" not in page_data:
        warnings.append("missing blocks field — inserting empty root")
        page_data["blocks"] = []

    # Decode blocks if it's a JSON string (Frappe sometimes stores it stringified)
    blocks = page_data["blocks"]
    if isinstance(blocks, str):
        try:
            blocks = json.loads(blocks)
            warnings.append("decoded blocks from JSON string")
        except json.JSONDecodeError:
            warnings.append("blocks is invalid JSON string — resetting to empty root")
            blocks = []

    # Ensure blocks is actually a list
    if not isinstance(blocks, list):
        warnings.append(f"blocks is {type(blocks).__name__}, not array — resetting")
        blocks = []

    # Ensure non-empty
    if not blocks:
        warnings.append("blocks is empty — inserting default root")
        blocks = [{"blockId": "root", "element": "div", "children": []}]

    # Wrap in root if missing
    if blocks[0].get("blockId") != "root":
        warnings.append("no root block found — wrapping all blocks in root")
        blocks = [{
            "blockId":       "root",
            "element":       "div",
            "originalElement": "body",
            "draggable":     False,
            "children":      blocks,
            "baseStyles":    ROOT_STYLES,
        }]

    # Recursively fix all blocks
    seen: set = set()
    page_data["blocks"] = [fix_block(b, seen) for b in blocks]

    return page_data


# ---------------------------------------------------------------------------
# Schema validation (post-repair)
# ---------------------------------------------------------------------------

def schema_validate(page_data: dict) -> list[str]:
    """
    Run jsonschema validation on the repaired page.
    Returns a list of validation error messages (empty = fully valid).
    Note: only validates top-level block structure, not deep children,
    since jsonschema doesn't recurse into children automatically.
    """
    errors = []
    try:
        jsonschema.validate(instance=page_data, schema=PAGE_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema: {e.message} (path: {' → '.join(str(p) for p in e.absolute_path)})")
    except jsonschema.SchemaError as e:
        errors.append(f"internal schema error: {e.message}")
    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(page_data: dict) -> tuple[dict, list[str]]:
    """
    Validate and auto-repair an already-parsed page dict.
    Returns (repaired_page, warnings).
    Called directly from app.py / pipeline.py with a dict.
    """
    warnings: list[str] = []
    page_data = repair(page_data, warnings)
    schema_errors = schema_validate(page_data)
    if schema_errors:
        warnings.extend(schema_errors)
    return page_data, warnings


def process(raw_output: str) -> tuple[dict | None, list[str], str | None]:
    """
    Full pipeline: raw LLM string → validated + repaired page dict.
    Returns (page_data, warnings, error_message).
    error_message is None on success.
    Called from app.py with raw string output.
    """
    warnings: list[str] = []

    try:
        data, strategy = extract_json(raw_output)
    except ValueError as e:
        return None, warnings, str(e)

    if strategy != "direct":
        warnings.append(f"JSON extracted using strategy: {strategy}")

    fixed, repair_warnings = validate(data)
    warnings.extend(repair_warnings)
    return fixed, warnings, None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    TESTS = {
        "clean input": '''{
  "page_title": "Coffee Shop",
  "blocks": [{"blockId": "root", "element": "div", "children": [
    {"blockId": "hero1", "element": "section", "innerHTML": "<p>Welcome</p>",
     "children": [], "baseStyles": {"backgroundColor": "#1a1a1a"}}
  ]}]
}''',

        "markdown fences": '''```json
{
  "page_title": "Coffee Shop",
  "blocks": [{"blockId": "root", "element": "div", "children": []}]
}
```''',

        "prose preamble": '''Sure! Here is the JSON for your page:
{
  "page_title": "My Site",
  "blocks": [{"blockId": "root", "element": "div", "children": []}]
}
Let me know if you need changes!''',

        "bare array (LLM skipped wrapper)": '''[
  {"blockId": "root", "element": "div", "children": [
    {"blockId": "h1block", "element": "h1", "innerHTML": "Hello", "children": []}
  ]}
]''',

        '"name" instead of "page_title"': '''{
  "name": "my-page",
  "blocks": [{"blockId": "root", "element": "div", "children": []}]
}''',

        '"styles" instead of "baseStyles"': '''{
  "page_title": "Test",
  "blocks": [{"blockId": "root", "element": "div", "children": [
    {"blockId": "x1", "element": "h1", "innerHTML": "Hi",
     "styles": {"color": "red", "fontSize": "32px"}, "children": []}
  ]}]
}''',

        "duplicate blockIds": '''{
  "page_title": "Dupe Test",
  "blocks": [{"blockId": "root", "element": "div", "children": [
    {"blockId": "abc", "element": "p", "innerHTML": "First",  "children": []},
    {"blockId": "abc", "element": "p", "innerHTML": "Second", "children": []}
  ]}]
}''',

        "missing blockIds entirely": '''{
  "page_title": "No IDs",
  "blocks": [{"element": "div", "children": [
    {"element": "h1", "innerHTML": "Title", "children": []},
    {"element": "p",  "innerHTML": "Body",  "children": []}
  ]}]
}''',

        "missing root block (auto-wrap)": '''{
  "page_title": "No Root",
  "blocks": [
    {"blockId": "sec1", "element": "section", "innerHTML": "", "children": []},
    {"blockId": "sec2", "element": "footer",  "innerHTML": "", "children": []}
  ]
}''',

        "blocks as JSON string": '''{
  "page_title": "Stringified",
  "blocks": "[{\\"blockId\\": \\"root\\", \\"element\\": \\"div\\", \\"children\\": []}]"
}''',

        "completely broken output": "Here is your page! I generated something great for you.",

        # Real LLM output — Llama 3.1 via Ollama, prompt: "coffee shop landing page with dark hero, tagline, and order now button"
        "real LLM output: coffee shop (clean)": '{"page_title":"Coffee Shop","blocks":[{"blockId":"root","element":"div","originalElement":"body","draggable":false,"children":[{"blockId":"1b30ourvn","element":"header","blockName":"navbar","children":[],"baseStyles":{"alignItems":"center","display":"flex","flexDirection":"row","justifyContent":"center","width":"100%"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null},{"blockId":"y172bydtd","element":"section","blockName":"hero","children":[{"blockId":"e3q1ren1n","element":"div","blockName":"container","children":[{"blockId":"xnedtn8n5","element":"h1","children":[],"innerHTML":"Expertly crafted coffee","baseStyles":{"color":"#FFF","fontSize":"48px","fontWeight":"700","lineHeight":"104%","maxWidth":"450px","textAlign":"center"},"mobileStyles":{"fontSize":"34px"},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null},{"blockId":"la28139uz","element":"p","children":[],"innerHTML":"<p>Experience the rich flavors of our expertly roasted coffee.</p>","baseStyles":{"color":"#FFF","fontSize":"16px","maxWidth":"350px","textAlign":"center"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null},{"blockId":"tfewi8dhz","element":"div","blockName":"actions","children":[{"blockId":"o12wwgkuj","element":"a","blockName":"get-started","children":[{"blockId":"0r1vo5jrc","element":"p","children":[],"innerHTML":"<p>Order Now</p>","baseStyles":{"color":"#FFF","fontSize":"14px"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}],"attributes":{"href":"/order-now"},"baseStyles":{"alignItems":"center","backgroundColor":"#333","borderRadius":"12px","display":"flex","justifyContent":"center","paddingBottom":"12px","paddingLeft":"14px","paddingRight":"14px","paddingTop":"12px"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}],"baseStyles":{"display":"flex","flexDirection":"row","gap":"12px","marginTop":"26px"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}],"baseStyles":{"alignItems":"center","display":"flex","flexDirection":"column","justifyContent":"center","width":"100%"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}],"baseStyles":{"alignItems":"center","display":"flex","flexDirection":"column","justifyContent":"center","width":"100%"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}],"baseStyles":{"alignItems":"center","display":"flex","flexDirection":"column","flexShrink":0,"position":"relative"},"mobileStyles":{},"tabletStyles":{},"rawStyles":{},"classes":[],"dataKey":null,"dynamicValues":[],"blockClientScript":"","blockDataScript":"","props":{},"customAttributes":{},"activeState":null}]}',
    }

    passed = 0
    failed = 0

    for name, raw in TESTS.items():
        result, warnings, err = process(raw)
        status = "PASS" if result is not None else "FAIL"
        if result is not None:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] {name}")
        if warnings:
            for w in warnings:
                print(f"       ⚠  {w}")
        if err:
            print(f"       ✗  error: {err}")
        if result:
            # Quick sanity checks
            assert isinstance(result.get("page_title"), str), "page_title must be str"
            assert isinstance(result.get("blocks"), list),    "blocks must be list"
            assert result["blocks"][0]["blockId"] == "root",  "first block must be root"
            print(f"       ✓  {result['page_title']} | {len(result['blocks'])} top-level block(s)")
        print()

    print(f"Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")
    sys.exit(0 if failed == 0 else 1)
