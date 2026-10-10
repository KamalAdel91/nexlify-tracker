from typing import Optional, Dict, Any
import json

import frappe
from frappe import _


@frappe.whitelist()
def get_universal_tracker_config(
    doctype: str,
    docname: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns workflow stages, history,
    and optionally tasks from Nexlify Tracker config.

    Works even if no Nexlify Tracker record exists.
    """

    # ---------------------------------------------------
    # 1. Get active workflow
    # ---------------------------------------------------
    workflow = frappe.db.get_value(
        "Workflow",
        {
            "document_type": doctype,
            "is_active": 1
        },
        ["name", "workflow_state_field"],
        as_dict=True
    )
    workflow_name = workflow.name if workflow else None

    if not workflow_name:
        return {
            "error": "No active workflow found"
        }

    # ---------------------------------------------------
    # 2. Get workflow stages in order
    # ---------------------------------------------------
    stages = frappe.get_all(
        "Workflow Document State",
        filters={
            "parent": workflow_name
        },
        fields=["state"],
        order_by="idx asc"
    )

    # One entry per state, in order. States styled "Danger" (Rejected, Cancelled...)
    # are side exits, not steps, so they are not shown.
    seen = set()
    main_stages = []
    for s in stages:
        if s.state in seen:
            continue
        seen.add(s.state)
        s.side_exit = frappe.db.get_value("Workflow State", s.state, "style") == "Danger"
        main_stages.append(s)
    stages = main_stages

    # Workflow field from the Workflow itself (a Nexlify Tracker config can still override it)
    workflow_field = workflow.workflow_state_field or "workflow_state"

    # ---------------------------------------------------
    # 3. Get Nexlify Tracker config (optional)
    # ---------------------------------------------------
    tasks = []

    tracker_config = frappe.db.get_value(
        "Nexlify Tracker",
        {
            "nexlify_tracker_document_type": doctype,
            "nexlify_tracker_is_active": 1
        },
        [
            "nexlify_tracker_workflow_field",
            "name"
        ],
        as_dict=True
    )

    if tracker_config:

        if tracker_config.get("nexlify_tracker_workflow_field"):
            workflow_field = (
                tracker_config.nexlify_tracker_workflow_field
            )

        task_rows = frappe.get_all(
            "Nexlify Tracker Task",
            filters={
                "parent": tracker_config.name
            },
            fields=[
                "nexlify_tracker_task_stage",
                "nexlify_tracker_task_description",
                "nexlify_tracker_task_field_name",
                "nexlify_tracker_task_link_field_name",
                "nexlify_tracker_task_link_doc_type"
            ],
            order_by="idx asc"
        )

        for t in task_rows:
            tasks.append({
                "stage":
                    t.get("nexlify_tracker_task_stage"),

                "task":
                    t.get("nexlify_tracker_task_description"),

                "field_name":
                    t.get("nexlify_tracker_task_field_name"),

                "link_field_name":
                    t.get("nexlify_tracker_task_link_field_name"),

                "link_doc_type":
                    t.get("nexlify_tracker_task_link_doc_type")
            })

    # ---------------------------------------------------
    # 4. Get workflow history
    # ---------------------------------------------------
    history = []

    if docname:

        versions = frappe.get_all(
            "Version",
            filters={
                "ref_doctype": doctype,
                "docname": docname
            },
            fields=[
                "owner",
                "creation",
                "data"
            ],
            order_by="creation asc"
        )

        for version in versions:

            try:
                data = json.loads(version.data)
                changed = data.get("changed", [])

                for change in changed:

                    if change[0] == workflow_field:

                        user_info = (
                            frappe.db.get_value(
                                "User",
                                version.owner,
                                [
                                    "full_name",
                                    "user_image"
                                ],
                                as_dict=True
                            )
                            or {}
                        )

                        history.append({
                            "full_name":
                                user_info.get("full_name")
                                or version.owner,

                            "user_image":
                                user_info.get("user_image")
                                or "",

                            "creation":
                                version.creation,

                            "workflow_state":
                                change[1]
                        })

            except Exception:
                pass

    # Side exits (styled "Danger": On Hold, Rejected, Cancelled...) are not steps:
    # they show only while the document is in one, or once its history went through it.
    current_state = frappe.db.get_value(doctype, docname, workflow_field) if docname else None
    visited = {h["workflow_state"] for h in history}
    stages = [{"state": s.state} for s in stages if not s.side_exit or s.state == current_state or s.state in visited]

    # ---------------------------------------------------
    # Return response
    # ---------------------------------------------------
    return {
        "stages": stages,
        "history": history,
        "workflow_field": workflow_field,
        "tasks": tasks
    }