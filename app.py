"""
AI Music Detector - Flask API Server
API REST para detectar música generada con IA

OPTIMIZADO: Solo realiza detección de IA vs Humano
(Sin extracción de BPM, Key, Energy, Danceability - procesado en el cliente)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from classifier import AIDetector
from visualizer import SpectralVisualizer
import traceback
import io
import base64
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configurar CORS desde variables de entorno
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
CORS(app, origins=CORS_ORIGINS)

# Configuración desde variables de entorno con valores por defecto
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'mp3,wav,ogg,m4a,flac,aac').split(','))
MAX_FILE_SIZE = int(os.getenv('MAX_CONTENT_LENGTH', 68157440))  # 65 MB por defecto
MODEL_PATH = os.getenv('MODEL_PATH', './models/detector.pkl')
USE_PRETRAINED_MODEL = os.getenv('USE_PRETRAINED_MODEL', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEV_MODE = os.getenv('DEV_MODE', 'True').lower() == 'true'

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Inicializar detector y visualizador
detector = AIDetector()
visualizer = SpectralVisualizer()


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'message': 'AI Music Detector API is running (AI detection only)',
        'version': '2.0.0'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """
    Endpoint principal para detectar música generada con IA

    Espera un archivo de audio en multipart/form-data

    Returns:
        JSON con detección de IA:
        - is_ai_generated: bool
        - confidence: float (0-1)
        - ai_probability: float (0-100)
        - human_probability: float (0-100)
    """
    try:
        # Verificar que se envió un archivo
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No se encontró archivo de audio',
                'message': 'Debes enviar un archivo con el campo "audio"'
            }), 400

        file = request.files['audio']

        # Verificar que se seleccionó un archivo
        if file.filename == '':
            return jsonify({
                'error': 'No se seleccionó archivo',
                'message': 'El nombre del archivo está vacío'
            }), 400

        # Verificar extensión
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Formato no soportado',
                'message': f'Formatos permitidos: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        try:
            # Analizar audio
            result = detector.predict(temp_path)

            # Añadir información adicional
            result['filename'] = filename
            result['status'] = 'success'

            return jsonify(result), 200

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        print(f"Error en análisis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error al procesar audio',
            'message': str(e),
            'status': 'error'
        }), 500


@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Endpoint para analizar múltiples archivos

    Returns:
        JSON con resultados de todos los análisis
    """
    try:
        files = request.files.getlist('audio')

        if not files:
            return jsonify({
                'error': 'No se encontraron archivos',
                'message': 'Debes enviar al menos un archivo'
            }), 400

        results = []

        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue

            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(temp_path)
                result = detector.predict(temp_path)
                result['filename'] = filename
                result['status'] = 'success'
                results.append(result)

            except Exception as e:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': str(e)
                })

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        return jsonify({
            'status': 'success',
            'total': len(results),
            'results': results
        }), 200

    except Exception as e:
        print(f"Error en batch analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error al procesar archivos',
            'message': str(e),
            'status': 'error'
        }), 500


@app.route('/api/info', methods=['GET'])
def get_info():
    """
    Retorna información sobre el detector

    Returns:
        JSON con información del sistema
    """
    return jsonify({
        'name': 'AI Music Detector',
        'description': 'Detecta música generada con IA usando análisis espectral (Solo AI detection - sin BPM/Key/Energy)',
        'version': '2.0.0',
        'based_on': 'ISMIR 2025 paper: A Fourier Explanation of AI-music Artifacts',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
        'analysis_method': 'Fakeprint analysis + Logistic Regression',
        'frequency_range': '5000-16000 Hz',
        'model_status': 'heuristic' if not detector.is_trained else 'trained',
        'features': 'AI detection only (musical features processed client-side)'
    })


@app.route('/api/visualize', methods=['POST'])
def visualize_audio():
    """
    Endpoint para generar visualización del análisis espectral

    Retorna un gráfico completo con:
    - Espectrograma
    - Fakeprint (5-16 kHz)
    - Distribución de energía espectral
    - Tabla de características

    Returns:
        JSON con imagen en base64 y datos del análisis
    """
    try:
        # Verificar que se envió un archivo
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No se encontró archivo de audio',
                'message': 'Debes enviar un archivo con el campo "audio"'
            }), 400

        file = request.files['audio']

        if file.filename == '':
            return jsonify({
                'error': 'No se seleccionó archivo',
                'message': 'El nombre del archivo está vacío'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Formato no soportado',
                'message': f'Formatos permitidos: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        try:
            # Generar visualización
            image_base64, analysis_data = visualizer.generate_analysis_plot(temp_path)

            return jsonify({
                'status': 'success',
                'filename': filename,
                'image': image_base64,
                'analysis': analysis_data
            }), 200

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        print(f"Error en visualización: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error al generar visualización',
            'message': str(e),
            'status': 'error'
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Maneja archivos demasiado grandes"""
    return jsonify({
        'error': 'Archivo demasiado grande',
        'message': f'El tamaño máximo permitido es {MAX_FILE_SIZE / (1024 * 1024)} MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Maneja rutas no encontradas"""
    return jsonify({
        'error': 'Endpoint no encontrado',
        'message': 'La ruta solicitada no existe'
    }), 404


if __name__ == '__main__':
    # Configuración desde variables de entorno
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    print("=" * 50)
    print("AI Music Detector - Backend Server v2.0")
    print("OPTIMIZED: AI Detection Only")
    print("=" * 50)
    print(f"Entorno: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Modo Debug: {FLASK_DEBUG}")
    print(f"Formatos soportados: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Tamaño máximo: {MAX_FILE_SIZE / (1024 * 1024)} MB")
    print(f"Directorio de uploads: {UPLOAD_FOLDER}")
    print(f"Modo del modelo: {'Heurístico' if not detector.is_trained else 'Entrenado'}")
    print(f"CORS origins: {CORS_ORIGINS}")
    print(f"Funcionalidad: Solo detección de IA (BPM/Key/Energy en cliente)")
    print("=" * 50)
    print(f"\nServidor iniciando en http://{HOST}:{PORT}")
    print("\nEndpoints disponibles:")
    print("  GET  /health            - Health check")
    print("  GET  /api/info          - Información del detector")
    print("  POST /api/analyze       - Detectar si audio es generado con IA")
    print("  POST /api/visualize     - Generar gráfico de análisis espectral")
    print("  POST /api/batch-analyze - Analizar múltiples archivos")
    print("=" * 50)

    # Iniciar servidor
    app.run(host=HOST, port=PORT, debug=FLASK_DEBUG)
