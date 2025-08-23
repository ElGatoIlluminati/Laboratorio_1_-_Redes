#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio 4 - Servidor HTTP (recibe de Servicio 3) / Cliente TCP (envía a Servicio 1)
Laboratorio 1 - Redes de Computadores
"""

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
        """Maneja solicitudes POST HTTP"""
        try:
            # Leer el contenido del cuerpo
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            print(f"Mensaje HTTP recibido: {body}")
            
            # Enviar respuesta HTTP
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Mensaje recibido correctamente')
            
            # Procesar el mensaje en el servicio
            self.servicio.procesar_mensaje_http(body)
            
        except Exception as e:
            print(f"Error en do_POST: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        """Desactiva logs automáticos del servidor HTTP"""
        pass

class Servicio4:
    def __init__(self):
        self.host = 'localhost'
        self.port_servidor = 8004  # Puerto donde escucha este servicio (HTTP)
        self.port_destino = 8001   # Puerto del servicio 1 (TCP)
        self.servidor_activo = True
        self.archivo_salida = "mensaje_final.txt"

    def crear_handler(self):
        """Crea el handler HTTP con referencia al servicio"""
        def handler(*args, **kwargs):
            return HTTPHandler(self, *args, **kwargs)
        return handler

    def enviar_a_servicio1_tcp(self, mensaje):
        """Envía mensaje al servicio 1 vía TCP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje.encode('utf-8'))
                print(f"Mensaje enviado al Servicio 1: {mensaje}")
        except Exception as e:
            print(f"Error enviando mensaje al Servicio 1: {e}")

    def procesar_mensaje_http(self, mensaje):
        """Procesa mensajes recibidos vía HTTP"""
        try:
            print(f"Procesando mensaje: {mensaje}")
            
            # Verificar si es señal de finalización
            if self.es_mensaje_finalizacion(mensaje):
                print("Señal de finalización recibida del Servicio 3")
                self.finalizar_servicio()
                return
            
            # Procesar mensaje normal - El timestamp puede contener espacios y guiones
            # Buscar el patrón: YYYY-MM-DD HH:MM:SS-[número]-[número]-[mensaje]
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
                
                # Verificar si el mensaje cumple con el largo mínimo
                if largo_actual >= largo_minimo:
                    print("¡El mensaje ha alcanzado el largo mínimo!")
                    self.guardar_mensaje_final(mensaje_actual, timestamp)
                    self.iniciar_finalizacion()
                else:
                    print("El mensaje aún no alcanza el largo mínimo. Continuando...")
                    
                    # Solicitar nueva palabra
                    nueva_palabra = input("Ingrese una nueva palabra: ").strip()
                    while not nueva_palabra:
                        nueva_palabra = input("La palabra no puede estar vacía. Ingrese una nueva palabra: ").strip()
                    
                    # Actualizar mensaje
                    mensaje_actualizado = f"{mensaje_actual} {nueva_palabra}"
                    nuevo_largo = len(mensaje_actualizado.split())
                    nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    mensaje_completo = f"{nuevo_timestamp}-{largo_minimo}-{nuevo_largo}-{mensaje_actualizado}"
                    
                    print(f"Mensaje actualizado: {mensaje_completo}")
                    
                    # Enviar al servicio 1 para continuar el ciclo
                    self.enviar_a_servicio1_tcp(mensaje_completo)
            else:
                print("Error: Formato de mensaje inválido. No coincide con el patrón esperado.")
                    
        except Exception as e:
            print(f"Error procesando mensaje HTTP: {e}")

    def guardar_mensaje_final(self, mensaje, timestamp):
        """Guarda el mensaje final en un archivo de texto"""
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
        # Patrón: cualquier timestamp seguido de -FIN_CADENA
        patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
        return bool(re.match(patron, mensaje))

    def iniciar_finalizacion(self):
        """Inicia la cadena de finalización"""
        print("Iniciando cadena de finalización...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_fin = f"{timestamp}-FIN_CADENA"
        
        # Enviar señal de finalización al servicio 1
        try:
            self.enviar_a_servicio1_tcp(mensaje_fin)
            print("Señal de finalización enviada al Servicio 1")
        except Exception as e:
            print(f"Error enviando señal de finalización: {e}")
        
        # Finalizar este servicio
        self.finalizar_servicio()

    def finalizar_servicio(self):
        """Finaliza el servicio ordenadamente"""
        print("Finalizando Servicio 4...")
        self.servidor_activo = False

    def ejecutar_servidor_http(self):
        """Ejecuta el servidor HTTP"""
        try:
            server = HTTPServer((self.host, self.port_servidor), self.crear_handler())
            server.timeout = 1.0  # Timeout para permitir verificar servidor_activo
            
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
        """Ejecuta el servicio completo"""
        print("=== SERVICIO 4 - HTTP SERVER / TCP CLIENT ===")
        
        # Iniciar servidor HTTP
        servidor_thread = threading.Thread(target=self.ejecutar_servidor_http)
        servidor_thread.daemon = True
        servidor_thread.start()
        
        # Mantener el servicio activo
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