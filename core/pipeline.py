import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ollama import generate_page
from core.validator import validate
from core.frappe_api import import_page, get_session


def run(description, import_to_frappe=False):
    try:
        page_data = generate_page(description)
    except Exception as e:
        return {"ok": False, "error": f"generation failed: {e}"}

    page_data, warnings = validate(page_data)
    result = {"ok": True, "page": page_data, "warnings": warnings}

    if import_to_frappe:
        try:
            imported = import_page(page_data, get_session())
            result["imported"] = imported
        except Exception as e:
            result["import_error"] = str(e)

    return result


if __name__ == "__main__":
    import json
    res = run("a coffee shop landing page with dark hero and order button", import_to_frappe=False)
    print(json.dumps(res, indent=2))