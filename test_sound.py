import logging
import time
from mouse_guard import MouseGuardApp

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def test_alarm():
    app = MouseGuardApp()
    app.umbral = 2
    app.repeticiones = 1
    
    print("Testing emitir_sonido directly...")
    app.emitir_sonido()
    print("Finished emitir_sonido.")

if __name__ == "__main__":
    test_alarm()
