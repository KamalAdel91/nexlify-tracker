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
# a .bundle.js gets a hashed file name on every build, so browsers never keep an old copy
app_include_js = "nexlify_tracker.bundle.js"

# --- Permissions (empty for now) ---
has_permission = {}

export_python_type_annotations = True
require_type_annotated_api_methods = True

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "Nexlify Tracker"]]
    },
    {
        "doctype": "Server Script",
        "filters": [["module", "=", "Nexlify Tracker"]]
    },
    {
        "doctype": "Client Script",
        "filters": [["module", "=", "Nexlify Tracker"]]
    },
    {
        "doctype": "Property Setter",
        "filters": [["module", "=", "Nexlify Tracker"]]
    }
]