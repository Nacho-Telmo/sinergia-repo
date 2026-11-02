# Sinergia-Reflector-Top

Aplicación gráfica desarrollada en Python y Tkinter para optimizar y actualizar los espejos (mirrors) de Arch Linux utilizando la herramienta **Reflector**.

## Características
- Interfaz gráfica en modo oscuro con diseño moderno.
- Opciones rápidas para seleccionar el **Top 10, 20 o 30** espejos más veloces mediante protocolos **HTTPS**.
- Respaldo automático previo (`mirrorlist.bak`).
- Barra de progreso dinámica e hilos en segundo plano para evitar que la interfaz se congele.
- Autenticación segura mediante `pkexec`.

## Requisitos
- Arch Linux o derivadas 
- Python 3 y `python-tk`
- `reflector`
