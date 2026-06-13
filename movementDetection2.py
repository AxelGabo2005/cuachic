import cv2
import numpy as np

# --- ADAPTADO PARA WINDOWS CON WEBCAM USB ---
# CAP_DSHOW es el backend nativo de Windows (DirectShow).
# Reemplaza CAP_V4L2 que solo funciona en Linux/Jetson.
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Si el índice 0 no funciona, prueba con 1 o 2:
# cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Error: No se puede acceder a la camara.")
    print("Prueba cambiando el numero en VideoCapture(0) por 1 o 2.")
    exit()

# Forzamos la resolución de captura
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

previous_frame = None

cv2.namedWindow("Deteccion de Movimiento", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Deteccion de Movimiento", 600, 600)

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

    # Sustraccion de fondo (Absdiff)
    frame_delta = cv2.absdiff(previous_frame, gray_frame)

    # Generacion de la mascara binaria
    _, threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)

    # Extraccion de contornos de la mascara
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Filtro de area minima para evitar ruido por parpadeo de luz
        if cv2.contourArea(contour) > 100:

            # Dibujado de la silueta del movimiento (Puntos verdes)
            for point in contour:
                x, y = point[0]
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            # Dibujado de la caja delimitadora (Rectangulo morado)
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (77, 0, 110), 2)

    # Visualizacion
    cv2.imshow("Deteccion de Movimiento", frame)

    # Actualizacion del bufer para el siguiente ciclo
    previous_frame = gray_frame

    # Interrupcion por teclado
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Limpieza de memoria y hardware
cap.release()
cv2.destroyAllWindows()