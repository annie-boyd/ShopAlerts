from dataclasses import dataclass

@dataclass
class SoldItem:
    """ contains information about a sold item """
    sale_id: int
    item_name: str
    buyer: str
    price: float
