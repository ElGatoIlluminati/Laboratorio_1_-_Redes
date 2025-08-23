#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio 3 - Servidor UDP (recibe de Servicio 2) / Cliente HTTP TCP (envía a Servicio 4)
Laboratorio 1 - Redes de Computadores
"""

import socket
import datetime
import threading
import time
import re

# Configuración global
HOST = 'localhost'
PORT_SERVIDOR = 8003  # Puerto donde escucha este servicio (UDP)
PORT_DESTINO = 8004   # Puerto del servicio 4 (HTTP)
servidor_activo = True

def enviar_http_a_servicio4(mensaje):
    """Envía mensaje al servicio 4 vía HTTP usando socket TCP"""
    try:
        # Crear solicitud HTTP POST
        body = mensaje
        content_length = len(body.encode('utf-8'))
        
        http_request = (
            f"POST /mensaje HTTP/1.1\r\n"
            f"Host: {HOST}:{PORT_DESTINO}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        
        # Enviar vía socket TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(http_request.encode('utf-8'))
            
            # Recibir respuesta
            response = sock.recv(1024).decode('utf-8')
            print(f"Mensaje HTTP enviado al Servicio 4. Respuesta: {response.split('\\r\\n')[0]}")
            
    except Exception as e:
        print(f"Error enviando mensaje HTTP al Servicio 4: {e}")

def es_mensaje_finalizacion(mensaje):
    """Verifica si es un mensaje de finalización"""
    patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
    return bool(re.match(patron, mensaje))

def enviar_finalizacion_siguiente():
    """Envía señal de finalización al siguiente servicio en la cadena vía HTTP"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        enviar_http_a_servicio4(mensaje_fin)
        print(f"Señal de finalización enviada al Servicio 4 (HTTP): {mensaje_fin}")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")

def procesar_mensaje_udp(data, addr):
    """Procesa mensajes recibidos vía UDP"""
    global servidor_activo
    try:
        mensaje = data.decode('utf-8')
        print(f"Mensaje recibido de Servicio 2 (UDP): {mensaje}")
        
        # Verificar si es señal de finalización
        if es_mensaje_finalizacion(mensaje):
            print("Señal de finalización recibida del Servicio 2")
            enviar_finalizacion_siguiente()
            servidor_activo = False
            return
        
        # Procesar mensaje normal usando regex para parsing correcto
        patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
        match = re.match(patron, mensaje)
        
        if match:
            timestamp, largo_minimo, largo_actual, mensaje_actual = match.groups()
            
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
            
            # Enviar al servicio 4 vía HTTP
            enviar_http_a_servicio4(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido en Servicio 3")
            
    except Exception as e:
        print(f"Error procesando mensaje UDP: {e}")

def ejecutar_servidor_udp():
    """Ejecuta el servidor UDP"""
    global servidor_activo
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
        server_sock.bind((HOST, PORT_SERVIDOR))
        server_sock.settimeout(1.0)  # Timeout para permitir verificar servidor_activo
        
        print(f"Servicio 3 escuchando en {HOST}:{PORT_SERVIDOR} (UDP)")
        
        while servidor_activo:
            try:
                data, addr = server_sock.recvfrom(1024)
                print(f"Mensaje UDP recibido de {addr}")
                
                # Procesar en hilo separado para no bloquear el servidor
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

def main():
    """Función principal"""
    global servidor_activo
    print("=== SERVICIO 3 - UDP SERVER / HTTP CLIENT ===")
    
    # Iniciar servidor UDP
    servidor_thread = threading.Thread(target=ejecutar_servidor_udp)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # Mantener el servicio activo
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 3...")
        servidor_activo = False

if __name__ == "__main__":
    main()