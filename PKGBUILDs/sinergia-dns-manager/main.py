#!/usr/bin/env python3
import re
import shlex
import subprocess
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Proveedores de DNS (enfocados en IPv4)
DNS_PROVIDERS = {
    "AdGuard DNS (Recomendado - Sin publicidad)": {
        "ipv4": ["94.140.14.14", "94.140.15.15"],
        "desc": "Bloqueo automático de anuncios, rastreadores y protección de privacidad.",
    },
    "AdGuard DNS - Protección Familiar": {
        "ipv4": ["94.140.14.15", "94.140.15.16"],
        "desc": "Bloqueo de contenido para adultos y control parental seguro.",
    },
    "Cloudflare (Rápido y Privado)": {
        "ipv4": ["1.1.1.1", "1.0.0.1"],
        "desc": "Enfoque en velocidad extrema y política estricta de cero registro.",
    },
    "Google Public DNS": {
        "ipv4": ["8.8.8.8", "8.8.4.4"],
        "desc": "Los servidores DNS tradicionales provistos por Google.",
    },
    "Quad9 (Seguridad y Malware)": {
        "ipv4": ["9.9.9.9", "149.112.112.112"],
        "desc": "Bloqueo activo de sitios de phishing y dominios maliciosos.",
    },
    "Automático (DHCP del Router / ISP)": {
        "ipv4": [],
        "desc": "Restaura la configuración predeterminada provista por tu red.",
    },
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
        info_frame.setStyleSheet(
            "background: transparent; border: 1px solid rgba(127, 140, 141, 0.3); border-radius: 6px;"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(8)

        self.lbl_connection = QLabel(
            f"<b>Conexión activa:</b> {self.get_active_connection() or 'Ninguna detectada'}"
        )
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
        self.desc_frame.setStyleSheet(
            "background: transparent; border: 1px solid rgba(127, 140, 141, 0.3); border-radius: 6px;"
        )
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

    def _is_resolved_active(self) -> bool:
        try:
            res = subprocess.run(
                ["systemctl", "is-active", "--quiet", "systemd-resolved"],
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def _get_default_route_device(self) -> str | None:
        try:
            output = subprocess.check_output(
                ["ip", "-o", "route", "show", "default"],
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
            )
            for line in output.splitlines():
                parts = line.split()
                if "dev" in parts:
                    idx = parts.index("dev")
                    if idx + 1 < len(parts):
                        return parts[idx + 1]
        except Exception:
            pass
        return None

    def get_active_connection(self):
        """Detecta el nombre de la conexión de red activa mediante NetworkManager."""
        default_dev = self._get_default_route_device()
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,DEVICE,STATE", "connection", "show", "--active"],
                universal_newlines=True,
            )
            fallback_conn = None
            for line in output.strip().splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    name, dev, state = parts[0], parts[1], parts[2]
                    if dev in ("lo", "virbr0") or dev.startswith(("docker", "br-", "veth")):
                        continue
                    if default_dev and dev == default_dev:
                        return name
                    if not fallback_conn and state == "activated":
                        fallback_conn = name
            return fallback_conn
        except Exception:
            pass
        return None

    def get_active_device(self, conn_name):
        """Obtiene la interfaz de red física/inalámbrica asociada a la conexión activa."""
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
                universal_newlines=True,
            )
            for line in output.strip().splitlines():
                if line.startswith(f"{conn_name}:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
        except Exception:
            pass
        return None

    def _get_resolved_active_dns(self, device: str | None) -> list[str]:
        """Obtiene los servidores DNS activos reportados por systemd-resolved."""
        if not self._is_resolved_active():
            return []
        try:
            output = subprocess.check_output(
                ["resolvectl", "status"],
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
            )
            ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
            # Buscar primero en el bloque de la interfaz activa
            if device:
                link_match = re.search(
                    rf"Link \d+ \({re.escape(device)}\):.*?(?=\nLink \d+|\Z)",
                    output,
                    re.S,
                )
                if link_match:
                    block = link_match.group(0)
                    for line in block.splitlines():
                        if "Current DNS Server:" in line:
                            m = ip_pattern.search(line)
                            if m:
                                return [m.group(0)]
                    for line in block.splitlines():
                        if "DNS Servers:" in line:
                            ips = ip_pattern.findall(line)
                            if ips:
                                return ips

            # Fallback al servidor actual global si no se encontró en el enlace
            for line in output.splitlines():
                if "Current DNS Server:" in line:
                    m = ip_pattern.search(line)
                    if m:
                        return [m.group(0)]
        except Exception:
            pass
        return []

    def get_current_dns_servers(self):
        """Consulta los DNS actuales y los cruza con DNS_PROVIDERS para mostrar el nombre amigable."""
        conn_name = self.get_active_connection()
        if not conn_name:
            return "Sin conexión activa"

        device = self.get_active_device(conn_name)
        found_ips = []

        # 1. Consultar configuración explícita en NetworkManager
        nm_dns = ""
        try:
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "ipv4.dns", "con", "show", conn_name],
                universal_newlines=True,
            )
            for line in output.strip().splitlines():
                if line.startswith("ipv4.dns:"):
                    nm_dns = line.split(":", 1)[1].strip()
        except Exception:
            pass

        if nm_dns:
            found_ips = [ip.strip() for ip in nm_dns.replace(",", " ").split() if ip.strip()]
        else:
            # 2. Consultar DNS activos en systemd-resolved si está en uso
            resolved_ips = self._get_resolved_active_dns(device)
            if resolved_ips:
                found_ips = resolved_ips

        # 3. Fallback a /etc/resolv.conf
        if not found_ips:
            try:
                with open("/etc/resolv.conf", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) > 1 and parts[1] != "127.0.0.53":
                                found_ips.append(parts[1])
            except Exception:
                pass

        if not found_ips and not nm_dns:
            return "Automático (DHCP / ISP)"

        matched_name = None
        for name, data in DNS_PROVIDERS.items():
            prov_ipv4 = data.get("ipv4", [])
            if prov_ipv4 and any(ip in prov_ipv4 for ip in found_ips):
                matched_name = name
                break

        if matched_name:
            return f"<b>{matched_name}</b> ({', '.join(found_ips)})"
        elif found_ips:
            return f"Personalizado / Red ({', '.join(found_ips)})"
        else:
            return "Automático (DHCP / ISP)"

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
        """Aplica la configuración DNS, evita que DHCP/IPv6 del ISP la pise y sincroniza resolved/VMs."""
        conn_name = self.get_active_connection()
        if not conn_name:
            QMessageBox.warning(self, "Error de red", "No se encontró ninguna conexión de red activa.")
            return

        selected_key = self.combo_providers.currentText()
        provider = DNS_PROVIDERS.get(selected_key)
        ipv4_list = provider.get("ipv4", [])
        ipv4_dns = " ".join(ipv4_list)

        q_conn = shlex.quote(conn_name)
        device = self.get_active_device(conn_name)
        q_dev = shlex.quote(device) if device else ""

        cmd_networkd_fix = (
            "if systemctl is-active --quiet NetworkManager && systemctl is-active --quiet systemd-networkd; then "
            "systemctl disable --now systemd-networkd.service systemd-networkd.socket "
            "systemd-networkd-varlink.socket systemd-networkd-varlink-metrics.socket "
            "systemd-networkd-resolve-hook.socket >/dev/null 2>&1 || true; "
            "mkdir -p /etc/systemd/network.bak && "
            "mv /etc/systemd/network/20-*.network /etc/systemd/network.bak/ 2>/dev/null || true; "
            "fi"
        )

        if ipv4_dns:
            q_dns = shlex.quote(ipv4_dns)
            cmd_nm = (
                f"nmcli con mod {q_conn} "
                f"ipv4.dns {q_dns} ipv4.ignore-auto-dns yes "
                f"ipv6.ignore-auto-dns yes"
            )
            cmd_resolved = (
                f"if systemctl is-active --quiet systemd-resolved; then "
                f"mkdir -p /etc/systemd/resolved.conf.d && "
                f"printf '[Resolve]\nDNS={ipv4_dns}\nFallbackDNS=\n' > /etc/systemd/resolved.conf.d/99-sinergia-dns.conf && "
                f"systemctl restart systemd-resolved && "
                f"{f'resolvectl dns {q_dev} {ipv4_dns} && ' if q_dev else ''}"
                f"resolvectl flush-caches; "
                f"fi"
            )
        else:
            all_ipv4 = []
            for p_data in DNS_PROVIDERS.values():
                all_ipv4.extend(p_data.get("ipv4", []))
            remove_args_v4 = " ".join([f"-ipv4.dns {shlex.quote(ip)}" for ip in sorted(set(all_ipv4))])
            nm_parts = [f"nmcli con mod {q_conn}"]
            if remove_args_v4:
                nm_parts.append(remove_args_v4)
            nm_parts.extend(["ipv4.ignore-auto-dns no", "ipv6.ignore-auto-dns no"])
            cmd_nm = " ".join(nm_parts)
            cmd_resolved = (
                f"if systemctl is-active --quiet systemd-resolved; then "
                f"rm -f /etc/systemd/resolved.conf.d/99-sinergia-dns.conf && "
                f"systemctl restart systemd-resolved && "
                f"{f'resolvectl revert {q_dev} && ' if q_dev else ''}"
                f"resolvectl flush-caches; "
                f"fi"
            )

        net_command = f"{cmd_networkd_fix} && {cmd_nm} && nmcli con up {q_conn} && {cmd_resolved}"

        # Hook inteligente para KVM/libvirt: si existe la red 'default', la recarga para restaurar el NAT de las VMs
        libvirt_fix = (
            " && (virsh net-info default &>/dev/null && "
            "(virsh net-destroy default && virsh net-start default) || true)"
        )

        full_command = f"{net_command}{libvirt_fix}"

        try:
            subprocess.run(
                ["pkexec", "bash", "-c", full_command],
                check=True,
                capture_output=True,
                text=True,
            )

            # Refrescar etiquetas en pantalla
            active_conn = self.get_active_connection() or conn_name
            self.lbl_connection.setText(f"<b>Conexión activa:</b> {active_conn}")
            updated_dns_named = self.get_current_dns_servers()
            self.lbl_current_dns.setText(f"<b>DNS en uso actual:</b> {updated_dns_named}")
            self.lbl_current_dns.update()
            QApplication.processEvents()

            QMessageBox.information(
                self,
                "¡Éxito!",
                f"Los servidores DNS se aplicaron correctamente en '{active_conn}' y las interfaces virtuales se sincronizaron.",
            )
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or "").strip()
            msg = (
                "No se pudieron aplicar los cambios. Es posible que se haya cancelado la autenticación o la contraseña sea incorrecta."
                + (f"\n\nDetalle:\n{detail}" if detail else "")
            )
            QMessageBox.critical(
                self,
                "Cancelado o Error",
                msg,
            )


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        QApplication.setDesktopFileName("sinergia-dns-manager")

        window = SinergiaDNSManager()
        window.show()
        sys.exit(app.exec())
    except Exception:
        import traceback

        print("CRITICAL ERROR:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
