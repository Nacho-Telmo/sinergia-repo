#!/usr/bin/env python3

import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk


class ReflectorApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Sinergia Reflector Top")
    self.root.geometry("540x540")
    self.root.resizable(False, False)

    # Configuración de colores para el tema oscuro
    self.bg_color = "#2b2b2b"
    self.frame_bg = "#3c3f41"
    self.accent_color = "#2ecc71"

    # Aplicar color de fondo a la ventana principal
    self.root.configure(bg=self.bg_color)

    # Variable para almacenar la opción seleccionada (10, 20 o 30)
    self.mirror_count = tk.IntVar(value=10)

    self.create_widgets()

  def create_widgets(self):
    # Título principal con el nombre de la aplicación
    title_label = tk.Label(
        self.root,
        text="Sinergia-Reflector-Top",
        font=("Arial", 14, "bold"),
        bg=self.bg_color,
        fg="#ffffff",
    )
    title_label.pack(pady=12)

    # Contenedor de opciones (Radiobuttons)
    frame_options = tk.LabelFrame(
        self.root,
        text=" Opciones de velocidad ",
        font=("Arial", 10, "bold"),
        bg=self.frame_bg,
        fg="#ffffff",
        padx=20,
        pady=10,
    )
    frame_options.pack(fill="x", padx=20, pady=5)

    # Opciones con colores propios para cada texto
    options = [
        ("Top 10 espejos más veloces", 10, "#ff79c6"),  # Rosado / Magenta
        ("Top 20 espejos más veloces", 20, "#50fa7b"),  # Verde brillante
        ("Top 30 espejos más veloces", 30, "#8be9fd"),  # Cyan claro
    ]

    for text, value, color in options:
      tk.Radiobutton(
          frame_options,
          text=text,
          variable=self.mirror_count,
          value=value,
          font=("Arial", 10, "bold"),
          bg=self.frame_bg,
          fg=color,
          selectcolor=self.bg_color,
          activebackground=self.frame_bg,
          activeforeground=color,
      ).pack(anchor="w", pady=4)

    # Botón de ejecución
    self.btn_run = tk.Button(
        self.root,
        text="Generar Backup y Actualizar",
        command=self.start_reflector_thread,
        bg=self.accent_color,
        fg="#1e1e1e",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=6,
        relief=tk.FLAT,
        cursor="hand2",
    )
    self.btn_run.pack(pady=12)

    # Barra de progreso (Indeterminada para mostrar actividad)
    self.progress = ttk.Progressbar(
        self.root, orient="horizontal", length=490, mode="indeterminate"
    )
    self.progress.pack(pady=5)

    # Área de registro / Vista Previa detallada
    lbl_log = tk.Label(
        self.root,
        text="Vista previa y registro de la operación:",
        font=("Arial", 9),
        bg=self.bg_color,
        fg="#b2bec3",
    )
    lbl_log.pack(anchor="w", padx=25, pady=(5, 0))

    self.status_box = scrolledtext.ScrolledText(
        self.root,
        width=62,
        height=12,
        font=("Consolas", 9),
        bg="#1e1e1e",
        fg="#00ffcc",
        insertbackground="white",
    )
    self.status_box.pack(pady=5)
    self.status_box.insert(
        tk.END,
        "Sistema listo. Se creará un respaldo automático en"
        " /etc/pacman.d/mirrorlist.bak\n",
    )
    self.status_box.config(state=tk.DISABLED)

  def start_reflector_thread(self):
    # Deshabilitar botón y activar barra de progreso en un hilo separado
    self.btn_run.config(state=tk.DISABLED, bg="#7f8c8d")
    self.progress.start(10)
    self.log("\n[i] Iniciando proceso de sondeo y respaldo...\n")

    thread = threading.Thread(target=self.run_reflector)
    thread.daemon = True
    thread.start()

  def run_reflector(self):
    count = self.mirror_count.get()

    # Comando optimizado: --latest 40 y --threads 5 para acelerar el sondeo masivo
    bash_script = (
        f"cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak && "
        f"reflector --latest 40 --age 24 --protocol https --sort rate --threads 5 --number"
        f" {count} --save /etc/pacman.d/mirrorlist"
    )

    cmd = ["pkexec", "bash", "-c", bash_script]

    try:
      # Se incluye env=os.environ para que pkexec detecte la sesión gráfica (DISPLAY) y pida la contraseña
      process = subprocess.Popen(
          cmd,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          text=True,
          env=os.environ,
      )
      stdout, stderr = process.communicate()

      if process.returncode == 0:
        self.log(
            "[✔] ¡Copia de respaldo creada en"
            " /etc/pacman.d/mirrorlist.bak!\n"
        )
        self.log(
            f"[✔] ¡Espejos actualizados con éxito (Top {count})!\n\n"
        )
        self.log(
            "--- Vista previa de los espejos seleccionados ---\n"
            + stdout.strip()
            + "\n"
        )
        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "Sinergia-Reflector-Top",
                f"Se han configurado los {count} espejos más veloces y se"
                " guardó el respaldo.",
            ),
        )
      else:
        err_msg = stderr.strip() or "Acción cancelada o error de permisos."
        self.log(f"[✘] Aviso/Error: {err_msg}\n")
        self.root.after(
            0,
            lambda: messagebox.showwarning(
                "Aviso", "La operación fue cancelada o no se otorgaron permisos."
            ),
        )
    except Exception as e:
        self.log(f"[✘] Excepción crítica: {str(e)}\n")
        self.root.after(
            0,
            lambda: messagebox.showerror("Error", f"Ocurrió un error:\n{e}"),
        )
    finally:
      self.root.after(0, self.stop_progress)

  def stop_progress(self):
    self.progress.stop()
    self.btn_run.config(state=tk.NORMAL, bg=self.accent_color)

  def log(self, message):
    self.status_box.config(state=tk.NORMAL)
    self.status_box.insert(tk.END, message)
    self.status_box.see(tk.END)
    self.status_box.config(state=tk.DISABLED)


if __name__ == "__main__":
  root = tk.Tk()
  app = ReflectorApp(root)
  root.mainloop()



