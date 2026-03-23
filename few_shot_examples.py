import json

EXAMPLE = {
    "page_title": "Coffee Shop",
    "blocks": [{
        "blockId": "root",
        "element": "div",
        "originalElement": "body",
        "draggable": False,
        "children": [
            {
                "blockId": "nav1a2b3c",
                "element": "header",
                "blockName": "navbar",
                "children": [
                    {
                        "blockId": "logo1234a",
                        "element": "p",
                        "children": [],
                        "innerHTML": "<p>Brand</p>",
                        "baseStyles": {"fontSize": "20px", "fontWeight": "bold"},
                        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                        "attributes": {}, "classes": [], "dataKey": None,
                        "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    }
                ],
                "baseStyles": {"alignItems": "center", "display": "flex", "justifyContent": "space-between", "padding": "16px 40px", "width": "100%"},
                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                "attributes": {}, "classes": [], "dataKey": None,
                "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                "props": {}, "customAttributes": {}, "activeState": None
            },
            {
                "blockId": "hero1a2b3",
                "element": "section",
                "blockName": "hero",
                "children": [
                    {
                        "blockId": "h1abc1234",
                        "element": "h1",
                        "children": [],
                        "innerHTML": "Best Coffee in Town",
                        "baseStyles": {"color": "#ffffff", "fontSize": "48px", "fontWeight": "bold", "textAlign": "center"},
                        "mobileStyles": {"fontSize": "32px"}, "tabletStyles": {}, "rawStyles": {},
                        "attributes": {}, "classes": [], "dataKey": None,
                        "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    },
                    {
                        "blockId": "para1234a",
                        "element": "p",
                        "children": [],
                        "innerHTML": "<p>Fresh brews every morning.</p>",
                        "baseStyles": {"color": "#cccccc", "fontSize": "18px", "textAlign": "center"},
                        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                        "attributes": {}, "classes": [], "dataKey": None,
                        "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    },
                    {
                        "blockId": "btn12345a",
                        "element": "a",
                        "children": [
                            {
                                "blockId": "btntext1a",
                                "element": "p",
                                "children": [],
                                "innerHTML": "<p>Order Now</p>",
                                "baseStyles": {"color": "#ffffff", "fontSize": "16px"},
                                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                                "attributes": {}, "classes": [], "dataKey": None,
                                "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                                "props": {}, "customAttributes": {}, "activeState": None
                            }
                        ],
                        "innerHTML": "",
                        "baseStyles": {"alignItems": "center", "backgroundColor": "#444444", "borderRadius": "8px", "display": "flex", "justifyContent": "center", "marginTop": "24px", "paddingBottom": "12px", "paddingLeft": "24px", "paddingRight": "24px", "paddingTop": "12px"},
                        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                        "attributes": {"href": "/order"}, "classes": [], "dataKey": None,
                        "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                        "props": {}, "customAttributes": {}, "activeState": None
                    }
                ],
                "baseStyles": {"alignItems": "center", "display": "flex", "flexDirection": "column", "justifyContent": "center", "paddingBottom": "120px", "paddingTop": "120px", "width": "100%"},
                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                "attributes": {}, "classes": [], "dataKey": None,
                "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
                "props": {}, "customAttributes": {}, "activeState": None
            }
        ],
        "baseStyles": {"alignItems": "center", "backgroundColor": "#f8f8f8", "display": "flex", "flexDirection": "column", "flexShrink": 0, "position": "relative"},
        "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
        "attributes": {}, "classes": [], "dataKey": None,
        "dynamicValues": [], "blockClientScript": "", "blockDataScript": "",
        "props": {}, "customAttributes": {}, "activeState": None
    }]
}

FEW_SHOT_PROMPT = f"""Here is a real example of valid Frappe Builder page JSON. Follow this exact structure:

{json.dumps({"page_title": EXAMPLE["page_title"], "blocks": EXAMPLE["blocks"]}, indent=2)}

Now generate a similar JSON for the description below. Use the same block structure, required fields, and style patterns. JSON only, nothing else:

"""

if __name__ == "__main__":
    print(f"Prompt length: {len(FEW_SHOT_PROMPT)} chars")