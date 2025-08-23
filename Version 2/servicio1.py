#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio 1 - Servidor TCP que inicia la cadena del juego
Laboratorio 1 - Redes de Computadores
"""

import socket
import datetime
import threading
import time
import re

# Configuración global
HOST = 'localhost'
PORT_SERVIDOR = 8001  # Puerto donde escucha este servicio
PORT_DESTINO = 8002   # Puerto del servicio 2
servidor_activo = True

def enviar_a_servicio2(mensaje):
    """Envía mensaje al servicio 2 vía TCP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje.encode('utf-8'))
            print(f"Mensaje enviado al Servicio 2: {mensaje}")
    except Exception as e:
        print(f"Error enviando mensaje al Servicio 2: {e}")

def iniciar_interaccion():
    """Solicita los datos iniciales y comienza el juego"""
    print("=== SERVICIO 1 - INICIO DE INTERACCIÓN ===")
    
    # Solicitar largo mínimo
    while True:
        try:
            largo_minimo = int(input("Ingrese el largo mínimo del mensaje final: "))
            if largo_minimo > 0:
                break
            else:
                print("El largo mínimo debe ser mayor a 0")
        except ValueError:
            print("Por favor, ingrese un número válido")
    
    # Solicitar palabra inicial
    palabra_inicial = input("Ingrese la palabra inicial: ").strip()
    while not palabra_inicial:
        palabra_inicial = input("La palabra no puede estar vacía. Ingrese la palabra inicial: ").strip()
    
    # Crear mensaje inicial
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    largo_actual = len(palabra_inicial.split())
    mensaje = f"{timestamp}-{largo_minimo}-{largo_actual}-{palabra_inicial}"
    
    print(f"Enviando mensaje inicial: {mensaje}")
    enviar_a_servicio2(mensaje)

def es_mensaje_finalizacion(mensaje):
    """Verifica si es un mensaje de finalización"""
    patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
    return bool(re.match(patron, mensaje))

def enviar_finalizacion_siguiente():
    """Envía señal de finalización al siguiente servicio en la cadena"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_fin = f"{timestamp}-FIN_CADENA"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT_DESTINO))
            sock.send(mensaje_fin.encode('utf-8'))
            print(f"Señal de finalización enviada al Servicio 2: {mensaje_fin}")
    except Exception as e:
        print(f"Error enviando señal de finalización: {e}")

def manejar_cliente(conn, addr):
    """Maneja conexiones entrantes desde el servicio 4"""
    global servidor_activo
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return
            
        print(f"Mensaje recibido de Servicio 4: {data}")
        
        # Verificar si es señal de finalización
        if es_mensaje_finalizacion(data):
            print("Señal de finalización recibida del Servicio 4")
            enviar_finalizacion_siguiente()
            servidor_activo = False
            return
        
        # Procesar mensaje normal usando regex para parsing correcto
        patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
        match = re.match(patron, data)
        
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
            
            # Enviar al servicio 2
            time.sleep(1)  # Pequeña pausa para evitar conflictos
            enviar_a_servicio2(mensaje_completo)
        else:
            print("Error: Formato de mensaje inválido en Servicio 1")
            
    except Exception as e:
        print(f"Error manejando cliente: {e}")
    finally:
        conn.close()

def ejecutar_servidor():
    """Ejecuta el servidor TCP"""
    global servidor_activo
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT_SERVIDOR))
        server_sock.listen(5)
        server_sock.settimeout(1.0)  # Timeout para permitir verificar servidor_activo
        
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

def main():
    """Función principal"""
    global servidor_activo
    # Iniciar servidor en hilo separado
    servidor_thread = threading.Thread(target=ejecutar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # Iniciar interacción
    iniciar_interaccion()
    
    # Mantener el servicio activo
    try:
        while servidor_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Finalizando...")
    finally:
        print("Finalizando Servicio 1...")
        servidor_activo = False

if __name__ == "__main__":
    main()