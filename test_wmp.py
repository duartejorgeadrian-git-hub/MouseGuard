import time
import os
from comtypes import CoInitialize
import comtypes.client

def play_audio(filepath):
    CoInitialize()
    try:
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.URL = os.path.abspath(filepath)
        wmp.controls.play()
        time.sleep(0.5) # wait for it to start
        while wmp.playState == 3: # 3 = Playing
            time.sleep(0.1)
        print("Playback finished.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    play_audio("purge_siren.mp3")
