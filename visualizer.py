"""
AI Music Detector - Visualizador de Análisis Espectral
Genera gráficos para comparar características entre música humana e IA
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import io
import base64
from audio_analyzer import AudioAnalyzer


class SpectralVisualizer:
    """
    Genera visualizaciones del análisis espectral
    """

    def __init__(self):
        self.analyzer = AudioAnalyzer()
        # Configuración de estilo
        plt.style.use('seaborn-v0_8-darkgrid')

    def generate_analysis_plot(self, audio_path):
        """
        Genera un gráfico completo del análisis espectral

        Args:
            audio_path: Ruta al archivo de audio

        Returns:
            base64_image: Imagen codificada en base64
            analysis_data: Diccionario con datos del análisis
        """
        # Cargar audio
        audio = self.analyzer.load_audio(audio_path)

        # Calcular características
        spec = self.analyzer.compute_spectrogram(audio)
        fakeprint = self.analyzer.compute_fakeprint(audio)
        features = self.analyzer.extract_additional_features(audio)

        # Crear figura con subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Análisis Espectral de Audio', fontsize=16, fontweight='bold')

        # 1. Espectrograma completo
        ax1 = axes[0, 0]
        freqs = np.linspace(0, self.analyzer.sr / 2, num=spec.shape[0])
        times = np.linspace(0, len(audio) / self.analyzer.sr, num=spec.shape[1])

        im1 = ax1.pcolormesh(times, freqs, spec, shading='auto', cmap='viridis')
        ax1.set_ylabel('Frecuencia (Hz)')
        ax1.set_xlabel('Tiempo (s)')
        ax1.set_title('Espectrograma Completo')
        ax1.set_ylim([0, 16000])
        plt.colorbar(im1, ax=ax1, label='Magnitud (dB)')

        # 2. Fakeprint (Huella espectral en frecuencias altas)
        ax2 = axes[0, 1]
        fakeprint_freqs = np.linspace(5000, 16000, len(fakeprint))
        ax2.plot(fakeprint_freqs, fakeprint, linewidth=2, color='red')
        ax2.fill_between(fakeprint_freqs, fakeprint, alpha=0.3, color='red')
        ax2.set_xlabel('Frecuencia (Hz)')
        ax2.set_ylabel('Intensidad Normalizada')
        ax2.set_title('Fakeprint (5-16 kHz)')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([5000, 16000])

        # Añadir líneas de referencia
        mean_val = np.mean(fakeprint)
        max_val = np.max(fakeprint)
        ax2.axhline(y=mean_val, color='blue', linestyle='--',
                    label=f'Media: {mean_val:.3f}', alpha=0.7)
        ax2.axhline(y=max_val, color='green', linestyle='--',
                    label=f'Máx: {max_val:.3f}', alpha=0.7)
        ax2.legend()

        # 3. Distribución de energía espectral
        ax3 = axes[1, 0]
        mean_spec = np.mean(spec, axis=1)
        all_freqs = np.linspace(0, self.analyzer.sr / 2, len(mean_spec))

        ax3.plot(all_freqs, mean_spec, linewidth=1.5, color='purple')
        ax3.fill_between(all_freqs, mean_spec, alpha=0.3, color='purple')

        # Marcar región de interés (5-16 kHz)
        ax3.axvspan(5000, 16000, alpha=0.2, color='yellow',
                    label='Región de análisis (5-16 kHz)')

        ax3.set_xlabel('Frecuencia (Hz)')
        ax3.set_ylabel('Magnitud Promedio (dB)')
        ax3.set_title('Distribución de Energía Espectral')
        ax3.set_xlim([0, 16000])
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        # 4. Características clave (Tabla de valores)
        ax4 = axes[1, 1]
        ax4.axis('off')

        # Calcular métricas
        fakeprint_mean = np.mean(fakeprint)
        fakeprint_max = np.max(fakeprint)
        fakeprint_variance = np.var(fakeprint)
        fakeprint_peaks = len(np.where(fakeprint > 0.5)[0])
        high_freq_energy = features['high_freq_energy']

        # Crear tabla de características
        table_data = [
            ['Característica', 'Valor', 'Indicador IA'],
            ['─' * 20, '─' * 10, '─' * 15],
            ['Fakeprint Media', f'{fakeprint_mean:.4f}',
             '✓ Alta' if fakeprint_mean > 0.2 else '✗ Baja'],
            ['Fakeprint Máximo', f'{fakeprint_max:.4f}',
             '✓ Alto' if fakeprint_max > 0.6 else '✗ Bajo'],
            ['Varianza', f'{fakeprint_variance:.6f}',
             '✓ Baja' if fakeprint_variance < 0.05 else '✗ Alta'],
            ['Picos (>0.5)', f'{fakeprint_peaks}',
             '✓ Muchos' if fakeprint_peaks > 50 else '✗ Pocos'],
            ['Energía HF', f'{high_freq_energy:.6f}',
             '✓ Alta' if high_freq_energy > 0.0001 else '✗ Baja'],
            ['─' * 20, '─' * 10, '─' * 15],
            ['Centroide Espectral', f"{features['spectral_centroid_mean']:.1f} Hz", '-'],
            ['Rolloff Espectral', f"{features['spectral_rolloff_mean']:.1f} Hz", '-'],
        ]

        # Renderizar tabla
        table = ax4.table(cellText=table_data, cellLoc='left', loc='center',
                         colWidths=[0.5, 0.25, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # Colorear encabezado
        for i in range(3):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax4.set_title('Características del Análisis', fontweight='bold', pad=20)

        # Ajustar layout
        plt.tight_layout()

        # Convertir a base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        # Preparar datos del análisis
        analysis_data = {
            'fakeprint_mean': float(fakeprint_mean),
            'fakeprint_max': float(fakeprint_max),
            'fakeprint_variance': float(fakeprint_variance),
            'fakeprint_peaks': int(fakeprint_peaks),
            'high_freq_energy': float(high_freq_energy),
            'spectral_centroid_mean': float(features['spectral_centroid_mean']),
            'spectral_rolloff_mean': float(features['spectral_rolloff_mean']),
        }

        return image_base64, analysis_data

    def generate_comparison_plot(self, audio_paths, labels):
        """
        Genera un gráfico comparativo entre múltiples audios

        Args:
            audio_paths: Lista de rutas a archivos
            labels: Lista de etiquetas (ej: ['Humano', 'IA'])

        Returns:
            base64_image: Imagen codificada en base64
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('Comparación de Fakeprints', fontsize=16, fontweight='bold')

        colors = ['blue', 'red', 'green', 'orange', 'purple']

        # Plot 1: Fakeprints superpuestos
        ax1 = axes[0]
        for i, (path, label) in enumerate(zip(audio_paths, labels)):
            audio = self.analyzer.load_audio(path)
            fakeprint = self.analyzer.compute_fakeprint(audio)
            freqs = np.linspace(5000, 16000, len(fakeprint))

            ax1.plot(freqs, fakeprint, linewidth=2,
                    color=colors[i % len(colors)], label=label, alpha=0.7)

        ax1.set_xlabel('Frecuencia (Hz)')
        ax1.set_ylabel('Intensidad Normalizada')
        ax1.set_title('Superposición de Fakeprints')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Comparación de métricas
        ax2 = axes[1]
        metrics = []

        for path in audio_paths:
            audio = self.analyzer.load_audio(path)
            fakeprint = self.analyzer.compute_fakeprint(audio)
            features = self.analyzer.extract_additional_features(audio)

            metrics.append({
                'mean': np.mean(fakeprint),
                'max': np.max(fakeprint),
                'peaks': len(np.where(fakeprint > 0.5)[0]),
                'hf_energy': features['high_freq_energy'] * 100000  # Escalar para visualización
            })

        # Crear gráfico de barras agrupadas
        x = np.arange(len(labels))
        width = 0.2

        means = [m['mean'] for m in metrics]
        maxs = [m['max'] for m in metrics]
        peaks = [m['peaks'] / 100 for m in metrics]  # Normalizar
        hf_energies = [m['hf_energy'] for m in metrics]

        ax2.bar(x - 1.5*width, means, width, label='Media', alpha=0.8)
        ax2.bar(x - 0.5*width, maxs, width, label='Máximo', alpha=0.8)
        ax2.bar(x + 0.5*width, peaks, width, label='Picos/100', alpha=0.8)
        ax2.bar(x + 1.5*width, hf_energies, width, label='Energía HF×10⁵', alpha=0.8)

        ax2.set_xlabel('Tipo de Audio')
        ax2.set_ylabel('Valor')
        ax2.set_title('Comparación de Métricas')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Convertir a base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return image_base64
