Repositorio Oficial de Sinergia - Comunidad Linuxera

Repositorio oficial de paquetes precompilados mantenido por Sinergia - Comunidad Linuxera. Diseñado para Arch Linux y cualquier distribución derivada (EndeavourOS, Manjaro, Garuda, CachyOS, ArcoLinux, etc.).

Todos los paquetes y la base de datos están firmados mediante clave criptográfica GPG para garantizar descargas seguras e inalteradas.

📋 Requisitos Previos

Sistema operativo basado en Arch Linux.

Gestor de paquetes pacman.

Herramientas básicas de terminal (curl, sudo).

🚀 Guía de Instalación

Paso 1: Importar la Clave GPG del Repositorio

Para que pacman pueda validar las firmas de los paquetes de Sinergia, importá y confirmá la clave pública en el llavero oficial de tu sistema:

curl -s https://Nacho-Telmo.github.io/sinergia-repo/x86_64/sinergia.gpg | sudo pacman-key --add -
sudo pacman-key --lsign-key 4CBFA5A14BB153A7


Datos de Identificación de la Clave:

ID de Clave: 4CBFA5A14BB153A7

Propietario: Sinergia - Comunidad Linuxera (Repositorio de Sinergia) <sinergia.comunidad.linuxera@gmail.com>

Paso 2: Agregar el Repositorio a pacman.conf

Editá el archivo de configuración de pacman con tu editor preferido:

sudo nano /etc/pacman.conf


Agregá el siguiente bloque al final de todo el archivo:

[sinergia]
SigLevel = Required DatabaseOptional
Server = https://Nacho-Telmo.github.io/sinergia-repo/$arch


(En Nano: guardá los cambios presionando Ctrl + O, luego Enter y salí con Ctrl + X).

Paso 3: Sincronizar la Base de Datos

Actualizá los índices de tu sistema para reconocer la lista de software de Sinergia:

sudo pacman -Syy


📦 Gestión de Paquetes

Listar todo el software disponible en el repositorio

pacman -Sl sinergia


Buscar un paquete específico

pacman -Ss sinergia


Instalar una aplicación

sudo pacman -S sinergia-appimage-manager


🛠️ Solución de Problemas

Error de Clave Desconocida (key "4CBFA5A14BB153A7" is unknown)

Si pacman arroja un error al verificar firmas, re-importá la clave directamente ejecutando:

sudo pacman-key --add https://Nacho-Telmo.github.io/sinergia-repo/x86_64/sinergia.gpg
sudo pacman-key --lsign-key 4CBFA5A14BB153A7


🔗 Enlaces de la Comunidad

📺 YouTube: Sinergia Comunidad Linuxera

🐙 GitHub Repository: Nacho-Telmo/sinergia-repo
