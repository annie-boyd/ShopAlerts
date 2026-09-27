"""
 Unit tests for ShopAlerts.

 Run from the project folder:
     python3 -m unittest discover tests -v

These tests don't actually touch the real Etsy API, your real .etsy_last_seen.json, or the screen,
and the internet is also faked, and last-seen is saved to a temporary folder. 
"""
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

# let the tests import the project files from the folder above
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import etsy_source
from etsy_source import EtsySaleSource
from order import Order
from popup import popup_text


# ---------- helpers ----------

def fake_receipt(**changes):
    """A made-up Etsy receipt with only the fields the app reads. Pass keyword args to change any of them."""
    receipt = {
        "receipt_id": 1,
        "name": "Buzz Lightyear",
        "created_timestamp": 1000,
        "transactions": [{"title": "Print", "quantity": 2}, {"title": "Mug", "quantity": 1}],
        "subtotal": {"amount": 4500, "divisor": 100, "currency_code": "USD"},
    }
    receipt.update(changes)
    return receipt


def fake_response(receipts):
    """What urlopen would return for a successful request: JSON shaped like Etsy's reply."""
    return io.BytesIO(json.dumps({"count": len(receipts), "results": receipts}).encode())


def http_error(code):
    """An HTTPError like the one urlopen raises when Etsy answers with an error code."""
    return urllib.error.HTTPError("https://api.etsy.com", code, "error", {}, io.BytesIO(b""))


class EtsyTestCase(unittest.TestCase):
    """Base class: gives each test an EtsySaleSource that never touches the internet or your real files."""

    def setUp(self):
        # save last-seen in a temporary folder instead of the project
        self.temp_dir = tempfile.TemporaryDirectory()
        patches = [
            mock.patch.object(etsy_source, "LAST_SEEN_PATH", os.path.join(self.temp_dir.name, "last_seen.json")),
            mock.patch.object(etsy_source, "get_access_token", return_value="123.fake-token"),
            mock.patch.object(etsy_source, "api_headers", return_value={}),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.addCleanup(self.temp_dir.cleanup)

        # __new__ makes the object without running __init__ 
        self.source = EtsySaleSource.__new__(EtsySaleSource)
        self.source.shop_id = 1
        self.source.last_seen = 0
        self.source.poll_seconds = 30

    def fake_urlopen(self, result):
        """
        Replace urlopen for the rest of this test.
        Pass fake_response([...]) for a successful reply, or an exception like http_error(429) to fail.
        """
        kind = "side_effect" if isinstance(result, Exception) else "return_value"
        patch = mock.patch("urllib.request.urlopen", **{kind: result})
        patch.start()
        self.addCleanup(patch.stop)


# ---------- tests ----------

class TestToOrder(EtsyTestCase):
    """_to_order keeps only what the popup needs from a receipt."""

    def test_receipt_becomes_order(self):
        order = self.source._to_order(fake_receipt())
        self.assertEqual(order.buyer, "Buzz")                        # first name only
        self.assertEqual(order.items, ["Print", "Print", "Mug"])    # quantity 2 = two entries
        self.assertEqual(order.total_price, 45.0)                    # 4500 / 100

    def test_blank_name_becomes_someone(self):
        # a name of only spaces used to crash the polling thread
        for name in ["", "   "]:
            self.assertEqual(self.source._to_order(fake_receipt(name=name)).buyer, "Someone")


class TestGetNewSales(EtsyTestCase):
    """Fetching new orders, and handling Etsy's rate limit."""

    def test_returns_orders_and_remembers_the_newest(self):
        self.fake_urlopen(fake_response([
            fake_receipt(receipt_id=1, created_timestamp=100),
            fake_receipt(receipt_id=2, created_timestamp=200),
        ]))
        orders = self.source.get_new_sales()

        self.assertEqual([order.sale_id for order in orders], [1, 2])
        self.assertEqual(self.source.last_seen, 200)
        self.assertEqual(self.source._load_last_seen(), 200)  # saved, so a restart won't repeat these

    def test_rate_limit_backs_off_up_to_300_then_resets(self):
        self.fake_urlopen(http_error(429))
        with mock.patch("builtins.print"):  # hide the "Etsy returned 429" messages
            for expected in [60, 120, 240, 300, 300]:
                self.assertEqual(self.source.get_new_sales(), [])
                self.assertEqual(self.source.poll_seconds, expected)

        self.fake_urlopen(fake_response([]))  # Etsy is fine again
        self.source.get_new_sales()
        self.assertEqual(self.source.poll_seconds, 30)


class TestPopupText(unittest.TestCase):
    """The two lines of text on the popup."""

    def test_one_order_vs_several_combined(self):
        iris = Order(1, "Iris", ["A", "B", "C"], 1.0)
        lily = Order(2, "Lily", ["D"], 1.0)
        rose = Order(3, "Rose", ["E", "F", "G"], 1.0)

        self.assertEqual(popup_text([iris]), ("You made a sale!", "Iris ordered 3 items!"))
        self.assertEqual(popup_text([lily]), ("You made a sale!", "Lily ordered 1 item!"))
        self.assertEqual(popup_text([iris, lily, rose]), ("You made 3 sales!", "7 items in total!"))


if __name__ == "__main__":
    unittest.main()
