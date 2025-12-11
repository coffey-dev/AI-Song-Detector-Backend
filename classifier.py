"""
AI Music Detector - Clasificador
"""

import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from audio_analyzer import AudioAnalyzer


class AIDetector:
    """
    Clasificador para detectar música generada con IA
    """

    def __init__(self, model_path=None):
        """
        Inicializa el detector

        Args:
            model_path: Ruta al modelo pre-entrenado (opcional)
        """
        self.analyzer = AudioAnalyzer()
        self.model = None
        self.is_trained = False

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            self.is_trained = True

    def train(self, real_audio_paths, synthetic_audio_paths):
        """
        Entrena el clasificador

        Args:
            real_audio_paths: Lista de rutas a archivos de música real
            synthetic_audio_paths: Lista de rutas a archivos de música sintética
        """
        print("Extrayendo características de música real...")
        real_features = [self.analyzer.analyze_audio_file(path) for path in real_audio_paths]

        print("Extrayendo características de música sintética...")
        synth_features = [self.analyzer.analyze_audio_file(path) for path in synthetic_audio_paths]

        # Preparar datos
        X_real = np.stack(real_features)
        X_synth = np.stack(synth_features)

        X = np.concatenate([X_real, X_synth], axis=0)
        y = np.concatenate([np.zeros(len(X_real)), np.ones(len(X_synth))], axis=0)

        # Crear y entrenar modelo
        print("Entrenando modelo...")
        self.model = LogisticRegression(class_weight="balanced", max_iter=1000)
        self.model.fit(X, y)
        self.is_trained = True
        print("Modelo entrenado!")

    def predict(self, audio_path):
        """
        Predice si un audio es generado con IA

        Args:
            audio_path: Ruta al archivo de audio

        Returns:
            dict con:
                - is_ai_generated: bool
                - confidence: float (0-1)
                - ai_probability: float (0-100)
                - human_probability: float (0-100)
                - duration: float (segundos)
                - quality: str (Low/Medium/High/Lossless)
                - bpm: float (beats per minute)
                - key: str (tonalidad musical)
                - danceability: float (0-1)
                - energy: float (0-1)
        """
        # Extraer metadata del audio (incluyendo análisis musicales)
        # Esta función ya carga el audio internamente
        metadata = self._extract_audio_metadata(audio_path)

        if not self.is_trained:
            # Cargar audio una sola vez para análisis heurístico
            # Reutilizar la carga para evitar redundancia
            audio = self.analyzer.load_audio(audio_path)
            result = self._predict_heuristic_with_audio(audio, audio_path)
            # Agregar metadata
            result.update(metadata)
            return result

        # Extraer características
        features = self.analyzer.analyze_audio_file(audio_path)
        features = features.reshape(1, -1)

        # Predecir
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]

        is_ai = bool(prediction == 1)
        ai_prob = float(probability[1] * 100)  # Probabilidad de ser IA
        confidence = float(max(probability))

        result = {
            'is_ai_generated': is_ai,
            'confidence': confidence,
            'ai_probability': ai_prob,
            'human_probability': float(probability[0] * 100)
        }

        # Agregar metadata musical
        result.update(metadata)

        return result

    def _extract_audio_metadata(self, audio_path):
        """
        Extrae duración, calidad y análisis musicales del audio

        Args:
            audio_path: Ruta al archivo de audio

        Returns:
            dict con metadata completa: {
                'duration': float,
                'quality': str,
                'bpm': float,
                'key': str,
                'danceability': float (0-1),
                'energy': float (0-1)
            }
        """
        import librosa
        import os

        try:
            print(f"Iniciando análisis de metadata para: {audio_path}")
            # Cargar audio con límite de duración para optimizar procesamiento
            # Máximo 3 minutos (180 segundos) para evitar timeouts
            print("Cargando audio (máx 180s)...")
            y, sr = librosa.load(audio_path, sr=None, duration=180)
            print(f"Audio cargado: {len(y)} samples, {sr} Hz")

            # 1. DURACIÓN Y CALIDAD (análisis existente)
            duration = librosa.get_duration(y=y, sr=sr)
            print(f"Duración del audio: {duration:.2f}s")

            file_size = os.path.getsize(audio_path)
            bitrate_kbps = (file_size * 8) / (duration * 1000) if duration > 0 else 0

            if bitrate_kbps >= 320:
                quality = "Lossless"
            elif bitrate_kbps >= 192:
                quality = "High"
            elif bitrate_kbps >= 128:
                quality = "Medium"
            else:
                quality = "Low"

            # 2. BPM (Beats Per Minute)
            try:
                print("Calculando BPM...")
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                bpm = float(tempo)
                print(f"BPM calculado: {bpm}")
            except Exception as e:
                print(f"Error calculando BPM: {e}")
                bpm = None

            # 3. TONALIDAD (Key)
            try:
                print("Detectando tonalidad...")
                # Usar chromagram para detectar la tonalidad
                chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
                # Promediar sobre el tiempo
                chroma_mean = np.mean(chromagram, axis=1)
                # Encontrar el tono más prominente
                key_index = int(np.argmax(chroma_mean))
                keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                key = keys[key_index]
                print(f"Tonalidad detectada: {key}")
            except Exception as e:
                print(f"Error calculando tonalidad: {e}")
                key = None

            # 4. DANCEABILITY (bailabilidad)
            try:
                # Basado en:
                # - Regularidad del beat
                # - Energía en frecuencias bajas (bass)
                # - Estabilidad temporal del tempo

                # 4a. Regularidad del beat
                if len(beats) > 1:
                    beat_intervals = np.diff(librosa.frames_to_time(beats, sr=sr))
                    beat_regularity = 1.0 - min(np.std(beat_intervals) / (np.mean(beat_intervals) + 1e-6), 1.0)
                else:
                    beat_regularity = 0.0

                # 4b. Energía en bajos (importante para bailabilidad)
                spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
                # Normalizar (centroid bajo = más graves = más bailable)
                bass_emphasis = max(0, 1.0 - (spectral_centroid / (sr / 2)))

                # 4c. Combinar factores
                danceability = float(0.6 * beat_regularity + 0.4 * bass_emphasis)
                danceability = np.clip(danceability, 0.0, 1.0)

            except Exception as e:
                print(f"Error calculando danceability: {e}")
                danceability = None

            # 5. ENERGY (energía)
            try:
                # Basado en:
                # - RMS (Root Mean Square) de la señal
                # - Varianza espectral
                # - Dinámica (rango entre loud/quiet)

                # 5a. RMS energy
                rms = librosa.feature.rms(y=y)[0]
                rms_mean = float(np.mean(rms))

                # 5b. Varianza espectral (más varianza = más energía)
                spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
                spectral_variance = float(np.std(spectral_rolloff))

                # Normalizar valores
                # RMS típicamente está entre 0.01 y 0.3
                rms_normalized = np.clip(rms_mean / 0.3, 0.0, 1.0)
                # Spectral variance típicamente entre 0 y 5000
                spectral_normalized = np.clip(spectral_variance / 5000, 0.0, 1.0)

                # Combinar (RMS es más importante)
                energy = float(0.7 * rms_normalized + 0.3 * spectral_normalized)
                energy = np.clip(energy, 0.0, 1.0)

            except Exception as e:
                print(f"Error calculando energy: {e}")
                energy = None

            return {
                'duration': float(duration),
                'quality': quality,
                'bpm': bpm,
                'key': key,
                'danceability': danceability,
                'energy': energy
            }

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {
                'duration': None,
                'quality': None,
                'bpm': None,
                'key': None,
                'danceability': None,
                'energy': None
            }

    def _predict_heuristic_with_audio(self, audio, audio_path):
        """
        Predicción mejorada usando audio ya cargado (optimización)

        Args:
            audio: Audio ya cargado
            audio_path: Ruta al archivo (para logging)

        Returns:
            dict con resultados detallados
        """
        fakeprint = self.analyzer.compute_fakeprint(audio)
        extra_features = self.analyzer.extract_additional_features(audio)
        return self._compute_heuristic_prediction(fakeprint, extra_features)

    def _predict_heuristic(self, audio_path):
        """
        Predicción mejorada basada en análisis espectral avanzado
        Implementa hallazgos del paper ISMIR 2025: "A Fourier Explanation of AI-music Artifacts"

        Los modelos generativos producen artefactos espectrales predecibles debido a:
        1. Periodicidad en el espectro por deconvoluciones
        2. Picos regulares en frecuencias específicas (5-16 kHz)
        3. Patrones uniformes vs. irregularidad natural de música humana

        Args:
            audio_path: Ruta al archivo

        Returns:
            dict con resultados detallados
        """
        # Extraer características
        audio = self.analyzer.load_audio(audio_path)
        fakeprint = self.analyzer.compute_fakeprint(audio)
        extra_features = self.analyzer.extract_additional_features(audio)
        return self._compute_heuristic_prediction(fakeprint, extra_features)

    def _compute_heuristic_prediction(self, fakeprint, extra_features):
        """
        Calcula la predicción heurística basada en características extraídas

        Args:
            fakeprint: Vector de características espectrales
            extra_features: Diccionario con características adicionales

        Returns:
            dict con resultados de la predicción
        """
        # =====================================================
        # ANÁLISIS 1: DETECCIÓN DE PICOS ESPECTRALES
        # =====================================================
        # Basado en paper: modelos IA generan 100+ picos regulares

        # Múltiples umbrales para análisis más robusto
        peaks_high = np.where(fakeprint > 0.5)[0]      # Picos fuertes
        peaks_medium = np.where(fakeprint > 0.3)[0]    # Picos moderados
        peaks_low = np.where(fakeprint > 0.1)[0]       # Picos débiles

        peak_count_high = len(peaks_high)
        peak_count_medium = len(peaks_medium)
        peak_count_low = len(peaks_low)

        # Densidad de picos (normalizado por longitud del fakeprint)
        peak_density_high = peak_count_high / len(fakeprint) if len(fakeprint) > 0 else 0
        peak_density_medium = peak_count_medium / len(fakeprint) if len(fakeprint) > 0 else 0
        peak_density_low = peak_count_low / len(fakeprint) if len(fakeprint) > 0 else 0

        # =====================================================
        # ANÁLISIS 2: REGULARIDAD DE PICOS (CLAVE DEL PAPER)
        # =====================================================
        # Música IA: picos espaciados regularmente (artefactos de deconvolución)
        # Música humana: picos irregulares (armónicos naturales)

        peak_regularity_score = 0.0
        peak_spacing_variance = 0.0
        peak_spacing_cv = 0.0  # Coeficiente de variación

        if len(peaks_medium) > 3:
            # Calcular distancias entre picos consecutivos
            peak_spacings = np.diff(peaks_medium)

            # Varianza baja = espaciamiento regular = IA
            # Varianza alta = espaciamiento irregular = humano
            peak_spacing_variance = float(np.std(peak_spacings))

            # Coeficiente de variación (normalizado)
            mean_spacing = np.mean(peak_spacings)
            if mean_spacing > 0:
                cv = peak_spacing_variance / mean_spacing
                peak_spacing_cv = float(cv)  # Guardar para logging
                # CV bajo indica regularidad (IA), CV alto indica irregularidad (humano)
                # Usamos una función sigmoide invertida centrada en cv=0.5
                # cv < 0.3: muy regular → score alto (0.8-1.0) → IA
                # cv 0.3-0.7: neutral → score medio (0.3-0.7)
                # cv > 0.7: muy irregular → score bajo/negativo (0-0.3) → humano
                if cv < 0.3:
                    # Muy regular = muy probable IA
                    peak_regularity_score = 0.8 + (0.3 - cv) * 0.67  # 0.8 a 1.0
                elif cv < 0.5:
                    # Algo regular = probable IA
                    peak_regularity_score = 0.5 + (0.5 - cv) * 1.5  # 0.5 a 0.8
                elif cv < 0.7:
                    # Neutral = incierto
                    peak_regularity_score = 0.3 + (0.7 - cv) * 1.0  # 0.3 a 0.5
                else:
                    # Muy irregular = probable humano (score bajo)
                    peak_regularity_score = max(0.0, 0.3 - (cv - 0.7) * 0.5)  # 0.3 a 0.0
            else:
                peak_regularity_score = 0.5

        # =====================================================
        # ANÁLISIS 3: INTENSIDAD Y FORMA DEL FAKEPRINT
        # =====================================================

        fakeprint_mean = float(np.nan_to_num(np.mean(fakeprint), nan=0.0))
        fakeprint_max = float(np.nan_to_num(np.max(fakeprint), nan=0.0))
        fakeprint_std = float(np.nan_to_num(np.std(fakeprint), nan=0.0))

        # Percentiles para análisis de distribución
        fakeprint_p75 = float(np.percentile(fakeprint, 75))
        fakeprint_p90 = float(np.percentile(fakeprint, 90))

        # Kurtosis: mide "peakedness" de la distribución
        # IA tiende a tener kurtosis alta (muchos picos agudos)
        fakeprint_kurtosis = float(np.nan_to_num(
            np.mean((fakeprint - fakeprint_mean)**4) / (fakeprint_std**4 + 1e-10),
            nan=0.0
        ))

        # =====================================================
        # ANÁLISIS 4: ENERGÍA EN BANDAS ESPECÍFICAS
        # =====================================================

        high_freq_energy = float(extra_features.get('high_freq_energy', 0.0))

        # Ratio de energía: alta frecuencia vs total
        total_energy = float(np.sum(fakeprint**2))
        high_freq_ratio = high_freq_energy / (total_energy + 1e-10)

        # =====================================================
        # ANÁLISIS 5: PERIODICIDAD ESPECTRAL (PAPER ISMIR)
        # =====================================================
        # Detectar patrones repetitivos en el fakeprint usando autocorrelación

        periodicity_score = 0.0
        if len(fakeprint) > 10:
            # Autocorrelación normalizada
            autocorr = np.correlate(fakeprint - fakeprint_mean,
                                   fakeprint - fakeprint_mean,
                                   mode='full')
            autocorr = autocorr[len(autocorr)//2:]  # Solo parte positiva
            autocorr = autocorr / (autocorr[0] + 1e-10)  # Normalizar

            # Buscar picos secundarios (indican periodicidad)
            if len(autocorr) > 5:
                secondary_peaks = autocorr[2:min(50, len(autocorr))]
                periodicity_score = float(np.max(secondary_peaks)) if len(secondary_peaks) > 0 else 0.0

        # =====================================================
        # SCORING MEJORADO BASADO EN PAPER ISMIR 2025
        # =====================================================
        # CLAVE: El paper enfatiza que los picos deben ser REGULARES Y PREDECIBLES
        # Muchos picos irregulares = música humana compleja
        # Pocos picos regulares = artefactos de IA

        score = 0.0

        # 1. CONTEO DE PICOS CON REGULARIDAD (0-35 puntos) - INDICADOR PRINCIPAL
        # Combinar cantidad con regularidad para evitar falsos positivos
        peak_regularity_multiplier = 1.0 + peak_regularity_score  # 1.0 a 2.0

        # Rango óptimo para IA: 50-150 picos moderados
        if 50 <= peak_count_medium <= 150:
            # En el rango IA, multiplicar por regularidad
            base_points = 20
            score += base_points * peak_regularity_multiplier
        elif peak_count_medium < 50:
            # Muy pocos picos = probable humano o baja calidad
            score += peak_count_medium * 0.3 * peak_regularity_multiplier
        else:
            # Demasiados picos (>150) = probable música humana compleja
            # Penalizar proporcionalmente
            excess = peak_count_medium - 150
            penalty = min(20, excess * 0.1)  # Máximo -20 puntos
            score += (20 - penalty) * peak_regularity_multiplier

        # 2. PICOS FUERTES CON MODERACIÓN (0-15 puntos)
        # Picos muy fuertes son indicador, pero demasiados = humano
        if 5 <= peak_count_high <= 30:
            score += 15
        elif peak_count_high < 5:
            score += peak_count_high * 3.0
        else:
            # Demasiados picos fuertes (>30) = probable humano
            excess = peak_count_high - 30
            penalty = min(10, excess * 0.2)
            score += (15 - penalty)

        # 3. INTENSIDAD DEL FAKEPRINT (0-15 puntos)
        # Media moderada es más sospechosa que muy alta
        if 0.06 <= fakeprint_mean <= 0.10:
            # Rango típico de IA (estrecho y específico)
            score += 15
        elif fakeprint_mean < 0.06:
            score += fakeprint_mean * 250
        elif 0.10 < fakeprint_mean <= 0.12:
            # Moderadamente alto
            score += 10
        else:
            # Mean muy alta (>0.12) = probable música humana con muchos armónicos
            score += max(0, 8 - (fakeprint_mean - 0.12) * 80)

        # 4. MÁXIMO DEL FAKEPRINT (0-8 puntos)
        # Reducir peso - max=1.0 es común en ambos casos
        if fakeprint_max > 0.8:
            score += 8
        elif fakeprint_max > 0.6:
            score += 6
        else:
            score += fakeprint_max * 10

        # 5. PERCENTIL 90 (0-10 puntos)
        # Moderado es más sospechoso que muy alto
        if 0.12 <= fakeprint_p90 <= 0.22:
            # Rango específico de IA
            score += 10
        elif fakeprint_p90 < 0.12:
            score += fakeprint_p90 * 80
        elif 0.22 < fakeprint_p90 <= 0.28:
            # Moderadamente alto
            score += 5
        else:
            # P90 muy alto (>0.28) = música compleja con muchos armónicos
            score += max(0, 3 - (fakeprint_p90 - 0.28) * 15)

        # 6. PERIODICIDAD ESPECTRAL (0-12 puntos)
        # Patrones periódicos fuertes son indicador de IA
        # Periodicidad moderada es común en música con estructura repetitiva
        if periodicity_score > 0.5:
            score += 12
        elif periodicity_score > 0.40:
            score += 8
        elif periodicity_score > 0.30:
            score += 4
        elif periodicity_score > 0.20:
            score += 2
        else:
            score += periodicity_score * 8

        # 7. REGULARIDAD DE PICOS (0-20 puntos) - PESO AUMENTADO
        # El CV bajo es el indicador más importante según el paper
        regularity_points = peak_regularity_score * 20
        score += regularity_points

        # =====================================================
        # AJUSTES AVANZADOS Y PENALIZACIONES
        # =====================================================

        # REGLA 1: Bonus por kurtosis alta (0-20 puntos)
        # Kurtosis alta indica distribución "picuda" con picos extremos = artefactos de IA
        # Música normal tiene kurtosis ~3, IA puede tener >10
        kurtosis_bonus = 0
        if fakeprint_kurtosis > 15.0:
            kurtosis_bonus = 20  # Extremadamente alto
        elif fakeprint_kurtosis > 10.0:
            # Entre 10-15: bonus proporcional
            kurtosis_bonus = 15 + (fakeprint_kurtosis - 10) * 1.0  # 15-20 pts
        elif fakeprint_kurtosis > 6.0:
            # Entre 6-10: bonus moderado-alto
            kurtosis_bonus = 8 + (fakeprint_kurtosis - 6) * 1.75  # 8-15 pts
        elif fakeprint_kurtosis > 4.0:
            # Entre 4-6: bonus bajo
            kurtosis_bonus = (fakeprint_kurtosis - 4) * 4  # 0-8 pts
        # Kurtosis < 4 no suma puntos (normal)

        score += kurtosis_bonus

        # REGLA 2: Ajuste por energía de alta frecuencia anómala (0-10 puntos)
        # HF = 0 puede ser compresión MP3 pesada O procesamiento de IA
        # Reducir el peso de este indicador
        hf_adjustment = 0
        if high_freq_energy == 0.0 or high_freq_energy < 0.0000001:
            # HF absolutamente nula = sospechoso pero no definitivo
            # Solo sumar si hay otros indicadores
            if kurtosis_bonus > 10 or peak_regularity_score > 0.5:
                hf_adjustment = 10  # Bonus moderado si hay otras señales
            else:
                hf_adjustment = 3  # Bonus mínimo, puede ser solo compresión
        elif high_freq_energy < 0.00001:
            # HF muy baja = ambiguo
            hf_adjustment = 2
        elif high_freq_energy < 0.00005:
            # HF baja = típico de música humana bien masterizada
            hf_adjustment = -3  # Leve penalización (menos IA)
        # HF normal o alta no ajusta

        score += hf_adjustment

        # REGLA 3: Análisis combinado - Indicador muy fuerte de IA
        # Si kurtosis alta + HF baja + regularidad media-alta = probable IA
        combined_ia_indicator = False
        combined_bonus = 0

        if (5.0 < fakeprint_kurtosis < 10.0 and
            high_freq_energy < 0.00005 and
            peak_regularity_score > 0.3):
            # Patrón contradictorio: kurtosis alta (típico IA) + HF baja (típico humano) + regularidad
            # Esto sugiere IA que intenta imitar masterización humana
            combined_ia_indicator = True
            combined_bonus = 15
            score += combined_bonus

        # REGLA 4: Bonus por picos abundantes y regulares
        if peak_count_medium > 50 and peak_regularity_score > 0.6:
            score += 5

        # Asegurar que el score esté en rango válido [0, 100]
        score = max(0.0, min(score, 100.0))

        # =====================================================
        # LOGGING DETALLADO
        # =====================================================

        print(f"\n{'='*60}")
        print(f"  ANÁLISIS HEURÍSTICO MEJORADO (ISMIR 2025)")
        print(f"{'='*60}")
        print(f"\n[1] PICOS ESPECTRALES:")
        print(f"    • Picos fuertes (>0.5):   {peak_count_high:4d}  | Densidad: {peak_density_high:.3f}")
        print(f"    • Picos moderados (>0.3): {peak_count_medium:4d}  | Densidad: {peak_density_medium:.3f}")
        print(f"    • Picos débiles (>0.1):   {peak_count_low:4d}")

        print(f"\n[2] REGULARIDAD (Clave):")
        print(f"    • Coef. variación (CV):   {peak_spacing_cv:.3f}  (bajo=regular/IA, alto=irregular/humano)")
        print(f"    • Score de regularidad:   {peak_regularity_score:.3f}  (0=irregular, 1=regular)")
        print(f"    • Varianza espaciamiento: {peak_spacing_variance:.3f}")
        print(f"    • Puntos por regularidad: {regularity_points:.1f}/25")

        print(f"\n[3] ESTADÍSTICAS FAKEPRINT:")
        print(f"    • Media:       {fakeprint_mean:.4f}")
        print(f"    • Máximo:      {fakeprint_max:.4f}")
        print(f"    • Desv. Est.:  {fakeprint_std:.4f}")
        print(f"    • Percentil 90: {fakeprint_p90:.4f}")
        print(f"    • Kurtosis:    {fakeprint_kurtosis:.2f}")

        print(f"\n[4] PERIODICIDAD:")
        print(f"    • Score autocorr: {periodicity_score:.3f}")

        print(f"\n[5] ENERGÍA:")
        print(f"    • Alta frecuencia: {high_freq_energy:.6f}")
        print(f"    • Ratio HF/Total:  {high_freq_ratio:.4f}")

        print(f"\n[6] AJUSTES Y PENALIZACIONES:")
        if kurtosis_bonus > 0:
            print(f"    🤖 Kurtosis extrema ({fakeprint_kurtosis:.1f}): +{kurtosis_bonus:.1f} pts (indicador IA)")
        if hf_adjustment != 0:
            sign = "+" if hf_adjustment > 0 else ""
            indicator = "🤖" if hf_adjustment > 0 else "✓"
            interpretation = "sospechoso de IA" if hf_adjustment > 0 else "típico humano"
            print(f"    {indicator}  Energía HF ({high_freq_energy:.6f}): {sign}{hf_adjustment:.1f} pts ({interpretation})")
        if combined_ia_indicator:
            print(f"    🔍 Patrón IA detectado (kurtosis+HF+regularidad): +{combined_bonus:.1f} pts")

        print(f"\n{'='*60}")
        print(f"  SCORE FINAL: {score:.1f}/100")
        if score > 70:
            print(f"  CONCLUSIÓN: 🤖 Muy probable IA")
        elif score > 50:
            print(f"  CONCLUSIÓN: ⚠️  Probable IA")
        elif score > 30:
            print(f"  CONCLUSIÓN: ❓ Incierto")
        else:
            print(f"  CONCLUSIÓN: 🎵 Probable Música Humana")
        print(f"{'='*60}\n")

        # =====================================================
        # RESULTADO FINAL
        # =====================================================

        ai_probability = float(np.clip(score, 0, 100))
        is_ai = ai_probability > 50

        # Confianza basada en distancia al umbral
        confidence = float(abs(ai_probability - 50) / 50)

        return {
            'is_ai_generated': bool(is_ai),
            'confidence': confidence,
            'ai_probability': ai_probability,
            'human_probability': float(100 - ai_probability),
            'details': {
                # Conteo de picos
                'peak_count_high': int(peak_count_high),
                'peak_count_medium': int(peak_count_medium),
                'peak_count_low': int(peak_count_low),
                'peak_density_high': float(peak_density_high),
                'peak_density_medium': float(peak_density_medium),
                'peak_density_low': float(peak_density_low),

                # Regularidad (indicador clave)
                'peak_regularity_score': float(peak_regularity_score),
                'peak_spacing_variance': float(peak_spacing_variance),
                'peak_spacing_cv': float(peak_spacing_cv),

                # Estadísticas del fakeprint
                'fakeprint_mean': float(fakeprint_mean),
                'fakeprint_max': float(fakeprint_max),
                'fakeprint_std': float(fakeprint_std),
                'fakeprint_kurtosis': float(fakeprint_kurtosis),

                # Periodicidad
                'periodicity_score': float(periodicity_score),

                # Energía
                'high_freq_energy': float(high_freq_energy),
                'high_freq_ratio': float(high_freq_ratio),

                # Ajustes y penalizaciones
                'kurtosis_bonus': float(kurtosis_bonus),
                'hf_adjustment': float(hf_adjustment),
                'combined_ia_indicator': bool(combined_ia_indicator),
                'combined_bonus': float(combined_bonus),

                # Score total
                'score': float(score)
            }
        }

    def save_model(self, path):
        """
        Guarda el modelo entrenado

        Args:
            path: Ruta donde guardar el modelo
        """
        if self.model is None:
            raise ValueError("No hay modelo para guardar")

        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"Modelo guardado en {path}")

    def load_model(self, path):
        """
        Carga un modelo pre-entrenado

        Args:
            path: Ruta al modelo
        """
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        self.is_trained = True
        print(f"Modelo cargado desde {path}")


# Script de prueba
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python classifier.py <archivo_audio>")
        sys.exit(1)

    detector = AIDetector()
    result = detector.predict(sys.argv[1])

    print("\n=== Resultado del Análisis ===")
    print(f"¿Generado con IA?: {'SÍ' if result['is_ai_generated'] else 'NO'}")
    print(f"Probabilidad IA: {result['ai_probability']:.1f}%")
    print(f"Probabilidad Humana: {result['human_probability']:.1f}%")
    print(f"Confianza: {result['confidence']:.2f}")

    if 'details' in result:
        print("\n=== Detalles Técnicos ===")
        for key, value in result['details'].items():
            print(f"{key}: {value}")
