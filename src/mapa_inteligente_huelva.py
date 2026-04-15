import rasterio
import numpy as np
from pyproj import Transformer
import folium
from folium.plugins import MarkerCluster
from pyswip import Prolog
import os
import random
from scipy.ndimage import gaussian_gradient_magnitude

# 1. Configurar Prolog
prolog = Prolog()
prolog.consult("motor.pl")

archivo_mdt = os.path.join("..", "datos", "mdt", "MDT02-ETRS89-HU29-0982-3-COB2.tif")

with rasterio.open(archivo_mdt) as ds:
    transformer = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
    
    # Análisis de relieve
    altitudes = ds.read(1)
    altitudes[altitudes < -100] = np.mean(altitudes[altitudes > -100])
    gradiente = gaussian_gradient_magnitude(altitudes, sigma=1)
    mapa_pendientes = (gradiente / ds.res[0]) * 100

    # Centro del mapa
    centro_y, centro_x = ds.height // 2, ds.width // 2
    lon_c, lat_c = ds.xy(centro_y, centro_x)
    ln_f, lt_f = transformer.transform(lon_c, lat_c)
    
    # --- CONFIGURACIÓN DE CAPAS (VISTA REAL) ---
    m = folium.Map(location=[lt_f, ln_f], zoom_start=15, tiles=None) # Empezamos vacío

    # Añadimos la capa de Satélite (ESRI)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Vista Satélite Real',
        overlay=False,
        control=True
    ).add_to(m)

    # Añadimos la capa de Mapa Callejero (CartoDB)
    folium.TileLayer(
        tiles='CartoDB positron',
        name='Mapa Callejero',
        overlay=False,
        control=True
    ).add_to(m)

    # 2. CREAR EL GRUPO DE MARCADORES
    marker_cluster = MarkerCluster(name="Predicciones Arqueológicas").add_to(m)

    # Escaneo (Paso ajustado para Trigueros)
    paso = 130 
    for f in range(0, ds.height, paso):
        for c in range(0, ds.width, paso):
            f_r = max(0, min(f + random.randint(-15, 15), ds.height - 1))
            c_r = max(0, min(c + random.randint(-15, 15), ds.width - 1))

            altitud = altitudes[f_r, c_r]
            pendiente = mapa_pendientes[f_r, c_r]

            query = f"evaluar({pendiente:.2f}, {altitud:.2f}, Probabilidad)"
            res = list(prolog.query(query))
            
            if res and res[0]["Probabilidad"] == 'Alta':
                x_utm, y_utm = ds.xy(f_r, c_r)
                lon, lat = transformer.transform(x_utm, y_utm)
                
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>Probabilidad Alta</b><br>Pendiente: {pendiente:.2f}%",
                    icon=folium.Icon(color="red", icon="screenshot")
                ).add_to(marker_cluster)

    # --- ACTIVAR EL SELECTOR DE VISTAS ---
    folium.LayerControl().add_to(m)

    m.save("mapa_satelite_huelva.html")
    print("✅ ¡Mapa con vista satélite generado!")