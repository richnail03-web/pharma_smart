import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from pharma_smart.pharma_smart_erp.smart_po_logic import (
	pick_best_supplier,
	round_up_to_carton,
	shortfall_qty,
)

CARTON_FIELD = "custom_carton_size"


class SmartPO(Document):
	def validate(self):
		seen = set()
		for row in self.items:
			if flt(row.required_qty) <= 0:
				frappe.throw(_("Row {0}: Required Qty must be more than zero").format(row.idx))
			if row.item_code in seen:
				frappe.throw(_("Row {0}: {1} is listed twice. Combine it into one row.").format(row.idx, row.item_code))
			seen.add(row.item_code)

	@frappe.whitelist()
	def calculate(self):
		"""Fill stock, shortfall, carton-rounded order quantity, cheapest supplier and rate."""
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		on_date = getdate(nowdate())
		disabled = set(frappe.get_all("Supplier", filters={"disabled": 1}, pluck="name"))
		problems = 0

		for row in self.items:
			row.notes = ""
			item = frappe.db.get_value(
				"Item", row.item_code,
				["item_name", "stock_uom", "purchase_uom", CARTON_FIELD, "disabled", "is_purchase_item"],
				as_dict=True,
			)
			if not item:
				row.notes = _("Item not found")
				problems += 1
				continue
			if item.disabled or not item.is_purchase_item:
				row.notes = _("Item is disabled or not allowed for purchase")
				row.order_qty = 0
				problems += 1
				continue

			ordering_uom = item.purchase_uom or item.stock_uom
			factor = self._conversion_factor(row.item_code, ordering_uom, item.stock_uom)
			if not factor:
				row.notes = _("No unit conversion from {0} to {1} on the Item (UOM tab)").format(
					ordering_uom, item.stock_uom
				)
				row.order_qty = 0
				problems += 1
				continue

			bin_data = frappe.db.get_value(
				"Bin", {"item_code": row.item_code, "warehouse": self.warehouse},
				["actual_qty", "ordered_qty"], as_dict=True,
			) or frappe._dict(actual_qty=0, ordered_qty=0)

			actual = flt(bin_data.actual_qty) / factor
			on_order = flt(bin_data.ordered_qty) / factor if self.include_open_orders else 0
			carton = flt(item.get(CARTON_FIELD)) or 1

			row.uom = ordering_uom
			row.carton_size = carton
			row.available_qty = actual + on_order
			row.shortfall_qty = shortfall_qty(row.required_qty, actual, on_order)
			row.order_qty = round_up_to_carton(row.shortfall_qty, carton)

			if row.order_qty > 0:
				prices = frappe.get_all(
					"Item Price",
					filters={"item_code": row.item_code, "buying": 1, "supplier": ["is", "set"]},
					fields=["supplier", "price_list_rate", "uom", "currency", "valid_from", "valid_upto"],
				)
				supplier, rate = pick_best_supplier(
					prices, ordering_uom, item.stock_uom, factor, company_currency, on_date, disabled
				)
				row.supplier = supplier
				row.rate = rate
				if not supplier:
					row.notes = _("No supplier price found. Add an Item Price (Buying) with a Supplier.")
					problems += 1
			else:
				row.supplier = None
				row.rate = 0
				row.notes = _("Enough stock. Nothing to order.")
			row.amount = flt(row.order_qty) * flt(row.rate)

		self.result_notes = (
			_("{0} row(s) need attention. See the Notes column.").format(problems) if problems else ""
		)
		self.save()
		return problems

	@frappe.whitelist()
	def create_purchase_orders(self):
		"""Create one DRAFT Purchase Order per supplier from the rows as they stand now."""
		if self.purchase_orders:
			frappe.throw(_("Purchase Orders were already created: {0}").format(self.purchase_orders))

		groups, skipped = {}, []
		for row in self.items:
			if flt(row.order_qty) <= 0:
				continue
			if not row.supplier or flt(row.rate) <= 0:
				skipped.append(row.item_code)
				continue
			groups.setdefault(row.supplier, []).append(row)

		if not groups:
			frappe.throw(_("Nothing to order. Run Calculate Order first, and check supplier prices."))

		created = []
		for supplier, rows in groups.items():
			po = frappe.new_doc("Purchase Order")
			po.company = self.company
			po.supplier = supplier
			po.transaction_date = nowdate()
			po.schedule_date = self.schedule_date
			po.ignore_pricing_rule = 1
			for row in rows:
				factor = self._conversion_factor(
					row.item_code, row.uom, frappe.db.get_value("Item", row.item_code, "stock_uom")
				)
				po.append(
					"items",
					{
						"item_code": row.item_code,
						"qty": row.order_qty,
						"uom": row.uom,
						"conversion_factor": factor,
						"rate": row.rate,
						"price_list_rate": row.rate,
						"warehouse": self.warehouse,
						"schedule_date": self.schedule_date,
					},
				)
			po.insert()
			created.append(po.name)

		self.purchase_orders = ", ".join(created)
		if skipped:
			self.result_notes = _("Not ordered (no supplier or rate): {0}").format(", ".join(skipped))
		self.save()
		return created

	@staticmethod
	def _conversion_factor(item_code, uom, stock_uom):
		"""Stock units in ONE `uom` (e.g. Box = 24 Tablets -> 24). Returns 0 if unknown."""
		if not uom or uom == stock_uom:
			return 1.0
		return flt(
			frappe.db.get_value(
				"UOM Conversion Detail", {"parent": item_code, "parenttype": "Item", "uom": uom}, "conversion_factor"
			)
		)
