# ShopAlerts

A small desktop app that alerts you when your Etsy shop makes a sale. When a new order comes in, it shows a small popup and plays a sound.

Right now ShopAlerts uses a **mock sale source**. It makes up sales at random and does not call the Etsy API, so you can demo it without real shop data.

Later updates will include the actual Etsy API.

## Requirements

- Python 3.9+ with Tkinter 
- macOS: the sound alert uses `afplay`

There are no third-party dependencies.

## Running

```bash
python3 main.py
```

The main Tk window stays hidden. A background thread checks for new sales once per second, and the GUI thread picks them up from a queue every 500 ms.

## Project structure

| File | Purpose |
| --- | --- |
| `main.py` | Entry point. Starts the polling thread and the Tk event loop, and passes sales from the queue to the popup. |
| `sale_source.py` | `SaleSource` abstract base class: the interface for anything that reports new sales. |
| `mock_source.py` | `MockSaleSource`: returns a fake sale about 20% of the time (random item, buyer and price). |
| `sold_item.py` | `SoldItem` dataclass: `sale_id`, `item_name`, `buyer`, `price`. |
| `popup.py` | `show_popup(root, sale)`: the sale notification popup. |
| `sale_notifier.py` | `notify(sale)`: plays `sounds/alert.wav`. |
| `sounds/alert.wav` | The alert sound. |

## How it works

```
MockSaleSource ──(poll thread, 1s)──▶ queue ──(Tk main thread, 500ms)──▶ show_popup
```

Tkinter must run on the main thread, so polling happens on a separate daemon thread. The two threads communicate through a thread-safe `queue.Queue`, and `root.after()` keeps the GUI checking that queue without blocking.

To connect a real shop, write a new `SaleSource` subclass that calls the Etsy API and use it in place of `MockSaleSource` in `main.py`. Nothing else needs to change.

## Status / TODO

- [ ] `show_popup` is not implemented yet and raises `NotImplementedError`, so the app currently crashes on the first sale. <br>Planned: a borderless `Toplevel` in the bottom-right corner that fades in and out using `-alpha` and closes itself.
- [ ] `sale_notifier.notify` (the sound) is not yet called from `main.py`.
- [ ] Support orders with multiple items (rename `SoldItem` to `Order`, with `items` and `total_price`).
- [ ] Real Etsy API `SaleSource`.

