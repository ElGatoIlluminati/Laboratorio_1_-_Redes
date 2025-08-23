import socket
import datetime
import threading
import time
import re

class Servicio1:
    def __init__(self):
        self.host = 'localhost'
        self.port_servidor = 8001 
        self.port_destino = 8002  
        self.servidor_activo = True
        self.largo_min = 0
        self.p_inicial = ""

    def iniciar_interaccion(self):
        print("SERVICIO 1")
        
        while True:
            try:
                self.largo_min = int(input("Ingrese el largo mínimo mensaje final: "))
                if self.largo_min > 0:
                    break
                else:
                    print("Largo mínimo debe ser mayor a 0")
            except ValueError:
                print("Numero no valido")
        
        self.p_inicial = input("Palabra inicial: ").strip()
        while not self.p_inicial:
            self.p_inicial = input("No puede estar vacía. Ingresar palabra inicial: ").strip()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        l_actual = len(self.p_inicial.split())
        mensaje = f"{timestamp}-{self.largo_min}-{l_actual}-{self.p_inicial}"
        
        print(f"Enviando mensaje inicial: {mensaje}")
        self.enviar_a_servicio2(mensaje)

    def enviar_a_servicio2(self, mensaje):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje.encode('utf-8'))
                print(f"Mensaje enviado a Servicio 2: {mensaje}")
        except Exception as e:
            print(f"Error enviando mensaje a Servicio 2: {e}")

    def manejar_cliente(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                return
                
            print(f"Mensaje recibido de Servicio 4: {data}")
            
            if self.es_mensaje_finalizacion(data):
                print("Señal de finalización recibida del Servicio 4")
                self.fin_servicio()
                return
            
            patron = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d+)-(\d+)-(.+)$'
            match = re.match(patron, data)
            
            if match:
                timestamp, largo_min, l_actual, mensaje_actual = match.groups()
                
                nuevapalabra = input("Nueva palabra: ").strip()
                while not nuevapalabra:
                    nuevapalabra = input("No puede estar vacía >:c. Ingrese nueva palabra: ").strip()
                
                m_actualizado = f"{mensaje_actual} {nuevapalabra}"
                nuevo_largo = len(m_actualizado.split())
                nuevo_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                mensaje_completo = f"{nuevo_timestamp}-{largo_min}-{nuevo_largo}-{m_actualizado}"
                
                print(f"Mensaje actualizado: {mensaje_completo}")
                time.sleep(1)  
                self.enviar_a_servicio2(mensaje_completo)
            else:
                print("Error: Formato de mensaje inválido en Servicio 1")
                
        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            conn.close()

    def es_mensaje_finalizacion(self, mensaje):
        return mensaje.count('-') == 1 and "FIN" in mensaje.upper()

    def enviar_fin_sig(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_fin = f"{timestamp}-FIN_CADENA"
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_destino))
                sock.send(mensaje_fin.encode('utf-8'))
                print(f"Señal de finalización enviada al Servicio 2: {mensaje_fin}")
        except Exception as e:
            print(f"Error enviando señal finalización: {e}")

    def fin_servicio(self):
        print("finalizando servicio 1...")
        self.servidor_activo = False

    def ejecutar_servidor(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port_servidor))
            server_sock.listen(5)
            server_sock.settimeout(1.0)  
            
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
        servidor_thread = threading.Thread(target=self.ejecutar_servidor)
        servidor_thread.daemon = True
        servidor_thread.start()
        
        self.iniciar_interaccion()
        try:
            while self.servidor_activo:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSe produjo una interrupcion, finalizando :c")
        finally:
            self.fin_servicio()

if __name__ == "__main__":
    servicio = Servicio1()
    servicio.ejecutar()
