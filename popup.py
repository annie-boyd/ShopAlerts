import os
import tkinter as tk

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SCALE = 2  # make the pixel art bigger by a whole number so it stays sharp

FADE_STEPS = 10   # how many small changes in each fade
FADE_MS = 30      # time between changes, so each fade takes about 0.3s
SHOW_MS = 10000   # how long it stays fully visible

SPRITE = 32       # each frame in the sprite sheets is 32x32
BOUNCE_MS = 250   # time between bounce frames
BLINK_MS = 400    # how long the heart stays on (and off)
GROUND_Y = 356    # bottom of the bear frames on the canvas (feet land on the sidewalk)

FONT = "Pixelify Sans"  # free pixel font from Google Fonts, must be installed on this Mac
TEXT_COLOR = "#ff7fa6"  # the heart's pink, shifted slightly toward blue
OUTLINE_COLOR = "#fff5db"  # cream from the sky, so the text stands out from the clouds
TEXT_X, TEXT_Y = 24, 20  # top-left of the message, in the empty sky

def show_popup(root, sale) -> None:
    """Show a small popup window with sale info that appears briefly
    and then closes itself.

    `root` is the Tk root window created in main.py — this function
    should NOT create its own Tk() instance, since Tkinter only wants
    one per program. Build a Toplevel(root) instead.

    """
    popup = tk.Toplevel(root)
    popup.overrideredirect(True)  # no title bar
    popup.attributes("-alpha", 0.0)  # start invisible so it doesn't flash before fading in

    # load the shop and scale it up
    shop = tk.PhotoImage(file=os.path.join(ASSETS, "ShopBG_320x180px.png")).zoom(SCALE)
    width, height = shop.width(), shop.height()

    # a canvas the same size as the image, with no border
    canvas = tk.Canvas(popup, width=width, height=height,
                       highlightthickness=0, bd=0)
    canvas.pack()
    canvas.create_image(0, 0, image=shop, anchor="nw")  # top-left corner

    # keep a reference, or Python deletes the image and the popup shows blank
    canvas.shop_image = shop

    bears = tk.PhotoImage(file=os.path.join(ASSETS, "BearSprites.png"))
    bubbles = tk.PhotoImage(file=os.path.join(ASSETS, "SpeechBubbles.png"))

    canvas.frames = []  # keep references so the images don't disappear
    # (center x, bear row, which frame it starts on) - starting on different frames makes them bounce out of sync
    for x, bear_row, start in [(330, 2, 0), (390, 4, 1)]:
        bear_frames = [cut_frame(bears, 0, bear_row), cut_frame(bears, 1, bear_row)]
        heart_frame = cut_frame(bubbles, 0, 0)
        canvas.frames += bear_frames + [heart_frame]

        bear = canvas.create_image(x, GROUND_Y, anchor="s")
        heart = canvas.create_image(x, GROUND_Y - 44, image=heart_frame, anchor="s")
        bounce(popup, canvas, bear, bear_frames, start)
        blink(popup, canvas, heart)

    # sale message in the sky
    count = len(sale.items)
    outlined_text(canvas, TEXT_X, TEXT_Y, "You made a sale!", (FONT, 30))
    outlined_text(canvas, TEXT_X, TEXT_Y + 44,
                  f"{sale.buyer} ordered {count} item{'' if count == 1 else 's'}!", (FONT, 21))

    # bottom-right of the screen, 20px from the edges
    x = root.winfo_screenwidth() - width - 20
    y = root.winfo_screenheight() - height - 80  # extra room for the Dock
    popup.geometry(f"{width}x{height}+{x}+{y}")

    # fade in, wait, fade out, then close
    fade(popup, 0.0, 1.0, on_done=lambda: popup.after(
        SHOW_MS, lambda: fade(popup, 1.0, 0.0, on_done=popup.destroy)))

def fade(popup, start, end, on_done=None, step=0):
    """Change the window's transparency from start to end a little at a time."""
    if not popup.winfo_exists():  # stop if the window has already closed
        return
    alpha = start + (end - start) * step / FADE_STEPS
    popup.attributes("-alpha", alpha)
    if step < FADE_STEPS:
        popup.after(FADE_MS, fade, popup, start, end, on_done, step + 1)
    elif on_done:
        on_done()


def outlined_text(canvas, x, y, text, font):
    """Draw text with a cream outline around it, pixel-art style."""
    # draw the text in cream, shifted 2px in every direction, to make the outline...
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            if dx or dy:
                canvas.create_text(x + dx, y + dy, text=text, font=font,
                                   fill=OUTLINE_COLOR, anchor="nw")
    # ...then the real text on top
    canvas.create_text(x, y, text=text, font=font, fill=TEXT_COLOR, anchor="nw")


def cut_frame(sheet, col, row):
    """Cut one 32x32 frame out of a sprite sheet and scale it up."""
    x, y = col * SPRITE, row * SPRITE
    frame = tk.PhotoImage()
    frame.tk.call(frame, "copy", sheet, "-from", x, y, x + SPRITE, y + SPRITE,
                  "-zoom", SCALE)
    return frame


def bounce(popup, canvas, item, frames, index=0):
    """Swap between two frames forever (until the popup closes)."""
    if not popup.winfo_exists():
        return
    canvas.itemconfig(item, image=frames[index])
    popup.after(BOUNCE_MS, bounce, popup, canvas, item, frames, 1 - index)


def blink(popup, canvas, item, visible=True):
    """Show and hide an item over and over (until the popup closes)."""
    if not popup.winfo_exists():
        return
    canvas.itemconfig(item, state="normal" if visible else "hidden")
    popup.after(BLINK_MS, blink, popup, canvas, item, not visible)
