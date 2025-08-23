#LIBRERÍAS NECESARIAS-------------------------------------------------------

import socket
import datetime
import threading
import time
import re

#VARIABLES NECESARIAS-------------------------------------------------------

HOST = 'localhost'
PORT_SERVIDOR = 8003  
PORT_DESTINO = 8004   
servidor_activo = True

#FUNCIÓN ENVIAR MENSAJE HTTP AL SERVICIO 4----------------------------------
#     Esta función construye una petición HTTP POST completa con headers
#     apropiados y envía el mensaje al Servicio 4. Utiliza el protocolo
#     HTTP/1.1 con Content-Type text/plain y maneja la respuesta del servidor.
#
#     PARÁMETROS:
#          mensaje = cadena de texto que será enviada como body de la petición HTTP
#---------------------------------------------------------------------------

def enviar_http_a_servicio4(mensaje):
    try:
        body = mensaje
        content_length = len(body.encode('utf-8'))
        
        # CONSTRUIR PETICIÓN HTTP POST COMPLETA------------------------------
        http_request = (
            f"POST /mensaje HTTP/1.1\r\n"
            f"Host: {HOST}:{PORT_DESTINO}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        
        # ENVIAR PETICIÓN Y RECIBIR RESPUESTA--------------------------------
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(http_request.encode('utf-8'))
            
            response = sock.recv(1024).decode('utf-8')
            print(f"Mensaje HTTP enviado al Servicio 4. Respuesta: {response.split('\\r\\n')[0]}")
            
    except Exception as e:
        print(f"Error enviando mensaje HTTP al Servicio 4: {e}")

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
#     servicio en la cadena utilizando protocolo HTTP. Genera un timestamp
#     actual y construye el mensaje con formato timestamp-FIN_CADENA.
#
#     PARÁMETROS:
#          Ninguno
#---------------------------------------------------------------------------

def enviar_finalizacion_siguiente():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        enviar_http_a_servicio4(mensaje_fin)
        print(f"Señal de finalización enviada al Servicio 4 (HTTP): {mensaje_fin}")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")

#FUNCIÓN PROCESAR MENSAJE UDP-----------------------------------------------
#     Esta función se ejecuta en un hilo separado para procesar cada mensaje
#     UDP recibido del Servicio 2. Maneja tanto mensajes normales como
#     señales de finalización, solicita nueva palabra al usuario y
#     construye el mensaje actualizado para enviar al siguiente servicio.
#
#     PARÁMETROS:
#          data = datos recibidos del socket UDP
#          addr = dirección del cliente que envió el mensaje UDP
#---------------------------------------------------------------------------

def procesar_mensaje_udp(data, addr):
    global servidor_activo
    try:
        mensaje = data.decode('utf-8')
        print(f"Mensaje recibido de Servicio 2 (UDP): {mensaje}")
        
        # VERIFICAR SI ES SEÑAL DE FINALIZACIÓN------------------------------
        if es_mensaje_finalizacion(mensaje):
            print("Señal de finalización recibida del Servicio 2")
            enviar_finalizacion_siguiente()
            servidor_activo = False
            return
        
        # PROCESAR MENSAJE NORMAL CON EXPRESIONES REGULARES------------------
        patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
        match = re.match(patron, mensaje)
        
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
            
            # ENVIAR VÍA HTTP AL SERVICIO 4-----------------------------------
            enviar_http_a_servicio4(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido en Servicio 3")
            
    except Exception as e:
        print(f"Error procesando mensaje UDP: {e}")

#FUNCIÓN EJECUTAR SERVIDOR UDP----------------------------------------------
#     Esta función ejecuta el servidor UDP que recibe mensajes del Servicio 2.
#     UDP es un protocolo sin conexión, por lo que utiliza recvfrom para
#     recibir datos. Utiliza threading para procesar cada mensaje en
#     hilos separados y mantiene un timeout para verificar el estado del servidor.
#
#     PARÁMETROS:
#          Ninguno (utiliza variables globales)
#---------------------------------------------------------------------------

def ejecutar_servidor_udp():
    global servidor_activo
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
        server_sock.bind((HOST, PORT_SERVIDOR))
        server_sock.settimeout(1.0)
        
        print(f"Servicio 3 escuchando en {HOST}:{PORT_SERVIDOR} (UDP)")
        
        while servidor_activo:
            try:
                data, addr = server_sock.recvfrom(1024)
                print(f"Mensaje UDP recibido de {addr}")
                
                # PROCESAR MENSAJE EN HILO SEPARADO--------------------------
                client_thread = threading.Thread(
                    target=procesar_mensaje_udp, 
                    args=(data, addr)
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if servidor_activo:
                    print(f"Error en servidor UDP: {e}")
                break

#FUNCIÓN PRINCIPAL DEL PROGRAMA---------------------------------------------

def main():
    global servidor_activo
    print("=== SERVICIO 3 - UDP SERVER / HTTP CLIENT ===")
    
    # INICIAR SERVIDOR UDP EN HILO SEPARADO---------------------------------
    servidor_thread = threading.Thread(target=ejecutar_servidor_udp)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # MANTENER EL SERVICIO ACTIVO-------------------------------------------
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 3...")
        servidor_activo = False

#EJECUCIÓN DEL PROGRAMA PRINCIPAL-------------------------------------------

if __name__ == "__main__":
    main()