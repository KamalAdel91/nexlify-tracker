// nexlify_tracker.js - Business Process panel on every form whose DocType has an active Workflow.
// The server decides each step's status (done, current, exit, skipped, todo); this file only draws it.
frappe.provide("nexlify_tracker");

Object.assign(nexlify_tracker, {
	COLORS: { done: "#28a745", current: "#1a73e8", exit: "#e53e3e" },
	ICONS: { done: "✓", skipped: "–", exit: "!" },

	schedule(frm) {
		clearTimeout(frm._nexlify_tracker_timer);
		frm._nexlify_tracker_timer = setTimeout(() => nexlify_tracker.load(frm), 100);
	},

	load(frm) {
		const $old = () => $(frm.wrapper).find(".nexlify-smart-tracker");
		// The form already carries its Workflow: no server call for DocTypes without one.
		if (frm.is_new() || !frappe.workflow.get_state_fieldname(frm.doctype)) {
			$old().remove();
			return;
		}
		const docname = frm.doc.name;
		frappe.call({
			method: "nexlify_tracker.api.get_universal_tracker_config",
			args: { doctype: frm.doctype, docname },
			callback(r) {
				if (frm.doc.name !== docname) return;
				$old().remove();
				if (r.message && !r.message.error) nexlify_tracker.render(frm, r.message);
			},
		});
	},

	set_style(dark) {
		$("#nexlify-tracker-style").remove();
		$("head").append(`<style id="nexlify-tracker-style">
			.nexlify-smart-tracker { width: 100%; max-width: 100%; box-sizing: border-box; overflow-x: hidden; margin-bottom: 15px; }
			.nexlify-smart-tracker .sidebar-section-tracker { padding: 12px; border-radius: 8px; border: 1px solid ${dark ? "#1e293b" : "#e2e8f0"}; background: ${dark ? "#111827" : "#ffffff"}; width: 100%; box-sizing: border-box; }
			.nexlify-smart-tracker .mobile-btn-style { background: ${dark ? "#1e293b" : "#f8fafc"}; padding: 12px 16px; border-radius: 8px; border: 1px solid ${dark ? "#334155" : "#e2e8f0"}; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
			.nexlify-smart-tracker .main-tracker-header { cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; }
			.nexlify-smart-tracker .nexlify-sidebar-stage { position: relative; padding-bottom: 18px; display: flex; gap: 10px; align-items: flex-start; width: 100%; box-sizing: border-box; }
			.nexlify-smart-tracker .nexlify-sidebar-stage:last-child { padding-bottom: 0; }
			.nexlify-smart-tracker .nexlify-v-line { position: absolute; left: 14px; top: 28px; width: 2px; height: calc(100% - 18px); z-index: 1; }
			.nexlify-smart-tracker .nexlify-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 2; font-size: 11px; font-weight: bold; flex-shrink: 0; cursor: pointer; color: white; }
			.nexlify-smart-tracker .stage-header { cursor: pointer; display: flex; justify-content: space-between; align-items: flex-start; flex: 1; min-width: 0; gap: 8px; }
			.nexlify-smart-tracker .stage-title { white-space: normal; word-break: break-word; flex: 1; line-height: 1.4; font-size: 11px; font-weight: 600; }
			.nexlify-smart-tracker .stage-arrow { font-size: 10px; color: #888; transition: transform 0.3s ease; display: inline-block; }
			.nexlify-smart-tracker .stage-details { margin-top: 8px; padding-left: 2px; overflow: hidden; }
			.nexlify-smart-tracker .nexlify-link-tag { text-decoration: none !important; color: #1a73e8 !important; font-size: 10px; background: ${dark ? "#1e293b" : "#f0f7ff"}; padding: 4px 6px; border-radius: 4px; border: 1px solid ${dark ? "#334155" : "#dbeafe"}; margin-left: 8px; display: inline-flex; align-items: center; justify-content: center; }
		</style>`);
	},

	render(frm, config) {
		const e = frappe.utils.escape_html;
		const dark = $("html").attr("data-theme") === "dark";
		const mobile = $(window).width() <= 991;
		const grey = dark ? "#334155" : "#cbd5e1";
		const text = dark ? "#cbd5e1" : "#1e293b";
		const stages = config.stages || [];
		nexlify_tracker.set_style(dark);

		const steps_html = stages.map((s, i) => {
			const color = nexlify_tracker.COLORS[s.status] || grey;
			const icon = nexlify_tracker.ICONS[s.status] || i + 1;
			const open = s.status === "current" || s.status === "exit";
			const title_color = open ? color : s.status === "skipped" ? "#888" : text;
			const next = stages[i + 1];
			const line = next
				? `<div class="nexlify-v-line" style="background: ${next.status !== "todo" ? "#28a745" : dark ? "#334155" : "#e2e8f0"};"></div>`
				: "";

			let who = "";
			if (s.full_name) {
				const avatar = s.user_image
					? `<img src="${e(s.user_image)}" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover; flex-shrink: 0; margin-top: 2px;">`
					: `<div style="width: 20px; height: 20px; border-radius: 50%; background: ${dark ? "#1e293b" : "#e2e8f0"}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;"><i class="fa fa-user" style="font-size: 10px; color: #888;"></i></div>`;
				who = `
					<div style="font-size: 10px; color: #888; margin-top: 8px; display: flex; align-items: flex-start; gap: 8px; width: 100%;">
						${avatar}
						<div style="display: flex; flex-direction: column; gap: 1px; min-width: 0; flex: 1;">
							<div style="font-weight: 600; color: ${text}; white-space: normal; word-break: break-word; line-height: 1.2;">${e(s.full_name)}</div>
							<div style="font-size: 9px; color: #888; line-height: 1.1;">${e(frappe.datetime.str_to_user(s.on).replace(/:\d{2}$/, ""))}</div>
						</div>
					</div>`;
			}

			const tasks = (config.tasks || [])
				.filter((t) => t.stage === s.state)
				.map((t) => {
					const value = frm.doc[t.field_name];
					const done = Array.isArray(value) ? value.length > 0 : !!value;
					const link_val = t.link_field_name ? frm.doc[t.link_field_name] : null;
					const link = link_val && t.link_doc_type
						? `<a href="${e(frappe.utils.get_form_link(t.link_doc_type, link_val))}" target="_blank" class="nexlify-link-tag" title="${e(link_val)}"><i class="fa fa-external-link"></i></a>`
						: "";
					return `
						<div style="font-size: 10px; color: ${done ? "#28a745" : "#e53e3e"}; margin-top: 4px; display: flex; align-items: center; justify-content: space-between;">
							<div style="white-space: normal; word-break: break-word; flex: 1;"><span>${done ? "✓" : "○"}</span> ${e(__(t.task || ""))}</div>
							${link}
						</div>`;
				})
				.join("");

			return `
				<div class="nexlify-sidebar-stage">
					${line}
					<div class="nexlify-dot" style="background: ${color}; border: 2px solid ${color};">${icon}</div>
					<div style="flex: 1; min-width: 0; margin-top: 4px;">
						<div class="stage-header">
							<span class="stage-title" style="color: ${title_color};">${e(__(s.state))}</span>
							<span class="stage-arrow" style="transform: rotate(${open ? 90 : 0}deg);">▶</span>
						</div>
						<div class="stage-details" style="display: ${open ? "block" : "none"};">${tasks}${who}</div>
					</div>
				</div>`;
		}).join("");

		const border = `1px solid ${dark ? "#1e293b" : "#e2e8f0"}`;
		const $tracker = $(`
			<div class="nexlify-smart-tracker">
				<div class="sidebar-section-tracker" style="${mobile ? "padding: 0; border: none; background: transparent;" : ""}">
					<div class="main-tracker-header ${mobile ? "mobile-btn-style" : ""}" style="border-bottom: ${border}; padding-bottom: 8px; margin-bottom: 12px;">
						<span style="font-size: ${mobile ? "13px" : "10px"}; font-weight: bold; text-transform: uppercase; color: ${mobile ? "#1a73e8" : "#888"};">${e(__("Business Process"))}</span>
						<span class="main-arrow" style="font-size: 12px; color: #888; font-weight: bold;">▼</span>
					</div>
					<div class="main-body" style="display: ${mobile ? "none" : "block"}; overflow: hidden; ${mobile ? `margin-top: 10px; padding: 15px; border-radius: 8px; background: ${dark ? "#111827" : "#ffffff"}; border: 1px solid ${dark ? "#1e293b" : "#e2e8f0"};` : ""}">
						${steps_html}
					</div>
				</div>
			</div>`);

		$tracker.on("click", ".stage-header, .nexlify-dot", function () {
			const $stage = $(this).closest(".nexlify-sidebar-stage");
			const $details = $stage.find(".stage-details");
			$details.slideToggle(300, () => {
				$stage.find(".stage-arrow").css("transform", $details.is(":visible") ? "rotate(90deg)" : "rotate(0deg)");
			});
		});
		$tracker.on("click", ".main-tracker-header", function () {
			const $header = $(this);
			const $body = $tracker.find(".main-body");
			$body.slideToggle(400, () => {
				const visible = $body.is(":visible");
				$tracker.find(".main-arrow").text(visible ? "▼" : "▶");
				if (!mobile) {
					$header.css({
						"border-bottom": visible ? border : "none",
						"margin-bottom": visible ? "12px" : "0",
						"padding-bottom": visible ? "8px" : "0",
					});
				}
			});
		});

		(mobile ? $(frm.layout.wrapper) : $(frm.wrapper).find(".layout-side-section")).prepend($tracker);
	},
});

frappe.ui.form.on("*", {
	refresh(frm) {
		nexlify_tracker.schedule(frm);
	},
});
