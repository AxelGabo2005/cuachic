import cv2
import numpy as np

def inicializar_camara():
    pipeline_csi = (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1 ! "
        "nvvidconv ! video/x-raw, format=(string)BGRx ! "
        "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
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
        print("ÉXITO: Cámara USB conectada.")
        return cap
        
    return None

def main():
    cap = inicializar_camara()
    
    if cap is None:
        print("ERROR FATAL: La cámara no responde.")
        return

    print("=== NIX-LAB: SISTEMA DEFINITIVO ANTI-RUIDO (SINGLE TARGET) ===")

    # Molde para limpiar puntos falsos
    kernel = np.ones((5, 5), np.uint8)

    while True:
        ret, frame = cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Desenfocamos un poco más para matar texturas del papel
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        
        # Threshold Adaptativo: Se ajusta a la luz automáticamente, 
        # C=6 ayuda a eliminar el ruido del fondo de la mesa
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 31, 6)

        # MORPH_OPEN elimina la basura visual pequeña
        thresh_limpio = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(thresh_limpio, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        mejor_cnt = None
        mejor_score = 9999.0  # Un puntaje alto significa "mucho error"

        for cnt in contours:
            area = cv2.contourArea(cnt)
            
            # Filtro de distancia (cerca y lejos)
            if 150 < area < 4000:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = float(w) / h
                
                # La C es casi un cuadrado perfecto (aspect ratio cercano a 1.0)
                if 0.75 < aspect < 1.25:
                    hull = cv2.convexHull(cnt)
                    solidity = area / (cv2.contourArea(hull) + 1e-5)
                    
                    # La C tiene una solidez ideal de aprox 0.55 a 0.65
                    if 0.45 < solidity < 0.72:
                        
                        # --- SISTEMA DE PUNTUACIÓN (SCORING) ---
                        # Calculamos qué tan "perfecto" es este contorno. 
                        # 0.0 es la forma perfecta de una "C".
                        error_aspecto = abs(1.0 - aspect)
                        error_solidez = abs(0.6 - solidity)
                        score_total = error_aspecto + error_solidez
                        
                        # Nos quedamos SOLAMENTE con el que tenga el mejor puntaje
                        if score_total < mejor_score:
                            mejor_score = score_total
                            mejor_cnt = cnt

        # DIBUJAMOS SOLO SI ENCONTRAMOS EL TARGET GANADOR
        if mejor_cnt is not None:
            x, y, w, h = cv2.boundingRect(mejor_cnt)
            M = cv2.moments(mejor_cnt)
            
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                bx = x + w // 2
                by = y + h // 2
                
                dx = bx - cx
                dy = by - cy
                
                # Dibujamos el contorno exacto
                cv2.drawContours(frame, [mejor_cnt], -1, (0, 255, 0), 3)
                
                # Flecha indicando la apertura (larga y precisa)
                fin_x = cx + int(dx * 7)
                fin_y = cy + int(dy * 7)
                
                cv2.arrowedLine(frame, (cx, cy), (fin_x, fin_y), (0, 0, 255), 4, tipLength=0.3)
                
                cv2.putText(frame, "TARGET-3C LOCKED", (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('NIX-LAB: VISION FINAL', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()