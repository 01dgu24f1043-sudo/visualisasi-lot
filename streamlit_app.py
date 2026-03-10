import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import json
from folium.plugins import Fullscreen

# --- TETAPAN ASAS HALAMAN ---
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "1": {"nama": "Admin", "pwd": "123"},
        "01dgu24f1043": {"nama": "Alif", "pwd": "123"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "123"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI PEMBANTU ---
def decimal_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    if m >= 60: m = 0; d += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- PENGURUSAN LOGIN ---
if not st.session_state["logged_in"]:
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        user_id = st.text_input("ID Pengguna")
        user_pwd = st.text_input("Kata Laluan", type="password")
        if st.button("Masuk", use_container_width=True):
            db = st.session_state["user_db"]
            if user_id in db and db[user_id]["pwd"] == user_pwd:
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = db[user_id]["nama"]
                st.rerun()
            else: st.error("ID/Password Salah")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👋 Hi, {st.session_state['user_name']}")
    uploaded_file = st.file_uploader("📂 Upload CSV (STN, E, N)", type=["csv"])
    
    st.header("⚙️ Tetapan")
    epsg_input = st.text_input("Kod EPSG (cth: 4390)", "4390")
    show_satellite = st.toggle("Imej Satelit", value=True)
    
    if st.button("🚪 Log Keluar", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- HEADER ---
st.markdown("<h1 style='text-align:center;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Sistem Visualisasi Lot & Eksport QGIS</h3>", unsafe_allow_html=True)
st.divider()

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        # Transformasi Koordinat
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        
        # Setup Map
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19)
        if show_satellite:
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                             attr='Google', name='Google Satellite', max_zoom=22).add_to(m)
        
        points = []
        features = []
        total_dist = 0
        
        # Pengiraan Area
        area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

        for i in range(len(df)):
            p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
            loc1, loc2 = [p1['lat'], p1['lon']], [p2['lat'], p2['lon']]
            points.append(loc1)

            # Kira Bearing & Jarak
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            total_dist += dist
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # --- GEOJSON: TITIK STESEN ---
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p1['lon'], p1['lat']]},
                "properties": {"Label": f"STN {int(p1['STN'])}", "Type": "Station", "E": p1['E'], "N": p1['N']}
            })

            # --- GEOJSON: GARISAN (BEARING/JARAK) ---
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]},
                "properties": {"Label": f"{decimal_to_dms(brg)} | {dist:.3f}m", "Type": "Boundary"}
            })

            # Folium Markers
            folium.CircleMarker(loc1, radius=5, color='red', fill=True).add_to(m)
            folium.Marker(loc1, icon=folium.DivIcon(html=f'<div style="font-size:12pt; color:white; font-weight:bold;">{int(p1["STN"])}</div>')).add_to(m)

        # --- GEOJSON: POLIGON (LUAS) ---
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]},
            "properties": {"Label": f"LUAS: {area:.3f} m2", "Type": "Area", "Perimeter": total_dist}
        })

        folium.Polygon(locations=points, color="cyan", weight=3, fill=True, fill_opacity=0.2).add_to(m)
        
        # Papar Map
        st_folium(m, width="100%", height=600)

        # Tombol Download
        geojson_data = {"type": "FeatureCollection", "features": features}
        st.sidebar.download_button("📥 Muat Turun Fail QGIS", json.dumps(geojson_data, indent=4), "lot_puo_auto.geojson", use_container_width=True)

    except Exception as e:
        st.error(f"Sila pastikan format CSV betul (STN, E, N). Ralat: {e}")
