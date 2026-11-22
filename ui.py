"""Interfaz CustomTkinter en español."""

from __future__ import annotations

from pathlib import Path
from tkinter import Event, filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from icon_manager import IconState, convert_to_ico, preview_image
from registry_manager import RegistryManager


class IconPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, title: str, state: IconState, on_select) -> None:
        super().__init__(master, corner_radius=16)
        self.state = state
        self.on_select = on_select
        self.source: Path | None = None
        self._normal_color = self.cget("fg_color")
        self.preview = ctk.CTkLabel(
            self, text="Arrastrá una imagen aquí o hacé clic para buscar",
            width=150, height=140, wraplength=180
        )
        self.preview.pack(padx=20, pady=(18, 8))
        self.filename_label = ctk.CTkLabel(self, text="Ninguna imagen seleccionada", wraplength=220)
        self.filename_label.pack(padx=16, pady=(0, 4))
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(pady=4)
        self.select_button = ctk.CTkButton(self, text="Seleccionar imagen", command=self.select)
        self.select_button.pack(padx=20, pady=(8, 20))
        self._register_drop_targets()

    def _register_drop_targets(self) -> None:
        for widget in (self, self.preview, self.filename_label, self.title_label, self.select_button):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._drop)
            widget.dnd_bind("<<DragEnter>>", self._drag_enter)
            widget.dnd_bind("<<DragLeave>>", self._drag_leave)

    def _drag_enter(self, _event: Event) -> None:
        self.configure(fg_color=("#dbeafe", "#1e3a5f"))

    def _drag_leave(self, _event: Event) -> None:
        self.configure(fg_color=self._normal_color)

    def _drop(self, event: Event) -> str:
        self._drag_leave(event)
        paths = event.widget.tk.splitlist(event.data)
        if len(paths) != 1:
            messagebox.showerror("Archivo no válido", "Soltá una sola imagen por vez.")
            return "break"
        self.load(Path(paths[0]))
        return "break"

    def load(self, selected: Path) -> None:
        try:
            image = preview_image(selected)
            rendered = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.preview.configure(image=rendered, text="")
            self.preview.image = rendered
            self.filename_label.configure(text=selected.name)
            self.source = selected
            self.on_select()
        except (OSError, ValueError) as error:
            messagebox.showerror("Imagen no válida", str(error))

    def select(self) -> None:
        selected = filedialog.askopenfilename(title="Seleccionar icono", filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg *.ico"), ("Todos los archivos", "*.*")])
        if not selected:
            return
        self.load(Path(selected))


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self) -> None:
        ctk.CTk.__init__(self)
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Recycle Bin Customizer")
        self.geometry("640x470")
        self.minsize(580, 430)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        title_label = ctk.CTkLabel(
            self, text="Recycle Bin Customizer",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=24, pady=(24, 18))
        panels = ctk.CTkFrame(self, fg_color="transparent")
        panels.grid(row=1, column=0, sticky="nsew", padx=24)
        panels.grid_columnconfigure(0, weight=1)
        panels.grid_columnconfigure(1, weight=1)
        panels.grid_rowconfigure(0, weight=1)
        self.empty_panel = IconPanel(panels, "Papelera vacía", "empty", self._update_buttons)
        self.full_panel = IconPanel(panels, "Papelera llena", "full", self._update_buttons)
        self.empty_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.full_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, pady=(18, 22))
        self.apply_button = ctk.CTkButton(actions, text="Aplicar cambios", command=self.apply, state="disabled")
        self.apply_button.pack(side="left", padx=8)
        ctk.CTkButton(actions, text="Restaurar originales", fg_color="transparent", border_width=1,
                      command=self.restore).pack(side="left", padx=8)

    def _update_buttons(self) -> None:
        if self.empty_panel.source and self.full_panel.source:
            self.apply_button.configure(state="normal")

    def apply(self) -> None:
        try:
            empty = convert_to_ico(self.empty_panel.source, "empty")
            full = convert_to_ico(self.full_panel.source, "full")
            RegistryManager().apply_icons(empty, full)
            messagebox.showinfo("Cambios aplicados", "Los iconos de la Papelera fueron actualizados.")
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo aplicar", str(error))

    def restore(self) -> None:
        try:
            RegistryManager().restore_originals()
            messagebox.showinfo("Restauración completa", "Se recuperó la configuración original.")
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo restaurar", str(error))


def run() -> None:
    App().mainloop()

