import os
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster
import rasterio
import numpy as np
from pyproj import Transformer
from pyswip import Prolog
import json
if 'DYLD_LIBRARY_PATH' not in os.environ:
    os.environ['SWI_HOME_DIR'] = '/usr/lib/swi-prolog'
from scipy.ndimage import gaussian_gradient_magnitude

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="IA Arqueológica Huelva")
st.title("🏛️ Sistema Arqueológico Inteligente - Trigueros")

DB_PUNTOS = "puntos_guardados.json"

# --- PERSISTENCIA ---
def cargar_puntos_disco():
    if os.path.exists(DB_PUNTOS):
        with open(DB_PUNTOS, "r") as f: return json.load(f)
    return []

def guardar_punto_disco(punto):
    puntos = cargar_puntos_disco()
    puntos.append(punto)
    with open(DB_PUNTOS, "w") as f: json.dump(puntos, f)

# 1. INICIALIZAR PROLOG
if 'prolog' not in st.session_state:
    st.session_state.prolog = Prolog()
    if os.path.exists("motor.pl"):
        with open("motor.pl", "r", encoding="utf-8", errors="ignore") as f:
            reglas = f.read()
        with open("motor_utf8.pl", "w", encoding="utf-8") as f:
            f.write(reglas)
        st.session_state.prolog.consult("motor_utf8.pl")
    
    st.session_state.puntos_confirmados = cargar_puntos_disco()
    for p in st.session_state.puntos_confirmados:
        st.session_state.prolog.assertz(f"hecho_confirmado({p['p']:.2f}, {p['a']:.2f}, 'Si')")
        if 'hallazgo' in p:
            hallazgo_pl = p['hallazgo'].replace(" ", "_").lower()
            st.session_state.prolog.assertz(f"hallazgo_registrado({p['p']:.2f}, {p['a']:.2f}, '{hallazgo_pl}')")

# 2. CARGAR DATOS (MDT)
@st.cache_resource
def obtener_datos_estables():
    ruta = os.path.join("..", "datos", "mdt", "MDT02-ETRS89-HU29-0982-3-COB2.tif")
    if not os.path.exists(ruta):
        st.error(f"No se encuentra el archivo: {ruta}")
        st.stop()
        
    with rasterio.open(ruta) as ds:
        alt = ds.read(1)
        alt[alt < -100] = np.mean(alt[alt > -100])
        grad = gaussian_gradient_magnitude(alt, sigma=1)
        pend = (grad / ds.res[0]) * 100
        to_latlon = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
        to_utm = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
        centro_y, centro_x = ds.height // 2, ds.width // 2
        ln, lt = to_latlon.transform(*ds.xy(centro_y, centro_x))
        return alt, pend, ds.transform, ds.crs, (lt, ln), ds.height, ds.width, to_utm, to_latlon

alt, pend, trans, crs, centro, h, w, to_utm, to_latlon = obtener_datos_estables()

# 3. INTERFAZ EN COLUMNAS
col_mapa, col_info = st.columns([3, 1])

with col_mapa:
    m = folium.Map(location=centro, zoom_start=15, tiles="CartoDB positron")
  
    folium.plugins.LocateControl(
        keepCurrentZoomLevel=True,
        flyTo=True
    ).add_to(m)

    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                     attr='Esri', name='Satélite Real').add_to(m)

    cluster = MarkerCluster(name="Predicciones IA").add_to(m)

    for p in st.session_state.puntos_confirmados:
        folium.Marker(
            location=[p['lat'], p['lon']], 
            icon=folium.Icon(color="green", icon="star"),
            popup=f"Hallazgo: {p.get('hallazgo', 'Verificado')}"
        ).add_to(m)

    paso = 300 
    for f in range(0, h, paso):
        for c in range(0, w, paso):
            a_p, p_p = alt[f, c], pend[f, c]
            query = f"interpretar({p_p:.2f}, {a_p:.2f}, Pr, E, Ex)"
            try:
                q = st.session_state.prolog.query(query)
                res = list(q); q.close()
                if res and res[0]["Pr"] in ['Alta', 'Media-Alta', 'Muy Alta']:
                    x_m = trans[2] + c * trans[0]
                    y_m = trans[5] + f * trans[4]
                    lon, lat = to_latlon.transform(x_m, y_m)
                    folium.Marker(
                        location=[lat, lon], 
                        icon=folium.Icon(color="red", icon="info-sign"),
                        popup=f"<b>IA: {res[0]['E']}</b>"
                    ).add_to(cluster)
            except: continue

    folium.LayerControl().add_to(m)
    output = st_folium(m, width=900, height=600, key="mapa_v_final", 
                       returned_objects=["last_clicked", "last_object_clicked"])

# 4. PANEL DE CONTROL, ANÁLISIS Y APRENDIZAJE
punto_analizar = None
if output:
    if output.get("last_object_clicked"): punto_analizar = output["last_object_clicked"]
    elif output.get("last_clicked"): punto_analizar = output["last_clicked"]

with col_info:
    st.subheader("Panel de Control")
    
    if punto_analizar:
        lat_c, lon_c = punto_analizar["lat"], punto_analizar["lng"]
        
        try:
            # Transformación y validación de límites
            x_u, y_u = to_utm.transform(lon_c, lat_c)
            from rasterio.transform import rowcol
            row, col = rowcol(trans, x_u, y_u)
            
            if 0 <= row < h and 0 <= col < w:
                v_alt = alt[row, col]
                v_pend = pend[row, col]

                st.markdown("---")
                st.write(f"**Coordenadas:** `{lat_c:.5f}, {lon_c:.5f}`")
                
                # Consulta de Inteligencia Artificial
                query = f"interpretar({v_pend:.2f}, {v_alt:.2f}, Pr, E, Ex)"
                q = st.session_state.prolog.query(query)
                res = list(q); q.close()
                
                if res:
                    st.metric("Probabilidad", res[0]['Pr'])
                    st.write(f"**Época Sugerida:** {res[0]['E']}")
                    st.info(f"**Análisis:** {res[0]['Ex']}")
                    st.write(f"⛰️ {v_alt:.1f}m | 📐 {v_pend:.1f}%")

                # --- SECCIÓN DE REGISTRO PARA APRENDIZAJE ---
                st.markdown("### 🏺 Registrar Hallazgo")
                tipo_resto = st.selectbox("¿Qué has encontrado?", 
                                         ["Ceramica Romana", "Tegula (Ladrillo)", "Silex/Piedra tallada", "Estructura/Muro", "Moneda", "Otro"])
                comentario = st.text_input("Nota adicional (opcional)")

                if st.button("✅ Confirmar y Entrenar IA"):
                    nuevo_p = {
                        'lat': lat_c, 'lon': lon_c, 
                        'a': float(v_alt), 'p': float(v_pend),
                        'hallazgo': tipo_resto, 'nota': comentario
                    }
                    if nuevo_p not in st.session_state.puntos_confirmados:
                        st.session_state.puntos_confirmados.append(nuevo_p)
                        guardar_punto_disco(nuevo_p)
                        
                        # Inyección de conocimiento dinámico en Prolog
                        hallazgo_pl = tipo_resto.replace(" ", "_").lower()
                        st.session_state.prolog.assertz(f"hallazgo_registrado({v_pend:.2f}, {v_alt:.2f}, '{hallazgo_pl}')")
                        st.session_state.prolog.assertz(f"hecho_confirmado({v_pend:.2f}, {v_alt:.2f}, 'Si')")
                        
                        st.success("¡Punto guardado y IA actualizada!")
                        st.rerun()
            else:
                st.warning("El punto seleccionado está fuera del área de datos LIDAR.")
                st.caption(f"Límites del mapa: Fila {row}, Col {col}")
        except Exception as e:
            st.error(f"Error en el procesamiento: {e}")
    else:
        st.write("Haz click en un punto rojo o en el terreno para analizar y registrar hallazgos.")

    st.divider()
    if st.button("🗑️ Resetear Memoria IA"):
        if os.path.exists(DB_PUNTOS): os.remove(DB_PUNTOS)
        st.session_state.puntos_confirmados = []
        st.rerun()