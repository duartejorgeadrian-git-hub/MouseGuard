import time
import winsound
import ctypes
import sys
import os
import argparse
import logging
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

class MouseGuard:
    def __init__(self, umbral=60, audio_personalizado=None, use_console=False):
        self.umbral = umbral
        self.audio_personalizado = audio_personalizado
        self.use_tray = not use_console and HAS_TRAY
        self.ultimo_movimiento = time.time()
        self.listener = None
        self.corriendo = False
        self._configurar_logging()

    def _configurar_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def al_evento_mouse(self, *args):
        self.ultimo_movimiento = time.time()

    def emitir_sonido_estridente(self):
        exito = False
        
        if self.audio_personalizado and os.path.exists(self.audio_personalizado) and self.audio_personalizado.lower().endswith('.wav'):
            try:
                winsound.PlaySound(self.audio_personalizado, winsound.SND_FILENAME | winsound.SND_SYNC)
                exito = True
            except Exception:
                pass 

        if not exito:
            try:
                winsound.PlaySound('SystemHand', winsound.SND_ALIAS | winsound.SND_SYNC)
                exito = True
            except Exception:
                pass 

        if not exito:
            try:
                ctypes.windll.user32.MessageBeep(0x00000010)
                time.sleep(0.4) 
                exito = True
            except Exception:
                pass 
                
        if not exito:
            try:
                winsound.Beep(2500, 400) 
            except Exception:
                pass

    def _bucle_monitoreo(self):
        try:
            while self.corriendo:
                tiempo_actual = time.time()
                tiempo_inactivo = tiempo_actual - self.ultimo_movimiento

                if tiempo_inactivo > self.umbral:
                    logging.warning(f"ALERTA DETONADA: ¡MOUSE OLVIDADO! ({int(tiempo_inactivo)}s de inactividad)")
                    
                    for _ in range(8):
                        if not self.corriendo:
                            break
                        self.emitir_sonido_estridente()
                        time.sleep(0.1)
                    
                    self.ultimo_movimiento = time.time()
                    logging.info("Alarma finalizada. Monitoreo reanudado...")

                time.sleep(1)
        except Exception as e:
            logging.error(f"Error en bucle de monitoreo: {e}")

    def mostrar_manual(self, icon=None, item=None):
        # Crear una pequeña ventana oculta de tkinter como root para evitar glitches
        root = tk.Tk()
        root.withdraw()
        # Mostrar el mensaje de información
        mensaje = (
            "Bienvenido al Manual de Uso de MouseGuard\n\n"
            "¿Para qué sirve?\n"
            "MouseGuard emite una fuerte alerta sonora si no detecta "
            f"actividad en el mouse durante {self.umbral} segundos. "
            "Su objetivo es recordarte que no olvides llevar tu mouse inalámbrico "
            "contigo cuando te retires de la computadora.\n\n"
            "¿Cómo funciona?\n"
            "Mientras la aplicación esté abierta (puedes ver un icono azul en la "
            "bandeja del sistema, junto a la hora de Windows), estará vigilando el mouse.\n"
            "- Si mueves el mouse, el contador se reinicia.\n"
            "- Si lo dejas quieto y te vas, sonará la alarma repetidamente.\n\n"
            "¿Cómo detenerlo?\n"
            "Para cerrar la aplicación, haz clic derecho sobre su icono en la bandeja "
            "del sistema y selecciona 'Salir'.\n\n"
            "Tip: Para cambiar el tiempo de espera, puedes abrir el ejecutable desde la consola de "
            "comandos agregando '--umbral SEG' (ej: MouseGuard.exe --umbral 120)."
        )
        messagebox.showinfo("Manual de Uso - MouseGuard", mensaje)
        root.destroy()

    def iniciar(self):
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
            # Iniciar monitoreo en un hilo
            hilo_monitoreo = threading.Thread(target=self._bucle_monitoreo, daemon=True)
            hilo_monitoreo.start()
            self._iniciar_tray()
        else:
            print("==================================================")
            print("       SISTEMA DE SEGURIDAD DE HARDWARE ACTIVO    ")
            print("==================================================")
            print("[*] Presiona Ctrl+C en esta ventana para detener.\n")
            try:
                self._bucle_monitoreo()
            except KeyboardInterrupt:
                self.detener()

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

    def _crear_icono(self):
        # Crear una imagen simple (un cuadrado azul)
        image = Image.new('RGB', (64, 64), color=(0, 120, 215))
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        return image

    def _iniciar_tray(self):
        image = self._crear_icono()
        menu = pystray.Menu(
            pystray.MenuItem("Manual de Uso", self.mostrar_manual),
            pystray.MenuItem("Salir", self.detener)
        )
        icon = pystray.Icon("MouseGuard", image, "MouseGuard", menu)
        icon.run()

def main():
    parser = argparse.ArgumentParser(description="MouseGuard: Sistema de Seguridad de Hardware.")
    parser.add_argument(
        "--umbral",
        type=int,
        default=60,
        help="Tiempo de inactividad en segundos para disparar la alarma (por defecto: 60)"
    )
    parser.add_argument(
        "--audio",
        type=str,
        default=None,
        help="Ruta a un archivo .wav para usar como alarma personalizada"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Ejecutar mostrando la consola (en lugar del modo oculto predeterminado)"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Abrir el manual de uso interactivo y salir"
    )
    
    args = parser.parse_args()
    
    guard = MouseGuard(umbral=args.umbral, audio_personalizado=args.audio, use_console=args.console)
    
    if args.manual:
        guard.mostrar_manual()
        sys.exit(0)

    if not args.console and not HAS_TRAY:
        print("[!] Advertencia: Faltan dependencias (pystray/Pillow). Ejecutando en modo consola.")
        guard.use_tray = False

    guard.iniciar()

if __name__ == "__main__":
    main()