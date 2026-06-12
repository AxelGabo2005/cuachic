# HAZMAT Detection — YOLOv8 + OpenCV

Detección en tiempo real de señales HAZMAT (materiales peligrosos) usando un modelo YOLOv8 personalizado (`cuachic.pt`) y una cámara USB o integrada.

---

## Requisitos del sistema

| Componente | Mínimo recomendado |
|---|---|
| Python | 3.8 o superior |
| RAM | 4 GB |
| Cámara | USB o integrada compatible con OpenCV |
| GPU (opcional) | CUDA compatible (NVIDIA Jetson, RTX, etc.) |
| OS | Ubuntu 20.04 / 22.04 · Windows 10/11 · JetPack 5.x |

---

## Archivos necesarios

```
proyecto/
├── hazmat_detection.py   # Script principal
├── cuachic.pt            # Modelo entrenado (incluido)
└── README.md
```

> ⚠️ El archivo `cuachic.pt` debe estar en la **misma carpeta** que el script, o bien ajusta la variable `MODEL_PATH` con la ruta completa.

---

## Instalación de dependencias

### 1. Instalar PyTorch

#### PC con GPU NVIDIA (CUDA 11.8):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### PC sin GPU / solo CPU:
```bash
pip install torch torchvision
```

#### NVIDIA Jetson (JetPack 5.x):
PyTorch viene preinstalado con JetPack. Verifica con:
```bash
python3 -c "import torch; print(torch.__version__)"
```
Si no está, sigue la guía oficial: https://docs.nvidia.com/deeplearning/frameworks/install-pytorch-jetson-platform/

---

### 2. Instalar el resto de dependencias

```bash
pip install ultralytics opencv-python
```

O con un solo comando:
```bash
pip install ultralytics opencv-python torch torchvision
```

---

### 3. Verificar instalación

```bash
python3 -c "import ultralytics; import cv2; import torch; print('Todo OK')"
```

---

## Ejecución

```bash
python3 hazmat_detection.py
```

Presiona **ESC** para salir.

---

## Parámetros configurables

Abre el script y ajusta las variables al inicio según tu hardware:

```python
MODEL_PATH     = "cuachic.pt"   # Ruta al modelo
CAMERA_ID      = 0              # 0 = cámara por defecto, 1 = segunda cámara, etc.
CONFIDENCE     = 0.50           # Umbral de confianza (0.0 – 1.0)

IMG_SIZE       = 416            # Tamaño de inferencia:
                                #   320 → muy rápido, menos preciso
                                #   416 → balanceado  ← recomendado Jetson
                                #   640 → más preciso, más lento

PROCESS_EVERY  = 2              # Procesa 1 de cada N frames (reduce carga CPU/GPU)

CAM_WIDTH      = 1080           # Resolución de captura
CAM_HEIGHT     = 1080

WINDOW_WIDTH   = 1280           # Tamaño de la ventana de visualización
WINDOW_HEIGHT  = 1080
```

---

## Sobre el modelo `cuachic.pt`

- Formato: **YOLOv8** (Ultralytics)
- Entrenado para detectar: señales y etiquetas de materiales peligrosos (HAZMAT)
- Clases detectadas: definidas en el entrenamiento del modelo
- Para ver las clases disponibles ejecuta:

```python
from ultralytics import YOLO
model = YOLO("cuachic.pt")
print(model.names)
```

---

## Notas para NVIDIA Jetson

- Usa `IMG_SIZE = 320` o `416` para mantener FPS estable.
- Usa `PROCESS_EVERY = 2` o `3` si el CPU/GPU está saturado.
- La variable de entorno `TORCH_COMPILE_DISABLE=1` ya está en el script y es **obligatoria en Jetson** para evitar errores de compilación con versiones antiguas de PyTorch.
- Si usas cámara CSI (no USB), cambia:
  ```python
  cap = cv2.VideoCapture(
      "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720,"
      " format=NV12, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx"
      " ! videoconvert ! video/x-raw, format=BGR ! appsink",
      cv2.CAP_GSTREAMER
  )
  ```

---

## Solución de problemas comunes

| Error | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: ultralytics` | Librería no instalada | `pip install ultralytics` |
| `No se pudo abrir la cámara` | ID de cámara incorrecto | Cambia `CAMERA_ID = 1` o `2` |
| `TORCH_COMPILE_DISABLE` warning | Versión antigua de PyTorch | Ya está manejado en el script |
| FPS muy bajo | Hardware limitado | Reduce `IMG_SIZE` o aumenta `PROCESS_EVERY` |
| CUDA not available | PyTorch sin GPU | Instala versión CUDA o acepta CPU |

---

## Dependencias resumidas

```
ultralytics>=8.0.0
opencv-python>=4.7.0
torch>=1.13.0
torchvision>=0.14.0
```

También puedes crear un archivo `requirements.txt` con ese contenido e instalar con:

```bash
pip install -r requirements.txt
```
