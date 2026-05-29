import cv2
import numpy as np
import time

def inicializar_camara():
    # Pipeline optimizado al máximo. 
    pipeline_csi = (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
        "nvvidconv ! video/x-raw, format=BGRx ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink max-buffers=1 drop=true"
    )
    
    print("Iniciando hardware de video...")
    cap = cv2.VideoCapture(pipeline_csi, cv2.CAP_GSTREAMER)
    if cap.isOpened():
        print("ÉXITO: Cámara CSI conectada.")
        return cap
        
    print("CSI no detectado. Intentando puerto USB...")
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Forzar a la cámara USB a no acumular memoria caché
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        print("ÉXITO: Cámara USB conectada.")
        return cap
    return None

def main():
    cap = inicializar_camara()
    if cap is None:
        print("ERROR FATAL: La cámara no responde.")
        return

    print("=== NIX-LAB: RADAR BARE METAL (CERO COLAPSOS) ===")

    ret, prev_frame = cap.read()
    if not ret: return
    
    # Trabajamos directamente en INT8 (Enteros). Cero floats.
    prev_gray = cv2.cvtColor(cv2.resize(prev_frame, (320, 240)), cv2.COLOR_BGR2GRAY)
    
    contador_frames = 0
    contornos_cacheados = []
    
    start_time = time.time()

    while True:
        current_time = time.time()
        ret, frame = cap.read()
        if not ret: break
        
        contador_frames += 1
        alerta = False
        
        # --- EL MOTOR ASÍNCRONO (FRAME SKIPPING) ---
        # Solo calculamos matemáticas 1 de cada 3 frames. 
        # La Jetson descansará el 66% del tiempo, evitando sobrecalentamientos.
        if contador_frames % 3 == 0:
            gray = cv2.cvtColor(cv2.resize(frame, (320, 240)), cv2.COLOR_BGR2GRAY)
            
            # Diferencia estricta entre el frame anterior y el actual.
            delta = cv2.absdiff(prev_gray, gray)
            
            # Umbral en 20: Sensible a dedos y cuadros negros en movimiento.
            _, thresh = cv2.threshold(delta, 20, 255, cv2.THRESH_BINARY)
            
            # Buscamos contornos y los guardamos en caché.
            contornos_cacheados, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Actualizamos el frame de referencia.
            prev_gray = gray
            
        # --- DIBUJO FLUIDO ---
        # Aunque la matemática descanse, los gráficos se dibujan a 30 FPS 
        # usando la memoria caché, manteniendo la visualización impecable.
        for cnt in contornos_cacheados:
            # Área mínima de 80: Atrapa la falange de un dedo sin detectar ruido de fondo.
            if cv2.contourArea(cnt) > 80:
                alerta = True
                
                # Escalado y silueta elástica ligera
                cnt_grande = cnt * 2
                hull = cv2.convexHull(cnt_grande)
                cv2.drawContours(frame, [hull], -1, (0, 255, 0), 2)
                
                # Punto de precisión
                M = cv2.moments(cnt_grande)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)

        # HUD
        fps = 1.0 / (current_time - start_time)
        start_time = current_time
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if alerta:
            cv2.putText(frame, "STATUS: TRACKING", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        else:
            cv2.putText(frame, "STATUS: CLEAR", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

        cv2.imshow('NIX-LAB: RADAR LIGERO', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main() 