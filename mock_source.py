from sold_item import SoldItem
from sale_source import SaleSource
import random

class MockSaleSource(SaleSource):
    """
    Pretends to be Etsy: invents a fake sale sometimes instead of
    calling any real API. Used for demos so no real shop data is ever involved.

    """

    def get_new_sales(self) -> list:

        sale_items = ["Sunflower Oil Painting", "Sunflower Paper Print", "Sunflower Canvas Print"]
        weights = [10, 30, 60]

        chosen_item = random.choices(sale_items, weights=weights, k=1)[0]

        if random.random() < 0.2:  # 20% chance of a new sale
            buyers = ["Iris", "Lily", "Daisy", "Rose"]
            new_sale = SoldItem(
                sale_id = random.randint(1000, 9999),
                item_name = chosen_item,
                buyer = random.choice(buyers),
                price = round(random.uniform(10.0, 100.0), 2)
            )
            return [new_sale]
        else:
            return []