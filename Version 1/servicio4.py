import socket
import datetime
import threading
import time
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, servicio_instance, *args, **kwargs):
        self.servicio = servicio_instance
        super().__init__(*args, **kwargs)

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            print(f"Mensaje HTTP recibido: {body}")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Mensaje recibido correctamente')
            self.servicio.procesar_mensaje_http(body)
            
        except Exception as e:
            print(f"Error en do_POST: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class Servicio4:
    def __init__(self):
        self.host = 'localhost'
        self.port_servidor = 8004
        self.port_destino = 8001
        self.servidor_activo = True
        self.archivo_salida = "mensaje_final.txt"

    def crear_handler(self):
        def handler(*args, **kwargs):
            return HTTPHandler(self, *args, **kwargs)
        return handler

    def enviar_a_servicio1_tcp(self, mensaje):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje.encode('utf-8'))
                print(f"Mensaje enviado al Servicio 1: {mensaje}")
        except Exception as e:
            print(f"Error enviando mensaje al Servicio 1: {e}")

    def procesar_mensaje_http(self, mensaje):
        try:
            print(f"Procesando mensaje: {mensaje}")
            if self.es_mensaje_finalizacion(mensaje):
                print("Señal de finalización recibida del Servicio 3")
                self.finalizar_servicio()
                return
            patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
            match = re.match(patron, mensaje)
            
            if match:
                timestamp, largo_minimo_str, largo_actual_str, mensaje_actual = match.groups()
                
                try:
                    largo_minimo = int(largo_minimo_str)
                    largo_actual = int(largo_actual_str)
                except ValueError:
                    print("Error: Formato de números inválido en el mensaje")
                    return
                
                print(f"Timestamp: {timestamp}")
                print(f"Largo mínimo: {largo_minimo}, Largo actual: {largo_actual}")
                print(f"Mensaje actual: {mensaje_actual}")
                if largo_actual >= largo_minimo:
                    print("¡El mensaje ha alcanzado el largo mínimo!")
                    self.guardar_mensaje_final(mensaje_actual, timestamp)
                    self.iniciar_finalizacion()
                else:
                    print("El mensaje aún no alcanza el largo mínimo. Continuando...")
                    nueva_palabra = input("Ingrese una nueva palabra: ").strip()
                    while not nueva_palabra:
                        nueva_palabra = input("La palabra no puede estar vacía. Ingrese una nueva palabra: ").strip()
                    mensaje_actualizado = f"{mensaje_actual} {nueva_palabra}"
                    nuevo_largo = len(mensaje_actualizado.split())
                    nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    mensaje_completo = f"{nuevo_timestamp}-{largo_minimo}-{nuevo_largo}-{mensaje_actualizado}"
                    print(f"Mensaje actualizado: {mensaje_completo}")
                    self.enviar_a_servicio1_tcp(mensaje_completo)
            else:
                print("Error: Formato de mensaje inválido. No coincide con el patrón esperado.")
                    
        except Exception as e:
            print(f"Error procesando mensaje HTTP: {e}")

    def guardar_mensaje_final(self, mensaje, timestamp):
        try:
            with open(self.archivo_salida, 'w', encoding='utf-8') as archivo:
                archivo.write(f"Mensaje final completado\n")
                archivo.write(f"Timestamp: {timestamp}\n")
                archivo.write(f"Mensaje: {mensaje}\n")
                archivo.write(f"Cantidad de palabras: {len(mensaje.split())}\n")
            print(f"Mensaje final guardado en {self.archivo_salida}")
        except Exception as e:
            print(f"Error guardando archivo: {e}")

    def es_mensaje_finalizacion(self, mensaje):
        return mensaje.count('-') == 1 and "FIN" in mensaje.upper()

    def iniciar_finalizacion(self):
        print("Iniciando cadena de finalización...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_fin = f"{timestamp}-FIN_CADENA"
        try:
            self.enviar_a_servicio1_tcp(mensaje_fin)
            print("Señal de finalización enviada al Servicio 1")
        except Exception as e:
            print(f"Error enviando señal de finalización: {e}")
        self.finalizar_servicio()

    def finalizar_servicio(self):
        print("Finalizando Servicio 4...")
        self.servidor_activo = False

    def ejecutar_servidor_http(self):
        try:
            server = HTTPServer((self.host, self.port_servidor), self.crear_handler())
            server.timeout = 1.0
            print(f"Servicio 4 escuchando en {self.host}:{self.port_servidor} (HTTP)")
            while self.servidor_activo:
                try:
                    server.handle_request()
                except Exception as e:
                    if self.servidor_activo:
                        print(f"Error en servidor HTTP: {e}")
                    break             
        except Exception as e:
            print(f"Error iniciando servidor HTTP: {e}")

    def ejecutar(self):
        print("=== SERVICIO 4 - HTTP SERVER / TCP CLIENT ===")
        servidor_thread = threading.Thread(target=self.ejecutar_servidor_http)
        servidor_thread.daemon = True
        servidor_thread.start()
        try:
            while self.servidor_activo:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupción detectada. Finalizando...")
        finally:
            self.finalizar_servicio()

if __name__ == "__main__":
    servicio = Servicio4()
    servicio.ejecutar()
