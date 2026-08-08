# YT Downloader

Web app local para descargar videos de YouTube como MP3 o MP4.

## Requisitos

- Python 3.x
- Node.js (para resolver challenges de YouTube)
- ffmpeg

## Instalación

```bash
pip install flask yt-dlp
```

Instala ffmpeg: https://ffmpeg.org/download.html

## Uso

1. Exporta tus cookies de YouTube con la extensión "Get cookies.txt LOCALLY" y guárdalas como `cookies cookies.txt` en la carpeta raíz.
2. Edita `app.py` y ajusta la ruta de `FFMPEG` y `COOKIES` según tu sistema.
3. Ejecuta el servidor:

```bash
python app.py
```

4. Abre http://localhost:5055 en tu navegador.
5. Pega una o varias URLs de YouTube (una por línea), elige el formato y descarga.

## Características

- Descarga MP3 (solo audio) o MP4 (video completo)
- Progreso en tiempo real via Server-Sent Events
- Múltiples descargas en paralelo
- Botón de descarga directa al terminar
