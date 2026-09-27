"""
 main.py - driver for shop alert system

 ShopAlert gives a desktop notification for new sales on an Etsy shop. 
 It uses mock_source.py to get fake new sales from the Etsy API, and sale_notifier.py to send a desktop notification.

 By: Annie Boyd
 9-17-2026

 v 2.0: 9-26-2026
 Added the implementation for getting real sales from the Etsy API instead of using the mock
 You can toggle between mock or real sales by switching the SALE_SOURCE variable in the .env file!

 """
from mock_source import MockSaleSource
from etsy_source import EtsySaleSource
from etsy_auth import load_env # load environment variables from .env file

# for polling
import threading
from time import sleep

# imports for the GUI and queue
import queue
import tkinter as tk
from popup import show_popup
from sale_notifier import notify

alert_queue = queue.Queue()
current_popup = None  # the popup on screen, if any

def main():
    # separate thread for polling so the GUI can run in the main thread without being blocked
    threading.Thread(target=poll_sales, daemon=True).start()

    global root
    root = tk.Tk() # start main window for popup
    root.withdraw() # hide main window
    root.after(500, check_for_sales) # starts the polling
    root.mainloop() # starts event loop for GUI

def pick_sale_source():
    """Use the real Etsy shop if SALE_SOURCE=etsy in .env, otherwise uses mock."""
    try:
        setting = load_env().get("SALE_SOURCE", "mock")
    except (FileNotFoundError, SystemExit):
        # no .env file, or no Etsy keys in it yet, so the mock is the only option
        setting = "mock"
    if setting == "etsy":
        return EtsySaleSource()
    return MockSaleSource()

def poll_sales():
    """Poll for new sales in a separate thread."""
    sale_source = pick_sale_source()

    while True:
        new_sales = sale_source.get_new_sales()
        for sale in new_sales:
            alert_queue.put(sale)
        sleep(sale_source.poll_seconds)

def check_for_sales():
    """
    Check the queue for new sales. If no popup is showing, show everything
    that's waiting in one popup (combined if there's more than one order).
    Calls itself again to keep checking for new sales.
    """
    global current_popup

    # only show a new popup once the last one has closed. until then, orders wait in the queue
    if current_popup is None or not current_popup.winfo_exists():
        orders = []
        while not alert_queue.empty():
            orders.append(alert_queue.get())

        if orders:
            current_popup = show_popup(root, orders)
            notify(orders)  # one chime for the whole popup

    root.after(500, check_for_sales) # reschedule itself to check for sales again in 500ms

if __name__ == "__main__":
    main()


