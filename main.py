"""
 main.py - driver for shop alert system

 ShopAlert gives a desktop notification for new sales on an Etsy shop. 
 It uses mock_source.py to get fake new sales from the Etsy API, and sale_notifier.py to send a desktop notification.

 By: Annie Boyd
 9-17-2026
 """

from time import sleep

from mock_source import MockSaleSource

def main():
    sale_source = MockSaleSource()
    while True:
        new_sale = sale_source.get_new_sales()
        if new_sale:
            print(f"You made a sale! {new_sale[0].buyer} bought {new_sale[0].item_name} for ${new_sale[0].price}.")
        sleep(1)

if __name__ == "__main__":
    main()
