import time
import sys
import os
import argparse
import logging
import threading
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pynput import mouse

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from playsound import playsound
except ImportError:
    playsound = None

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    """ Obtener la ruta absoluta del recurso, compatible con PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DEFAULT_AUDIO = resource_path("purge_siren.mp3")
ICON_PATH = resource_path("icon.ico")

class MouseGuard:
    def __init__(self, use_console=False):
        self.use_tray = not use_console and HAS_TRAY
        self.ultimo_movimiento = time.time()
        self.listener = None
        self.corriendo = False
        
        # Valores por defecto
        self.umbral = 60
        self.audio_personalizado = DEFAULT_AUDIO
        self.repeticiones = 1

        self._configurar_logging()
        self.cargar_configuracion()

    def _configurar_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def cargar_configuracion(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.umbral = data.get('umbral', 60)
                    self.audio_personalizado = data.get('audio', DEFAULT_AUDIO)
                    self.repeticiones = data.get('repeticiones', 1)
                self.iniciar()
            except Exception as e:
                logging.error(f"Error al leer config.json: {e}")
                self.mostrar_configuracion()
        else:
            self.mostrar_configuracion()

    def guardar_configuracion(self, umbral, audio, repeticiones):
        self.umbral = umbral
        self.audio_personalizado = audio
        self.repeticiones = repeticiones
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'umbral': self.umbral,
                    'audio': self.audio_personalizado,
                    'repeticiones': self.repeticiones
                }, f, indent=4)
        except Exception as e:
            logging.error(f"Error al guardar config.json: {e}")

    def mostrar_configuracion(self, icon=None, item=None):
        def guardar():
            try:
                u = int(entry_umbral.get())
                r = int(scale_rep.get())
                a = var_audio.get()
                if not os.path.exists(a):
                    a = DEFAULT_AUDIO
                self.guardar_configuracion(u, a, r)
                root.destroy()
                if not self.corriendo:
                    self.iniciar()
            except ValueError:
                messagebox.showerror("Error", "El umbral debe ser un número entero.")

        def seleccionar_audio():
            filepath = filedialog.askopenfilename(
                title="Seleccionar sonido",
                filetypes=(("Archivos de audio", "*.mp3 *.wav"), ("Todos los archivos", "*.*"))
            )
            if filepath:
                var_audio.set(filepath)

        root = tk.Tk()
        root.title("Configuración - MouseGuard")
        root.geometry("450x380")
        root.resizable(False, False)
        
        try:
            root.iconbitmap(ICON_PATH)
        except:
            pass

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Umbral
        ttk.Label(frame, text="Tiempo de inactividad (segundos):").pack(anchor=tk.W)
        entry_umbral = ttk.Entry(frame)
        entry_umbral.insert(0, str(self.umbral))
        entry_umbral.pack(fill=tk.X, pady=(0, 15))

        # Audio
        ttk.Label(frame, text="Archivo de Sonido:").pack(anchor=tk.W)
        var_audio = tk.StringVar(value=self.audio_personalizado)
        audio_frame = ttk.Frame(frame)
        audio_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Entry(audio_frame, textvariable=var_audio, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(audio_frame, text="Examinar...", command=seleccionar_audio).pack(side=tk.RIGHT)

        # Repeticiones
        ttk.Label(frame, text="Intensidad de repeticiones (Para sonidos cortos):").pack(anchor=tk.W)
        scale_rep = tk.Scale(frame, from_=1, to=20, orient=tk.HORIZONTAL)
        scale_rep.set(self.repeticiones)
        scale_rep.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(frame, text="Guardar y Ejecutar", command=guardar).pack(fill=tk.X, pady=10)
        
        # Centrar
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (450 // 2)
        y = (root.winfo_screenheight() // 2) - (380 // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()

    def maximizar_volumen(self):
        if not HAS_PYCAW:
            return
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(1.0, None) # 1.0 es 100%
            logging.info("Volumen del sistema maximizado al 100%.")
        except Exception as e:
            logging.error(f"Error al maximizar volumen: {e}")

    def al_evento_mouse(self, *args):
        self.ultimo_movimiento = time.time()

    def emitir_sonido(self):
        self.maximizar_volumen()
        
        audio = self.audio_personalizado
        if not os.path.exists(audio):
            audio = DEFAULT_AUDIO
            
        for _ in range(self.repeticiones):
            if not self.corriendo:
                break
            if playsound and os.path.exists(audio):
                try:
                    playsound(audio)
                except Exception as e:
                    logging.error(f"Error playsound: {e}")
                    self._sonido_fallback()
            else:
                self._sonido_fallback()

    def _sonido_fallback(self):
        try:
            import winsound
            winsound.PlaySound('SystemHand', winsound.SND_ALIAS | winsound.SND_SYNC)
        except:
            pass

    def _bucle_monitoreo(self):
        try:
            while self.corriendo:
                tiempo_actual = time.time()
                tiempo_inactivo = tiempo_actual - self.ultimo_movimiento

                if tiempo_inactivo > self.umbral:
                    logging.warning(f"ALERTA DETONADA: ¡MOUSE OLVIDADO! ({int(tiempo_inactivo)}s de inactividad)")
                    self.emitir_sonido()
                    
                    self.ultimo_movimiento = time.time()
                    logging.info("Alarma finalizada. Monitoreo reanudado...")

                time.sleep(1)
        except Exception as e:
            logging.error(f"Error en bucle de monitoreo: {e}")

    def iniciar(self):
        if self.corriendo:
            return
            
        logging.info("Iniciando MouseGuard...")
        logging.info(f"Umbral de disparo: {self.umbral} segundos de inactividad.")

        try:
            self.listener = mouse.Listener(
                on_move=self.al_evento_mouse,
                on_click=self.al_evento_mouse,
                on_scroll=self.al_evento_mouse
            )
            self.listener.start()
        except Exception as e:
            logging.error(f"Fallo al iniciar la lectura del dispositivo: {e}")
            sys.exit(1)

        self.ultimo_movimiento = time.time()
        self.corriendo = True

        if self.use_tray:
            logging.info("Modo System Tray (Bandeja del sistema).")
            hilo_monitoreo = threading.Thread(target=self._bucle_monitoreo, daemon=True)
            hilo_monitoreo.start()
            return True
        else:
            print("==================================================")
            print("       SISTEMA DE SEGURIDAD DE HARDWARE ACTIVO    ")
            print("==================================================")
            print("[*] Presiona Ctrl+C en esta ventana para detener.\n")
            try:
                self._bucle_monitoreo()
            except KeyboardInterrupt:
                self.detener()
            return False

    def detener(self, icon=None, item=None):
        logging.info("Secuencia de apagado iniciada. Deteniendo listener...")
        self.corriendo = False
        if self.listener:
            self.listener.stop()
        if icon:
            icon.stop()
        logging.info("Sistema detenido exitosamente.")
        if not self.use_tray:
            sys.exit(0)

    def _iniciar_tray(self):
        try:
            image = Image.open(ICON_PATH)
        except:
            image = Image.new('RGB', (64, 64), color=(0, 120, 215))
            
        menu = pystray.Menu(
            pystray.MenuItem("Configuración", self.mostrar_configuracion),
            pystray.MenuItem("Salir", self.detener)
        )
        icon = pystray.Icon("MouseGuard", image, "MouseGuard", menu)
        icon.run()

def main():
    parser = argparse.ArgumentParser(description="MouseGuard: Sistema de Seguridad de Hardware.")
    parser.add_argument("--console", action="store_true", help="Ejecutar mostrando la consola")
    args = parser.parse_args()
    
    guard = MouseGuard(use_console=args.console)
    
    if not guard.corriendo:
        sys.exit(0)
        
    if guard.use_tray:
        guard._iniciar_tray()

if __name__ == "__main__":
    main()