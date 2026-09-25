from abc import ABC, abstractmethod


class SaleSource(ABC):
    """
    Anything that can report new sales since the last check
    """

    # seconds between polls; Etsy allows 10k requests/day, so 30s (~2,880/day) definitely stays under threshold
    poll_seconds = 30

    @abstractmethod
    def get_new_sales(self) -> list:
        """
        Return sales that have happened since the last call,
        should return [] when nothing new happened.
        """
        raise NotImplementedError
