#!/usr/bin/env python3
import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtGui import QIcon

# Proveedores de DNS (enfocados exclusivamente en IPv4)
DNS_PROVIDERS = {
    "AdGuard DNS (Recomendado - Sin publicidad)": {
        "ipv4": ["94.140.14.14", "94.140.15.15"],
        "desc": "Bloqueo automático de anuncios, rastreadores y protección de privacidad."
    },
    "AdGuard DNS - Protección Familiar": {
        "ipv4": ["94.140.14.15", "94.140.15.16"],
        "desc": "Bloqueo de contenido para adultos y control parental seguro."
    },
    "Cloudflare (Rápido y Privado)": {
        "ipv4": ["1.1.1.1", "1.0.0.1"],
        "desc": "Enfoque en velocidad extrema y política estricta de cero registro."
    },
    "Google Public DNS": {
        "ipv4": ["8.8.8.8", "8.8.4.4"],
        "desc": "Los servidores DNS tradicionales provistos por Google."
    },
    "Quad9 (Seguridad y Malware)": {
        "ipv4": ["9.9.9.9", "149.112.112.112"],
        "desc": "Bloqueo activo de sitios de phishing y dominios maliciosos."
    },
    "Automático (DHCP del Router / ISP)": {
        "ipv4": [],
        "desc": "Restaura la configuración predeterminada provista por tu red."
    }
}

class SinergiaDNSManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia DNS Manager")
        self.setFixedSize(600, 460)

        # Establecer el icono de la ventana basado en el tema del sistema
        self.setWindowIcon(QIcon.fromTheme("sinergia-dns-manager"))

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Título
        title_label = QLabel("Gestor de DNS - Sinergia")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71;")
        layout.addWidget(title_label)

        # Estado de la red y DNS actuales en uso
        info_frame = QFrame()
        info_frame.setStyleSheet("background: transparent; border: 1px solid rgba(127, 140, 141, 0.3); border-radius: 6px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(8)

        self.lbl_connection = QLabel(f"<b>Conexión activa:</b> {self.get_active_connection() or 'Ninguna detectada'}")
        self.lbl_connection.setWordWrap(True)
        self.lbl_connection.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        info_layout.addWidget(self.lbl_connection)

        current_dns_named = self.get_current_dns_servers()
        self.lbl_current_dns = QLabel(f"<b>DNS en uso actual:</b> {current_dns_named}")
        self.lbl_current_dns.setWordWrap(True)
        self.lbl_current_dns.setStyleSheet("color: #2980b9; font-size: 12px;")
        info_layout.addWidget(self.lbl_current_dns)

        layout.addWidget(info_frame)

        # Selector de Proveedor
        lbl_select = QLabel("Seleccioná tu proveedor de DNS preferido:")
        layout.addWidget(lbl_select)

        self.combo_providers = QComboBox()
        self.combo_providers.addItems(list(DNS_PROVIDERS.keys()))
        self.combo_providers.currentIndexChanged.connect(self.update_description)
        layout.addWidget(self.combo_providers)

        # Tarjeta de descripción del proveedor
        self.desc_frame = QFrame()
        self.desc_frame.setStyleSheet("background: transparent; border: 1px solid rgba(127, 140, 141, 0.3); border-radius: 6px;")
        desc_layout = QVBoxLayout(self.desc_frame)
        desc_layout.setContentsMargins(14, 12, 14, 12)

        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #bdc3c7; font-size: 12px; line-height: 140%;")
        desc_layout.addWidget(self.lbl_desc)
        layout.addWidget(self.desc_frame)

        self.update_description()
        layout.addStretch()

        # Botón Aplicar
        self.btn_apply = QPushButton("Aplicar Cambios de DNS")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        self.btn_apply.clicked.connect(self.apply_selected_dns)
        layout.addWidget(self.btn_apply)

    def get_active_connection(self):
        """Detecta el nombre de la conexión de red activa mediante NetworkManager."""
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,STATE", "connection", "show", "--active"],
                universal_newlines=True
            )
            for line in output.strip().split("\n"):
                if "activated" in line:
                    return line.split(":")[0]
        except Exception:
            pass
        return None

    def get_active_device(self, conn_name):
        """Obtiene la interfaz de red física/inalámbrica asociada a la conexión activa."""
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
                universal_newlines=True
            )
            for line in output.strip().split("\n"):
                if line.startswith(f"{conn_name}:"):
                    parts = line.split(":")
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
        except Exception:
            pass
        return None

    def get_current_dns_servers(self):
        """Consulta los DNS actuales y los cruza con DNS_PROVIDERS para mostrar el nombre amigable."""
        conn_name = self.get_active_connection()
        if not conn_name:
            return "Sin conexión activa"

        raw_dns = ""
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "ipv4.dns", "con", "show", conn_name],
                universal_newlines=True
            )
            for line in output.strip().split("\n"):
                if line.startswith("ipv4.dns:"):
                    raw_dns = line.split(":", 1)[1].strip()
        except Exception:
            pass

        if not raw_dns:
            try:
                with open("/etc/resolv.conf", "r") as f:
                    dns_list = []
                    for line in f:
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) > 1 and parts[1] != "127.0.0.53":
                                dns_list.append(parts[1])
                    if dns_list:
                        raw_dns = " ".join(dns_list)
            except Exception:
                pass

        if not raw_dns:
            return "Automático (DHCP / ISP)"

        found_ips = [ip.strip() for ip in raw_dns.replace(",", " ").split() if ip.strip()]

        matched_name = None
        for name, data in DNS_PROVIDERS.items():
            prov_ipv4 = data.get("ipv4", [])
            if prov_ipv4 and any(ip in prov_ipv4 for ip in found_ips):
                matched_name = name
                break

        if matched_name:
            return f"<b>{matched_name}</b> ({', '.join(found_ips)})"
        else:
            return f"Personalizado ({', '.join(found_ips)})"

    def update_description(self):
        """Muestra los detalles de IPv4 del proveedor seleccionado en el combo."""
        selected = self.combo_providers.currentText()
        p = DNS_PROVIDERS.get(selected, {})
        ipv4_str = ", ".join(p.get("ipv4", [])) or "Automático (DHCP)"

        text = (
            f"<b>Descripción:</b> {p.get('desc', '')}<br><br>"
            f"<b>Servidores IPv4:</b> {ipv4_str}"
        )
        self.lbl_desc.setText(text)

    def apply_selected_dns(self):
        """Aplica la configuración exclusivamente en IPv4, reaplica en caliente y restaura el puente de VMs."""
        conn_name = self.get_active_connection()
        if not conn_name:
            QMessageBox.warning(self, "Error de red", "No se encontró ninguna conexión de red activa.")
            return

        selected_key = self.combo_providers.currentText()
        provider = DNS_PROVIDERS.get(selected_key)
        ipv4_dns = " ".join(provider["ipv4"])

        # Recopilar todas las IPs conocidas para limpiar perfiles anteriores en modo automático
        all_ipv4 = []
        for p_data in DNS_PROVIDERS.values():
            all_ipv4.extend(p_data.get("ipv4", []))

        # Configurar exclusivamente IPv4 (sin tocar IPv6)
        if ipv4_dns:
            cmd_ipv4 = f'nmcli con mod "{conn_name}" ipv4.dns "{ipv4_dns}" ipv4.ignore-auto-dns yes'
        else:
            remove_args_v4 = " ".join([f'-ipv4.dns "{ip}"' for ip in set(all_ipv4)])
            cmd_ipv4 = f'nmcli con mod "{conn_name}" {remove_args_v4} ipv4.ignore-auto-dns no'

        # Detectar el dispositivo activo
        device = self.get_active_device(conn_name)

        # Comando base de red en caliente
        if device:
            net_command = f'{cmd_ipv4} && nmcli device reapply "{device}"'
        else:
            net_command = f'{cmd_ipv4} && nmcli con up "{conn_name}"'

        # Hook inteligente para KVM/libvirt: si existe la red 'default', la recarga para restaurar el NAT de las VMs
        libvirt_fix = ' && (virsh net-info default &>/dev/null && (virsh net-destroy default && virsh net-start default) || true)'

        full_command = f'{net_command}{libvirt_fix}'

        try:
            # Ejecución segura con privilegios administrativos
            subprocess.run(["pkexec", "bash", "-c", full_command], check=True)

            # Refrescar etiqueta en pantalla
            updated_dns_named = self.get_current_dns_servers()
            self.lbl_current_dns.setText(f"<b>DNS en uso actual:</b> {updated_dns_named}")

            QMessageBox.information(
                self,
                "¡Éxito!",
                f"Los servidores DNS se aplicaron correctamente en '{conn_name}' y las interfaces virtuales se sincronizaron."
            )
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "Cancelado o Error",
                "No se pudieron aplicar los cambios. Es posible que se haya cancelado la autenticación o la contraseña sea incorrecta."
            )

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        QApplication.setDesktopFileName("sinergia-dns-manager")

        window = SinergiaDNSManager()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print("CRITICAL ERROR:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
