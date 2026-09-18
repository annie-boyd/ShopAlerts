import subprocess


def notify(sale) -> None:
  """
  Play a sound and show a short popup animation for a new sale.

  Show a small popup window with the sale info that appears briefly then goes away on its own 
 
  """

  #plays an alert sound for a new sale
  subprocess.run(["afplay", "sounds/alert.wav"])

  