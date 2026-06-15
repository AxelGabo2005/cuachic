import cv2
import numpy as np
from datetime import datetime
import os

# --- 1. CONFIGURACIÓN DE RUTAS Y ARCHIVOS ---
carpeta_salida = "recortes_qr_alineados"
archivo_registro = "registro_qr.csv"
archivo_ejecucion = "num_ejecucion.txt"

if not os.path.exists(carpeta_salida):
    os.makedirs(carpeta_salida)

# --- 2. CONTROL DEL NÚMERO DE EJECUCIÓN ---
# Leemos el archivo para saber en qué ejecución vamos. Si no existe, empezamos en 1.
num_ejecucion = 1
if os.path.exists(archivo_ejecucion):
    with open(archivo_ejecucion, "r") as f:
        try:
            num_ejecucion = int(f.read().strip()) + 1
        except ValueError:
            pass

# Guardamos el nuevo número para la próxima vez
with open(archivo_ejecucion, "w") as f:
    f.write(str(num_ejecucion))

# Guardamos la hora exacta en la que inició esta sesión
hora_inicio_ejecucion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 3. INICIALIZACIÓN DEL REGISTRO CSV ---
if not os.path.exists(archivo_registro):
    with open(archivo_registro, "w") as f:
        # Nuevas cabeceras estructuradas
        f.write("Num_Ejecucion,Inicio_Ejecucion,Hora_Deteccion,Datos_QR,Ruta_Imagen\n")

# --- 4. CONFIGURACIÓN DE VISIÓN ---
cap = cv2.VideoCapture(0)
qr_detector = cv2.QRCodeDetector()
codigos_procesados = set()

# Definimos el tamaño exacto en píxeles que queremos para la imagen final orientada
TAMANO_QR = 200
# Coordenadas destino para forzar los puntos a un cuadrado perfecto y plano
pts_destino = np.float32([
    [0, 0],                               # Arriba Izquierda
    [TAMANO_QR - 1, 0],                   # Arriba Derecha
    [TAMANO_QR - 1, TAMANO_QR - 1],       # Abajo Derecha
    [0, TAMANO_QR - 1]                    # Abajo Izquierda
])

cv2.namedWindow("Deteccion de QR", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Deteccion de QR", 600, 600)

print(f"--- Iniciando Ejecución #{num_ejecucion} a las {hora_inicio_ejecucion} ---")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    value, pts, _ = qr_detector.detectAndDecode(frame)

    if pts is not None and value:
        # Reformateamos a enteros para dibujar, pero guardamos la versión float para la perspectiva
        pts = np.int32(pts).reshape(-1, 2)

        if value not in codigos_procesados:
            codigos_procesados.add(value)

            ahora = datetime.now()
            hora_deteccion = ahora.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_archivo = ahora.strftime("%Y%m%d_%H%M%S")

            # --- 5. CORRECCIÓN DE PERSPECTIVA (WARPING) ---
            # OpenCV normalmente entrega los puntos en este orden: 
            # superior-izq, superior-der, inferior-der, inferior-izq.
            pts_origen = np.float32(pts)
            
            # Calculamos la matriz matemática que endereza el polígono
            matriz_perspectiva = cv2.getPerspectiveTransform(pts_origen, pts_destino)
            
            # Aplicamos la matriz al frame original. El resultado es un QR recto y estandarizado a 200x200px
            qr_alineado = cv2.warpPerspective(frame, matriz_perspectiva, (TAMANO_QR, TAMANO_QR))

            # --- 6. GUARDADO FINAL ---
            nombre_seguro = "".join([c for c in value if c.isalnum()])[:10]
            ruta_imagen = f"{carpeta_salida}/Ej{num_ejecucion}_{timestamp_archivo}_{nombre_seguro}.jpg"
            
            cv2.imwrite(ruta_imagen, qr_alineado)

            with open(archivo_registro, "a") as f:
                # Escribimos toda la data requerida separada por comas
                f.write(f"{num_ejecucion},{hora_inicio_ejecucion},{hora_deteccion},\"{value}\",{ruta_imagen}\n")
            
            print(f"Ejecución {num_ejecucion} | Guardado: {value} | Hora: {hora_deteccion}")

        # Dibujo visual en pantalla
        for i in range(4):
            cv2.line(frame, tuple(pts[i]), tuple(pts[(i + 1) % 4]), (0, 255, 0), 3)
        cv2.putText(frame, "Detectado", (pts[0][0], pts[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("Deteccion de QR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()