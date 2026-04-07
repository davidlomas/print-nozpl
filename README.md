# Print NO-ZPL (ZPL a PDF a Impresora)

Este es un programa en Python, especialmente útil en macOS y Linux, que vigila permanentemente una carpeta configurada (por defecto `./labels`). Si detecta que se añade un archivo con extensión `.txt` o `.zpl`, lee su contenido en formato ZPL, genera automáticamente un archivo PDF del diseño usando la API en línea de **Labelary**, y manda dicho PDF directamente a la cola de impresión de la impresora configurada.

Finalmente, cambiará la extensión de tu archivo original a `.printed` para evitar que vuelva a imprimirse, y borrará el PDF temporal para mantenerlo limpio.

## Requisitos Previos

- Python 3.6 o superior
- Conexión a internet (para comunicarse con el API de Labelary y procesar el ZPL perfecto)

## Instalación

1. Clona o descarga este repositorio en tu equipo.
2. Abre la terminal, colócate dentro del directorio del proyecto.
3. Instala las dependencias necesarias de python (como `watchdog` y `requests`) ejecutando:

```bash
pip install -r requirements.txt
```

## Configuración 

Antes de iniciar el programa debes revisar y editar el archivo `config.json`. Si no existe, al ejecutar el programa se creará uno base.

Ejemplo de `config.json`:
```json
{
    "watch_folder": "./labels",
    "printer_name": "Brother_HL_1210W_series",
    "label_width_inches": 4,
    "label_height_inches": 8,
    "print_density_dpmm": 8
}
```

- **`watch_folder`**: La ruta de la carpeta que la aplicación debe estar observando para nuevos archivos.
- **`printer_name`**: El nombre exacto de la impresora en el sistema.
  - *Importante para macOS/Linux:* El comando intero `lp` reemplaza los espacios del sistema por guiones bajos. Si tu impresora se llama "Mi Impresora", debes configurarlo como `Mi_Impresora`.
  - Para saber exactamente cómo ve tu sistema a tus impresoras instaladas, puedes correr en tu terminal el comando: `lpstat -p`
- **`label_width_inches`** y **`label_height_inches`**: El ancho y alto de tu etiqueta en pulgadas (ej. `4` y `8` para tamaño 4x8).
- **`print_density_dpmm`**: Densidad de tu impresora (ej. `8` para 203dpi, `12` para 300dpi).

## Posibles Problemas con el Nombre de la Impresora en Mac

Asegúrate de comprobar el nombre exacto de tu impresora desde la línea de comandos ejecutando:
```bash
lpstat -p
```
Y busca el nombre exacto después de "la impresora ..." e ingrésalo en el `config.json`.

## Ejecución

Para encender el sistema solo debes correr el siguiente comando en la terminal (puedes detenerlo presionando `Ctrl+C` en cualquier momento):

```bash
python main.py
```

En cuanto esté corriendo, simplemente lanza un archivo de texto dentro de la capeta `labels` y observa la magia en tu consola.
