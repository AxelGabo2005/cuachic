# Sistema de Detección de Movimiento Rápido para NVIDIA Jetson

Este repositorio contiene un sistema de visión artificial de bajo consumo computacional utilizando OpenCV. El script `movementDetection.py` detecta movimiento en tiempo real mediante la técnica de **sustracción de fondo**. 

Está diseñado y optimizado específicamente para ejecutarse en placas NVIDIA Jetson (arquitectura ARM64 / JetPack) utilizando una cámara web por USB, liberando recursos del procesador y manteniendo una alta tasa de fotogramas (FPS).

---

## 1. Requisitos Previos y Configuración de Hardware

Antes de ejecutar el código, la placa Jetson necesita estar configurada para aceptar periféricos de video y mostrar ventanas gráficas de Linux.

### A. Permisos de Video (Importante)
En Linux, debes darle permiso a tu usuario para acceder a los puertos de la cámara USB (`/dev/video0`). Abre la terminal de la Jetson y ejecuta esto **una sola vez**:

```bash
sudo usermod -aG video $USER
```
*(Es necesario reiniciar la placa para que este cambio surta efecto).*

### B. Entorno Gráfico (Pantalla)
El código utiliza ventanas emergentes (`cv2.imshow`) para mostrar el resultado. 
* Si tienes la Jetson conectada directamente a un monitor con HDMI/DisplayPort, funcionará de forma nativa.
* Si controlas la Jetson desde tu computadora por control remoto (SSH), debes conectarte habilitando el reenvío de ventanas gráficas (X11 forwarding). Conéctate usando: 

```bash
ssh -X tu_usuario@ip_de_la_jetson
```

---

## 2. Instalación de Dependencias

**ADVERTENCIA CRÍTICA:** NO instales OpenCV usando `pip install opencv-python` en la Jetson. Eso descargará una versión genérica que no tiene acceso a la aceleración por hardware de la placa.

Para aprovechar el hardware nativo de NVIDIA JetPack, instala la versión optimizada desde los repositorios de Ubuntu ejecutando:

```bash
sudo apt-get update
sudo apt-get install python3-opencv python3-numpy
```

---

## 3. Notas Técnicas sobre el Código

El archivo principal del repositorio es `movementDetection.py`. Al revisarlo o editarlo, ten en cuenta lo siguiente:

* **Backend V4L2:** El código inicializa la cámara utilizando `cv2.CAP_V4L2`. Esto fuerza la lectura eficiente para una **cámara web USB** en Linux.
* **Cámaras CSI (Cable plano):** Si en el futuro cambias a una cámara nativa de circuito conectada directamente a los pines de la Jetson, OpenCV no la detectará con el índice `0`. Deberás editar el código y cambiar esa línea por el pipeline de GStreamer correspondiente.
* **Optimización de Ruido:** El algoritmo aplica un `GaussianBlur` y filtra contornos menores a 100 píxeles de área para evitar falsos positivos causados por polvo o parpadeos de las luces de la habitación.

---

## 4. Ejecución

Una vez clonado el repositorio y conectada tu cámara USB, abre la terminal en la carpeta del proyecto y arranca el nodo de visión con:

```bash
python3 movementDetection.py
```

### Controles durante la ejecución
* **Para salir de forma segura:** Haz clic en la ventana de video para seleccionarla y presiona la letra **q** en tu teclado. Esto cerrará el programa y liberará el hardware de la cámara.
* **Cierre forzado:** Si la ventana se congela o pierdes la conexión gráfica, ve a la terminal y presiona **Ctrl + C** para abortar el proceso de Python.
