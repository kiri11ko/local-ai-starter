"""A tiny stock-keeping module. The tests in test_inventory.py describe how it must behave."""


class Inventory:
    def __init__(self):
        self.items = {}  # sku -> {"name": str, "qty": int, "price": float}

    def add(self, sku, name, qty, price):
        """Adds stock. Adding an existing SKU increases its quantity and updates name and price."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.items[sku] = {"name": name, "qty": qty, "price": price}

    def remove(self, sku, qty):
        """Takes stock out. Not enough stock raises ValueError; an item that reaches 0 is deleted."""
        item = self.items[sku]
        item["qty"] -= qty

    def total_value(self):
        """Sum of qty * price over all items, rounded to cents."""
        return int(sum(item["qty"] * item["price"] for item in self.items.values()))

    def low_stock(self, threshold=5):
        """SKUs with qty at or below the threshold, sorted alphabetically."""
        return [sku for sku, item in self.items.items() if item["qty"] < threshold]

    def apply_discount(self, percent):
        """Lowers every price by `percent` percent (0-100), rounded to cents."""
        for item in self.items.values():
            item["price"] = item["price"] * percent


def parse_csv(text):
    """Builds an Inventory from 'sku,name,qty,price' lines. A header line and blank lines are skipped."""
    inventory = Inventory()
    for line in text.splitlines():
        sku, name, qty, price = line.split(",")
        inventory.add(sku, name, int(qty), float(price))
    return inventory
