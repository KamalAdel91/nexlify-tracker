import json

import frappe


@frappe.whitelist()
def get_universal_tracker_config(doctype: str, docname: str | None = None) -> dict:
	"""The Business Process panel of a form: the Workflow's steps and where the document stands.

	Steps are the Workflow's states in order. States styled "Danger" (On Hold, Cancelled...) are side exits,
	not steps: one shows only while the document is in it, right after the step it left from.
	Each step carries its status (done, current, exit, skipped, todo) and, once done, who finished it and when.
	"""
	frappe.has_permission(doctype, "read", doc=docname, throw=True)

	workflow = frappe.db.get_value(
		"Workflow", {"document_type": doctype, "is_active": 1}, ["name", "workflow_state_field"], as_dict=True
	)
	if not workflow:
		return {"error": "No active workflow found"}

	workflow_field = workflow.workflow_state_field or "workflow_state"
	tasks = []
	config = frappe.db.get_value(
		"Nexlify Tracker",
		{"nexlify_tracker_document_type": doctype, "nexlify_tracker_is_active": 1},
		["name", "nexlify_tracker_workflow_field"],
		as_dict=True,
	)
	if config:
		field = config.nexlify_tracker_workflow_field
		if field and frappe.get_meta(doctype).has_field(field):
			workflow_field = field
		tasks = [
			{
				"stage": t.nexlify_tracker_task_stage,
				"task": t.nexlify_tracker_task_description,
				"field_name": t.nexlify_tracker_task_field_name,
				"link_field_name": t.nexlify_tracker_task_link_field_name,
				"link_doc_type": t.nexlify_tracker_task_link_doc_type,
			}
			for t in frappe.get_all(
				"Nexlify Tracker Task",
				filters={"parent": config.name, "parenttype": "Nexlify Tracker"},
				fields=[
					"nexlify_tracker_task_stage",
					"nexlify_tracker_task_description",
					"nexlify_tracker_task_field_name",
					"nexlify_tracker_task_link_field_name",
					"nexlify_tracker_task_link_doc_type",
				],
				order_by="idx asc",
			)
		]

	order = list(
		dict.fromkeys(
			frappe.get_all(
				"Workflow Document State",
				filters={"parent": workflow.name, "parenttype": "Workflow"},
				order_by="idx asc",
				pluck="state",
			)
		)
	)
	styles = dict(
		frappe.get_all("Workflow State", filters={"name": ("in", order)}, fields=["name", "style"], as_list=True)
	) if order else {}
	side_exits = {s for s in order if styles.get(s) == "Danger"}
	steps = [s for s in order if s not in side_exits]

	# Moves of the state field, from the document's Versions: each change is [field, old, new].
	moves = []
	if docname:
		versions = frappe.get_all(
			"Version",
			filters={"ref_doctype": doctype, "docname": docname, "data": ("like", f'%"{workflow_field}"%')},
			fields=["owner", "creation", "data"],
			order_by="creation asc",
		)
		for version in versions:
			try:
				changed = json.loads(version.data).get("changed") or []
			except ValueError:
				continue
			for change in changed:
				if len(change) > 2 and change[0] == workflow_field and change[1] != change[2]:
					moves.append(frappe._dict(left=change[1], to=change[2], user=version.owner, on=version.creation))
	current = frappe.db.get_value(doctype, docname, workflow_field) if docname else None

	# The states the document was in, oldest first (what was set without a Version is missing).
	timeline = ([moves[0].left] if moves else []) + [m.to for m in moves]

	path = list(steps)
	if current in side_exits:
		came_from = next((s for s in reversed(timeline) if s in steps), None) or next(
			(
				s
				for s in steps
				if frappe.db.exists(
					"Workflow Transition", {"parent": workflow.name, "state": s, "next_state": current}
				)
			),
			None,
		)
		at = path.index(came_from) + 1 if came_from else sum(1 for s in order[: order.index(current)] if s in steps)
		path.insert(at, current)

	now = path.index(current) if current in path else -1
	# Skipped steps are told apart only when every recorded state is a known one (a Select field is stored translated).
	complete = bool(moves) and all(s in order for s in timeline)
	passed = set(timeline) | set(steps[:1])

	stages = []
	for i, state in enumerate(path):
		move = None
		if now < 0 or i > now:
			status = "todo"
		elif i < now:
			status = "done" if not complete or state in passed else "skipped"
			move = next((m for m in reversed(moves) if m.left == state), None)
		else:
			status = "exit" if state in side_exits else ("done" if state == steps[-1] else "current")
			if status != "current":
				move = next((m for m in reversed(moves) if m.to == state), None)
		stages.append({"state": state, "status": status, "user": move.user if move else None, "on": move.on if move else None})

	users = {s["user"] for s in stages if s["user"]}
	info = {
		u.name: u
		for u in frappe.get_all("User", filters={"name": ("in", list(users))}, fields=["name", "full_name", "user_image"])
	} if users else {}
	for s in stages:
		u = info.get(s["user"]) or {}
		s["full_name"] = u.get("full_name") or s["user"]
		s["user_image"] = u.get("user_image") or ""

	return {"stages": stages, "workflow_field": workflow_field, "tasks": tasks}
