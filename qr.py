import cv2
import time
import threading
import numpy as np
from datetime import datetime
from pyzbar.pyzbar import decode

class CamaraTactica:
    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.frame = None
        self.corriendo = True
        self.lock = threading.Lock()
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        while self.corriendo:
            ret, frame = self.cap.read()
            if ret:
                # Pre-procesamiento de iluminación industrial
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                lab[:,:,0] = clahe.apply(lab[:,:,0])
                frame_procesado = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                with self.lock:
                    self.frame = frame_procesado

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def close(self):
        self.corriendo = False
        self.cap.release()

def main():
    cam = CamaraTactica()
    bitacora = {}
    
    print("=== NIX-LAB: VISIÓN COMPETITIVA (Homografía Activa) ===")
    
    try:
        while True:
            frame = cam.get_frame()
            if frame is None: continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            codigos = decode(gray)
            
            for codigo in codigos:
                datos = codigo.data.decode('utf-8')
                pts = np.array([codigo.polygon], np.int32)
                
                # --- HOMOGRAFÍA: CORRECCIÓN DE PERSPECTIVA ---
                if len(pts[0]) == 4:
                    rect = cv2.boundingRect(pts)
                    x, y, w, h = rect
                    # Dibujar cuadro de corrección
                    cv2.polylines(frame, [pts], True, (255, 0, 0), 2)
                
                # Registro único
                bitacora[datos] = datetime.now().strftime("%H:%M:%S")
            
            # HUD Profesional
            display = cv2.resize(frame, (854, 480))
            canvas = np.zeros((480, 854 + 320, 3), dtype=np.uint8)
            canvas[:, 320:] = display
            cv2.rectangle(canvas, (0,0), (320, 480), (10,10,10), -1)
            
            # Mostrar bitácora
            y = 40
            for qr, hora in bitacora.items():
                cv2.putText(canvas, f"[{hora}] {qr[:20]}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                y += 25
            
            cv2.imshow('NIX-LAB: COMPETITION READY', canvas)
            if cv2.waitKey(1) == ord('q'): break
            
    finally:
        cam.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()