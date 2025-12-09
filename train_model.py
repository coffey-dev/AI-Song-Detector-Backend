"""
Script de Entrenamiento del Modelo AI Music Detector
======================================================

Este script entrena el clasificador usando archivos de audio reales y sintéticos.

Uso:
    python train_model.py --real <carpeta_musica_real> --ai <carpeta_musica_ai>

Ejemplo:
    python train_model.py --real ./data/human --ai ./data/ai_generated

Estructura esperada:
    data/
    ├── human/           # Música creada por humanos
    │   ├── song1.mp3
    │   ├── song2.wav
    │   └── ...
    └── ai_generated/    # Música generada con IA
        ├── ai_song1.mp3
        ├── ai_song2.wav
        └── ...
"""

import os
import sys
import argparse
import glob
from classifier import AIDetector
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np


def collect_audio_files(directory, extensions=['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']):
    """
    Recopila todos los archivos de audio de un directorio

    Args:
        directory: Ruta al directorio
        extensions: Lista de extensiones permitidas

    Returns:
        Lista de rutas a archivos de audio
    """
    audio_files = []
    for ext in extensions:
        pattern = os.path.join(directory, '**', ext)
        audio_files.extend(glob.glob(pattern, recursive=True))

    return audio_files


def create_sample_structure():
    """
    Crea estructura de directorios de ejemplo para el entrenamiento
    """
    print("\n" + "="*60)
    print("ESTRUCTURA DE DATOS REQUERIDA")
    print("="*60)
    print("""
Para entrenar el modelo, necesitas organizar tus archivos de audio así:

ai-music-detector-backend/
└── data/
    ├── human/              # Música creada por humanos
    │   ├── song1.mp3
    │   ├── song2.wav
    │   └── ...
    └── ai_generated/       # Música generada con IA
        ├── ai_song1.mp3
        ├── ai_song2.wav
        └── ...

Recomendaciones:
- Mínimo 20 archivos de cada tipo (más es mejor)
- Archivos de buena calidad (no degradados)
- Variedad de estilos musicales
- Duración: 30 segundos o más por archivo

Fuentes sugeridas para música IA:
- Suno AI (https://www.suno.ai/)
- Udio (https://www.udio.com/)
- MusicGen
- AudioCraft

Fuentes para música humana:
- Grabaciones propias
- Bibliotecas de música libre (Free Music Archive, etc.)
- Canciones con licencia Creative Commons
    """)
    print("="*60)


def train_and_evaluate(real_dir, ai_dir, model_output_path='./models/detector.pkl', test_size=0.2):
    """
    Entrena el modelo y evalúa su desempeño

    Args:
        real_dir: Directorio con música humana
        ai_dir: Directorio con música IA
        model_output_path: Donde guardar el modelo entrenado
        test_size: Porcentaje de datos para testing
    """
    print("\n" + "="*60)
    print("ENTRENAMIENTO DEL MODELO AI MUSIC DETECTOR")
    print("="*60)

    # Recopilar archivos
    print("\n[1/6] Recopilando archivos de audio...")
    real_files = collect_audio_files(real_dir)
    ai_files = collect_audio_files(ai_dir)

    print(f"   ✓ Archivos de música humana: {len(real_files)}")
    print(f"   ✓ Archivos de música IA: {len(ai_files)}")

    if len(real_files) < 10 or len(ai_files) < 10:
        print("\n❌ ERROR: Se necesitan al menos 10 archivos de cada tipo")
        print("   Recomendación: 20+ archivos de cada tipo para mejor precisión")
        return False

    # Dividir en train/test
    print("\n[2/6] Dividiendo datos en entrenamiento y prueba...")
    real_train, real_test = train_test_split(real_files, test_size=test_size, random_state=42)
    ai_train, ai_test = train_test_split(ai_files, test_size=test_size, random_state=42)

    print(f"   ✓ Entrenamiento: {len(real_train)} humanos, {len(ai_train)} IA")
    print(f"   ✓ Prueba: {len(real_test)} humanos, {len(ai_test)} IA")

    # Entrenar modelo
    print("\n[3/6] Entrenando modelo de clasificación...")
    detector = AIDetector()

    try:
        detector.train(real_train, ai_train)
        print("   ✓ Modelo entrenado exitosamente!")
    except Exception as e:
        print(f"\n❌ ERROR al entrenar: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Evaluar en conjunto de prueba
    print("\n[4/6] Evaluando modelo en datos de prueba...")

    y_true = []
    y_pred = []
    y_prob = []

    print("   Analizando archivos de prueba...")

    # Evaluar música humana
    for i, audio_path in enumerate(real_test):
        try:
            result = detector.predict(audio_path)
            y_true.append(0)  # 0 = humano
            y_pred.append(1 if result['is_ai_generated'] else 0)
            y_prob.append(result['ai_probability'])
            print(f"   [{i+1}/{len(real_test)}] Humano: {os.path.basename(audio_path)}", end='\r')
        except Exception as e:
            print(f"\n   ⚠ Error con {audio_path}: {str(e)}")

    print(f"   ✓ Evaluados {len(real_test)} archivos humanos")

    # Evaluar música IA
    for i, audio_path in enumerate(ai_test):
        try:
            result = detector.predict(audio_path)
            y_true.append(1)  # 1 = IA
            y_pred.append(1 if result['is_ai_generated'] else 0)
            y_prob.append(result['ai_probability'])
            print(f"   [{i+1}/{len(ai_test)}] IA: {os.path.basename(audio_path)}", end='\r')
        except Exception as e:
            print(f"\n   ⚠ Error con {audio_path}: {str(e)}")

    print(f"   ✓ Evaluados {len(ai_test)} archivos IA")

    # Calcular métricas
    print("\n[5/6] Calculando métricas de desempeño...")

    accuracy = accuracy_score(y_true, y_pred)

    print("\n" + "="*60)
    print("RESULTADOS DEL MODELO")
    print("="*60)
    print(f"\nPrecisión Global: {accuracy*100:.2f}%\n")

    print("Reporte de Clasificación:")
    print("-" * 60)
    print(classification_report(
        y_true,
        y_pred,
        target_names=['Música Humana', 'Música IA'],
        digits=3
    ))

    print("\nMatriz de Confusión:")
    print("-" * 60)
    cm = confusion_matrix(y_true, y_pred)
    print(f"                 Predicho Humano  |  Predicho IA")
    print(f"Real Humano:            {cm[0][0]:3d}       |      {cm[0][1]:3d}")
    print(f"Real IA:                {cm[1][0]:3d}       |      {cm[1][1]:3d}")
    print("-" * 60)

    # Calcular métricas adicionales
    if len(cm) == 2:
        tn, fp, fn, tp = cm.ravel()

        # Tasa de Verdaderos Positivos (sensibilidad)
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0

        # Tasa de Verdaderos Negativos (especificidad)
        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0

        # Tasa de Falsos Positivos
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

        # Tasa de Falsos Negativos
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

        print("\nMétricas Adicionales:")
        print(f"  • Sensibilidad (detecta IA correctamente): {tpr*100:.1f}%")
        print(f"  • Especificidad (detecta humano correctamente): {tnr*100:.1f}%")
        print(f"  • Tasa Falsos Positivos (humano marcado como IA): {fpr*100:.1f}%")
        print(f"  • Tasa Falsos Negativos (IA marcada como humana): {fnr*100:.1f}%")

    print("="*60)

    # Guardar modelo
    print(f"\n[6/6] Guardando modelo en {model_output_path}...")
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    detector.save_model(model_output_path)
    print(f"   ✓ Modelo guardado exitosamente!")

    print("\n" + "="*60)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("="*60)
    print(f"\nEl modelo está listo para usar en la aplicación.")
    print(f"Para usarlo, configura en el .env:")
    print(f"  USE_PRETRAINED_MODEL=True")
    print(f"  MODEL_PATH={model_output_path}")
    print("="*60 + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Entrena el modelo AI Music Detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Entrenar con carpetas predeterminadas
  python train_model.py --real ./data/human --ai ./data/ai_generated

  # Especificar ruta de salida del modelo
  python train_model.py --real ./data/human --ai ./data/ai_generated --output ./models/custom_model.pkl

  # Usar 30% de datos para testing
  python train_model.py --real ./data/human --ai ./data/ai_generated --test-size 0.3

  # Ver estructura de datos requerida
  python train_model.py --help-structure
        """
    )

    parser.add_argument(
        '--real',
        type=str,
        help='Directorio con archivos de música humana'
    )

    parser.add_argument(
        '--ai',
        type=str,
        help='Directorio con archivos de música generada con IA'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./models/detector.pkl',
        help='Ruta donde guardar el modelo entrenado (default: ./models/detector.pkl)'
    )

    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Porcentaje de datos para testing (default: 0.2 = 20%%)'
    )

    parser.add_argument(
        '--help-structure',
        action='store_true',
        help='Muestra la estructura de directorios requerida y sale'
    )

    args = parser.parse_args()

    # Mostrar ayuda de estructura
    if args.help_structure:
        create_sample_structure()
        return 0

    # Validar argumentos
    if not args.real or not args.ai:
        print("❌ ERROR: Debes especificar las carpetas --real y --ai")
        print("Usa --help para ver opciones o --help-structure para ver la estructura requerida")
        return 1

    # Verificar que existan los directorios
    if not os.path.exists(args.real):
        print(f"❌ ERROR: El directorio '{args.real}' no existe")
        return 1

    if not os.path.exists(args.ai):
        print(f"❌ ERROR: El directorio '{args.ai}' no existe")
        return 1

    # Entrenar modelo
    success = train_and_evaluate(
        real_dir=args.real,
        ai_dir=args.ai,
        model_output_path=args.output,
        test_size=args.test_size
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
