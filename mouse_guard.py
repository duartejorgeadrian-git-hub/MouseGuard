import os
import sys
import time
import json
import logging
import threading
import ctypes
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pystray
from PIL import Image
import pynput

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DEFAULT_AUDIO = ""
ICON_PATH = resource_path("icon.ico")

class MouseGuardApp:
    def __init__(self):
        self.umbral = 5
        self.audio_personalizado = DEFAULT_AUDIO
        self.repeticiones = 1
        
        self.corriendo = True
        self.alarma_activa = False
        self.ultimo_movimiento = time.time()
        
        self.cola_gui = queue.Queue()
        self.cargar_configuracion()
        
        # Iniciar hilos en segundo plano
        self.listener = pynput.mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
        self.listener.start()
        
        self.hilo_monitoreo = threading.Thread(target=self._bucle_monitoreo, daemon=True)
        self.hilo_monitoreo.start()
        
        self.hilo_tray = threading.Thread(target=self._bucle_tray, daemon=True)
        self.hilo_tray.start()
        
        # Inicializar GUI principal
        self.root = tk.Tk()
        self.root.title("MouseGuard - Configuración")
        self.root.geometry("450x450") # Mas alto
        self.root.resizable(True, True) # Permitir redimensionar
        
        try:
            self.root.iconbitmap(ICON_PATH)
        except:
            pass
            
        self._setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_ventana)
        
        # Verificar cola para comunicación entre hilos
        self.root.after(100, self._verificar_cola)
        
        # Centrar ventana
        self.root.eval('tk::PlaceWindow . center')
        
        # Si ya había config, ocultamos inicialmente (para iniciar silenciado en tray)
        if os.path.exists(CONFIG_FILE):
            self.root.withdraw()
            
    def _setup_gui(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Configuración de MouseGuard", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Tiempo de Inactividad
        frame_tiempo = ttk.LabelFrame(main_frame, text="Tiempo de Inactividad", padding=10)
        frame_tiempo.pack(fill=tk.X, pady=5)
        
        self.lbl_umbral = ttk.Label(frame_tiempo, text=f"{self.umbral} Segundos")
        self.lbl_umbral.pack(side=tk.LEFT, padx=5)
        
        self.val_umbral = tk.IntVar(value=self.umbral)
        slider_umbral = ttk.Scale(frame_tiempo, from_=1, to=3600, orient=tk.HORIZONTAL, variable=self.val_umbral, command=self._actualizar_lbl_umbral)
        slider_umbral.pack(fill=tk.X, expand=True, padx=5)
        
        # Audio
        frame_audio = ttk.LabelFrame(main_frame, text="Sonido de Alerta", padding=10)
        frame_audio.pack(fill=tk.X, pady=5)
        
        self.val_audio = tk.StringVar(value=os.path.basename(self.audio_personalizado))
        ttk.Label(frame_audio, textvariable=self.val_audio, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_audio, text="Examinar...", command=self._seleccionar_audio).pack(side=tk.RIGHT, padx=5)
        
        # Repeticiones
        frame_rep = ttk.LabelFrame(main_frame, text="Intensidad (Repeticiones)", padding=10)
        frame_rep.pack(fill=tk.X, pady=5)
        
        self.lbl_rep = ttk.Label(frame_rep, text=f"{self.repeticiones} Veces")
        self.lbl_rep.pack(side=tk.LEFT, padx=5)
        
        self.val_rep = tk.IntVar(value=self.repeticiones)
        slider_rep = ttk.Scale(frame_rep, from_=1, to=20, orient=tk.HORIZONTAL, variable=self.val_rep, command=self._actualizar_lbl_rep)
        slider_rep.pack(fill=tk.X, expand=True, padx=5)
        
        # Boton Guardar y Manual
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(botones_frame, text="Ver Manual", command=self.mostrar_manual).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(botones_frame, text="Guardar y Minimizar a Bandeja", command=self.guardar_y_ocultar).pack(side=tk.RIGHT, expand=True, padx=5)
        
    def _actualizar_lbl_umbral(self, *args):
        self.lbl_umbral.config(text=f"{self.val_umbral.get()} Segundos")
        
    def _actualizar_lbl_rep(self, *args):
        self.lbl_rep.config(text=f"{self.val_rep.get()} Veces")
        
    def _seleccionar_audio(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar Sonido",
            filetypes=[("Archivos de Audio", "*.wav *.mp3 *.aiff *.ogg"), ("Todos", "*.*")]
        )
        if filepath:
            self.audio_personalizado = filepath
            self.val_audio.set(os.path.basename(filepath))
            
    def guardar_y_ocultar(self):
        self.umbral = self.val_umbral.get()
        self.repeticiones = self.val_rep.get()
        
        data = {
            "umbral": self.umbral,
            "audio": self.audio_personalizado,
            "repeticiones": self.repeticiones
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        logging.info("Configuracion guardada correctamente.")
        self.ultimo_movimiento = time.time()
        self.alarma_activa = False
        self.ocultar_ventana()
        
    def mostrar_manual(self):
        man = tk.Toplevel(self.root)
        man.title("Manual de Uso - MouseGuard")
        man.geometry("500x400")
        man.resizable(False, False)
        try:
            man.iconbitmap(ICON_PATH)
        except:
            pass
            
        text = tk.Text(man, wrap=tk.WORD, font=("Arial", 10), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        manual_content = """=== MANUAL DE USO DE MOUSEGUARD ===

1. TIEMPO DE INACTIVIDAD
Define cuántos segundos pueden pasar sin que se mueva el mouse antes de que se dispare la alarma. 

2. SONIDO DE ALERTA
Por defecto se incluye una sirena. Si descargaste 'The purge siren.mp3' o cualquier otro archivo, usa el botón 'Examinar...' para seleccionarlo. ¡Soporta MP3 y WAV!

3. INTENSIDAD (REPETICIONES)
Si tu sonido es muy corto (ej: un beep de 1 segundo), puedes aumentar las repeticiones para que suene varias veces seguidas. Si es un archivo largo como la sirena de la purga, con 1 repetición es suficiente.

4. MODO INVISIBLE (BANDEJA DEL SISTEMA)
Al hacer clic en 'Guardar y Minimizar a Bandeja', el programa se esconderá. Verás su ícono (un escudo) junto a la hora de Windows. Si necesitas volver a configurar algo o detener el programa, haz clic derecho sobre ese ícono.

NOTA: El programa forzará el volumen de tu PC al 100% justo antes de hacer sonar la alarma, para garantizar que siempre se escuche."""
        text.insert(tk.END, manual_content)
        text.config(state=tk.DISABLED)
        
    def ocultar_ventana(self):
        self.root.withdraw()
        
    def mostrar_ventana(self):
        # Recargar valores actuales
        self.val_umbral.set(self.umbral)
        self.val_rep.set(self.repeticiones)
        self.val_audio.set(os.path.basename(self.audio_personalizado))
        self._actualizar_lbl_umbral()
        self._actualizar_lbl_rep()
        self.root.deiconify()
        self.root.lift()
        
    def _verificar_cola(self):
        try:
            msg = self.cola_gui.get_nowait()
            if msg == "SHOW":
                self.mostrar_ventana()
            elif msg == "QUIT":
                self.corriendo = False
                self.root.quit()
                self.root.destroy()
                return
        except queue.Empty:
            pass
        self.root.after(100, self._verificar_cola)

    def cargar_configuracion(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.umbral = data.get("umbral", 5)
                    self.audio_personalizado = data.get("audio", DEFAULT_AUDIO)
                    self.repeticiones = data.get("repeticiones", 1)
            except Exception as e:
                logging.error(f"Error al cargar config: {e}")

    def on_move(self, x, y):
        self.ultimo_movimiento = time.time()
        if self.alarma_activa:
            self.alarma_activa = False
            self.detener_sonido()

    def on_click(self, x, y, button, pressed):
        self.ultimo_movimiento = time.time()
        if self.alarma_activa:
            self.alarma_activa = False
            self.detener_sonido()

    def on_scroll(self, x, y, dx, dy):
        self.ultimo_movimiento = time.time()
        if self.alarma_activa:
            self.alarma_activa = False
            self.detener_sonido()

    def maximizar_volumen(self):
        try:
            VK_VOLUME_UP = 0xAF
            for _ in range(50):
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            logging.info("Volumen del sistema maximizado al 100%.")
        except Exception as e:
            logging.error(f"No se pudo maximizar el volumen: {e}")

    def detener_sonido(self):
        try:
            ctypes.windll.winmm.mciSendStringW('stop myaudio', None, 0, None)
            ctypes.windll.winmm.mciSendStringW('close myaudio', None, 0, None)
        except:
            pass

    def emitir_sonido(self):
        self.maximizar_volumen()
        audio = self.audio_personalizado
        if not audio or not os.path.exists(audio):
            import winsound
            for _ in range(self.repeticiones):
                if not self.alarma_activa: break
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_SYNC)
            return
            
        audio_path = os.path.abspath(audio)
        for _ in range(self.repeticiones):
            if not self.corriendo or not self.alarma_activa:
                break
            try:
                self.detener_sonido()
                cmd_open = f'open "{audio_path}" type mpegvideo alias myaudio'
                res = ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None)
                if res != 0:
                    cmd_open = f'open "{audio_path}" alias myaudio'
                    ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None)
                    
                ctypes.windll.winmm.mciSendStringW('play myaudio', None, 0, None)
                
                buf = ctypes.create_unicode_buffer(128)
                while self.alarma_activa and self.corriendo:
                    ctypes.windll.winmm.mciSendStringW('status myaudio mode', buf, 128, None)
                    if buf.value != 'playing':
                        break
                    time.sleep(0.1)
                    
                self.detener_sonido()
            except Exception as e:
                logging.error(f"Error reproduciendo audio: {e}")
                
    def _bucle_monitoreo(self):
        while self.corriendo:
            if not self.alarma_activa:
                inactividad = time.time() - self.ultimo_movimiento
                if inactividad >= self.umbral:
                    self.alarma_activa = True
                    self.emitir_sonido()
            time.sleep(0.5)

    def _bucle_tray(self):
        try:
            if os.path.exists(ICON_PATH):
                image = Image.open(ICON_PATH)
            else:
                image = Image.new('RGB', (64, 64), color='red')
                
            menu = pystray.Menu(
                pystray.MenuItem("Configuración...", lambda: self.cola_gui.put("SHOW")),
                pystray.MenuItem("Salir", self._on_salir)
            )
            self.icon = pystray.Icon("MouseGuard", image, "MouseGuard Activo", menu)
            self.icon.run()
        except Exception as e:
            logging.error(f"Error en System Tray: {e}")
            
    def _on_salir(self):
        self.corriendo = False
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.cola_gui.put("QUIT")
        
    def run(self):
        # El hilo principal es el de la GUI (Tkinter)
        self.root.mainloop()

if __name__ == "__main__":
    app = MouseGuardApp()
    app.run()