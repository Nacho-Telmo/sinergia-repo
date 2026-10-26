# 🐧 Repositorio Oficial de Sinergia - Comunidad Linuxera

Repositorio de paquetes precompilados mantenido por **Sinergia Comunidad Linuxera**. Diseñado para **Arch Linux** y cualquier distribución derivada (**EndeavourOS, Manjaro, CachyOS, Garuda, ArcoLinux, etc.**).

Todos los paquetes y la base de datos están firmados criptográficamente con GPG para garantizar descargas seguras e inalteradas.

---

## ⚡ Guía de Instalación Rápida (3 Pasos)

### Paso 1: Importar y Validar la Clave GPG Pública

Ejecutá este comando en tu terminal para importar y validar la clave de firma del repositorio en el llavero de tu sistema:

```bash
curl -s https://Nacho-Telmo.github.io/sinergia-repo/x86_64/sinergia.gpg | sudo pacman-key --add -
sudo pacman-key --lsign-key 4CBFA5A14BB153A7
```

> **Detalles de la clave:**
> * **ID de Clave:** `4CBFA5A14BB153A7`
> * **Propietario:** `Sinergia - Comunidad Linuxera (Repositorio de Sinergia) <sinergia.comunidad.linuxera@gmail.com>`

---

### Paso 2: Agregar el Repositorio a `pacman.conf`

Edita el archivo de configuración de `pacman`:

```bash
sudo nano /etc/pacman.conf
```

Agregá las siguientes líneas al final del archivo:

```ini
[sinergia]
SigLevel = Required DatabaseOptional
Server = https://Nacho-Telmo.github.io/sinergia-repo/$arch
```

*(En Nano: guardá con `Ctrl + O`, presioná `Enter` y salí con `Ctrl + X`)*.

---

### Paso 3: Sincronizar las Bases de Datos

Actualizá los índices de tu sistema para reconocer el nuevo repositorio:

```bash
sudo pacman -Sy
```

---

## 📦 Software destacado

| Paquete | Descripción | Instalación |
| :--- | :--- | :--- |
| `sinergia-appimage-manager` | Gestor e integrador de aplicaciones AppImage | `sudo pacman -S sinergia-appimage-manager` |
| `sinergia-webapp-manager` | Creador y gestor de aplicaciones web (WebApps) | `sudo pacman -S sinergia-webapp-manager` |
| `flextile-git` | Script Flextile de tiling para KWin (KDE Plasma) | `sudo pacman -S flextile-git` |
| `sinergia-dd-burner` | Grabador de imágenes ISO en unidades USB | `sudo pacman -S sinergia-dd-burner` |
| `sinergia-reflector-top` | Optimizar y Actualizar los Espejos (Mirrors) de ArchLinux Utilizando la Herramienta Reflector | `sudo pacman -S sinergia-reflector-top` |

---

## 💡 Comandos Útiles

* **Buscar paquetes en el repositorio:**
  ```bash
  pacman -Ss sinergia
  ```

* **Listar todo el software servido por Sinergia:**
  ```bash
  pacman -Sl sinergia
  ```

* **Actualizar el sistema incluyendo paquetes de Sinergia:**
  ```bash
  sudo pacman -Syu
  ```

---

## 🛠️ Solución de Problemas

Si en algún momento el sistema indica un error de firmas (`error: sinergia: key "4CBFA5A14BB153A7" is unknown`), re-importá la clave directamente ejecutando:

```bash
curl -s https://Nacho-Telmo.github.io/sinergia-repo/x86_64/sinergia.gpg | sudo pacman-key --add -
sudo pacman-key --lsign-key 4CBFA5A14BB153A7
```

---

## 🌐 Enlaces de la Comunidad

* 📺 **Canal de YouTube:** [Sinergia Comunidad Linuxera](https://www.youtube.com/@Sinergia-Comunidad-Linuxera)
* 🐙 **GitHub Repositorio:** [Nacho-Telmo/sinergia-repo](https://github.com/Nacho-Telmo/sinergia-repo)
