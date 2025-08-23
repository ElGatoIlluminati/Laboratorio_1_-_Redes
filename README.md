# Laboratorio 1 Redes
---
## Grupo 15
| Integrante | Rol |
| ------------- | ------------- |
| Benjamin Cardenas | 202073572-7 |
| Francisca Salinas | 202173569-0 |
| Camila Rosales | 202173631-k |

## Aclaraciones:
- Esta tarea se desarrollo con Python 3.10 y superiores
- Se utilizó la librería "threading" de Python para el manejo de múltiples conexiones y mejor visualización.
- Se interpretó que el valor del largo mínimo debía ser el número de palabras, no de caracteres.
- El archivo de salida se sobrescribe en cada ejecución

## Instrucciones de Ejecución

La tarea se desarrollo a lo largo de 4 archivos distintos, uno para cada servicio, y se ejecuta de la siguiente manera: 

### 1. Los servicios se ejecutaron en el siguiente orden (cada uno en una terminal separada):

#### Terminal 1 - Servicio 1:
```bash
python3 servicio1.py
```

#### Terminal 2 - Servicio 2:
```bash
python3 servicio2.py
```

#### Terminal 3 - Servicio 3:
```bash
python3 servicio3.py
```

#### Terminal 4 - Servicio 4:
```bash
python3 servicio4.py
```

### 3. Seguir las instrucciones dadas en la terminal correspondiente (seguir el orden anteriormente mencionado)

### 4. Cuando se alcanza el largo mínimo, el Servicio 4 guarda el mensaje en `mensaje_final.txt` (Se inicia la cadena de finalización automáticamente y todos los servicios se cierran)

## Configuración de Puertos

| Servicio | Puerto |
|----------|--------|
| Servicio 1 | 8001 |
| Servicio 2 | 8002 |
| Servicio 3 | 8003 |
| Servicio 4 | 8004 |
