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

class Servicio1:
    def __init__(self):
        self.host = 'localhost'
        self.port_servidor = 8001  # Puerto donde escucha este servicio
        self.port_destino = 8002   # Puerto del servicio 2
        self.servidor_activo = True
        self.largo_minimo = 0
        self.palabra_inicial = ""

    def iniciar_interaccion(self):
        """Solicita los datos iniciales y comienza el juego"""
        print("=== SERVICIO 1 - INICIO DE INTERACCIÓN ===")
        
        # Solicitar largo mínimo
        while True:
            try:
                self.largo_minimo = int(input("Ingrese el largo mínimo del mensaje final: "))
                if self.largo_minimo > 0:
                    break
                else:
                    print("El largo mínimo debe ser mayor a 0")
            except ValueError:
                print("Por favor, ingrese un número válido")
        
        # Solicitar palabra inicial
        self.palabra_inicial = input("Ingrese la palabra inicial: ").strip()
        while not self.palabra_inicial:
            self.palabra_inicial = input("La palabra no puede estar vacía. Ingrese la palabra inicial: ").strip()
        
        # Crear mensaje inicial
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        largo_actual = len(self.palabra_inicial.split())
        mensaje = f"{timestamp}-{self.largo_minimo}-{largo_actual}-{self.palabra_inicial}"
        
        print(f"Enviando mensaje inicial: {mensaje}")
        self.enviar_a_servicio2(mensaje)

    def enviar_a_servicio2(self, mensaje):
        """Envía mensaje al servicio 2 vía TCP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje.encode('utf-8'))
                print(f"Mensaje enviado al Servicio 2: {mensaje}")
        except Exception as e:
            print(f"Error enviando mensaje al Servicio 2: {e}")

    def manejar_cliente(self, conn, addr):
        """Maneja conexiones entrantes desde el servicio 4"""
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                return
                
            print(f"Mensaje recibido de Servicio 4: {data}")
            
            # Verificar si es señal de finalización
            if self.es_mensaje_finalizacion(data):
                print("Señal de finalización recibida del Servicio 4")
                self.finalizar_servicio()
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
                self.enviar_a_servicio2(mensaje_completo)
            else:
                print("Error: Formato de mensaje inválido en Servicio 1")
                
        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            conn.close()

    def es_mensaje_finalizacion(self, mensaje):
        """Verifica si el mensaje es una señal de finalización"""
        return mensaje.count('-') == 1 and "FIN" in mensaje.upper()

    def enviar_finalizacion_siguiente(self):
        """Envía señal de finalización al siguiente servicio en la cadena"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_fin = f"{timestamp}-FIN_CADENA"
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje_fin.encode('utf-8'))
                print(f"Señal de finalización enviada al Servicio 2: {mensaje_fin}")
        except Exception as e:
            print(f"Error enviando señal de finalización: {e}")

    def finalizar_servicio(self):
        """Finaliza el servicio ordenadamente"""
        print("Finalizando Servicio 1...")
        self.servidor_activo = False

    def ejecutar_servidor(self):
        """Ejecuta el servidor TCP"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port_servidor))
            server_sock.listen(5)
            server_sock.settimeout(1.0)  # Timeout para permitir verificar servidor_activo
            
            print(f"Servicio 1 escuchando en {self.host}:{self.port_servidor}")
            
            while self.servidor_activo:
                try:
                    conn, addr = server_sock.accept()
                    print(f"Conexión recibida de {addr}")
                    client_thread = threading.Thread(
                        target=self.manejar_cliente, 
                        args=(conn, addr)
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.servidor_activo:
                        print(f"Error en servidor: {e}")
                    break

    def ejecutar(self):
        """Ejecuta el servicio completo"""
        # Iniciar servidor en hilo separado
        servidor_thread = threading.Thread(target=self.ejecutar_servidor)
        servidor_thread.daemon = True
        servidor_thread.start()
        
        # Iniciar interacción
        self.iniciar_interaccion()
        
        # Mantener el servicio activo
        try:
            while self.servidor_activo:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupción detectada. Finalizando...")
        finally:
            self.finalizar_servicio()

if __name__ == "__main__":
    servicio = Servicio1()
    servicio.ejecutar()