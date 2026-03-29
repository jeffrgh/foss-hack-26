app_name = "ai_page_builder"
app_title = "AI Page Builder"
app_publisher = "Abhinav Krishna"
app_description = "Generate Frappe Builder pages from natural language using AI"
app_email = "63704645+immessy@users.noreply.github.com"
app_license = "mit"

# Apps Screen Configuration

add_to_apps_screen = [
    {
        "name": "ai_page_builder",
        "logo": "/assets/ai_page_builder/logo.png",
        "title": "AI Page Builder",
        "route": "/ai-page-builder",
        "has_permission": "ai_page_builder.api.generate.has_app_permission"
    }
]

# Website Routes

website_route_rules = [
    {"from_route": "/ai-page-builder", "to_route": "ai-page-builder"},
]

# Static Assets

app_include_js = "/assets/ai_page_builder/js/ai_page_builder.js"

# Type Safety & Standards

export_python_type_annotations = True
require_type_annotated_api_methods = True