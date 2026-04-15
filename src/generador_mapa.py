import rasterio
from pyproj import Transformer
import folium
from pyswip import Prolog
import os

# 1. Configuración de Prolog
prolog = Prolog()
prolog.consult("motor.pl")

# 2. Configuración del Mapa
archivo_mdt = os.path.join("..", "datos", "mdt", "MDT02-ETRS89-HU29-0982-3-COB2.tif")

with rasterio.open(archivo_mdt) as ds:
    # Obtenemos el centro del mapa para situar la cámara de Google Maps
    centro_y, centro_x = ds.height // 2, ds.width // 2
    lon_centro, lat_centro = ds.xy(centro_y, centro_x)
    
    # Transformador de coordenadas (De UTM/ETRS89 a Latitud/Longitud de Google Maps)
    transformer = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
    ln_c, lt_c = transformer.transform(lon_centro, lat_centro)

    # Creamos el mapa base (Estilo Google Maps)
    m = folium.Map(location=[lt_c, ln_c], zoom_start=13, tiles="OpenStreetMap")

    print("Analizando zonas de interés en Trigueros...")

    # 3. Escaneo de puntos (Vamos a analizar una rejilla de puntos para no saturar)
    paso = 500 # Analiza un punto cada 500 píxeles
    for f in range(0, ds.height, paso):
        for c in range(0, ds.width, paso):
            # Leer altitud
            ventana = ds.read(1, window=((f, f+1), (c, c+1)))
            altitud = ventana[0, 0]
            
            # Simulamos cálculo de pendiente (simplificado para el mapa completo)
            pendiente = 2.0 # Aquí podrías integrar el cálculo real del script anterior
            
            # Consultar a Prolog
            query = f"evaluar({pendiente}, {altitud}, Probabilidad)"
            res = list(prolog.query(query))
            
            if res and res[0]["Probabilidad"] == 'Alta':
                # Convertir coordenadas del mapa a coordenadas reales (Lat/Lon)
                x_utm, y_utm = ds.xy(f, c)
                lon, lat = transformer.transform(x_utm, y_utm)
                
                # Añadir marcador al mapa
                folium.Marker(
                    location=[lat, lon],
                    popup=f"Probabilidad ALTA\nAltitud: {altitud:.2f}m",
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)

    # 4. Guardar el resultado
    ruta_salida = "mapa_arqueologico_huelva.html"
    m.save(ruta_salida)
    print(f"✅ Mapa generado con éxito: {os.path.abspath(ruta_salida)}")