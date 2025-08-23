#LIBRERÍAS NECESARIAS-------------------------------------------------------

import socket
import datetime
import threading
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

#VARIABLES NECESARIAS-------------------------------------------------------

HOST = 'localhost'
PORT_SERVIDOR = 8004  
PORT_DESTINO = 8001   
servidor_activo = True
ARCHIVO_SALIDA = "mensaje_final.txt"

#FUNCIÓN ENVIAR MENSAJE AL SERVICIO 1 VÍA TCP-------------------------------
#     Esta función se encarga de establecer una conexión TCP con el Servicio 1
#     para enviar mensajes o señales de finalización. Utiliza el protocolo
#     TCP que garantiza la entrega ordenada de los datos.
#
#     PARÁMETROS:
#          mensaje = cadena de texto que será enviada al Servicio 1 vía TCP
#---------------------------------------------------------------------------

def enviar_a_servicio1_tcp(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje.encode('utf-8'))
            print(f"Mensaje enviado al Servicio 1: {mensaje}")
    except Exception as e:
        print(f"Error enviando mensaje al Servicio 1: {e}")

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

#FUNCIÓN GUARDAR MENSAJE FINAL----------------------------------------------
#     Esta función guarda el mensaje final en un archivo de texto cuando
#     se alcanza el largo mínimo especificado. Incluye timestamp, mensaje
#     completo y cantidad de palabras para referencia posterior.
#
#     PARÁMETROS:
#          mensaje = cadena con el mensaje final completo
#          timestamp = marca de tiempo cuando se completó el mensaje
#---------------------------------------------------------------------------

def guardar_mensaje_final(mensaje, timestamp):
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as archivo:
            archivo.write(f"Mensaje final completado\n")
            archivo.write(f"Timestamp: {timestamp}\n")
            archivo.write(f"Mensaje: {mensaje}\n")
            archivo.write(f"Cantidad de palabras: {len(mensaje.split())}\n")
        
        print(f"Mensaje final guardado en {ARCHIVO_SALIDA}")
        
    except Exception as e:
        print(f"Error guardando archivo: {e}")

#FUNCIÓN INICIAR FINALIZACIÓN-----------------------------------------------
#     Esta función inicia la cadena de finalización cuando el mensaje
#     alcanza el largo mínimo requerido. Construye la señal de finalización
#     y la envía al Servicio 1 para cerrar el ciclo del sistema.
#
#     PARÁMETROS:
#          Ninguno (utiliza variables globales)
#---------------------------------------------------------------------------

def iniciar_finalizacion():
    global servidor_activo
    print("Iniciando cadena de finalización...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        enviar_a_servicio1_tcp(mensaje_fin)
        print("Señal de finalización enviada al Servicio 1")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")
    
    servidor_activo = False

#FUNCIÓN PROCESAR MENSAJE HTTP----------------------------------------------
#     Esta función procesa los mensajes HTTP recibidos del Servicio 3.
#     Verifica si el mensaje ha alcanzado el largo mínimo especificado,
#     y en caso afirmativo, guarda el mensaje final e inicia la finalización.
#     Si no ha alcanzado el largo mínimo, solicita una nueva palabra al usuario.
#
#     PARÁMETROS:
#          mensaje = cadena de texto recibida en el body de la petición HTTP
#---------------------------------------------------------------------------

def procesar_mensaje_http(mensaje):
    global servidor_activo
    try:
        print(f"Procesando mensaje: {mensaje}")
        
        # VERIFICAR SI ES SEÑAL DE FINALIZACIÓN------------------------------
        if es_mensaje_finalizacion(mensaje):
            print("Señal de finalización recibida del Servicio 3")
            servidor_activo = False
            return
        
        # PROCESAR MENSAJE NORMAL CON EXPRESIONES REGULARES------------------
        patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
        match = re.match(patron, mensaje)
        
        if match:
            timestamp, largo_minimo_str, largo_actual_str, mensaje_actual = match.groups()
            
            # CONVERTIR STRINGS A ENTEROS------------------------------------
            try:
                largo_minimo = int(largo_minimo_str)
                largo_actual = int(largo_actual_str)
            except ValueError:
                print("Error: Formato de números inválido en el mensaje")
                return
            
            print(f"Timestamp: {timestamp}")
            print(f"Largo mínimo: {largo_minimo}, Largo actual: {largo_actual}")
            print(f"Mensaje actual: {mensaje_actual}")
            
            # VERIFICAR SI SE ALCANZÓ EL LARGO MÍNIMO------------------------
            if largo_actual >= largo_minimo:
                print("¡El mensaje ha alcanzado el largo mínimo!")
                guardar_mensaje_final(mensaje_actual, timestamp)
                iniciar_finalizacion()
            else:
                print("El mensaje aún no alcanza el largo mínimo. Continuando...")
                
                nueva_palabra = input("Ingrese una nueva palabra: ").strip()
                while not nueva_palabra:
                    nueva_palabra = input("La palabra no puede estar vacía. Ingrese una nueva palabra: ").strip()
                
                # CONSTRUIR MENSAJE ACTUALIZADO------------------------------
                mensaje_actualizado = f"{mensaje_actual} {nueva_palabra}"
                nuevo_largo = len(mensaje_actualizado.split())
                nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                mensaje_completo = f"{nuevo_timestamp}-{largo_minimo}-{nuevo_largo}-{mensaje_actualizado}"
                
                print(f"Mensaje actualizado: {mensaje_completo}")
                
                # ENVIAR MENSAJE ACTUALIZADO AL SERVICIO 1-------------------
                enviar_a_servicio1_tcp(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido. No coincide con el patrón esperado.")
                
    except Exception as e:
        print(f"Error procesando mensaje HTTP: {e}")

#CLASE MANEJADOR DE PETICIONES HTTP-----------------------------------------
#     Esta clase hereda de BaseHTTPRequestHandler y define cómo manejar
#     las peticiones HTTP POST que llegan al servidor. Extrae el cuerpo
#     del mensaje, envía una respuesta HTTP apropiada y procesa el mensaje.
#---------------------------------------------------------------------------

class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # EXTRAER CUERPO DE LA PETICIÓN HTTP-----------------------------
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            print(f"Mensaje HTTP recibido: {body}")
            
            # ENVIAR RESPUESTA HTTP 200 OK-----------------------------------
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Mensaje recibido correctamente')
            
            # PROCESAR EL MENSAJE RECIBIDO-----------------------------------
            procesar_mensaje_http(body)
            
        except Exception as e:
            print(f"Error en do_POST: {e}")
            self.send_response(500)
            self.end_headers()

#FUNCIÓN EJECUTAR SERVIDOR HTTP---------------------------------------------
#     Esta función ejecuta el servidor HTTP que recibe peticiones POST
#     del Servicio 3. Utiliza la clase HTTPServer de Python y mantiene
#     un timeout para verificar periódicamente el estado del servidor.
#
#     PARÁMETROS:
#          Ninguno (utiliza variables globales)
#---------------------------------------------------------------------------

def ejecutar_servidor_http():
    global servidor_activo
    try:
        server = HTTPServer((HOST, PORT_SERVIDOR), HTTPHandler)
        server.timeout = 1.0  # Timeout para permitir verificar servidor_activo
        
        print(f"Servicio 4 escuchando en {HOST}:{PORT_SERVIDOR} (HTTP)")
        
        while servidor_activo:
            try:
                server.handle_request()
            except Exception as e:
                if servidor_activo:
                    print(f"Error en servidor HTTP: {e}")
                break
                
    except Exception as e:
        print(f"Error iniciando servidor HTTP: {e}")

#FUNCIÓN PRINCIPAL DEL PROGRAMA---------------------------------------------

def main():
    global servidor_activo
    print("=== SERVICIO 4 - HTTP SERVER / TCP CLIENT ===")
    
    # INICIAR SERVIDOR HTTP EN HILO SEPARADO--------------------------------
    servidor_thread = threading.Thread(target=ejecutar_servidor_http)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # MANTENER EL SERVICIO ACTIVO-------------------------------------------
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 4...")
        servidor_activo = False

#EJECUCIÓN DEL PROGRAMA PRINCIPAL-------------------------------------------

if __name__ == "__main__":
    main()