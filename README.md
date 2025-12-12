# AI Music Detector - Backend v2.0

Backend API optimizado para detectar música generada con Inteligencia Artificial.

## Descripción

Este backend implementa el método descrito en el paper ISMIR 2025 "A Fourier Explanation of AI-music Artifacts" usando la librería `librosa` para el análisis de audio.

**⚡ OPTIMIZADO v2.0**: Este backend ahora se enfoca **exclusivamente en detección de IA vs Humano**. Las características musicales (BPM, Key, Energy, Danceability) se procesan del lado del cliente usando módulos nativos para mayor rendimiento y menor latencia.

### Método de Detección

1. **Análisis Espectral**: Calcula el espectrograma usando STFT
2. **Fakeprint Extraction**: Extrae características espectrales en frecuencias altas (5-16 kHz)
3. **Lower Hull Analysis**: Normaliza usando el envolvente inferior
4. **Clasificación**: Usa regresión logística o heurística para clasificar

## Instalación

### Requisitos

- Python 3.8+
- pip

### Instalar dependencias

```bash
cd ai-music-detector-backend
pip install -r requirements.txt
```

### Dependencias adicionales (Linux)

Si tienes problemas con librosa, instala:

```bash
# Ubuntu/Debian
sudo apt-get install libsndfile1 ffmpeg

# Fedora/RHEL
sudo dnf install libsndfile ffmpeg
```

## Uso

### Iniciar el servidor

```bash
python app.py
```

El servidor estará disponible en `http://localhost:5000`

### Modo standalone

Puedes probar el clasificador directamente:

```bash
python classifier.py path/to/audio.mp3
```

## API Endpoints

### GET /health

Health check del servidor

**Response:**
```json
{
  "status": "ok",
  "message": "AI Music Detector API is running (AI detection only)",
  "version": "2.0.0"
}
```

### GET /api/info

Información sobre el detector

**Response:**
```json
{
  "name": "AI Music Detector",
  "description": "Detecta música generada con IA usando análisis espectral (Solo AI detection - sin BPM/Key/Energy)",
  "version": "2.0.0",
  "supported_formats": ["mp3", "wav", "ogg", "m4a", "flac", "aac"],
  "max_file_size_mb": 65,
  "analysis_method": "Fakeprint analysis + Logistic Regression",
  "frequency_range": "5000-16000 Hz",
  "features": "AI detection only (musical features processed client-side)"
}
```

### POST /api/analyze

Detecta si un archivo de audio fue generado con IA (sin extraer características musicales)

**Request:**
- Content-Type: `multipart/form-data`
- Field: `audio` (archivo de audio)

**Response:**
```json
{
  "is_ai_generated": false,
  "confidence": 0.85,
  "ai_probability": 15.3,
  "human_probability": 84.7,
  "filename": "song.mp3",
  "status": "success"
}
```

**Nota:** Este endpoint ya NO retorna BPM, Key, Energy ni Danceability. Esas características se procesan en el cliente para mayor rendimiento.

### POST /api/batch-analyze

Analiza múltiples archivos

**Request:**
- Content-Type: `multipart/form-data`
- Field: `audio` (múltiples archivos)

**Response:**
```json
{
  "status": "success",
  "total": 2,
  "results": [
    {
      "is_ai_generated": false,
      "ai_probability": 15.3,
      "filename": "song1.mp3"
    },
    {
      "is_ai_generated": true,
      "ai_probability": 89.2,
      "filename": "song2.mp3"
    }
  ]
}
```

## Pruebas con cURL

```bash
# Health check
curl http://localhost:5000/health

# Información
curl http://localhost:5000/api/info

# Analizar audio
curl -X POST -F "audio=@test.mp3" http://localhost:5000/api/analyze
```

## Configuración

Edita las constantes en `app.py`:

- `MAX_FILE_SIZE`: Tamaño máximo de archivo (default: 50 MB)
- `ALLOWED_EXTENSIONS`: Formatos permitidos
- `UPLOAD_FOLDER`: Carpeta temporal para uploads

En `audio_analyzer.py`:

- `sr`: Sample rate (default: 16000 Hz)
- `n_fft`: Tamaño de FFT (default: 16384)
- `fmin`, `fmax`: Rango de frecuencias (default: 5000-16000 Hz)

## Entrenamiento de Modelo

El sistema funciona con heurística por defecto. Para entrenar un modelo:

```python
from classifier import AIDetector

detector = AIDetector()

# Listas de archivos
real_files = ['real1.mp3', 'real2.mp3', ...]
ai_files = ['ai1.mp3', 'ai2.mp3', ...]

# Entrenar
detector.train(real_files, ai_files)

# Guardar
detector.save_model('model.pkl')
```

Para usar el modelo entrenado:

```python
detector = AIDetector(model_path='model.pkl')
```

## Producción

Para producción, usa un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Licencia

Este proyecto está basado en el paper ISMIR 2025 que tiene licencia CC BY-NC 4.0.
Solo para uso no comercial e investigación.
