# HAZMAT Detection — Dependencias

Librerías necesarias para ejecutar `cuachic.pt` con el script de detección.

---

## Instalación rápida

```bash
pip install ultralytics opencv-python
```

> PyTorch se instala automáticamente junto con `ultralytics`.  
> Si quieres aceleración por GPU, instálalo manualmente (ver abajo).

---

## Librerías requeridas

### `ultralytics`
Carga y ejecuta el modelo `cuachic.pt` (formato YOLOv8).
```bash
pip install ultralytics
```

### `opencv-python`
Captura de cámara y visualización de resultados.
```bash
pip install opencv-python
```

### `torch` + `torchvision`
Motor de inferencia. Se instala solo con `ultralytics`, pero si necesitas soporte GPU:

**Solo CPU:**
```bash
pip install torch torchvision
```

**GPU NVIDIA (CUDA 11.8):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**GPU NVIDIA (CUDA 12.1):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Jetson (JetPack 5.x):**  
PyTorch ya viene preinstalado. Solo instala:
```bash
pip install ultralytics opencv-python
```

---

## requirements.txt

```
ultralytics>=8.0.0
opencv-python>=4.7.0
torch>=1.13.0
torchvision>=0.14.0
```

Instalar desde el archivo:
```bash
pip install -r requirements.txt
```

---

## Verificar instalación

```bash
python3 -c "import ultralytics, cv2, torch; print('OK')"
```
