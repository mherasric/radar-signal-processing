import numpy as np
from exporta_pcap import *
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default='browser'
import pyvista as pv
import time
from scipy import signal

# Opciones vwntanas (con funcion//cn scipy)
# 'rectangular'// 'boxcar'             -> Sin ventana (máxima resolución, mucho ruido)
# 'triangular'//'triang'               -> Simple, reduce algo de ruido.
# 'barlett'//'bartlett'                -> Triangular estricta (cero en los bordes).
# 'hanning'// 'hann' o 'hanning'       -> buen equilibrio.
# 'hamming'                            -> Similar a Hanning pero no baja a cero en bordes.
# 'blackman'                           -> Muy buena reducción de ruido.
# 'blackman-harris'//'blackmanharris'  -> EXCELENTE para borrar ruido (sidelobes muy bajos).
# 'blackman-nuttall'//'nuttall'        -> Aún más agresiva contra el ruido.
# 'flat-top'//'flattop                 -> Hace el pico muy gordo, pero la altura (dB) es exacta. Para medir la potencia precisa del rebote, no la posición.
# 'gauss'                              -> Forma de campana natural.
# 'barlett-hann'                       -> Híbrido entre Barlett y Hanning.
# 'bohman'
# 'parzen'

# ('kaiser', beta) -> Si beta=0 es rectangular, si beta=14 es súper suave
# ('gaussian', std) -> Campana de Gauss. Necesitamos la desviación estándar.
# ('tukey', alpha) -> Es plana arriba y suave en los bordes. Preserva mucha energía del radar.
# ('chebwin', at) → Ventana de Chebyshev. Tú le dices cuántos dB quieres bajar el ruido 

#TIPO_VENTANA = 'rectangular' 

# Zero Padding: 
FACTOR_PADDING = 1 #si le meto mas es mejor pa interpolar
# ==========================================

# def generar_ventana(tipo, N):

#     n = np.arange(N)

#     if tipo == 'rectangular':
#         return np.ones(N)

#     elif tipo == 'triangular':
#         return 1 - np.abs((n - (N-1)/2) / (N/2))

#     elif tipo == 'barlett':
#         return np.bartlett(N)

#     elif tipo == 'hanning':
#         return np.hanning(N)

#     elif tipo == 'hamming':
#         return np.hamming(N)

#     elif tipo == 'blackman':
#         return np.blackman(N)

#     elif tipo == 'blackman-harris':
#         a0 = 0.35875; a1 = 0.48829; a2 = 0.14128; a3 = 0.01168
#         term1 = a1 * np.cos(2 * np.pi * n / (N - 1))
#         term2 = a2 * np.cos(4 * np.pi * n / (N - 1))
#         term3 = a3 * np.cos(6 * np.pi * n / (N - 1))
#         return a0 - term1 + term2 - term3

#     elif tipo == 'blackman-nuttall':
#         a0 = 0.3635819; a1 = 0.4891775; a2 = 0.1365995; a3 = 0.0106411
#         term1 = a1 * np.cos(2 * np.pi * n / (N - 1))
#         term2 = a2 * np.cos(4 * np.pi * n / (N - 1))
#         term3 = a3 * np.cos(6 * np.pi * n / (N - 1))
#         return a0 - term1 + term2 - term3

#     elif tipo == 'flat-top':
#         a0 = 1; a1 = 1.93; a2 = 1.29; a3 = 0.388; a4 = 0.032
#         term1 = a1 * np.cos(2 * np.pi * n / (N - 1))
#         term2 = a2 * np.cos(4 * np.pi * n / (N - 1))
#         term3 = a3 * np.cos(6 * np.pi * n / (N - 1))
#         term4 = a4 * np.cos(8 * np.pi * n / (N - 1))
#         return a0 - term1 + term2 - term3 + term4

#     elif tipo == 'gauss':
#         sigma = 0.4
#         return np.exp(-0.5 * ((n - (N - 1) / 2) / (sigma * (N - 1) / 2))**2)

#     elif tipo == 'barlett-hann':
#         return 0.62 - 0.48 * np.abs(n / (N - 1) - 0.5) - 0.38 * np.cos(2 * np.pi * (n / (N - 1)))

#     else:
#         print(f"AVISO: Ventana '{tipo}' no reconocida. Usando Rectangular.")
#         return np.ones(N)

def calcular_distancia_precisa(espectro_dB, resolucion_por_bin):
    """
    Toma un espectro FFT (dB) y calcula la distancia exacta del pico máximo
    usando interpolación gaussiana de 3 puntos.
    """
    # 1. Encontrar el bin del pico máximo
    idx_pico = np.argmax(espectro_dB)
    val_pico = espectro_dB[idx_pico] # Beta

    # Protección: Si el pico está en los bordes, no podemos interpolar
    if idx_pico <= 0 or idx_pico >= len(espectro_dB) - 1:
        return idx_pico * resolucion_por_bin

    # 2. Obtener valores de los vecinos
    val_izq = espectro_dB[idx_pico - 1] # Alpha
    val_der = espectro_dB[idx_pico + 1] # Gamma

    # 3. Fórmula de Interpolación Gaussiana (Parabólica en log)
    numerador = np.log(val_izq) - np.log(val_der) 
    
    delta = 0.5 * (val_izq - val_der) / (val_izq - 2 * val_pico + val_der)

    # 4. Calcular posición exacta (Bin fraccionario)
    bin_exacto = idx_pico + delta

    # 5. Convertir a metros
    distancia_metros = bin_exacto * resolucion_por_bin
    
    return distancia_metros

def aplicar_cfar(signal_dB, num_gap, num_cut, margen_dB):
    """
    Aplicamos CFAR a una señal 1D en dB
    - signal_dB: Array con la magnitud de la FFT
    - num_gap: Número de celdas de guarda a cada lado
    - num_cut: Número de celdas  bajo prueba, las que hay que analizar si son objetivos o no
    - margen_dB: Margen de seguridad, umbral sobre el ruido

    Retorna:
    - threshold: umbral dinámico calculado
    - detecciones: array booleano, true cuando haya objetivo
    """
    n = len(signal_dB)
    threshold = np.full(n, 200.0) # Iniciamos con un valor alto para no detectar bordes
    detecciones = np.zeros(n, dtype=bool)
    
    # Tamaño total de la ventana a un lado
    window_side = num_gap + num_cut
    
    # Recorremos la señal (saltando los bordes donde no cabe la ventana)
    for i in range(window_side, n - window_side):
        
        # 1. Sacar el vecindario (Izquierda y Derecha), saltando las celdas gap
        gap_left = signal_dB[i - window_side : i - num_gap]
        gap_right = signal_dB[i + num_gap + 1 : i + window_side + 1]
        
        # 2. Calcular el Nivel de Ruido (Promedio del vecindario)
        noise_level = np.mean(np.concatenate((gap_left, gap_right)))
        
        # 3. Calcular el Umbral (Ruido + margen)
        thresh_val = noise_level + margen_dB
        threshold[i] = thresh_val
        
        # 4. Es el pico mayor que el umbral?
        if signal_dB[i] > thresh_val:
            detecciones[i] = True
            
    return threshold, detecciones

def extrae_datos_IQ(data):
    datos = data["data"]
    contador = None
    i_q = None
    matriz_up = None
    matriz_up_i = None
    matriz_up_q = None
    matriz_down = None
    matriz_down_i = None
    matriz_down_q = None

    if ((datos[2] == 0xAC) or (datos[2] == 0xAD)): 
        if(datos[2] == 0xAC):
            i_q = 0 
        else:
            i_q = 1

        contador = int.from_bytes(datos[5:7], "big")

        # Protección try/except por si el paquete está corrupto
        try:
            array = np.asarray(datos[11:2*2*Nfft+11])
            aaa = (array.reshape(1024//2,2).view(np.uint16).byteswap())

            if(i_q == 0):
                matriz_up = aaa[:,0]
                matriz_up_i = (aaa[::2,0]).astype(np.float64) 
                matriz_up_q = (aaa[1::2,0]).astype(np.float64) 
            else:
                matriz_down = aaa[:,0]
                matriz_down_i = (aaa[::2,0]).astype(np.float64) 
                matriz_down_q = (aaa[1::2,0]).astype(np.float64)
        except:
            pass

    return{
        "contador": contador,
        "i_q": i_q,
        "matriz_up": matriz_up,
        "matriz_up_i": matriz_up_i,
        "matriz_up_q": matriz_up_q,
        "matriz_down": matriz_down,
        "matriz_down_i": matriz_down_i,
        "matriz_down_q": matriz_down_q,
    }

print("Init A4Radar:")
print("---------------------------------------------\r")


########################################################################
## CONSTANTS
########################################################################
DISTANCE_BETWEEN_RADAR = 3.47 # m
FREQ = 0.56 * 2# ms 

########################################################################
## Select file name
########################################################################

path = "./"
nombre_fich = "2026-02-17-20-36-26.a4radar"
recorta_inicio = 0
recorta_final = 0
ficheros = [nombre_fich]

for idx, fichero in enumerate(ficheros):
    print(fichero)
    file_name = path+fichero 
    fichero_name = fichero

    # Parametros RADAR
    num_muestras = 560
    Nfft = 256 
    num_bytes_FFT = 1088 # bytes
    Nfft_padded = Nfft * FACTOR_PADDING
    range_resolution = 0.075
    final_resolution = range_resolution * (num_muestras/(2*Nfft))
    bin_padded_res = range_resolution / FACTOR_PADDING #para la interpolacion

    # Parámetros CFAR
    CFAR_gap = 2 #bins de guarda, el ancho del coche aprox
    CFAR_cut = 10 #bins para medir ruido
    CFAR_margen = 10 #dB por encima del ruido para detectar

    # Parámetro umbral adaptativo
    factor_umbral = 6 #detectamos todo lo que sea 6 veces mas grande que el promedio

    try:
        df_og = read_pcap_to_dataframe(file_name)
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        continue

    columnas = None
    #print(df)
    datos = df_og.iloc[:,1]

    inicios_radar1 = [5901, 8991, 36960, 39119, 41248] 
    finales_radar1 = [6178, 9405, 37081, 39233, 41390]
    inicios_radar2 = [6028, 9130, 37066, 39209, 41358]
    finales_radar2 = [6307, 9525, 37197, 39346, 41502]

    direcciones = [0x11, 0x12] 
    print(f"direcciones: {direcciones}")

    matriz_FFT_Radar1 = None 
    matriz_FFT_Radar2 = None 

    for dir in direcciones:
        df = df_og[df_og['data'].apply(lambda x: x[1] == dir)]

        if not df.empty and (df.iloc[0,1][2] == 0xAD): df = df.iloc[1:,:]
        if not df.empty and (df.iloc[-1,1][2] == 0xAC): df = df.iloc[:-1,:]

        columnas = ["contador", "i_q", "matriz_up", "matriz_up_i", "matriz_up_q", "matriz_down", "matriz_down_i", "matriz_down_q"]
        df = pd.DataFrame(df.apply(extrae_datos_IQ, axis=1).to_list())
        df = df.dropna(how="all").reset_index(drop=True)

        df_comb = df.groupby(df.index // 2).agg({
            "contador": 'first',
            'matriz_up': 'first', 
            'matriz_up_i': 'first', 
            'matriz_up_q': 'first',
            'matriz_down': 'last', 
            'matriz_down_i': 'last', 
            'matriz_down_q': 'last'
        }).reset_index(drop=True).dropna(how="any")

        matriz_up_i = np.vstack(df_comb["matriz_up_i"].to_numpy())
        matriz_up_q = np.vstack(df_comb["matriz_up_q"].to_numpy())
        matriz_down_i = np.vstack(df_comb["matriz_down_i"].to_numpy())
        matriz_down_q = np.vstack(df_comb["matriz_down_q"].to_numpy())

        matriz_FFT = []
        matriz_FFT_up = []
        matriz_FFT_down = []
        phase = []

        window = signal.get_window('bartlett', Nfft)

        print(f"Procesando Radar {hex(dir)} | Ventana: Bartlett | Padding: x{FACTOR_PADDING}")

        #for i in range(len(matriz_up_i)):
        #signal_up = matriz_up_i[i] + 1j * matriz_up_q[i]
        #signal_down = matriz_down_i[i] + 1j * matriz_down_q[i]

        signal_up = matriz_up_i + 1j * matriz_up_q
        signal_down = matriz_down_i + 1j * matriz_down_q

        # 1. QUITAR LA MEDIA 
        #quitamos el pico que sale en dist 0, restamos la media, centramos la señal en 0 y el pico desaparece
        signal_up = signal_up - np.mean(signal_up)
        signal_down = signal_down - np.mean(signal_down)

        signal_up_g = signal_up - np.mean(signal_up) #g de guarra era para comparar con la versión fea

        # 2. APLICAR VENTANA
        #multiplicamos la señal por una curva suave
        signal_up = signal_up * window
        signal_down = signal_down * window

        # 3. ZERO PADDING + FFT
        #añadimos ceros al final de la señal antes de la fft
        fft_result_up = np.fft.fft(signal_up, n=Nfft_padded)
        fft_result_down = np.fft.fft(signal_down, n=Nfft_padded)

        fft_g= np.fft.fft(signal_up_g, n=Nfft_padded)

        # 4. Magnitud en dB
        mag_up = 20 * np.log10(np.maximum(np.abs(fft_result_up), 1e-9))
        mag_down = 20 * np.log10(np.maximum(np.abs(fft_result_down), 1e-9))

        mag_up_g = 20 * np.log10(np.maximum(np.abs(fft_g), 1e-9 ))

        # Recortamos a la mitad útil, con el padding el espectro se duplica, la simetria se mantiene
        mag_up = mag_up[:len(mag_up)//2]
        mag_down = mag_down[:len(mag_down)//2]

        mag_up_g = mag_up_g[:len(mag_up)//2]

        # --- INTERPOLACIÓN ---
        # Cogemos una trama donde haya coche (ej. 6000)
        trama_demo = 6000
        if trama_demo < len(mag_up):
            dist_interpolada = calcular_distancia_precisa(mag_up[trama_demo], bin_padded_res)
            # Calculamos la distancia (pico máximo del bin)
            bin_max = np.argmax(mag_up[trama_demo])
            dist_bin = bin_max * bin_padded_res
            
            print(f"\n[Radar {hex(dir)} - Trama {trama_demo}] Precisión Mejorada:")
            print(f"  - Distancia Bin Simple:   {dist_bin:.4f} m")
            print(f"  - Distancia Interpolada:  {dist_interpolada:.4f} m")
            print(f"  - Mejora de precisión:    {abs(dist_interpolada - dist_bin)*1000:.2f} mm\n")


        matriz_FFT=mag_up
        matriz_FFT_up=mag_up
        matriz_FFT_down=mag_down
        phase=phase

        matriz_FFT_g=mag_up_g

        matriz_FFT = np.array(matriz_FFT)

        matriz_FFT_g = np.array(matriz_FFT_g)

        if(dir == 0x11):
            matriz_FFT_Radar1 = matriz_FFT.copy()
            ini = inicios_radar1[3]
        else:
            matriz_FFT_Radar2 = matriz_FFT.copy()
            ini = inicios_radar2[3]

        # DIBUJADO 2D
        ini_draw = 6100 

        #-----PARA VER LA I Y LA Q---------
        fig = go.Figure()
        for i in range(ini_draw, ini_draw+1):
            fig.add_trace(
                go.Scattergl(
                    y = matriz_up_i[i],
                    name = f"I subida {i}"
                )
            )
            fig.add_trace(
                go.Scattergl(
                    y = matriz_up_q[i],
                    name = f"Q subida {i}"
                )
            )
        fig.update_layout(
            title = f"Video subida {hex(dir)}"
        )
        fig.show()

        import time 
        time.sleep(1.5)

        fig = go.Figure()
        for i in range(ini_draw, ini_draw+1):
            fig.add_trace(
                go.Scattergl(
                    #y = matriz_down_i[i],
                    y = np.real(signal_up[i]),
                    name = f"I bajada {i}"
                )
            )
            fig.add_trace(
                go.Scattergl(
                    #y = matriz_down_q[i],
                    y = np.imag(signal_up[i]),
                    name = f"Q bajada {i}"
                )
            )
        fig.update_layout(
            title = f"Video bajada {hex(dir)}"
        )
        fig.show()


        #-----FFT NORMAL----------------
        ini = ini_draw    
        fig = go.Figure()
        for i in range(ini, ini+20):
            fig.add_trace(
                go.Scattergl(
                    y = matriz_FFT[i],
                    name = f"FFT {i}"
                )
            )
        fig.update_layout(
            title = f"FFT Radar {hex(dir)}"
        )
        fig.show()

        ##---------FFT CON CFAR---------
        # i = ini_draw
        # fig = go.Figure()
    
        # if i < len(matriz_FFT):
        #     senal_actual = matriz_FFT[i]

        #     # 1. CALCULAMOS CFAR PARA ESTA TRAMA
        #     umbral_cfar, detectados = aplicar_cfar(senal_actual, CFAR_gap, CFAR_cut, CFAR_margen)

        #     # 2. Señal Original (Azul)
        #     fig.add_trace(go.Scattergl(
        #         y = senal_actual, 
        #         name = f"Señal Radar (Trama {i})",
        #         line = dict(color='royalblue')
        #     ))

        #     # 3. Umbral CFAR (Rojo)
        #     fig.add_trace(go.Scattergl(
        #         y = umbral_cfar, 
        #         name = "Umbral CFAR",
        #         line = dict(color='red', dash='dash') 
        #     ))

        #     # 4. Puntos Detectados (Estrellas Verdes)
        #     # Solo dibujamos puntosdetectados == True
        #     indices_detectados = np.where(detectados)[0]
        #     valores_detectados = senal_actual[indices_detectados]

        #     fig.add_trace(go.Scatter(
        #         x = indices_detectados,
        #         y = valores_detectados,
        #         mode = 'markers',
        #         name = '¡Objetivo Detectado!',
        #         marker = dict(color='green', size=10, symbol='star')
        #     ))

        #     fig.update_layout(
        #         title = f"Detector CFAR - Radar {hex(dir)}",
        #         xaxis_title = "Bin de Distancia",
        #         yaxis_title = "Amplitud (dB)"
        #     )
        #     fig.show()



        # -----UMBRAL ADAPTATIVO PARA UNA SOLA TRAMA-----
        # trama_objetivo = 6100

        # # 1. Extraemos SOLO la trama que queremos analizar de la matriz gigante
        # if trama_objetivo < len(fft_result_up):
        #     fft_trama = fft_result_up[trama_objetivo]

        #     fft_abs_lineal = np.abs(fft_trama) #magnitud lineal, valor abs real
        #     media_ruido_lineal = np.mean(fft_abs_lineal)
        #     umbral_lineal = media_ruido_lineal * factor_umbral

        #     mag_up_db = 20 * np.log10(np.maximum(fft_abs_lineal, 1e-9)) #convertimos todo a dB para poder dibujarlo
        #     umbral_db_val = 20 * np.log10(np.maximum(umbral_lineal, 1e-9))

        #     mitad = len(mag_up_db)//2 #la mitad util
        #     mag_up_db = mag_up_db[:mitad]

        #     linea_umbral_db = np.full(mitad, umbral_db_val) #linea umbral con el tamaño recortado

        #     indices_detectados = np.where(mag_up_db > umbral_db_val)[0] #ponemos [0] para extraer el array de indices que está dentro de la tupla
        #     valores_detectados = mag_up_db[indices_detectados] #detectamos qué picos superan el umbral, para poder pintarlos


        #     fig = go.Figure() #dibujamos

        #     # 1. Señal
        #     fig.add_trace(go.Scatter(
        #             y=mag_up_db, #le he quitado el [1] porque mag_up_db ya es solo 1 linea
        #             name="Señal FFT (dB) - Trama {trama_objetivo}", 
        #             line=dict(color='blue', width=2)
        #         ))
                
        #     # 2. El Umbral Adaptativo
        #     fig.add_trace(go.Scatter(
        #         y=linea_umbral_db,
        #         name=f"Umbral (x{factor_umbral})", 
        #         line=dict(color='red', dash='dash')
        #         ))
                
        #     # 3. Puntos detectados
        #     if len(indices_detectados) > 0:
        #         fig.add_trace(go.Scatter(
        #         x=indices_detectados, y=valores_detectados,
        #         mode='markers', 
        #         name='Puntos detectados', 
        #         marker=dict(color='green', size=12, symbol='star', line=dict(width=1, color='black'))
        #         ))
                
        #     fig.update_layout(
        #         title=f"Umbral Adaptativo - Radar {hex(dir)} - Trama {trama_objetivo}",
        #         xaxis_title="Bins",
        #         yaxis_title="Amplitud (dB)",
        #         template="plotly_white"
        #     )
            
        #     nombre_archivo = f"radar_umbral_trama_{trama_objetivo}.html"
        #     fig.write_html(nombre_archivo, auto_open=True)
        #     print(f"--> Gráfica guardada y abierta: {nombre_archivo}")
        # else:
        #     print(f"ERROR: La trama {trama_objetivo} no existe en el radar {hex(dir)}")


        # if ini_draw == trama_objetivo: 
        #      print(f"Generando gráfica HTML para la trama {trama_objetivo}...")
        #      fig = go.Figure()
             
        #      # 1. La Señal
        #      fig.add_trace(go.Scatter(
        #          y=mag_up_db, 
        #          name="Señal FFT (dB)", 
        #          line=dict(color='blue', width=2)
        #     ))
             
        #      # 2. El Umbral Adaptativo
        #      fig.add_trace(go.Scatter(
        #          y=linea_umbral_db,
        #          name=f"Umbral (x{factor_umbral})", 
        #          line=dict(color='red', dash='dash')
        #     ))
             
        #      # 3. Puntos detectados
        #      if len(indices_validos) > 0:
        #          fig.add_trace(go.Scatter(
        #             x=indices_validos, y=valores_validos,
        #             mode='markers', 
        #             name='¡Detectado!', 
        #             marker=dict(color='green', size=12, symbol='star', line=dict(width=1, color='black'))
        #          ))
             
        #      fig.update_layout(
        #          title=f"Umbral Adaptativo - Radar {hex(dir)} - Trama {trama_objetivo}",
        #          xaxis_title="Bins",
        #          yaxis_title="Amplitud (dB)",
        #          template="plotly_white"
        #      )
             
        #      nombre_archivo = f"radar_umbral_trama_{trama_objetivo}.html"
        #      fig.write_html(nombre_archivo, auto_open=True)
        #      print(f"--> Gráfica guardada y abierta: {nombre_archivo}")



        #------UMBRAL ADAPTATIVO TODAS LAS TRAMAS-------
        # mitad = fft_result_up.shape[1]//2 #recortamos a la mitad útil Primero para no hacer cálculos sobre el efecto espejo
        # fft_util = fft_result_up[:, :mitad]

        # fft_abs_lineal = np.abs(fft_util)

        # #calculamos la media del ruido de cada trama por separado
        # #axis=1: calcula la mdeia fila por fila
        # #keepdims=True mantiene la forma de columna para poder multiplicar
        # media_ruido_lineal = np.mean(fft_abs_lineal, axis=1, keepdims=True)
        
        # umbrales_lineales = media_ruido_lineal * factor_umbral #umbral para cada trama

        # mag_up_db = 20 * np.log10(np.maximum(fft_abs_lineal, 1e-9))
        # umbrales_db = 20 * np.log10(np.maximum(umbrales_lineales, 1e-9))

        # #comparamos cada punto de la matriz con el umbral de su propia fila
        # #devolvemos una matriz del mismo tamaño llena de True (Si hay coche) y False (ruido)
        # matriz_detecciones = mag_up_db > umbrales_db

        # matriz_FFT = mag_up_db
        # print(f"listo, {np.sum(matriz_detecciones)} detecciones totales encontradas en todo el archivo")

        # trama_objetivo = 6100
        
        # if trama_objetivo < len(mag_up_db):
        #     fig = go.Figure()
            
        #     # Señal de esa trama
        #     fig.add_trace(go.Scatter(
        #         y=mag_up_db[trama_objetivo], 
        #         name=f"Señal FFT (Trama {trama_objetivo})", 
        #         line=dict(color='blue', width=2)
        #     ))
            
        #     # Umbral de esa trama (OJO: umbrales_db es una columna, sacamos su valor)
        #     valor_umbral = umbrales_db[trama_objetivo][0] 
        #     linea_umbral = np.full(mitad, valor_umbral)
            
        #     fig.add_trace(go.Scatter(
        #         y=linea_umbral,
        #         name=f"Umbral (x{factor_umbral})", 
        #         line=dict(color='red', dash='dash')
        #     ))
            
        #     # Extraemos dónde hubo detecciones (Trues) en esta trama específica
        #     indices_detectados = np.where(matriz_detecciones[trama_objetivo])[0]
        #     valores_detectados = mag_up_db[trama_objetivo][indices_detectados]
            
        #     if len(indices_detectados) > 0:
        #         fig.add_trace(go.Scatter(
        #             x=indices_detectados, y=valores_detectados,
        #             mode='markers', name='¡Detectado!', 
        #             marker=dict(color='green', size=12, symbol='star', line=dict(width=1, color='black'))
        #         ))
            
        #     fig.update_layout(
        #         title=f"Verificación de Matriz Masiva - Radar {hex(dir)} - Trama {trama_objetivo}",
        #         xaxis_title="Bins", yaxis_title="Amplitud (dB)", template="plotly_white"
        #     )
            
        #     nombre_archivo = f"radar_verificacion_{hex(dir)}.html"
        #     fig.write_html(nombre_archivo, auto_open=True)
        




    ###----------- 3D FFTs------------------
    for idx in range(len(inicios_radar1)):
    
        plotter = pv.Plotter(lighting='none', shape=(1, 2))

        matriz_radar1 = matriz_FFT_Radar1[inicios_radar1[idx] : finales_radar1[idx]]
        matriz_radar2 = matriz_FFT_Radar2[inicios_radar2[idx] : finales_radar2[idx]]

        x_og = 0
        y_og = 0
        z_og = 0

        for i in range(2):
            plotter.subplot(0, i)

            if(i == 0):
                meshX = np.arange(-matriz_radar1.shape[0]//2, matriz_radar1.shape[0]//2, 1)
                meshY = np.arange(-matriz_radar1.shape[1]//2, matriz_radar1.shape[1]//2, 1)
                x2,y2 = np.meshgrid(meshY, meshX)

                z = np.array(matriz_radar1)
            else:
                # meshX = np.arange(-matriz_radar2.shape[0]//2, matriz_radar2.shape[0]//2, 1)
                # meshY = np.arange(-matriz_radar2.shape[1]//2, matriz_radar2.shape[1]//2, 1)
                # x2,y2 = np.meshgrid(meshY, meshX)

                #z = np.array(matriz_radar2)

                meshX = np.arange(-matriz_FFT_g.shape[0]//2, matriz_FFT_g.shape[0]//2, 1)
                meshY = np.arange(-matriz_FFT_g.shape[1]//2, matriz_FFT_g.shape[1]//2, 1)
                x2,y2 = np.meshgrid(meshY, meshX)

                z = np.array(matriz_FFT_g)



            if(i == 0):
                x_og = x2.copy()
                y_og = y2.copy()
                z_og = z.copy()

            scalars = z.ravel(order='F')  # Aplanar para escalar de color
            scalars = np.clip(scalars, 50, 120)

            x = (x2 - x2.min()) / (x2.max() - x2.min()) * 100
            y = (y2 - y2.min()) / (y2.max() - y2.min()) * 100

            text_actor = plotter.add_text("", position="right_edge", font_size=12)

            def update_mouse_position(point):
                if point is not None:
                    my_x, my_y, my_z = point
                    text_actor.SetText(0, f"Posición: x={(my_x / 100) * (x_og.max() - x_og.min()) + x_og.min() + (x_og.shape[1])//2:.2f}, y={(my_y / 100) * (y_og.max() - y_og.min()) + y_og.min() + len(y_og)//2 :.2f}, z={my_z:.2f}")
                    #text_actor.SetText(0, f"x={my_x:.2f}, y={my_y:.2f}, z={my_z:.2f}")
                else:
                    text_actor.SetText(0, "Fuera de la malla")

            if (i == 0):
                plotter.enable_surface_point_picking(callback=update_mouse_position, show_point=True, show_message=False)

                sun = pv.Light(
                    position=(44, 36, 100),
                    focal_point=(44, 36, 0),
                    intensity=0.8
                )
                sun.positional = False
                plotter.add_light(sun)

                plotter.add_axes()

            grid = pv.StructuredGrid(x, y, z)
            plotter.add_mesh(grid, scalars=scalars, cmap="jet", show_edges=False, ambient=0.6, diffuse=0.7, specular=0.0)
            plotter.add_title(f"FFT Radar {hex(0x11) if i == 0 else hex(0x12)}")

        plotter.show()
 