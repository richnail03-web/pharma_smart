"""Pure calculation helpers for Smart PO (no Frappe imports, so they are easy to test)."""

import math


def round_up_to_carton(shortfall, carton_size):
	"""Round a shortfall UP to a whole number of cartons.

	Example: shortfall 25, carton 10 -> 30. Shortfall 0 -> 0.
	"""
	shortfall = float(shortfall or 0)
	carton_size = float(carton_size or 0)
	if shortfall <= 0:
		return 0.0
	if carton_size <= 1:
		carton_size = 1.0
	# round() first so 3.0000000001 does not become 4 cartons
	return math.ceil(round(shortfall / carton_size, 6)) * carton_size


def shortfall_qty(required, actual, on_order=0.0):
	"""How much is still missing after counting stock (and optionally open orders)."""
	return max(0.0, float(required or 0) - float(actual or 0) - float(on_order or 0))


def rate_per_ordering_uom(price_rate, price_uom, ordering_uom, stock_uom, conversion_factor):
	"""Convert an Item Price rate to a rate per ordering unit.

	Returns None when the price is quoted in a unit we cannot convert.
	conversion_factor = stock units in ONE ordering unit (e.g. Box = 24 Tablets -> 24).
	"""
	price_rate = float(price_rate or 0)
	if not price_uom or price_uom == stock_uom:
		# price is per stock unit
		return price_rate * float(conversion_factor)
	if price_uom == ordering_uom:
		return price_rate
	return None


def pick_best_supplier(prices, ordering_uom, stock_uom, conversion_factor, company_currency, on_date, disabled_suppliers=()):
	"""Choose the cheapest valid supplier price.

	`prices` is a list of dicts with: supplier, price_list_rate, uom, currency, valid_from, valid_upto.
	Dates may be date objects or None. Returns (supplier, rate_per_ordering_uom) or (None, 0).
	"""
	best = None
	for p in prices:
		if p.get("supplier") in disabled_suppliers:
			continue
		if p.get("currency") and company_currency and p["currency"] != company_currency:
			continue
		if p.get("valid_from") and on_date < p["valid_from"]:
			continue
		if p.get("valid_upto") and on_date > p["valid_upto"]:
			continue
		rate = rate_per_ordering_uom(
			p.get("price_list_rate"), p.get("uom"), ordering_uom, stock_uom, conversion_factor
		)
		if not rate or rate <= 0:
			continue
		candidate = (rate, p["supplier"])
		if best is None or candidate < best:
			best = candidate
	if best is None:
		return None, 0.0
	return best[1], best[0]
