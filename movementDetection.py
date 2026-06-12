import cv2
import numpy as np

# --- OPTIMIZACIÓN PARA ARQUITECTURA JETSON ---
# Utilizamos el backend V4L2 (Video4Linux2). Esto evita cuellos de botella 
# en la CPU de la placa al capturar video desde una cámara web USB.
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# NOTA DE HARDWARE: Si decides no usar una cámara USB y conectas una cámara 
# CSI nativa (de cable plano), OpenCV no la detectará con el '0'.
# Deberás comentar la línea de arriba y usar esta tubería GStreamer:
# cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink", cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Error: No se puede acceder a la cámara de la Jetson.")
    exit()

# Forzamos la resolución de captura
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

previous_frame = None

cv2.namedWindow("Detección de Movimiento", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Detección de Movimiento", 600, 600)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar el frame.")
        break

    # Preprocesamiento de la imagen (Escala de grises + Desenfoque)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray_frame
        continue

    # Sustracción de fondo (Absdiff)
    frame_delta = cv2.absdiff(previous_frame, gray_frame)

    # Generación de la máscara binaria
    _, threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)

    # Extracción de contornos de la máscara
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Filtro de área mínima para evitar ruido por parpadeo de luz
        if cv2.contourArea(contour) > 100:
            
            # Dibujado de la silueta del movimiento (Puntos verdes)
            for point in contour:
                x, y = point[0]
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            # Dibujado de la caja delimitadora (Rectángulo morado/azul)
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (77, 0, 110), 2)

    # Visualización
    cv2.imshow("Detección de Movimiento", frame)

    # Actualización del búfer para el siguiente ciclo
    previous_frame = gray_frame

    # Interrupción por teclado
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Limpieza de memoria y hardware
cap.release()
cv2.destroyAllWindows()
