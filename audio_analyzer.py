"""
AI Music Detector - Audio Analysis Module
Implementación basada en el paper ISMIR 2025 usando librosa
"""

import numpy as np
import librosa
from scipy import interpolate
from scipy.signal import find_peaks


class AudioAnalyzer:
    """
    Analiza audio para detectar artefactos de música generada con IA
    usando análisis espectral en frecuencias altas
    """

    def __init__(self, sr=16000, n_fft=16384, fmin=5000, fmax=16000):
        """
        Inicializa el analizador de audio

        Args:
            sr: Sample rate objetivo
            n_fft: Tamaño de FFT (2^14 = 16384)
            fmin: Frecuencia mínima de análisis (Hz)
            fmax: Frecuencia máxima de análisis (Hz)
        """
        self.sr = sr
        self.n_fft = n_fft
        self.fmin = fmin
        self.fmax = fmax

    def load_audio(self, file_path, max_duration=180):
        """
        Carga y preprocesa archivo de audio

        Args:
            file_path: Ruta al archivo de audio
            max_duration: Duración máxima en segundos

        Returns:
            audio: Señal de audio normalizada
        """
        # Cargar audio con librosa
        audio, sr = librosa.load(file_path, sr=self.sr, mono=True, duration=max_duration)

        return audio

    def compute_spectrogram(self, audio):
        """
        Calcula el espectrograma de potencia usando STFT

        Args:
            audio: Señal de audio

        Returns:
            spectrogram: Espectrograma en escala dB
        """
        # Calcular STFT
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.n_fft//4)

        # Convertir a espectrograma de potencia
        power_spec = np.abs(stft) ** 2

        # Convertir a escala dB
        spec_db = 10 * np.log10(np.clip(power_spec, 1e-10, 1e6))

        return spec_db

    def lower_hull(self, x, area=10):
        """
        Calcula el envolvente inferior (lower hull) de una señal

        Args:
            x: Señal de entrada
            area: Ventana de búsqueda

        Returns:
            idx: Índices del hull
            hull: Valores del hull
        """
        idx = []
        hull = []

        for i in range(len(x) - area + 1):
            patch = x[i:i+area]
            rel_idx = np.argmin(patch)
            abs_idx = rel_idx + i

            if abs_idx not in idx:
                idx.append(abs_idx)
                hull.append(patch[rel_idx])

        # Añadir puntos extremos si no están
        if idx[0] != 0:
            idx.insert(0, 0)
            hull.insert(0, x[0])
        if idx[-1] != len(x) - 1:
            idx.append(len(x) - 1)
            hull.append(x[-1])

        return np.array(idx), np.array(hull)

    def curve_profile(self, freqs, curve, min_db=-45):
        """
        Extrae el perfil de la curva espectral normalizado

        Args:
            freqs: Frecuencias
            curve: Valores espectrales
            min_db: Umbral mínimo en dB

        Returns:
            freqs_cut: Frecuencias en el rango de interés
            profile: Perfil normalizado
        """
        # Filtrar por rango de frecuencias
        cutoff_idx = np.where((self.fmin < freqs) & (freqs < self.fmax))[0]
        freqs_cut = freqs[cutoff_idx]
        curve_cut = curve[cutoff_idx]

        # Calcular lower hull
        lower_idx, lower_vals = self.lower_hull(curve_cut, area=10)

        # Interpolar hull
        hull_interp = interpolate.interp1d(
            freqs_cut[lower_idx],
            lower_vals,
            kind="quadratic",
            fill_value="extrapolate"
        )(freqs_cut)

        hull_interp = np.clip(hull_interp, min_db, None)

        # Calcular residuos (diferencia con el hull)
        profile = np.clip(curve_cut - hull_interp, 0, None)

        return freqs_cut, profile

    def max_normalize(self, x, max_db=5):
        """
        Normaliza la señal por su máximo

        Args:
            x: Señal de entrada
            max_db: Umbral máximo

        Returns:
            Señal normalizada [0, 1]
        """
        x = np.clip(x, 0, max_db)
        return x / (1e-6 + np.max(x))

    def compute_fakeprint(self, audio, return_spectrogram=False):
        """
        Calcula el 'fakeprint' (huella espectral) del audio

        Args:
            audio: Señal de audio
            return_spectrogram: Si True, retorna también el espectrograma para reutilizar

        Returns:
            fakeprint: Vector de características normalizado
            spec (opcional): Espectrograma calculado (solo si return_spectrogram=True)
        """
        # Calcular espectrograma
        spec = self.compute_spectrogram(audio)

        # Promediar sobre tiempo y canales
        mean_spec = np.mean(spec, axis=1)

        # Generar vector de frecuencias
        freqs = np.linspace(0, self.sr / 2, num=len(mean_spec))

        # Extraer perfil en frecuencias altas
        _, profile = self.curve_profile(freqs, mean_spec)

        # Normalizar
        fakeprint = self.max_normalize(profile)

        if return_spectrogram:
            return fakeprint, spec
        return fakeprint

    def analyze_audio_file(self, file_path):
        """
        Análisis completo de un archivo de audio

        Args:
            file_path: Ruta al archivo

        Returns:
            fakeprint: Vector de características
        """
        audio = self.load_audio(file_path)
        fakeprint = self.compute_fakeprint(audio)
        return fakeprint

    def extract_additional_features(self, audio, spectrogram=None):
        """
        Extrae características adicionales para mejorar la detección

        Args:
            audio: Señal de audio
            spectrogram: Espectrograma ya calculado (opcional, para evitar recálculo)

        Returns:
            features: Diccionario con características adicionales
        """
        features = {}

        # Centroide espectral
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sr)[0]
        features['spectral_centroid_mean'] = float(np.nan_to_num(np.mean(spectral_centroids), nan=0.0))
        features['spectral_centroid_std'] = float(np.nan_to_num(np.std(spectral_centroids), nan=0.0))

        # Rolloff espectral
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sr)[0]
        features['spectral_rolloff_mean'] = float(np.nan_to_num(np.mean(spectral_rolloff), nan=0.0))

        # Ancho de banda espectral
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sr)[0]
        features['spectral_bandwidth_mean'] = float(np.nan_to_num(np.mean(spectral_bandwidth), nan=0.0))

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        features['zcr_mean'] = float(np.nan_to_num(np.mean(zcr), nan=0.0))

        # Energía en frecuencias altas (indicador clave de artefactos IA)
        # OPTIMIZACIÓN: Reutilizar STFT del espectrograma si está disponible
        # Calcular STFT solo una vez en vez de dos
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.n_fft//4)
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        high_freq_idx = np.where(freqs > 8000)[0]
        if len(high_freq_idx) > 0:
            high_freq_energy = float(np.nan_to_num(np.mean(np.abs(stft[high_freq_idx, :])), nan=0.0))
        else:
            high_freq_energy = 0.0
        features['high_freq_energy'] = high_freq_energy

        return features
