frappe.ui.form.on("Smart PO", {
	setup(frm) {
		frm.set_query("warehouse", () => ({
			filters: { company: frm.doc.company, is_group: 0 },
		}));
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value("company", frappe.defaults.get_user_default("Company"));
		}
	},

	refresh(frm) {
		if (frm.is_new()) return;

		const run = (method, message) => {
			frm.call({ doc: frm.doc, method: method, freeze: true, freeze_message: message }).then(() =>
				frm.reload_doc()
			);
		};
		const saved_then = (fn) => (frm.is_dirty() ? frm.save().then(fn) : fn());

		frm.add_custom_button(__("Calculate Order"), () => {
			saved_then(() => run("calculate", __("Calculating...")));
		}).addClass("btn-primary");

		if ((frm.doc.items || []).length && !frm.doc.purchase_orders) {
			frm.add_custom_button(__("Create Purchase Orders"), () => {
				frappe.confirm(
					__("Create draft Purchase Orders (one per supplier) from these rows?"),
					() => saved_then(() => run("create_purchase_orders", __("Creating purchase orders...")))
				);
			});
		}
	},
});

frappe.ui.form.on("Smart PO Item", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code) return;
		frappe.db.get_value("Item", row.item_code, ["stock_uom", "purchase_uom"]).then((r) => {
			const v = r.message || {};
			frappe.model.set_value(cdt, cdn, "uom", v.purchase_uom || v.stock_uom);
		});
	},
});
