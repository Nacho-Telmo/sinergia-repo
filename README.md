# Repositorio Sinergia 🐧

Repositorio de paquetes binarios optimizados para **Arch Linux** y distribuciones derivadas, mantenido de forma colaborativa por los miembros de la comunidad **Sinergia**.

---

## 🚀 Guía de Instalación

### Instalación Automática (Recomendado)
Para una experiencia rápida y sin fricciones, podés utilizar nuestro script de configuración automática. Este script se encarga de configurar **Chaotic-AUR**, instalar **yay**, añadir el repositorio de Sinergia con sus respectivas llaves GPG y dejar instalado **sinergia-welcome** en un solo paso:

```bash
curl -sL https://nacho-telmo.github.io/sinergia-repo/setup.sh | sudo bash
```

---

### Método Manual (Paso a Paso)
Si preferís configurar el repositorio de forma manual para cumplir estrictamente con las políticas de firmas digitales de `pacman` (`SigLevel = Required`), seguí estos pasos en tu terminal:

#### Paso 1: Importar la clave GPG del repositorio
Descarga e importa la clave pública oficial directamente al llavero de tu sistema:

```bash
curl -s https://nacho-telmo.github.io/sinergia-repo/x86_64/sinergia-key.asc | sudo pacman-key --add -
```

#### Paso 2: Firmar localmente la clave
Otorga confianza local a la clave importada para que `pacman` valide las firmas de los paquetes de forma segura:

```bash
sudo pacman-key --lsign-key 33986859CBA9A0329EE9321E1AA165CC95EBE1F1
```

#### Paso 3: Agregar el repositorio a tu configuración
Abre el archivo de configuración con tu editor de texto favorito:

```bash
sudo nano /etc/pacman.conf
```

Añade las siguientes líneas **al final** del archivo:

```ini
[sinergia]
SigLevel = Required DatabaseOptional
Server = https://nacho-telmo.github.io/sinergia-repo/x86_64/
```

#### Paso 4: Sincronizar las bases de datos
Fuerza el refresco de los repositorios para comenzar a utilizar el repositorio de Sinergia:

```bash
sudo pacman -Syy
```

---

## 📦 Aplicaciones Disponibles

El repositorio incluye herramientas y paquetes optimizados tales como:
- `better-iptv-bin`
- `sinergia-keyring`
- `sinergia-kernel-manager`
- `sinergia-appimage-manager`
- Y mucho más...

---

💬 **Comunidad:** [Unirte al grupo de Telegram](https://t.me/Guias_NovumSinergia)
