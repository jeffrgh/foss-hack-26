# Frappe Builder JSON Schema

## Page fields
```json
{
  "page_title": "My Page",
  "route": "pages/some-slug",
  "published": 1,
  "blocks": [...]
}
```

## Every block looks like this
```json
{
  "blockId": "abc123xyz",
  "element": "div",
  "children": [],
  "innerHTML": "",
  "blockName": "hero",
  "baseStyles": {},
  "mobileStyles": {},
  "tabletStyles": {},
  "rawStyles": {},
  "attributes": {},
  "classes": [],
  "dataKey": null,
  "dynamicValues": [],
  "blockClientScript": "",
  "blockDataScript": "",
  "props": {},
  "customAttributes": {},
  "activeState": null
}
```

## Root block (always first, always blockId "root")
```json
{
  "blockId": "root",
  "element": "div",
  "originalElement": "body",
  "draggable": false,
  "children": [...],
  "baseStyles": {
    "alignItems": "center",
    "display": "flex",
    "flexDirection": "column",
    "flexShrink": 0,
    "position": "relative"
  }
}
```

## Common elements

**section** - used for hero, footer, navbar etc
**div** - generic container
**h1, h2, p** - text blocks (use innerHTML for content)
**a** - links and buttons (set href in attributes)
**button** - clickable button
**input** - form fields (set placeholder in attributes)

## Text content
Use innerHTML for text. Wrap in p tags:
```json
"innerHTML": "<p>Your text here</p>"
```

## Styles
baseStyles = desktop CSS as camelCase keys:
```json
"baseStyles": {
  "display": "flex",
  "flexDirection": "column",
  "alignItems": "center",
  "backgroundColor": "#171717",
  "color": "#ffffff",
  "fontSize": "48px",
  "fontWeight": "bold",
  "padding": "20px",
  "borderRadius": "8px",
  "gap": "12px",
  "width": "100%"
}
```

## Important rules
1. blockId must be unique across all blocks (9 random chars)
2. Even leaf nodes need `"children": []`
3. blocks field in the page is stored as a JSON string
4. Don't duplicate blockIds or Frappe will break
