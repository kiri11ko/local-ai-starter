import unittest

from inventory import Inventory, parse_csv


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add("A1", "Apple", 10, 0.5)
        self.inv.add("B2", "Banana", 3, 0.25)

    def test_add_existing_sku_increases_quantity(self):
        self.inv.add("A1", "Green apple", 5, 0.6)
        self.assertEqual(self.inv.items["A1"], {"name": "Green apple", "qty": 15, "price": 0.6})

    def test_add_rejects_non_positive_quantity(self):
        with self.assertRaises(ValueError):
            self.inv.add("C3", "Cherry", 0, 1.0)

    def test_remove_decreases_quantity(self):
        self.inv.remove("A1", 4)
        self.assertEqual(self.inv.items["A1"]["qty"], 6)

    def test_remove_more_than_stock_raises(self):
        with self.assertRaises(ValueError):
            self.inv.remove("B2", 4)
        self.assertEqual(self.inv.items["B2"]["qty"], 3)

    def test_remove_to_zero_deletes_item(self):
        self.inv.remove("B2", 3)
        self.assertNotIn("B2", self.inv.items)

    def test_total_value_keeps_cents(self):
        self.assertEqual(self.inv.total_value(), 5.75)

    def test_low_stock_includes_threshold_and_is_sorted(self):
        self.inv.add("Z9", "Zucchini", 5, 1.0)
        self.inv.add("C3", "Cherry", 1, 2.0)
        self.assertEqual(self.inv.low_stock(5), ["B2", "C3", "Z9"])

    def test_apply_discount(self):
        self.inv.apply_discount(20)
        self.assertEqual(self.inv.items["A1"]["price"], 0.4)
        self.assertEqual(self.inv.items["B2"]["price"], 0.2)

    def test_apply_discount_validates_range(self):
        for bad in (-1, 101):
            with self.assertRaises(ValueError):
                self.inv.apply_discount(bad)

    def test_parse_csv_skips_header_and_blank_lines(self):
        text = "sku,name,qty,price\n A1 , Apple , 2 , 0.5 \n\nB2,Banana,1,0.25\n"
        inv = parse_csv(text)
        self.assertEqual(inv.items["A1"], {"name": "Apple", "qty": 2, "price": 0.5})
        self.assertEqual(inv.total_value(), 1.25)


if __name__ == "__main__":
    unittest.main()
