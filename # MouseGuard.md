# MouseGuard: Sistema de Seguridad de Hardware

MouseGuard es una aplicación de seguridad de hardware ligera y redundante para entornos Windows. Su propósito es monitorear la actividad del mouse inalámbrico y emitir una alerta sonora agresiva y de alta prioridad si se detecta un período prolongado de inactividad, previniendo así el olvido del dispositivo al abandonar el puesto de trabajo.

---

## ⚙️ Características Principales

* **Monitoreo Constante:** Captura eventos de movimiento, clics y scroll en tiempo real mediante la librería `pynput`.
* **Arquitectura de Audio Redundante:** Implementa un sistema *Fail-safe* de 3 capas para garantizar que la alerta suene incluso si el sistema operativo tiene restricciones de controladores.
* **Modo Oculto (System Tray):** La aplicación se ejecuta de manera silenciosa en la bandeja del sistema (al lado de la hora de Windows) con un ícono interactivo.
* **Manual Integrado:** Incluye un manual de usuario de fácil acceso a través del menú de la bandeja, diseñado para personas que no tienen experiencia técnica.

---

## 🚀 Instalación y Uso

**Uso Directo (El más fácil):**
Simplemente haz doble clic sobre el archivo ejecutable `MouseGuard.exe` ubicado en la carpeta `dist`.
Aparecerá un pequeño ícono azul en la bandeja del sistema de Windows. 
- Haz clic derecho sobre el ícono para leer el **Manual de Uso** o para **Salir** de la aplicación.

**Uso Avanzado (Consola):**
Si quieres configurar parámetros personalizados, puedes abrir una terminal y ejecutar la aplicación (ya sea el script Python o el .exe) con argumentos:
```bash
# Cambiar el tiempo de inactividad a 120 segundos
MouseGuard.exe --umbral 120

# Usar un archivo de audio diferente y mostrar la consola
MouseGuard.exe --audio mi_alarma.wav --console

# Mostrar la ayuda
MouseGuard.exe -h
```

---

## 🛠️ Compilación para Desarrolladores

Si deseas clonar el proyecto y compilarlo desde el código fuente, sigue estos pasos:

1. Clona este repositorio en tu equipo local.
2. Instala las dependencias requeridas: `pip install -r requirements.txt`
3. Ejecuta el script de construcción: `build.bat`
   - *Alternativamente:* `pyinstaller --noconsole --onefile mouse_guard.py`
4. El archivo final `.exe` se encontrará en la carpeta `dist/`.

---

## 📁 Estructura de Archivos Recomendada

### 1. Archivo `requirements.txt`
Contiene las dependencias necesarias:
```text
pynput==1.7.7
pystray>=0.19.3
Pillow>=9.0.0
pyinstaller>=6.0.0
```

### 2. Archivo `.gitignore`
Evita subir archivos basura, cachés de Python y los binarios generados (`dist/`, `build/`).

### 3. Archivo `LICENSE`
El proyecto se distribuye bajo la Licencia MIT.