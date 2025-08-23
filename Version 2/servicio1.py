#LIBRERÍAS NECESARIAS-------------------------------------------------------

import socket
import datetime
import threading
import time
import re

#VARIABLES NECESARIAS-------------------------------------------------------

HOST = 'localhost'
PORT_SERVIDOR = 8001  
PORT_DESTINO = 8002   
servidor_activo = True

#FUNCIÓN ENVIAR MENSAJE AL SERVICIO 2---------------------------------------
#     Esta función se encarga de establecer una conexión TCP con el Servicio 2
#     y enviar el mensaje correspondiente. Maneja los errores de conexión
#     que puedan ocurrir durante el proceso de envío.
#
#     PARÁMETROS:
#          mensaje = cadena de texto que será enviada al Servicio 2
#---------------------------------------------------------------------------

def enviar_a_servicio2(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje.encode('utf-8'))
            print(f"Mensaje enviado al Servicio 2: {mensaje}")
    except Exception as e:
        print(f"Error enviando mensaje al Servicio 2: {e}")

#FUNCIÓN INICIALIZAR INTERACCIÓN--------------------------------------------
#     Esta función se encarga de inicializar la interacción del sistema,
#     solicitando al usuario el largo mínimo del mensaje final y la palabra
#     inicial. Valida las entradas y construye el mensaje inicial con
#     formato timestamp-largo_minimo-largo_actual-palabra_inicial.
#
#     PARÁMETROS:
#          Ninguno (interactúa directamente con el usuario)
#---------------------------------------------------------------------------

def iniciar_interaccion():
    print("=== SERVICIO 1 - INICIO DE INTERACCIÓN ===")
    
    while True:
        try:
            largo_minimo = int(input("Ingrese el largo mínimo del mensaje final: "))
            if largo_minimo > 0:
                break
            else:
                print("El largo mínimo debe ser mayor a 0")
        except ValueError:
            print("Por favor, ingrese un número válido")
    
    palabra_inicial = input("Ingrese la palabra inicial: ").strip()
    while not palabra_inicial:
        palabra_inicial = input("La palabra no puede estar vacía. Ingrese la palabra inicial: ").strip()
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    largo_actual = len(palabra_inicial.split())
    mensaje = f"{timestamp}-{largo_minimo}-{largo_actual}-{palabra_inicial}"
    
    print(f"Enviando mensaje inicial: {mensaje}")
    enviar_a_servicio2(mensaje)

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
#     servicio en la cadena. Genera un timestamp actual y construye el
#     mensaje con formato timestamp-FIN_CADENA.
#
#     PARÁMETROS:
#          Ninguno
#---------------------------------------------------------------------------

def enviar_finalizacion_siguiente():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje_fin.encode('utf-8'))
            print(f"Señal de finalización enviada al Servicio 2: {mensaje_fin}")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")

#FUNCIÓN MANEJAR CLIENTE----------------------------------------------------
#     Esta función se ejecuta en un hilo separado para manejar cada conexión
#     de cliente que llega al servidor. Procesa los mensajes recibidos,
#     verifica si son señales de finalización y, en caso contrario,
#     solicita una nueva palabra al usuario para continuar la cadena.
#
#     PARÁMETROS:
#          conn = objeto de conexión del socket cliente
#          addr = dirección del cliente conectado
#---------------------------------------------------------------------------

def manejar_cliente(conn, addr):
    global servidor_activo
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return
            
        print(f"Mensaje recibido de Servicio 4: {data}")
        
        # VERIFICAR SI ES SEÑAL DE FINALIZACIÓN------------------------------
        if es_mensaje_finalizacion(data):
            print("Señal de finalización recibida del Servicio 4")
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
            
            time.sleep(1)  
            enviar_a_servicio2(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido en Servicio 1")
            
    except Exception as e:
        print(f"Error manejando cliente: {e}")
    finally:
        conn.close()

#FUNCIÓN EJECUTAR SERVIDOR TCP----------------------------------------------
#     Esta función ejecuta el servidor TCP que escucha conexiones entrantes
#     en el puerto especificado. Utiliza threading para manejar múltiples
#     conexiones simultáneas y mantiene un timeout para permitir verificar
#     el estado del servidor periódicamente.
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
        
        print(f"Servicio 1 escuchando en {HOST}:{PORT_SERVIDOR}")
        
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
    
    # INICIAR SERVIDOR EN HILO SEPARADO-------------------------------------
    servidor_thread = threading.Thread(target=ejecutar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    time.sleep(1.5)
    
    # INICIALIZAR LA INTERACCIÓN CON EL USUARIO-----------------------------
    iniciar_interaccion()
    
    # MANTENER EL SERVICIO ACTIVO-------------------------------------------
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 1...")
        servidor_activo = False

#EJECUCIÓN DEL PROGRAMA PRINCIPAL-------------------------------------------

if __name__ == "__main__":
    main()