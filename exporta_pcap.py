import dpkt
import pandas as pd
#import h5py

class NotCorrectFile(Exception):
    """Una excepción personalizada."""
    def __init__(self, mensaje=""):
        mensaje += "El fichero no es válido o está corrupto"
        self.mensaje = mensaje
        super().__init__(self.mensaje)

######################################################
##
## Recibe el nombre del fichero pcap o pcapng a leer y devuelve un dataframe con los datos
##
######################################################
"""
def read_pcap_to_dataframe(filename):
    tam_cabecera = 0
    
    with open(filename, 'rb') as f:
        cont = 0
        pcap = None
        while (pcap is None) and (cont < 1000):
            try:
                #raise ValueError
                pcap = dpkt.pcapng.Reader(f)
                tam_cabecera = 42
            except:
                f.seek(0)  
                cont += 1
                print("Excepcion 1")
                pcap = None
                try:
                    pcap = dpkt.pcap.Reader(f)
                    tam_cabecera = 32
                except:
                    f.seek(0) 
                    print("Excepcion 2")
                    pcap = None
                
        if (cont == 1000):
            raise NotCorrectFile

        cont = 0
        
        #data = [(ts, bytearray(pkt)[tam_cabecera:]) for ts, pkt in pcap if len(bytearray(pkt)) > tam_cabecera+1]  # Guardar tuplas (timestamp, paquete)
        
        data = []
        for ts, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                
                #print(type(eth.data))
                
                if(isinstance(eth.data, bytes)):
                
                    try:
                        ip = dpkt.ip.IP(buf)  # ¡Directamente IP!

                        if isinstance(ip.data, dpkt.udp.UDP):
                            udp = ip.data
                            #print(f"UDP: {udp.data.hex()}")
                            
                    except dpkt.UnpackError as e:
                        #print(f"Error: {e}, probamos eliminando los primeros 4 bytes")
                        
                        try:
                            ip = dpkt.ip.IP(buf[4:])  # ¡Directamente IP!

                            if isinstance(ip.data, dpkt.udp.UDP):
                                udp = ip.data
                        except Exception as e:
                            print(f"Ignoramos paquete: {e}")
                            continue
                        
                    payload = udp.data
                    #print(f"payload: {payload.hex()}")
                    if (payload[0] == 0x02) and ((payload[-2] == 0x06) or (payload[-2] == 0x03) or (payload[-2] == 0x00)) and ((payload[-1] == 0x03) or (payload[-1] == 0x55)):
                        #print(payload.hex())
                        data.append([ts, bytearray(payload)])
                        
                # Verificar si es un paquete IP
                #print(bytes(buf).hex())
                elif isinstance(eth.data, dpkt.ip.IP):
                    #print("es IP")
                    ip = eth.data
                    
                    # Verificar si es un paquete UDP
                    if isinstance(ip.data, dpkt.udp.UDP):
                        #print("es UDP")
                        udp = ip.data
                        payload = udp.data
                        #print(f"payload: {payload}")
                        if (payload[0] == 0x02) and ((payload[-2] == 0x06) or (payload[-2] == 0x03) or (payload[-2] == 0x00)) and ((payload[-1] == 0x03) or (payload[-1] == 0x55)):
                            #print(payload.hex())
                            data.append([ts, bytearray(payload)])
                            
            except dpkt.NeedData:
                print("Paquete incompleto, saltando...")
                continue
        
        df = pd.DataFrame.from_records(data,columns=["timestamp","data"])
        #df = df.sort_values("timestamp")
        
        return df
 """
 
def read_pcap_to_dataframe(filename):
    tam_cabecera = 0
    
    with open(filename, 'rb') as f:
        cont = 0
        pcap = None
        while (pcap is None) and (cont < 1000):
            try:
                #raise ValueError
                pcap = dpkt.pcapng.Reader(f)
                tam_cabecera = 42
            except:
                f.seek(0)  
                cont += 1
                print("Excepcion 1")
                pcap = None
                try:
                    pcap = dpkt.pcap.Reader(f)
                    tam_cabecera = 32
                except:
                    f.seek(0) 
                    print("Excepcion 2")
                    pcap = None
                
        if (cont == 1000):
            raise NotCorrectFile

        cont = 0
        
        #data = [(ts, bytearray(pkt)[tam_cabecera:]) for ts, pkt in pcap if len(bytearray(pkt)) > tam_cabecera+1]  # Guardar tuplas (timestamp, paquete)
        
        data = []
        while True:
            try:
                ts, buf = pcap.next()
            except StopIteration:
                break
            except dpkt.NeedData:
                print("Paquete incompleto, saltando")
                continue
            
            eth = dpkt.ethernet.Ethernet(buf)
            
            #print(type(eth.data))
            
            if(isinstance(eth.data, bytes)):
            
                try:
                    ip = dpkt.ip.IP(buf)  # ¡Directamente IP!

                    if isinstance(ip.data, dpkt.udp.UDP):
                        udp = ip.data
                        #print(f"UDP: {udp.data.hex()}")
                        
                except dpkt.UnpackError as e:
                    #print(f"Error: {e}, probamos eliminando los primeros 4 bytes")
                    
                    try:
                        ip = dpkt.ip.IP(buf[4:])  # ¡Directamente IP!

                        if isinstance(ip.data, dpkt.udp.UDP):
                            udp = ip.data
                    except Exception as e:
                        print(f"Ignoramos paquete: {e}")
                        continue
                    
                payload = udp.data
                #print(f"payload: {payload.hex()}")
                if (payload[0] == 0x02) and ((payload[-2] == 0x06) or (payload[-2] == 0x03) or (payload[-2] == 0x00)) and ((payload[-1] == 0x03) or (payload[-1] == 0x55)):
                    #print(payload.hex())
                    data.append([ts, bytearray(payload)])
                    
            # Verificar si es un paquete IP
            #print(bytes(buf).hex())
            elif isinstance(eth.data, dpkt.ip.IP):
                #print("es IP")
                ip = eth.data
                
                # Verificar si es un paquete UDP
                if isinstance(ip.data, dpkt.udp.UDP):
                    #print("es UDP")
                    udp = ip.data
                    payload = udp.data
                    #print(f"payload: {payload}")
                    if (payload[0] == 0x02) and ((payload[-2] == 0x06) or (payload[-2] == 0x03) or (payload[-2] == 0x00)) and ((payload[-1] == 0x03) or (payload[-1] == 0x55)):
                        #print(payload.hex())
                        data.append([ts, bytearray(payload)])
                            
        
        df = pd.DataFrame.from_records(data,columns=["timestamp","data"])
        #df = df.sort_values("timestamp")
        
        return df
 
def read_video_from_pcap(filename):
    data = []
    with open(filename, "rb") as f:
        cont = 0
        pcap = None
        while (pcap is None) and (cont < 1000):
            try:
                #raise ValueError
                pcap = dpkt.pcapng.Reader(f)
            except:
                f.seek(0)  
                cont += 1
                print("Excepcion 1")
                pcap = None
                try:
                    pcap = dpkt.pcap.Reader(f)
                except:
                    f.seek(0) 
                    print("Excepcion 2")
                    pcap = None
                
        if (cont == 1000):
            raise NotCorrectFile

        cont = 0
        """
        for timestamp, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)

                # Filtrar solo IPv4
                if not isinstance(eth.data, dpkt.ip.IP):
                    continue

                ip = eth.data

                # Filtrar solo UDP
                if not isinstance(ip.data, dpkt.udp.UDP):
                    continue

                udp = ip.data

                # Filtrar por puerto del vídeo
                #if udp.sport != VIDEO_PORT and udp.dport != VIDEO_PORT:
                #    continue

                # Extraer payload del paquete UDP
                #print(udp.sport)
                #print(bytes(ip).hex())
                #print("*******************************************************")
                payload = udp.data
                if payload:
                    if(len(payload) != 1088):
                        data.append([timestamp, bytearray(payload)])
                        
            except dpkt.NeedData:
                print("Paquete incompleto, saltando...")
                continue
        """
        while True:
            try:
                ts, buf = pcap.next()
            except StopIteration:
                break
            except dpkt.NeedData:
                print("Paquete incompleto, saltando")
                continue
            
            eth = dpkt.ethernet.Ethernet(buf)

            # Filtrar solo IPv4
            if not isinstance(eth.data, dpkt.ip.IP):
                continue

            ip = eth.data

            # Filtrar solo UDP
            if not isinstance(ip.data, dpkt.udp.UDP):
                continue

            udp = ip.data

            # Filtrar por puerto del vídeo
            #if udp.sport != VIDEO_PORT and udp.dport != VIDEO_PORT:
            #    continue

            # Extraer payload del paquete UDP
            #print(udp.sport)
            #print(bytes(ip).hex())
            #print("*******************************************************")
            payload = udp.data
            if payload:
                if(len(payload) != 1088):
                    data.append([ts, bytearray(payload)])
                    
    df = pd.DataFrame.from_records(data,columns=["timestamp","data"])
    return df
    
######################################################
##
## Recibe el nombre del fichero pcap o pcapng a leer y devuelve un el nombre del fichero h5 donde ha guardado los datos
## Va guardando poco a poco para no cargar demasiado en memoria
##
######################################################
"""
def read_pcap_to_csv(filename):
    tam_cabecera = 0
    
    with open(filename, 'rb') as f:
        cont = 0
        pcap = None
        while (pcap is None) and (cont < 1000):
            try:
                #raise ValueError
                pcap = dpkt.pcapng.Reader(f)
                tam_cabecera = 42
            except:
                f.seek(0)  # Volvemos al inicio antes de intentar abrir como PCA
                cont += 1
                print("Excepcion 1")
                pcap = None
                try:
                    pcap = dpkt.pcap.Reader(f)
                    tam_cabecera = 32
                except:
                    f.seek(0)  # Volvemos al inicio antes de intentar abrir como PCA
                    print("Excepcion 2")
                    pcap = None
                
        if (cont == 1000):
            raise NotCorrectFile
                
        cont = 0
        
        aux = []
        
        try:
            for ts, pkt in pcap:
                if (len(pkt) > tam_cabecera+1):
                    aux.append([ts, bytearray(pkt)[tam_cabecera:]])
                    cont += 1
                    
                if(len(aux) == 500000):
                    print("Procesando: " + str(len(aux)) + "; en total: " + str(cont))
                    df = pd.DataFrame(aux, columns=['timestamp', 'packet'])
                    
                    df = df.dropna()
                    fichero_objetivo = filename.replace(".a4radar",".h5")
                    
                    if (cont == 500000):
                        with h5py.File(fichero_objetivo, "w") as ff:
                            ff.create_dataset("df", data=df.values, chunks=True, maxshape=(None,9))
                            
                    else:
                        with h5py.File(fichero_objetivo, "a") as ff:
                            ff['df'].resize((ff['df'].shape[0] + df.values.shape[0],9))
                            ff['df'][-df.values.shape[0]:] = df.values
                    
                    aux.clear()
                    
            if(len(aux) > 0):
                print("Procesando: " + str(len(aux)) + "; en total: " + str(cont))
                df = pd.DataFrame(aux, columns=['timestamp', 'packet'])
                
                df = df.dropna()
                fichero_objetivo = filename.replace(".a4radar",".h5")
                
                if (cont < 500000):
                    with h5py.File(fichero_objetivo, "w") as ff:
                        ff.create_dataset("df", data=df.values, chunks=True, maxshape=(None,9))
                        
                else:
                    with h5py.File(fichero_objetivo, "a") as ff:
                        ff['df'].resize((ff['df'].shape[0] + df.values.shape[0],9))
                        ff['df'][-df.values.shape[0]:] = df.values
                
                aux.clear()   
                    
        except Exception as e:
            print("Ha fallado en el: " + e)
"""