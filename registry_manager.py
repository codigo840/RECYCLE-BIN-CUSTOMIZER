"""Acceso acotado al Registro para los iconos de la Papelera."""

from __future__ import annotations

import base64
import ctypes
import json
import os
from pathlib import Path
from typing import Any, Protocol

REGISTRY_SUBKEY = ("Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\CLSID\\"
                   "{645FF040-5081-101B-9F08-00AA002F954E}\\DefaultIcon")
VALUE_NAMES = ("", "empty", "full")


class RegistryBackend(Protocol):
    def read(self, value_name: str) -> tuple[Any, int] | None: ...
    def write(self, value_name: str, value: Any, value_type: int) -> None: ...
    def delete(self, value_name: str) -> None: ...


class WindowsRegistry:
    """Backend winreg que sólo abre la clave HKCU de DefaultIcon."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("El Registro de Windows sólo está disponible en Windows.")
        import winreg
        self._winreg = winreg

    def _with_key(self, access: int):
        return self._winreg.OpenKey(self._winreg.HKEY_CURRENT_USER, REGISTRY_SUBKEY, 0, access)

    def read(self, value_name: str) -> tuple[Any, int] | None:
        try:
            with self._with_key(self._winreg.KEY_READ) as key:
                return self._winreg.QueryValueEx(key, value_name)
        except FileNotFoundError:
            return None

    def write(self, value_name: str, value: Any, value_type: int) -> None:
        with self._winreg.CreateKeyEx(self._winreg.HKEY_CURRENT_USER, REGISTRY_SUBKEY, 0,
                                      self._winreg.KEY_SET_VALUE) as key:
            self._winreg.SetValueEx(key, value_name, 0, value_type, value)

    def delete(self, value_name: str) -> None:
        try:
            with self._with_key(self._winreg.KEY_SET_VALUE) as key:
                self._winreg.DeleteValue(key, value_name)
        except FileNotFoundError:
            pass


def _json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    return value


def _from_json_value(value: Any) -> Any:
    if isinstance(value, dict) and "__bytes__" in value:
        return base64.b64decode(value["__bytes__"])
    return value


class RegistryManager:
    def __init__(self, backend: RegistryBackend | None = None, backup_path: Path | None = None) -> None:
        self.backend = backend or WindowsRegistry()
        default_backup = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "RecycleBinCustomizer" / "registry_backup.json"
        self.backup_path = backup_path or default_backup

    def backup_exists(self) -> bool:
        return self.backup_path.is_file()

    def backup_originals(self) -> None:
        """Guarda una sola vez existencia, datos y tipo de los tres valores."""
        if self.backup_exists():
            return
        values: dict[str, dict[str, Any]] = {}
        for name in VALUE_NAMES:
            result = self.backend.read(name)
            values[name] = {"exists": result is not None,
                            "data": _json_value(result[0]) if result else None,
                            "type": result[1] if result else None}
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.backup_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"subkey": REGISTRY_SUBKEY, "values": values},
                                        indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.backup_path)

    def apply_icons(self, empty_path: Path, full_path: Path) -> None:
        self.backup_originals()
        # El valor predeterminado también se establece para shells que lo consultan.
        value_type = _string_type()
        self.backend.write("", f"{empty_path},0", value_type)
        self.backend.write("empty", f"{empty_path},0", value_type)
        self.backend.write("full", f"{full_path},0", value_type)
        notify_shell()

    def restore_originals(self) -> None:
        if not self.backup_exists():
            raise FileNotFoundError("Todavía no existe un respaldo de la configuración original.")
        payload = json.loads(self.backup_path.read_text(encoding="utf-8"))
        if payload.get("subkey") != REGISTRY_SUBKEY:
            raise ValueError("El respaldo no pertenece a la Papelera de reciclaje.")
        for name in VALUE_NAMES:
            saved = payload["values"][name]
            if saved["exists"]:
                self.backend.write(name, _from_json_value(saved["data"]), int(saved["type"]))
            else:
                self.backend.delete(name)
        notify_shell()


def _string_type() -> int:
    if os.name == "nt":
        import winreg
        return winreg.REG_SZ
    return 1  # útil para el backend de pruebas


def notify_shell() -> None:
    """Solicita a Explorer que actualice asociaciones/iconos sin reiniciar."""
    if os.name != "nt":
        return
    shell32 = ctypes.windll.shell32
    # SHCNE_ASSOCCHANGED, SHCNF_IDLIST
    shell32.SHChangeNotify(0x08000000, 0x0000, None, None)

