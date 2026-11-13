import unittest
from datetime import date

from pharma_smart.pharma_smart_erp.smart_po_logic import pick_best_supplier, round_up_to_carton, shortfall_qty


class TestSmartPOLogic(unittest.TestCase):
	def test_round_up(self):
		self.assertEqual(round_up_to_carton(25, 10), 30)
		self.assertEqual(round_up_to_carton(30, 10), 30)
		self.assertEqual(round_up_to_carton(1, 10), 10)
		self.assertEqual(round_up_to_carton(0, 10), 0)
		self.assertEqual(round_up_to_carton(7, 1), 7)
		self.assertEqual(round_up_to_carton(7, 0), 7)

	def test_shortfall(self):
		self.assertEqual(shortfall_qty(100, 40), 60)
		self.assertEqual(shortfall_qty(100, 40, 30), 30)
		self.assertEqual(shortfall_qty(100, 150), 0)

	def test_cheapest_supplier(self):
		prices = [
			{"supplier": "A", "price_list_rate": 10, "uom": "Box", "currency": "AED"},
			{"supplier": "B", "price_list_rate": 8, "uom": "Box", "currency": "AED"},
			{"supplier": "C", "price_list_rate": 0.3, "uom": "Tablet", "currency": "AED"},  # 0.3 * 24 = 7.2 per Box
		]
		self.assertEqual(
			pick_best_supplier(prices, "Box", "Tablet", 24, "AED", date(2026, 11, 13)), ("C", 0.3 * 24)
		)

	def test_skips_bad_prices(self):
		prices = [
			{"supplier": "A", "price_list_rate": 5, "uom": "Box", "currency": "USD"},
			{"supplier": "B", "price_list_rate": 5, "uom": "Box", "currency": "AED", "valid_upto": date(2026, 1, 1)},
			{"supplier": "C", "price_list_rate": 5, "uom": "Pallet", "currency": "AED"},
			{"supplier": "D", "price_list_rate": 6, "uom": "Box", "currency": "AED"},
		]
		self.assertEqual(
			pick_best_supplier(prices, "Box", "Tablet", 24, "AED", date(2026, 11, 13), disabled_suppliers={"D"}),
			(None, 0.0),
		)
		self.assertEqual(
			pick_best_supplier(prices, "Box", "Tablet", 24, "AED", date(2026, 11, 13)), ("D", 6.0)
		)


if __name__ == "__main__":
	unittest.main()
