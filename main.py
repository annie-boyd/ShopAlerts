"""
 main.py - driver for shop alert system

 ShopAlert gives a desktop notification for new sales on an Etsy shop. 
 It uses mock_source.py to get fake new sales from the Etsy API, and sale_notifier.py to send a desktop notification.

 By: Annie Boyd
 9-17-2026
 """
from mock_source import MockSaleSource

# for polling
import threading
from time import sleep

# imports for the GUI and queue
import queue
import tkinter as tk
from popup import show_popup

alert_queue = queue.Queue()

def main():
    # separate thread for polling so the GUI can run in the main thread without being blocked
    threading.Thread(target=poll_sales, daemon=True).start()

    global root
    root = tk.Tk() # start main window for popup
    root.withdraw() # hide main window
    root.after(500, check_for_sales) # starts the polling
    root.mainloop() # starts event loop for GUI

def poll_sales():
    """Poll for new sales in a separate thread."""
    sale_source = MockSaleSource()

    while True:
        new_sale = sale_source.get_new_sales()
        if new_sale:
            alert_queue.put(new_sale[0])
        sleep(sale_source.poll_seconds)

def check_for_sales():
    """
    Check for new sales in the queue and show a popup for each one.
    Calls itself again to keep checking for new sales.
    """
    while not alert_queue.empty():
        sale = alert_queue.get()
        show_popup(root, sale)

    root.after(500, check_for_sales) # reschedule itself to check for sales again in 500ms
    
if __name__ == "__main__":
    main()


