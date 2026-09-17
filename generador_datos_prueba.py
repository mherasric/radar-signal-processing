import numpy as np
import pandas as pd
import struct
import os
import time

def generar_archivo_sintetico(nombre_archivo="datos_sinteticos.a4radar", num_tramas=100):
    """
    Genera un archivo .a4radar simulado con ruido y un objetivo vibrante.
    """
    datos_simulados = []
    
    # Parámetros de la simulación
    radar_id = 0x20
    tipo_chirp = 0xAA # Usamos el tipo de chirp del nuevo radar
    Nfft = 256
    
    # Objetivo simulado
    bin_objetivo = 50
    amplitud_objetivo = 10000 
    frecuencia_vibracion = 2.0 # Hz
    
    for t in range(num_tramas):
        tiempo_segundos = t * 0.05
        
        # 1. Generar ruido de fondo (complejo)
        ruido_i = np.random.normal(0, 100, Nfft).astype(np.float64)
        ruido_q = np.random.normal(0, 100, Nfft).astype(np.float64)
        
        # 2. Simular el pico del objetivo con vibración en la fase
        fase_vibracion = np.sin(2 * np.pi * frecuencia_vibracion * tiempo_segundos)
        objetivo_i = amplitud_objetivo * np.cos(fase_vibracion)
        objetivo_q = amplitud_objetivo * np.sin(fase_vibracion)
        
        # Añadir el objetivo al bin correspondiente
        ruido_i[bin_objetivo] += objetivo_i
        ruido_q[bin_objetivo] += objetivo_q
        
        # 3. Intercalar I y Q y convertir a formato de bytes simulado
        # Nota: Esta es una simplificación extrema del formato pcap real para que pase por extrae_datos_IQ
        # extrae_datos_IQ espera uint16 y luego separa pares e impares.
        
        # Creamos un array combinado simulando el empaquetado
        array_iq = np.zeros(Nfft * 2, dtype=np.float64)
        array_iq[0::2] = ruido_i
        array_iq[1::2] = ruido_q
    
        
        # COMO ALTERNATIVA PARA EL GITHUB:
        # Modificaremos ligeramente probando.py para que, si no encuentra el archivo .a4radar,
        # genere y use un DataFrame simulado directamente, saltándose el parseo del PCAP.
        pass

    print(f"Archivo simulado '{nombre_archivo}' generado (Lógica pendiente de implementación completa debido a la complejidad del formato binario).")