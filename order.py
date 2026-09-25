from dataclasses import dataclass


@dataclass
class Order:
    """ contains information about an order, which can have multiple items """
    sale_id: int
    buyer: str
    items: list[str]
    total_price: float
