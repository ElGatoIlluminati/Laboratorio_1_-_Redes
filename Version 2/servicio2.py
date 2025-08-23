#LIBRERÍAS NECESARIAS-------------------------------------------------------

import socket
import datetime
import threading
import time
import re

#VARIABLES NECESARIAS-------------------------------------------------------

HOST = 'localhost'
PORT_SERVIDOR = 8002  
PORT_DESTINO = 8003   
servidor_activo = True

#FUNCIÓN ENVIAR MENSAJE AL SERVICIO 3 VÍA UDP-------------------------------
#     Esta función se encarga de establecer una conexión UDP con el Servicio 3
#     y enviar el mensaje correspondiente. UDP es un protocolo sin conexión
#     que no garantiza la entrega, pero es más rápido que TCP.
#
#     PARÁMETROS:
#          mensaje = cadena de texto que será enviada al Servicio 3 vía UDP
#---------------------------------------------------------------------------

def enviar_a_servicio3_udp(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(mensaje.encode('utf-8'), (HOST, PORT_DESTINO))
            print(f"Mensaje enviado al Servicio 3 (UDP): {mensaje}")
    except Exception as e:
        print(f"Error enviando mensaje al Servicio 3: {e}")

#FUNCIÓN VERIFICAR MENSAJE DE FINALIZACIÓN----------------------------------
#     Esta función utiliza expresiones regulares para verificar si un mensaje
#     recibido corresponde a una señal de finalización del sistema. El patrón
#     esperado es: YYYY-MM-DD HH:MM:SS-FIN
#
#     PARÁMETROS:
#          mensaje = cadena de texto a verificar
#     
#     RETORNA:
#          bool = True si es mensaje de finalización, False en caso contrario
#---------------------------------------------------------------------------

def es_mensaje_finalizacion(mensaje):
    patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
    return bool(re.match(patron, mensaje))

#FUNCIÓN ENVIAR FINALIZACIÓN AL SIGUIENTE SERVICIO-------------------------
#     Esta función construye y envía la señal de finalización al siguiente
#     servicio en la cadena utilizando protocolo UDP. Genera un timestamp
#     actual y construye el mensaje con formato timestamp-FIN_CADENA.
#
#     PARÁMETROS:
#          Ninguno
#---------------------------------------------------------------------------

def enviar_finalizacion_siguiente():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(mensaje_fin.encode('utf-8'), (HOST, PORT_DESTINO))
            print(f"Señal de finalización enviada al Servicio 3 (UDP): {mensaje_fin}")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")

#FUNCIÓN MANEJAR CLIENTE TCP------------------------------------------------
#     Esta función se ejecuta en un hilo separado para manejar cada conexión
#     TCP que llega al servidor desde el Servicio 1. Procesa los mensajes,
#     verifica señales de finalización y solicita nueva palabra al usuario
#     para continuar la cadena de mensajes.
#
#     PARÁMETROS:
#          conn = objeto de conexión del socket cliente TCP
#          addr = dirección del cliente conectado
#---------------------------------------------------------------------------

def manejar_cliente(conn, addr):
    global servidor_activo
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return
            
        print(f"Mensaje recibido de Servicio 1: {data}")
        
        # VERIFICAR SI ES SEÑAL DE FINALIZACIÓN------------------------------
        if es_mensaje_finalizacion(data):
            print("Señal de finalización recibida del Servicio 1")
            enviar_finalizacion_siguiente()
            servidor_activo = False
            return
        
        # PROCESAR MENSAJE NORMAL CON EXPRESIONES REGULARES------------------
        patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
        match = re.match(patron, data)
        
        if match:
            timestamp, largo_minimo, largo_actual, mensaje_actual = match.groups()
            
            nueva_palabra = input("Ingrese una nueva palabra: ").strip()
            while not nueva_palabra:
                nueva_palabra = input("La palabra no puede estar vacía. Ingrese una nueva palabra: ").strip()
            
            # CONSTRUIR MENSAJE ACTUALIZADO----------------------------------
            mensaje_actualizado = f"{mensaje_actual} {nueva_palabra}"
            nuevo_largo = len(mensaje_actualizado.split())
            nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            mensaje_completo = f"{nuevo_timestamp}-{largo_minimo}-{nuevo_largo}-{mensaje_actualizado}"
            
            print(f"Mensaje actualizado: {mensaje_completo}")
            
            # ENVIAR VÍA UDP AL SERVICIO 3-----------------------------------
            enviar_a_servicio3_udp(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido en Servicio 2")
            
    except Exception as e:
        print(f"Error manejando cliente: {e}")
    finally:
        conn.close()

#FUNCIÓN EJECUTAR SERVIDOR TCP----------------------------------------------
#     Esta función ejecuta el servidor TCP que recibe conexiones del
#     Servicio 1. Utiliza threading para manejar múltiples conexiones
#     simultáneas y mantiene un timeout para verificar periódicamente
#     el estado del servidor.
#
#     PARÁMETROS:
#          Ninguno (utiliza variables globales)
#---------------------------------------------------------------------------

def ejecutar_servidor():
    global servidor_activo
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT_SERVIDOR))
        server_sock.listen(5)
        server_sock.settimeout(1.0)  
        
        print(f"Servicio 2 escuchando en {HOST}:{PORT_SERVIDOR}")
        
        while servidor_activo:
            try:
                conn, addr = server_sock.accept()
                print(f"Conexión recibida de {addr}")
                client_thread = threading.Thread(
                    target=manejar_cliente, 
                    args=(conn, addr)
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if servidor_activo:
                    print(f"Error en servidor: {e}")
                break

#FUNCIÓN PRINCIPAL DEL PROGRAMA---------------------------------------------

def main():
    global servidor_activo
    print("=== SERVICIO 2 - TCP SERVER / UDP CLIENT ===")
    
    # INICIAR SERVIDOR TCP EN HILO SEPARADO---------------------------------
    servidor_thread = threading.Thread(target=ejecutar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # MANTENER EL SERVICIO ACTIVO-------------------------------------------
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 2...")
        servidor_activo = False

#EJECUCIÓN DEL PROGRAMA PRINCIPAL-------------------------------------------

if __name__ == "__main__":
    main()