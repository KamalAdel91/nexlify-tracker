# Copyright (c) 2026, Kamal Adel and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class NexlifyTrackerTask(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		nexlify_tracker_task_description: DF.Data | None
		nexlify_tracker_task_field_name: DF.Data | None
		nexlify_tracker_task_link_doc_type: DF.Link | None
		nexlify_tracker_task_link_field_name: DF.Data | None
		nexlify_tracker_task_stage: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
