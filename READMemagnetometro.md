# Fusión Cámara USB + Magnetómetro MLX90393 — Jetson Orin NX

Sistema que muestra el video en vivo de una webcam USB y superpone, en el centro
del encuadre (posición física conocida del sensor), un indicador del campo
magnético leído por un MLX90393: polaridad (Norte/Sur), fuerza y estado.

---

## 1. Hardware

- **Plataforma:** NVIDIA Jetson Orin NX (Ubuntu / L4T, JetPack 5.x)
- **Sensor:** Magnetómetro 3 ejes MLX90393 (módulo CJMCU), dirección I2C `0x0C`
- **Conexión I2C:** pines 27 (SDA) y 28 (SCL) → bus `/dev/i2c-1`
- **Cámara:** webcam USB estándar (UVC) en `/dev/video0`

> **Alimentación del sensor: 3.3V, NO 5V.** El MLX90393 es de 3.3V.

---

## 2. Software requerido

| Componente | Versión probada | Notas |
|------------|-----------------|-------|
| Python     | 3.8.10          | El que trae JetPack 5.x |
| OpenCV     | 4.13.0          | Suele venir preinstalado con JetPack |
| NumPy      | 1.24.4          | Mantener < 2.0 |
| smbus2     | 0.6.1           | Para I2C |

---

## 3. Instalación (SIN sudo)

Todo se instala en el espacio de usuario con `--user`. No requiere contraseña
de root para ejecutar.

### Paso A — Verificar lo que ya tienes

```bash
python3 -c "import sys, numpy, cv2; print('Python:', sys.version.split()[0]); print('NumPy:', numpy.__version__); print('OpenCV:', cv2.__version__)"
```

Si OpenCV y NumPy ya aparecen (lo habitual en JetPack), **no los reinstales**.

### Paso B — Instalar lo que falte

```bash
# smbus2 casi siempre es lo único que falta:
pip3 install --user smbus2

# Solo si OpenCV NO apareció en el Paso A:
pip3 install --user opencv-python "numpy<2"
```

### Paso C — Verificación final

```bash
python3 -c "import sys, numpy, cv2, smbus2; print('Python:', sys.version.split()[0]); print('NumPy:', numpy.__version__); print('OpenCV:', cv2.__version__); print('smbus2:', smbus2.__version__)"
```

Las cuatro deben imprimir sin error.

---

## 4. Permisos (sin sudo)

El programa necesita acceso a I2C y a la cámara. Esto se controla por
pertenencia a grupos, NO por ejecutar con sudo.

```bash
groups          # deben aparecer 'i2c' y 'video'
```

Si ambos aparecen, no necesitas sudo para nada. Si falta alguno, alguien con
contraseña lo agrega UNA sola vez:

```bash
sudo usermod -aG i2c,video $USER   # requiere reiniciar sesión después
```

---

## 5. Verificar el hardware antes de ejecutar

### Bus I2C y sensor

```bash
i2cdetect -y -r 1     # debe aparecer '0c' en la tabla
```

Si el `0c` aparece en otro bus (ej. el 8), edita `I2C_BUS` en el script.

### Cámara

```bash
ls -l /dev/video*     # debe existir /dev/video0
python3 test_camara.py   # debe mostrar el video; anota el índice que funcione
```

---

## 6. Ejecución

```bash
python3 fusion_camara_magnetometro.py
```

> Usar **python3** (apunta a 3.8.10 con las librerías). NO usar python3.9.

**Controles:**
- `q` → salir
- `c` → recalibrar el offset (hazlo con el imán LEJOS)

---

## 7. Ajustes en el script

Variables al inicio de `fusion_camara_magnetometro.py`:

| Variable      | Default | Para qué |
|---------------|---------|----------|
| `I2C_BUS`     | 1       | Bus del sensor (1 en esta Jetson) |
| `CAM_INDICE`  | 0       | Índice de la webcam (el que dio test_camara.py) |
| `UMBRAL_Z`    | 500.0   | Fuerza mínima en Z para dibujar el cuadro |
| `UMBRAL_N`    | 500.0   | Z por encima = Polo Norte |
| `UMBRAL_S`    | -500.0  | Z por debajo = Polo Sur |
| `ESCALA_Z`    | 0.05    | Cuánto crece el cuadro con la fuerza |

**Calibrar el umbral:** acerca el imán, mira el valor de `Z` en el HUD. Si tu
imán solo llega a ~200 uT, baja los umbrales a 100. Si el cuadro salta sin imán,
súbelos.

---

## 8. Qué hace y qué NO hace (importante)

**Hace:** muestra el video real + marca la zona FIJA del sensor (centro del
encuadre) + etiqueta con polaridad (N azul / S rojo) y fuerza del campo.

**NO hace:** localizar el imán en el espacio. Con UN solo magnetómetro es
físicamente imposible triangular dónde está la fuente. El cuadro indica el campo
que siente el sensor en su punto, no la posición del imán. Para ubicar el imán
visualmente haría falta detección por cámara (color/movimiento); para ubicarlo
magnéticamente, un array de varios sensores.

---

## 9. Problemas comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `No module named 'cv2'` | Ejecutaste con python3.9 | Usa `python3` (3.8) |
| `Errno 110 timed out` (todas las muestras) | Bus equivocado o cableado | Revisa `i2cdetect`, prueba bus 1 vs 8, revisa 3.3V y SDA/SCL |
| `Errno 121` ocasional | Ruido del cable de 60 cm | Normal, el programa reintenta solo |
| Cuadro no aparece con imán | Umbral muy alto | Baja `UMBRAL_Z/N/S` |
| Ventana negra (script viejo) | Es el script SOLO-magnetómetro | Usa `fusion_camara_magnetometro.py` |
| Avisos `QFontDatabase: Cannot find font` | Cosmético de OpenCV/Qt | Ignorar, no afecta |

---

## 10. Archivos del proyecto

- `fusion_camara_magnetometro.py` — programa principal (cámara + sensor)
- `magnetometro_mlx90393.py` — versión solo sensor (sin cámara, fondo negro)
- `test_camara.py` — prueba aislada de la webcam
