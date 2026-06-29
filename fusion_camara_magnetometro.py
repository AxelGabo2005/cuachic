#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
 FUSION CAMARA USB + MAGNETOMETRO MLX90393  (Jetson Orin NX)
====================================================================
 - La camara USB (V4L2) muestra el video real en tiempo real.
 - El MLX90393 se lee en un HILO aparte para NO frenar el video.
 - En el CENTRO del encuadre (posicion fisica conocida del sensor)
   se dibuja un cuadro que:
       * crece segun la fuerza |Z|  (iman mas cerca = mas grande)
       * es AZUL con "N" si Z es positivo alto  (Polo Norte)
       * es ROJO con "S" si Z es negativo bajo   (Polo Sur)
       * desaparece si |Z| esta por debajo del umbral
 - HUD fijo en la esquina con X/Y/Z y estado.

 NOTA HONESTA: con UN solo sensor no se localiza el iman en el
 espacio. El cuadro marca la ZONA del sensor y la etiqueta con el
 dato magnetico (polaridad + fuerza). No es triangulacion.

 Ejecutar con:  python3 fusion_camara_magnetometro.py
 Salir: tecla 'q'. Recalibrar: tecla 'c'.
====================================================================
"""

import cv2
import numpy as np
import time
import threading   # Para leer el sensor en paralelo al video

try:
    from smbus2 import SMBus, i2c_msg
except ImportError:
    raise SystemExit("Falta smbus2. Instala:  pip3 install --user smbus2")

# ====================================================================
#  1) CONFIGURACION (ajusta aqui)
# ====================================================================

# --- I2C / Sensor ---
I2C_BUS = 1                # <-- TU BUS (lo corregiste a 1). Cambia si hace falta.
MLX_ADDR = 0x0C            # Direccion del MLX90393

# --- Camara ---
CAM_INDICE = 0             # Indice que funciono en test_camara.py (cambia si era otro)
CAM_ANCHO = 640
CAM_ALTO = 480

# --- Umbrales de deteccion (uT aprox). Ajusta a tu iman/distancia ---
UMBRAL_Z = 500.0           # |Z| < esto => no se dibuja el cuadro
UMBRAL_N = 500.0           # Z >  +esto => Norte
UMBRAL_S = -500.0          # Z <   esto => Sur

# --- Calibracion ---
N_MUESTRAS_CALIBRACION = 50

# --- Escalado del cuadro central ---
ESCALA_Z = 0.05            # px de "radio" por unidad de |Z|
TAM_MIN = 40               # lado minimo del cuadro (px)
TAM_MAX = 300              # lado maximo (px)

# --- Sensibilidad (uT/LSB aprox) ---
SENS_XY = 0.150
SENS_Z = 0.242

# ====================================================================
#  2) COMANDOS MLX90393
# ====================================================================
CMD_SM = 0x30
CMD_RM = 0x40
CMD_RT = 0xF0
EJES_ZYX = 0x0E


class MLX90393:
    """Driver minimo del MLX90393 por smbus2."""

    def __init__(self, bus_num, address):
        self.address = address
        self.bus = SMBus(bus_num)

    def _transferir(self, datos_envio, n_lectura):
        escritura = i2c_msg.write(self.address, datos_envio)
        if n_lectura > 0:
            lectura = i2c_msg.read(self.address, n_lectura)
            self.bus.i2c_rdwr(escritura, lectura)
            return list(lectura)
        self.bus.i2c_rdwr(escritura)
        return []

    def reset(self):
        try:
            self._transferir([CMD_RT], 1)
        except Exception:
            pass
        time.sleep(0.05)

    def configurar(self):
        self.reset()

    def _iniciar(self):
        self._transferir([CMD_SM | EJES_ZYX], 1)

    def _leer(self):
        datos = self._transferir([CMD_RM | EJES_ZYX], 7)
        if len(datos) < 7:
            raise IOError("Lectura I2C incompleta")
        z = self._s16((datos[1] << 8) | datos[2])
        y = self._s16((datos[3] << 8) | datos[4])
        x = self._s16((datos[5] << 8) | datos[6])
        return x, y, z

    @staticmethod
    def _s16(v):
        return v - 65536 if v > 32767 else v

    def leer_xyz(self):
        self._iniciar()
        time.sleep(0.010)
        xr, yr, zr = self._leer()
        return xr * SENS_XY, yr * SENS_XY, zr * SENS_Z

    def cerrar(self):
        try:
            self.bus.close()
        except Exception:
            pass


# ====================================================================
#  3) HILO LECTOR DEL SENSOR (no bloquea el video)
# ====================================================================
class LectorMagnetometro(threading.Thread):
    """
    Lee el sensor en segundo plano. El bucle de video solo consulta
    los ultimos valores (rapido), sin esperar al I2C lento.
    """
    def __init__(self, sensor):
        super().__init__(daemon=True)
        self.sensor = sensor
        self.lock = threading.Lock()
        self.x = self.y = self.z = 0.0      # valores ya con offset
        self.offset = (0.0, 0.0, 0.0)
        self.activo = True
        self.ok = False                      # True si la ultima lectura fue valida

    def calibrar(self, n):
        print(f"[CALIBRACION] {n} muestras... NO acerques el iman.")
        sx = sy = sz = 0.0
        validas = 0
        for i in range(n):
            try:
                x, y, z = self.sensor.leer_xyz()
                sx += x; sy += y; sz += z
                validas += 1
            except Exception:
                pass
            time.sleep(0.02)
        if validas == 0:
            raise RuntimeError("Calibracion fallida: 0 muestras. Revisa cableado/bus.")
        self.offset = (sx/validas, sy/validas, sz/validas)
        print(f"[CALIBRACION] Offset: X={self.offset[0]:.1f} "
              f"Y={self.offset[1]:.1f} Z={self.offset[2]:.1f} "
              f"({validas}/{n} validas)")

    def run(self):
        ox, oy, oz = self.offset
        while self.activo:
            try:
                xr, yr, zr = self.sensor.leer_xyz()
                with self.lock:
                    self.x = xr - self.offset[0]
                    self.y = yr - self.offset[1]
                    self.z = zr - self.offset[2]
                    self.ok = True
            except Exception:
                with self.lock:
                    self.ok = False     # marca lectura mala (cable 60cm)
            time.sleep(0.02)

    def valores(self):
        with self.lock:
            return self.x, self.y, self.z, self.ok

    def detener(self):
        self.activo = False


# ====================================================================
#  4) CAMARA USB (V4L2)
# ====================================================================
def inicializar_camara():
    print("[INFO] Abriendo camara USB (V4L2)...")
    cap = cv2.VideoCapture(CAM_INDICE, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"[ERROR] No abre /dev/video{CAM_INDICE}. Prueba otro indice.")
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_ANCHO)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_ALTO)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # sin cache: video con menos retraso
    print("[INFO] Camara USB conectada.")
    return cap


# ====================================================================
#  5) DIBUJO DEL OVERLAY SOBRE EL VIDEO
# ====================================================================
def dibujar_overlay(frame, x, y, z, lectura_ok):
    """Dibuja sobre el frame REAL de la camara el cuadro central + HUD."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2     # centro del encuadre = posicion del sensor

    # --- Cruz central (marca la posicion fija del sensor) ---
    cv2.line(frame, (cx-15, cy), (cx+15, cy), (180, 180, 180), 1)
    cv2.line(frame, (cx, cy-15), (cx, cy+15), (180, 180, 180), 1)

    # --- HUD fijo arriba a la izquierda ---
    cv2.putText(frame, f"X: {x:7.1f} uT", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
    cv2.putText(frame, f"Y: {y:7.1f} uT", (10, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
    cv2.putText(frame, f"Z: {z:7.1f} uT", (10, 71),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

    # Indicador de salud del bus I2C (cable de 60 cm)
    estado_i2c = "I2C OK" if lectura_ok else "I2C ..."
    color_i2c = (0, 255, 0) if lectura_ok else (0, 165, 255)
    cv2.putText(frame, estado_i2c, (10, 94),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_i2c, 1)

    # --- Logica de deteccion / cuadro central ---
    if abs(z) < UMBRAL_Z:
        cv2.putText(frame, "STATUS: CLEAR (acerca el iman)", (10, h-15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame

    # Tamaño del cuadro segun |Z|
    lado = int(abs(z) * ESCALA_Z)
    lado = max(TAM_MIN, min(TAM_MAX, lado))
    m = lado // 2

    # Polaridad -> color + letra
    if z > UMBRAL_N:
        letra, color = "N", (255, 0, 0)     # Azul
    else:
        letra, color = "S", (0, 0, 255)     # Rojo

    # Cuadro centrado en el sensor
    cv2.rectangle(frame, (cx-m, cy-m), (cx+m, cy+m), color, 3)

    # Etiqueta DENTRO del cuadro: letra + fuerza
    esc = max(0.9, lado / 90.0)
    (tw, th), _ = cv2.getTextSize(letra, cv2.FONT_HERSHEY_SIMPLEX, esc, 2)
    cv2.putText(frame, letra, (cx - tw//2, cy + th//2),
                cv2.FONT_HERSHEY_SIMPLEX, esc, color, 2)
    cv2.putText(frame, f"{abs(z):.0f} uT", (cx-m, cy-m-8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # HUD de estado abajo
    polo = "NORTE" if letra == "N" else "SUR"
    cv2.putText(frame, f"STATUS: DETECTADO  POLO {polo}", (10, h-15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


# ====================================================================
#  6) PROGRAMA PRINCIPAL
# ====================================================================
def main():
    sensor = None
    lector = None
    cap = None
    try:
        # --- Sensor ---
        print(f"[INFO] Abriendo I2C /dev/i2c-{I2C_BUS} addr 0x{MLX_ADDR:02X}...")
        sensor = MLX90393(I2C_BUS, MLX_ADDR)
        sensor.configurar()

        lector = LectorMagnetometro(sensor)
        lector.calibrar(N_MUESTRAS_CALIBRACION)
        lector.start()   # arranca el hilo de lectura continua

        # --- Camara ---
        cap = inicializar_camara()
        if cap is None:
            raise RuntimeError("Camara no disponible.")

        print("[INFO] Todo listo. 'q' salir, 'c' recalibrar.")
        cv2.namedWindow("Fusion Camara + Magnetometro", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Fusion Camara + Magnetometro", CAM_ANCHO, CAM_ALTO)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Frame perdido.")
                break

            # Consulta rapida de los ultimos valores del sensor (no bloquea)
            x, y, z, ok = lector.valores()

            frame = dibujar_overlay(frame, x, y, z, ok)
            cv2.imshow("Fusion Camara + Magnetometro", frame)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q'):
                break
            elif tecla == ord('c'):
                # Recalibrar: pausamos el hilo, recalibramos, reanudamos
                lector.detener()
                lector.join()
                lector = LectorMagnetometro(sensor)
                lector.calibrar(N_MUESTRAS_CALIBRACION)
                lector.start()

    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido (Ctrl+C).")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if lector is not None:
            lector.detener()
        if cap is not None:
            cap.release()
        if sensor is not None:
            sensor.cerrar()
        cv2.destroyAllWindows()
        print("[INFO] Recursos liberados. Fin.")


if __name__ == "__main__":
    main()
