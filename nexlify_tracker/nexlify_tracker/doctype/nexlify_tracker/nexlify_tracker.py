# Copyright (c) 2026, Kamal Adel and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class NexlifyTracker(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from nexlify_tracker.nexlify_tracker.doctype.nexlify_tracker_task.nexlify_tracker_task import NexlifyTrackerTask

		nexlify_tracker_document_type: DF.Link
		nexlify_tracker_is_active: DF.Check
		nexlify_tracker_tasks: DF.Table[NexlifyTrackerTask]
		nexlify_tracker_workflow_field: DF.Data | None
	# end: auto-generated types

	pass
