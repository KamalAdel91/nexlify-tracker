import frappe

app_name = "nexlify_tracker"
app_title = "Nexlify Tracker"
app_publisher = "Kamal Adel"
app_description = "Universal Workflow Tracker Engine for ERPNext"
app_email = "Kamal.adel@outlook.com"
app_license = "mit"

# --- Documents to sync ---
documents = ["Nexlify Tracker", "Nexlify Tracker Task"]

# --- Global JavaScript ---
app_include_js = "/assets/nexlify_tracker/js/nexlify_tracker.js"

# --- Permissions (empty for now) ---
has_permission = {}

export_python_type_annotations = True
require_type_annotated_api_methods = True

fixtures = [
    {"doctype": "Custom Field"},
    {"doctype": "Property Setter"},
    {"doctype": "Client Script"},
    {"doctype": "Server Script"},

]