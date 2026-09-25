from order import Order
from sale_source import SaleSource
import random

class MockSaleSource(SaleSource):
    """
    Pretends to be Etsy: invents a fake sale sometimes instead of
    calling any real API. Used for demos so no real shop data is ever involved.

    """

    poll_seconds = 5  # no rate limit on fake data, so poll fast for demos

    # fake shop listings and their prices
    prices = {
        "Sunflower Oil Painting": 120.00,
        "Sunflower Canvas Print": 45.00,
        "Sunflower Paper Print": 18.00,
    }
    weights = [10, 60, 30]  # cheaper prints sell more often than the painting

    def get_new_sales(self) -> list:
        if random.random() < 0.2:  # 20% chance of a new sale
            buyers = ["Iris", "Lily", "Daisy", "Rose"]

            # an order has 1-4 items, picked with replacement so someone can buy two of the same print
            count = random.randint(1, 4)
            items = random.choices(list(self.prices), weights=self.weights, k=count)

            new_sale = Order(
                sale_id = random.randint(1000, 9999),
                buyer = random.choice(buyers),
                items = items,
                total_price = round(sum(self.prices[item] for item in items), 2)
            )
            return [new_sale]
        else:
            return []
