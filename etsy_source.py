"""
 etsy_source.py - gets real new orders from your Etsy shop

 Uses the tokens from etsy_auth.py. 
 
 To protect customers' privacy, only the fields we need for this popup are pulled,
 (first name, item titles, subtotal), and never prints or saves any of the other 
 information from the receipt, since it has customers' addresses and emails and other sensitive data.

 If you're interested in adding more fields to the popup, you can modify the _to_order method to include them,
 and you can find the API calls at https://developer.etsy.com/documentation/
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from etsy_auth import API_BASE, api_headers, get_access_token
from order import Order
from sale_source import SaleSource

HERE = os.path.dirname(os.path.abspath(__file__))
LAST_SEEN_PATH = os.path.join(HERE, ".etsy_last_seen.json")


class EtsySaleSource(SaleSource):
    """Reports new paid orders from the real Etsy shop."""

    def __init__(self):
        token = get_access_token()
        user_id = token.split(".")[0]  # the token starts with your Etsy user ID

        request = urllib.request.Request(f"{API_BASE}/users/{user_id}/shops",
                                         headers=api_headers(token))
        with urllib.request.urlopen(request) as response:
            shop = json.load(response)
        self.shop_id = shop["shop_id"]  # saved on self so get_new_sales can use it

        self.last_seen = self._load_last_seen()
        if self.last_seen is None:
            self.last_seen = int(time.time())
            self._save_last_seen(self.last_seen)

    def get_new_sales(self) -> list:
        """Return an Order for each paid receipt created since the last check."""
        request = urllib.request.Request(
            f"{API_BASE}/shops/{self.shop_id}/receipts?"
            f"min_created={self.last_seen + 1}"
            f"&was_paid=true"
            f"&sort_on=created&sort_order=asc"
            f"&limit=100",
            headers=api_headers(get_access_token())
        )
        # check for rate limiting and other errors
        try:
            with urllib.request.urlopen(request) as response:
                data = json.load(response)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Etsy returned 429")
                self.poll_seconds = min(self.poll_seconds * 2, 300)
                return []
            else:
                print(f"Etsy returned {e.code}")
                return []
        except urllib.error.URLError as e:
            print(f"No internet: {e.reason}")
            return []

        # reset polling interval
        self.poll_seconds = 30

        # the response gives a dictionary so we need just the results
        receipts = data["results"]
        orders = [self._to_order(receipt) for receipt in receipts]
        if orders:
            self.last_seen = max(receipt["created_timestamp"] for receipt in receipts)
            self._save_last_seen(self.last_seen)
        return orders

    def _to_order(self, receipt: dict) -> Order:
        """Keep only the fields the popup needs from one receipt."""
        buyer = receipt["name"].split()
        if buyer: 
            buyer = buyer[0]
        if not buyer:
            buyer = "Someone"
        items = []
        for transaction in receipt["transactions"]:
            for _ in range(transaction["quantity"]):
                items.append(transaction["title"])

        total_price = receipt["subtotal"]["amount"] / receipt["subtotal"]["divisor"] if "subtotal" in receipt else 0.0
        return Order(
            sale_id=receipt["receipt_id"],
            buyer=buyer,
            items=items,
            total_price=total_price
        )

    def _load_last_seen(self):
        """Return the saved last-seen timestamp, or None on the first run."""
        if not os.path.exists(LAST_SEEN_PATH):
            return None
        with open(LAST_SEEN_PATH, "r") as f:
            data = json.load(f)
        return data.get("last_seen")

    def _save_last_seen(self, timestamp: int) -> None:
        """Save the newest timestamp we've alerted for."""
        with open(LAST_SEEN_PATH, "w") as f:
            json.dump({"last_seen": timestamp}, f)
