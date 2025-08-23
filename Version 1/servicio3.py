import socket
import datetime
import threading
import time
import re

class Servicio3:
    def __init__(self):
        self.host = 'localhost'
        self.port_servidor = 8003
        self.port_destino = 8004
        self.servidor_activo = True

    def enviar_http_a_servicio4(self, mensaje):
        try:
            body = mensaje
            content_length = len(body.encode('utf-8'))
            http_request = (
                f"POST /mensaje HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port_destino}\r\n"
                f"Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {content_length}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{body}"
            )
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(http_request.encode('utf-8'))
                
                response = sock.recv(1024).decode('utf-8')
                print(f"Mensaje HTTP enviado al Servicio 4. Respuesta: {response.split('\\r\\n')[0]}")
                
        except Exception as e:
            print(f"Error enviando mensaje HTTP al Servicio 4: {e}")

    def procesar_mensaje_udp(self, data, addr):
        try:
            mensaje = data.decode('utf-8')
            print(f"Mensaje recibido de Servicio 2 (UDP): {mensaje}")
            
            if self.es_mensaje_finalizacion(mensaje):
                print("Señal de finalización recibida del Servicio 2")
                self.enviar_finalizacion_siguiente()
                self.finalizar_servicio()
                return
            
            patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
            match = re.match(patron, mensaje)
            
            if match:
                timestamp, largo_minimo, largo_actual, mensaje_actual = match.groups()
                
                nueva_palabra = input("Ingrese una nueva palabra: ").strip()
                while not nueva_palabra:
                    nueva_palabra = input("La palabra no puede estar vacía. Ingrese una nueva palabra: ").strip()
                
                mensaje_actualizado = f"{mensaje_actual} {nueva_palabra}"
                nuevo_largo = len(mensaje_actualizado.split())
                nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                mensaje_completo = f"{nuevo_timestamp}-{largo_minimo}-{nuevo_largo}-{mensaje_actualizado}"
                
                print(f"Mensaje actualizado: {mensaje_completo}")
                
                self.enviar_http_a_servicio4(mensaje_completo)
            else:
                print("Error: Formato de mensaje inválido en Servicio 3")
                
        except Exception as e:
            print(f"Error procesando mensaje UDP: {e}")

    def es_mensaje_finalizacion(self, mensaje):
        # Patrón: cualquier timestamp seguido de -FIN_CADENA
        patron = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-FIN'
        return bool(re.match(patron, mensaje))

    def enviar_finalizacion_siguiente(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_fin = f"{timestamp}-FIN_CADENA"
        
        try:
            self.enviar_http_a_servicio4(mensaje_fin)
            print(f"Señal de finalización enviada al Servicio 4 (HTTP): {mensaje_fin}")
        except Exception as e:
            print(f"Error enviando señal de finalización: {e}")

    def finalizar_servicio(self):
        print("Finalizando Servicio 3...")
        self.servidor_activo = False

    def ejecutar_servidor_udp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
            server_sock.bind((self.host, self.port_servidor))
            server_sock.settimeout(1.0)
            
            print(f"Servicio 3 escuchando en {self.host}:{self.port_servidor} (UDP)")
            
            while self.servidor_activo:
                try:
                    data, addr = server_sock.recvfrom(1024)
                    print(f"Mensaje UDP recibido de {addr}")
                    
                    client_thread = threading.Thread(
                        target=self.procesar_mensaje_udp, 
                        args=(data, addr)
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.servidor_activo:
                        print(f"Error en servidor UDP: {e}")
                    break

    def ejecutar(self):
        print("=== SERVICIO 3 - UDP SERVER / HTTP CLIENT ===")
        
        servidor_thread = threading.Thread(target=self.ejecutar_servidor_udp)
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
    servicio = Servicio3()
    servicio.ejecutar()
