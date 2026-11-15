from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ProgressBar, DataTable
import psutil
import signal
import sys
import time

class SinergiaTopApp(App):
    CSS = """
    Screen {
        background: #1e1e2e;
        color: #cdd6f4;
        layout: vertical;
    }
    Header {
        background: #11111b;
        color: #89b4fa;
        dock: top;
    }
    Footer {
        background: #11111b;
        color: #6c7086;
    }

    #header-container {
        dock: top;
        height: 2;
        background: #11111b;
        color: #89b4fa;
        layout: vertical;
        align: center middle;
        border-bottom: solid #313244;
    }
    #title {
        width: 100%;
        text-align: center;
        color: #89b4fa;
        text-style: bold;
    }
    #subtitle-uptime {
        width: 100%;
        text-align: center;
        color: #6c7086;
    }

    #main-top-split {
        layout: horizontal;
        height: 14;
        margin: 1 1 0 1;
    }

    #cpu-box {
        width: 55%;
        height: 14;
        background: #11111b;
        border: round #313244;
        padding: 0 1;
        margin-right: 1;
    }

    #right-column {
        width: 45%;
        layout: vertical;
        height: 14;
    }

    .box {
        background: #11111b;
        border: round #313244;
        padding: 0 1;
        height: 6;
        margin-bottom: 1;
    }

    #net-box {
        height: 7;
    }

    #cores-container {
        layout: grid;
        grid-size: 2;
        grid-gutter: 0 2;
        height: auto;
        margin-top: 1;
    }

    .core-row {
        layout: horizontal;
        height: 1;
    }
    .core-label {
        width: 6;
        color: #89b4fa;
        text-style: bold;
    }

    DataTable {
        background: #11111b;
        border: round #313244;
        margin: 1 1 0 1;
        height: 1fr;
    }

    DataTable > .datatable--cursor {
        background: #313244;
        color: #cdd6f4;
    }

    DataTable > .datatable--header {
        background: #11111b;
        color: #89b4fa;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Salir"),
        ("ctrl+c", "quit", "Salir")
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="header-container"):
            yield Static("Sinergia Top", id="title")
            self.uptime_label = Static("Uptime: --", id="subtitle-uptime")
            yield self.uptime_label

        with Container():
            with Horizontal(id="main-top-split"):
                with Container(id="cpu-box"):
                    yield Static("[bold #89b4fa]CPU CORES & TEMP[/]")
                    self.cpu_info_label = Static("Global: 0.0% | Temp: -- °C")
                    yield self.cpu_info_label
                    with Vertical(id="cores-container"):
                        pass

                with Vertical(id="right-column"):
                    # Caja unificada para RAM y SWAP
                    with Container(classes="box", id="ram-box"):
                        yield Static("[bold #a6e3a1]RAM & SWAP USAGE[/]")
                        self.ram_label = Static("RAM: 0.0 GB / 0.0 GB (0%)")
                        self.ram_bar = ProgressBar(total=100, show_eta=False)
                        self.swap_label = Static("SWAP: 0.0 GB / 0.0 GB (0%)")
                        self.swap_bar = ProgressBar(total=100, show_eta=False)
                        yield self.ram_label
                        yield self.ram_bar
                        yield self.swap_label
                        yield self.swap_bar

                    with Container(classes="box", id="net-box"):
                        yield Static("[bold #f9e2af]NETWORK I/O[/]")
                        self.net_up = Static("↑ 0.0 KB/s")
                        self.net_down = Static("↓ 0.0 KB/s")
                        yield self.net_up
                        yield self.net_down

            self.table = DataTable(id="proc-table")
            self.table.cursor_type = "row"
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        self.table.add_columns("PID", "USER", "NAME", "%CPU", "%MEM")
        self.prev_net = psutil.net_io_counters()
        self.boot_time = psutil.boot_time()

        # Detección inteligente y automática de núcleos de quien lo instale
        num_cores = psutil.cpu_count(logical=True) or 4
        self.core_bars = []

        cores_container = self.query_one("#cores-container", Vertical)
        for i in range(num_cores):
            label = Static(f"C{i:2d}", classes="core-label")
            bar = ProgressBar(total=100, show_eta=False)
            row = Horizontal(label, bar, classes="core-row")
            cores_container.mount(row)
            self.core_bars.append(bar)

        self.set_interval(1.0, self.update_metrics)

    def update_metrics(self) -> None:
        try:
            uptime_seconds = time.time() - self.boot_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            self.uptime_label.update(f"Uptime: {hours}h {minutes}m encendido")

            cpu_percents = psutil.cpu_percent(interval=0, percpu=True)
            global_cpu = sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0.0

            for i, pct in enumerate(cpu_percents):
                if i < len(self.core_bars):
                    self.core_bars[i].progress = pct

            cpu_temp_str = "N/A"
            temps = psutil.sensors_temperatures()
            if temps:
                for name in ['coretemp', 'k10temp', 'acpitz', 'cpu_thermal']:
                    if name in temps and temps[name]:
                        cpu_temp_str = f"{temps[name][0].current:.1f}°C"
                        break
                if cpu_temp_str == "N/A":
                    first_sensor = list(temps.values())[0]
                    if first_sensor:
                        cpu_temp_str = f"{first_sensor[0].current:.1f}°C"

            self.cpu_info_label.update(f"Global: {global_cpu:.1f}% | Temp: {cpu_temp_str}")

            # RAM y SWAP en tiempo real
            ram = psutil.virtual_memory()
            self.ram_label.update(f"RAM: {ram.used / (1024**3):.2f} / {ram.total / (1024**3):.2f} GB ({ram.percent}%)")
            self.ram_bar.progress = ram.percent

            swap = psutil.swap_memory()
            if swap.total > 0:
                self.swap_label.update(f"SWAP: {swap.used / (1024**3):.2f} / {swap.total / (1024**3):.2f} GB ({swap.percent}%)")
                self.swap_bar.progress = swap.percent
            else:
                self.swap_label.update("SWAP: No disponible / Desactivada")
                self.swap_bar.progress = 0.0

            current_net = psutil.net_io_counters()
            sent = (current_net.bytes_sent - self.prev_net.bytes_sent) / 1024
            recv = (current_net.bytes_recv - self.prev_net.bytes_recv) / 1024
            self.prev_net = current_net
            self.net_up.update(f"↑ {sent:.1f} KB/s")
            self.net_down.update(f"↓ {recv:.1f} KB/s")

            processes = []
            for p in psutil.process_iter(['pid', 'username', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            processes = sorted(processes, key=lambda x: x.get('cpu_percent') or 0.0, reverse=True)[:10]

            self.table.clear()
            for proc in processes:
                pid = str(proc.get('pid', ''))
                user = str(proc.get('username') or '')
                name = str(proc.get('name') or '')

                cpu_val = proc.get('cpu_percent') or 0.0
                mem_val = proc.get('memory_percent') or 0.0

                if cpu_val > 30.0:
                    cpu_str = f"[bold #f38ba8]{cpu_val:.1f}%[/]"
                elif cpu_val > 10.0:
                    cpu_str = f"[bold #f9e2af]{cpu_val:.1f}%[/]"
                else:
                    cpu_str = f"[#89b4fa]{cpu_val:.1f}%[/]"

                if mem_val > 20.0:
                    mem_str = f"[bold #f38ba8]{mem_val:.1f}%[/]"
                elif mem_val > 5.0:
                    mem_str = f"[bold #f9e2af]{mem_val:.1f}%[/]"
                else:
                    mem_str = f"[#a6e3a1]{mem_val:.1f}%[/]"

                self.table.add_row(
                    f"[#6c7086]{pid}[/]",
                    f"[#cdd6f4]{user}[/]",
                    f"[#cdd6f4]{name}[/]",
                    cpu_str,
                    mem_str
                )
        except Exception as e:
            print(f"Error actualizando métricas: {e}")

if __name__ == "__main__":
    app = SinergiaTopApp()

    def force_exit(sig, frame):
        try:
            app.exit()
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, force_exit)
    signal.signal(signal.SIGTERM, force_exit)
    signal.signal(signal.SIGHUP, force_exit)

    app.run()
