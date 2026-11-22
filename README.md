# Recycle Bin Customizer

Aplicación de escritorio para Windows 10/11 que cambia los iconos de la Papelera de reciclaje para los estados vacía y llena. La interfaz está en español, usa tema oscuro y no requiere permisos de administrador.

## Instalación y ejecución

Se requiere Python 3.11 o superior.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

En cada panel puede arrastrar una imagen directamente desde el Explorador de Windows o pulsar **Seleccionar imagen**. Se aceptan PNG, JPG, JPEG e ICO; al pasar un archivo sobre el panel se resalta y al soltarlo aparece la vista previa manteniendo la proporción original. Las imágenes se convierten a ICO con tamaños 16, 32, 48, 64, 128 y 256 px en `%LOCALAPPDATA%\RecycleBinCustomizer\icons`.

Antes del primer cambio se guarda una copia exacta de los valores `DefaultIcon` (incluyendo valores ausentes) en `%LOCALAPPDATA%\RecycleBinCustomizer\registry_backup.json`. Ese respaldo no se sobrescribe con aplicaciones posteriores. **Restaurar originales** recupera el respaldo y elimina sólo los valores que no existían previamente.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan un Registro en memoria y no modifican el Registro de Windows real.

## Ejecutable

```powershell
pyinstaller --noconfirm --clean RecycleBinCustomizer.spec
```

El ejecutable queda en `dist\RecycleBinCustomizer\RecycleBinCustomizer.exe`. Para un único archivo, agregue `--onefile`.

## Seguridad y alcance

Sólo se usa `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}\DefaultIcon`. No se ejecutan comandos externos ni se modifican claves globales. Explorer recibe una notificación `SHChangeNotify` para actualizar los iconos sin reiniciar cuando Windows lo permite.

