import os
import streamlit as st
import json
import rasterio
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, LocateControl
from pyproj import Transformer
from scipy.ndimage import gaussian_gradient_magnitude
import geopandas as gpd  # Nueva librería para hidrografía
from shapely.geometry import Point # Para cálculos espaciales

# --- Función para cargar la red hídrica ---
@st.cache_resource
def cargar_hidrografia():
    try:
        # Intentamos cargar la capa de líneas (ríos)
        ruta_rios = "datos/vectores/hidrografia/BTN0302L_RIO.shp"
        if os.path.exists(ruta_rios):
            rios = gpd.read_file(ruta_rios)
            # Aseguramos que use coordenadas geográficas (WGS84)
            rios = rios.to_crs(epsg=4326)
            return rios
        else:
            return None
    except Exception as e:
        st.error(f"Error al cargar ríos: {e}")
        return None

# Llamamos a la función al inicio
gdf_rios = cargar_hidrografia()

# --- 1. CONFIGURACIÓN DE ENTORNO PARA PROLOG ---
if 'SWI_HOME_DIR' not in os.environ:
    if os.path.exists('/usr/lib/swi-prolog'): 
        os.environ['SWI_HOME_DIR'] = '/usr/lib/swi-prolog'

try:
    from pyswip import Prolog
except ImportError:
    st.error("Error crítico: No se ha podido cargar la librería PySwip.")

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="IA Arqueológica Huelva")
st.title("🏛️ Sistema Arqueológico Inteligente - Trigueros")

DB_PUNTOS = "puntos_guardados.json"

# --- 3. FUNCIONES DE PERSISTENCIA ---
def cargar_puntos_disco():
    if os.path.exists(DB_PUNTOS):
        with open(DB_PUNTOS, "r") as f: return json.load(f)
    return []

def guardar_punto_disco(punto):
    puntos = cargar_puntos_disco()
    puntos.append(punto)
    with open(DB_PUNTOS, "w") as f: json.dump(puntos, f)

# --- 4. INICIALIZAR MOTOR PROLOG ---
if 'prolog' not in st.session_state:
    try:
        st.session_state.prolog = Prolog()
        ruta_motor = os.path.join(os.path.dirname(__file__), "motor.pl")
        
        if os.path.exists(ruta_motor):
            with open(ruta_motor, "r", encoding="utf-8", errors="ignore") as f:
                reglas = f.read()
            with open("motor_utf8.pl", "w", encoding="utf-8") as f:
                f.write(reglas)
            
            st.session_state.prolog.consult("motor_utf8.pl")
            
            st.session_state.puntos_confirmados = cargar_puntos_disco()
            for p in st.session_state.puntos_confirmados:
                st.session_state.prolog.assertz(f"hecho_confirmado({p['p']:.2f}, {p['a']:.2f}, 'Si')")
        else:
            st.error("No se encontró motor.pl")
    except Exception as e:
        st.error(f"Error al inicializar Prolog: {e}")

# --- 5. LÓGICA MULTIZONA Y SELECCIÓN ---
@st.cache_resource
def obtener_datos_estables(nombre_archivo):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(BASE_DIR, "datos", "mdt", nombre_archivo)

    if not os.path.exists(ruta):
        st.error(f"Archivo no encontrado: {ruta}")
        st.stop()
        
    with rasterio.open(ruta) as ds:
        alt = ds.read(1, out_shape=(ds.height // 2, ds.width // 2), 
                      resampling=rasterio.enums.Resampling.bilinear)
        alt[alt < -100] = np.mean(alt[alt > -100])
        grad = gaussian_gradient_magnitude(alt, sigma=1)
        pend = (grad / ds.res[0]) * 100
        
        to_latlon = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
        to_utm = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
        
        centro_y, centro_x = ds.height // 2, ds.width // 2
        ln, lt = to_latlon.transform(*ds.xy(centro_y, centro_x))
        
        return alt, pend, ds.transform, ds.crs, (lt, ln), ds.height//2, ds.width//2, to_utm, to_latlon

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
carpeta_mdt = os.path.join(BASE_DIR, "datos", "mdt")
mapas_encontrados = [f for f in os.listdir(carpeta_mdt) if f.endswith('.tif')]

with st.sidebar:
    st.header("Configuración de Zona")
    if mapas_encontrados:
        mapa_seleccionado = st.selectbox("Seleccionar Hoja MDT", mapas_encontrados)
        st.divider()
        st.subheader("Análisis de Campo")
        precision = st.slider("Densidad de escaneo (paso)", 50, 500, 200, 50)
        
        # Nueva visualización: Mostrar si los ríos están cargados
        if gdf_rios is not None:
            st.success("🛰️ Capa de Hidrografía activa")
        else:
            st.warning("⚠️ Sin datos de ríos")
    else:
        st.error("No se encontraron archivos .tif")
        st.stop()

alt, pend, trans, crs, centro, h, w, to_utm, to_latlon = obtener_datos_estables(mapa_seleccionado)

# --- 6. INTERFAZ ---
col_mapa, col_info = st.columns([3, 1])

with col_mapa:
    m = folium.Map(location=centro, zoom_start=15, tiles="CartoDB positron")
    LocateControl(keepCurrentZoomLevel=True, flyTo=True).add_to(m)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
        attr='Esri', name='Satélite Real'
    ).add_to(m)

    cluster = MarkerCluster(name="Predicciones IA").add_to(m)

    # Marcadores de hallazgos guardados
    for p in st.session_state.puntos_confirmados:
        folium.Marker(
            location=[p['lat'], p['lon']], 
            icon=folium.Icon(color="green", icon="star")
        ).add_to(m)

    # Escaneo automático (IA actual)
    paso = precision 
    for f in range(0, h, paso):
        for c in range(0, w, paso):
            a_p, p_p = alt[f, c], pend[f, c]
            # Como el escáner no calcula distancia para cada punto (sería muy lento), le pasamos un 9999 (lejos)
            query = f"interpretar({p_p:.2f}, {a_p:.2f}, 9999, Pr, E, Ex)"
            try:
                q = st.session_state.prolog.query(query)
                res = list(q); q.close()
                if res and res[0]["Pr"] in ['Alta', 'Media-Alta', 'Muy Alta']:
                    x_m = trans[2] + (c * 2) * trans[0]
                    y_m = trans[5] + (f * 2) * trans[4]
                    lon_p, lat_p = to_latlon.transform(x_m, y_m)
                    folium.Marker(
                        location=[lat_p, lon_p], 
                        icon=folium.Icon(color="red", icon="info-sign"),
                        popup=f"IA: {res[0]['E']}"
                    ).add_to(cluster)
            except: continue

    folium.LayerControl().add_to(m)
    output = st_folium(
        m, width=900, height=600, 
        key=f"mapa_{mapa_seleccionado}", 
        returned_objects=["last_clicked", "last_object_clicked"]
    )

# --- 7. PANEL DE CONTROL E INTELIGENCIA HÍDRICA ---
punto_analizar = None
if output:
    if output.get("last_object_clicked"): punto_analizar = output["last_object_clicked"]
    elif output.get("last_clicked"): punto_analizar = output["last_clicked"]

with col_info:
    st.subheader("Panel de Control")
    if punto_analizar:
        lat_c, lon_c = punto_analizar["lat"], punto_analizar["lng"]
        
        # --- CÁLCULO DISTANCIA AL AGUA (CORREGIDO PROFESIONAL) ---
       # --- CÁLCULO DISTANCIA AL AGUA (CORREGIDO Y SIN ERRORES) ---
        distancia_agua = 9999  # Valor por defecto
        
        if gdf_rios is not None:
            try:
                # 1. Creamos el punto con el clic (WGS84)
                punto_geo = gpd.GeoSeries([Point(lon_c, lat_c)], crs="EPSG:4326")
                
                # 2. Proyectamos a metros (UTM 30N para Huelva) para que la distancia sea real
                punto_metros = punto_geo.to_crs(epsg=25830)
                rios_metros = gdf_rios.to_crs(epsg=25830)
                
                # 3. Calculamos la distancia mínima en metros
                distancia_agua = rios_metros.distance(punto_metros.iloc[0]).min()
            except Exception as e:
                st.sidebar.error(f"Error en cálculo hídrico: {e}")
        
        try:
            x_u, y_u = to_utm.transform(lon_c, lat_c)
            from rasterio.transform import rowcol
            row, col = rowcol(trans, x_u, y_u)
            row_red, col_red = row // 2, col // 2

            if 0 <= row_red < h and 0 <= col_red < w:
                v_alt = alt[row_red, col_red]
                v_pend = pend[row_red, col_red]

                st.markdown("---")
                st.write(f"📍 `{lat_c:.5f}, {lon_c:.5f}`")
                
                # Mostramos la nueva métrica en el panel
                if distancia_agua < 1000:
                    st.write(f"💧 **Distancia al río:** {distancia_agua:.0f} metros")
                else:
                    st.write(f"💧 **Distancia al río:** >1 km")

                # Consulta a Prolog (Próximo paso: pasar distancia_agua a Prolog)
               # Busca esta línea y cámbiala (añade distancia_agua)
                query = f"interpretar({v_pend:.2f}, {v_alt:.2f}, {distancia_agua:.2f}, Pr, E, Ex)"
                q = st.session_state.prolog.query(query)
                res = list(q); q.close()
                
                if res:
                    st.metric("Probabilidad", res[0]['Pr'])
                    st.info(f"**Análisis:** {res[0]['Ex']}")
                    st.write(f"⛰️ {v_alt:.1f}m | 📐 {v_pend:.1f}%")

                st.markdown("### 🏺 Registrar Hallazgo")
                tipo_resto = st.selectbox("Hallazgo:", ["Ceramica Romana", "Tegula (Ladrillo)", "Moneda", "Estructura/Muro", "Otro"])
                
                if st.button("✅ Guardar"):
                    nuevo_p = {'lat': lat_c, 'lon': lon_c, 'a': float(v_alt), 'p': float(v_pend), 'hallazgo': tipo_resto}
                    st.session_state.puntos_confirmados.append(nuevo_p)
                    guardar_punto_disco(nuevo_p)
                    st.success("Guardado localmente")
                    st.rerun()
            else:
                st.warning("Fuera de mapa.")
        except Exception as e:
            st.error(f"Error técnico: {e}")
    else:
        st.write("Selecciona un punto en el mapa para analizar.")

    if st.button("🗑️ Reset"):
        if os.path.exists(DB_PUNTOS): os.remove(DB_PUNTOS)
        st.session_state.puntos_confirmados = []
        st.rerun()