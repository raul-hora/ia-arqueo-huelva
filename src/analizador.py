
import rasterio
import numpy as np
from pyswip import Prolog
import os

# 1. Configurar Prolog
prolog = Prolog()
prolog.consult("motor.pl")  # Cargamos tus reglas

# 2. Cargar el mapa de Huelva
ruta_mapa = os.path.join("..", "datos", "mdt", "MDT02-ETRS89-HU29-0982-3-COB2.tif")

with rasterio.open(ruta_mapa) as dataset:
    # Vamos a analizar un punto concreto del mapa (el centro, por ejemplo)
    # Leemos una pequeña ventana de datos para calcular la pendiente
    fila, col = dataset.height // 2, dataset.width // 2
    ventana = dataset.read(1, window=((fila-1, fila+2), (col-1, col+2)))
    
    altitud = ventana[1, 1]
    
    # Cálculo simple de pendiente (diferencia de altura entre píxeles)
    dz_dx = (ventana[1, 2] - ventana[1, 0]) / 4.0
    dz_dy = (ventana[2, 1] - ventana[0, 1]) / 4.0
    pendiente = np.sqrt(dz_dx**2 + dz_dy**2) * 100 # En porcentaje

    # 3. CONSULTA A LA INTELIGENCIA LÓGICA
    # Le pasamos los datos del mapa a Prolog
    query = f"evaluar({pendiente:.2f}, {altitud:.2f}, Probabilidad)"
    resultados = list(prolog.query(query))

    if resultados:
        prob = resultados[0]["Probabilidad"]
        print(f"\n--- RESULTADO DEL ANÁLISIS ---")
        print(f"📍 Coordenadas píxel: {fila}, {col}")
        print(f"⛰️ Altitud: {altitud:.2f} m")
        print(f"📐 Pendiente calculada: {pendiente:.2f}%")
        print(f"🎯 Probabilidad Arqueológica: {prob}")
        print(f"------------------------------")