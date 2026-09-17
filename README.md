# Procesamiento de Señales de Radar: Detección de Movimiento y Micro-Vibraciones

Este proyecto demuestra la implementación de un sistema de procesamiento de señales (DSP) en Python para analizar datos crudos provenientes de un dispositivo radar FMCW (Frequency-Modulated Continuous-Wave). 

El objetivo principal es extraer información precisa sobre la distancia, el movimiento macroscópico y las micro-vibraciones de un objetivo, aislando la señal útil del ruido ambiental.

## 🚀 Características Principales

*   **Procesamiento de Señal Base (DSP):** Implementación de la cadena de procesamiento completa partiendo de datos crudos I/Q (Fase en Cuadratura).
    *   Eliminación de la componente de continua (DC Removal) para mitigar reflejos estáticos y ruido interno.
    *   Aplicación de funciones ventana (ej. Bartlett, Hanning, Blackman-Nuttall) para reducir la fuga espectral (spectral leakage).
    *   Cálculo de la Transformada Rápida de Fourier (FFT) con técnica de *Zero Padding* para aumentar la resolución espectral aparente.
*   **Detección de Objetivos:**
    *   Implementación de algoritmos de detección basados en **Umbrales Adaptativos** dinámicos, calculados a partir de la media del ruido en cada trama.
    *   Desarrollo de un algoritmo **CFAR** (Constant False Alarm Rate) 1D parametrizable (Gap, Cut, Margen) para entornos con ruido variable.
*   **Análisis de Precisión Sub-Bin:**
    *   Cálculo de la distancia exacta al objetivo utilizando **Interpolación Gaussiana de 3 puntos** sobre el espectro de magnitud, superando el límite de resolución estándar del bin de la FFT.
*   **Análisis de Micro-Vibraciones (Extracción de Fase):**
    *   Detección de vibraciones milimétricas estacionarias mediante el seguimiento de la **fase compleja** ($\phi = \arctan(Q/I)$) en el bin de interés a lo largo del tiempo, aplicando técnicas de *unwrapping*.
*   **Visualización Avanzada:**
    *   Generación de gráficas interactivas 2D (espectros de magnitud, evolución temporal, umbrales) utilizando **Plotly**.
    *   Renderizado de mapas de calor espectrales en 3D utilizando **PyVista** para analizar la evolución temporal del radar.

## 🛠️ Tecnologías Utilizadas

*   **Python 3.x**
*   **Análisis de Datos & DSP:** `NumPy`, `SciPy`, `Pandas`
*   **Visualización:** `Plotly`, `PyVista`
*   **Procesamiento de Red:** `dpkt` (para el parseo inicial de paquetes PCAP)

## 📁 Estructura del Código

El script principal (`probando_2.py`) coordina el flujo de trabajo:

1.  **Lectura y Parseo:** Lee archivos `.a4radar` (formato PCAP modificado) y extrae las matrices I/Q usando la función `extrae_datos_IQ`. El script detecta dinámicamente el ID del radar presente en la grabación.
2.  **Acondicionamiento:** Apila los datos vectorialmente, aplica DC Removal y el ventaneado.
3.  **Análisis Espectral:** Calcula la FFT con Zero Padding y la convierte a decibelios (dB).
4.  **Detección y Visualización:** 
    *   Aplica algoritmos de detección (Umbral / CFAR).
    *   Calcula la distancia interpolada del pico principal.
    *   (Opcional) Genera visualizaciones interactivas HTML con Plotly y mallas 3D con PyVista.

## 📸 Demostración Visual


*   **Figura 1:** Detección de un objetivo mediante Umbral Adaptativo (Línea azul: Señal FFT, Línea Roja: Umbral, Estrellas Verdes: Detecciones). <img width="1350" height="624" alt="cfar" src="https://github.com/user-attachments/assets/cd8e2f95-bc6c-45a5-ad96-3a31edaea784" />
*   **Figura 2:** Análisis de micro-vibración a lo largo del tiempo (Variación de Fase). <img width="1350" height="625" alt="newplot (20)" src="https://github.com/user-attachments/assets/05014bc8-1316-42b3-9b85-c8c5153ccdd2" />
*   **Figura 3:** Mapa espectral 3D de la evolución de las tramas del radar. <img width="1356" height="715" alt="zp" src="https://github.com/user-attachments/assets/e3e5a739-3d7e-4fc0-ba95-7f9c61d81718" />


## 🔒 Nota sobre los Datos

Debido a acuerdos de confidencialidad, los archivos de datos crudos (`.a4radar`) originales de la empresa no están incluidos en este repositorio.
