### Pharma Smart ERP

Pharmacy ERP built on ERPNext

### What is in this app

- **Carton Size** field on every Item (Item form, next to Default Purchase UOM). Meaning: how many ordering units
  (the Default Purchase UOM, or the Stock UOM if none is set) are in one carton.
- **Smart PO** screen (search "Smart PO" in the top bar):
  1. Pick the warehouse, add items with the quantity you need to supply.
  2. **Calculate Order** checks stock (and optionally open purchase orders), works out the shortfall,
     rounds it up to full cartons, and picks the cheapest supplier from Item Price (Buying) records that have a Supplier.
  3. Review or edit supplier, rate and order quantity.
  4. **Create Purchase Orders** makes one DRAFT Purchase Order per supplier for you to review and submit.

Set up supplier prices first: Item Price, tick Buying, choose the Item, a Supplier, the rate, and the unit the rate is for.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app pharma_smart
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/pharma_smart
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

gpl-3.0
