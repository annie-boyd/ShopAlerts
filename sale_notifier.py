import os
import subprocess

SOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "alert.wav")


def notify(sale) -> None:
  """
  Play an alert sound for a new sale.

  Uses Popen instead of run so the sound plays in the background and
  the popup animation doesn't freeze while it plays.
  """
  subprocess.Popen(["afplay", SOUND])
