# ShopAlerts

A small desktop app that alerts you when your Etsy shop makes a sale. When a new order comes in, it shows a small popup and plays a sound.

![ShopAlerts popup: two pixel bears bouncing in front of a shop with "You made a sale!"](docs/demo.gif)

Right now ShopAlerts uses a **mock sale source**. It makes up sales at random and does not call the Etsy API, so you can demo it without real shop data.

Later updates will include the actual Etsy API.

## Requirements

- Python 3.9+ with Tkinter 
- macOS: the sound alert uses `afplay`
- Install [Pixelify Sans](https://fonts.google.com/specimen/Pixelify+Sans) font for the cute pixel style! Otherwise it'll be default.

There are no third-party dependencies.

## Etsy setup

1. In your Etsy app settings (in your Etsy developers account), add `http://localhost:3003/callback` as a redirect URI.
2. Fill in `ETSY_KEYSTRING` and `ETSY_SHARED_SECRET` in `.env` (see `.env.example`). `.env` is gitignored.
3. Run `python3 etsy_auth.py` once and approve access in the browser. Tokens are saved to `.etsy_tokens.json` (also gitignored) and refresh automatically.

The real source polls every 30 seconds so we don't go over Etsy's daily limit threshold (we're using about 2,880 of the 10,000 daily requests limit). The mock polls every 5 seconds.

## Running

```bash
python3 main.py
```

The main Tk window stays hidden. A background thread checks for new sales once per polling time (30s for Etsy, 5s if using mock), and the GUI thread picks them up from a queue every 500 ms.

## Project structure

| File | Purpose |
| --- | --- |
| `main.py` | Entry point. Starts the polling thread and the Tk event loop, and passes sales from the queue to the popup. |
| `sale_source.py` | `SaleSource` abstract base class: the interface for anything that reports new sales. |
| `mock_source.py` | `MockSaleSource`: returns a fake sale about 20% of the time (random item, buyer and price). |
| `order.py` | `Order` dataclass: `sale_id`, `buyer`, `items`, `total_price`. |
| `popup.py` | `show_popup(root, sale)`: the sale notification popup. |
| `sale_notifier.py` | `notify(sale)`: plays `sounds/alert.wav`. |
| `sounds/alert.wav` | The alert sound. |

## How it works

```
MockSaleSource ──(poll thread, 5s)──▶ queue ──(Tk main thread, 500ms)──▶ show_popup
```

Tkinter must run on the main thread, so polling happens on a separate daemon thread. The two threads communicate through a thread-safe `queue.Queue`, and `root.after()` keeps the GUI checking that queue without blocking.

To connect a real shop, use `SaleSource` in place of `MockSaleSource` in `main.py`.

## Credits

Pixel art from [Tiny Pixel Shop](https://florassence.itch.io/tiny-pixel-shop) by [@florassence](https://florassence.itch.io/). Its license doesn't allow redistribution, so the art isn't included in this repo. Download the pack and unzip it into an `assets/` folder in the project.

Alert sound: [Mystical Wind Chimes Transition FX](https://freesound.org/people/djlprojects/sounds/419594/) by djlprojects on Freesound (CC0).