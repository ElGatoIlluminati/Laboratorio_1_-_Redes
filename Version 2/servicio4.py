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
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración global
HOST = 'localhost'
PORT_SERVIDOR = 8004  # Puerto donde escucha este servicio (HTTP)
PORT_DESTINO = 8001   # Puerto del servicio 1 (TCP)
servidor_activo = True
ARCHIVO_SALIDA = "mensaje_final.txt"

def enviar_a_servicio1_tcp(mensaje):
    """Envía mensaje al servicio 1 vía TCP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje.encode('utf-8'))
            print(f"Mensaje enviado al Servicio 1: {mensaje}")
    except Exception as e:
        print(f"Error enviando mensaje al Servicio 1: {e}")

def es_mensaje_finalizacion(mensaje):
    """Verifica si es un mensaje de finalización"""
    patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
    return bool(re.match(patron, mensaje))

def guardar_mensaje_final(mensaje, timestamp):
    """Guarda el mensaje final en un archivo de texto"""
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as archivo:
            archivo.write(f"Mensaje final completado\n")
            archivo.write(f"Timestamp: {timestamp}\n")
            archivo.write(f"Mensaje: {mensaje}\n")
            archivo.write(f"Cantidad de palabras: {len(mensaje.split())}\n")
        
        print(f"Mensaje final guardado en {ARCHIVO_SALIDA}")
        
    except Exception as e:
        print(f"Error guardando archivo: {e}")

def iniciar_finalizacion():
    """Inicia la cadena de finalización"""
    global servidor_activo
    print("Iniciando cadena de finalización...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    # Enviar señal de finalización al servicio 1
    try:
        enviar_a_servicio1_tcp(mensaje_fin)
        print("Señal de finalización enviada al Servicio 1")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")
    
    # Finalizar este servicio
    servidor_activo = False

def procesar_mensaje_http(mensaje):
    """Procesa mensajes recibidos vía HTTP"""
    global servidor_activo
    try:
        print(f"Procesando mensaje: {mensaje}")
        
        # Verificar si es señal de finalización
        if es_mensaje_finalizacion(mensaje):
            print("Señal de finalización recibida del Servicio 3")
            servidor_activo = False
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
                guardar_mensaje_final(mensaje_actual, timestamp)
                iniciar_finalizacion()
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
                enviar_a_servicio1_tcp(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido. No coincide con el patrón esperado.")
                
    except Exception as e:
        print(f"Error procesando mensaje HTTP: {e}")

class HTTPHandler(BaseHTTPRequestHandler):
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
            
            # Procesar el mensaje
            procesar_mensaje_http(body)
            
        except Exception as e:
            print(f"Error en do_POST: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        """Desactiva logs automáticos del servidor HTTP"""
        pass

def ejecutar_servidor_http():
    """Ejecuta el servidor HTTP"""
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

def main():
    """Función principal"""
    global servidor_activo
    print("=== SERVICIO 4 - HTTP SERVER / TCP CLIENT ===")
    
    # Iniciar servidor HTTP
    servidor_thread = threading.Thread(target=ejecutar_servidor_http)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # Mantener el servicio activo
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 4...")
        servidor_activo = False

if __name__ == "__main__":
    main()