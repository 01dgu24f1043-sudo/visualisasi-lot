import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- FUNGSI DMS ---
def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- LOGIN SESSION (Sama seperti sebelum ini) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # (Kod login_page anda di sini)
    user_id = st.text_input("ID Pengguna")
    user_pwd = st.text_input("Kata Laluan", type="password")
    if st.button("Masuk"):
        if user_id == "01dgu24f1043" and user_pwd == "12345": # Contoh simple
            st.session_state["logged_in"] = True
            st.rerun()
else:
    # --- INTERFACE UTAMA ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])
    
    size_stn = st.sidebar.slider("Saiz No Stesen", 8, 20, 10)
    size_brg = st.sidebar.slider("Saiz Teks (Bearing/Jarak)", 6, 15, 8)
    epsg_input = st.sidebar.text_input("Kod EPSG", "4390")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            # 1. Transformasi Koordinat
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            
            # 2. Bina Peta Folium
            center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)
            
            # Layer Satelit Google
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google', name='Google Satellite', overlay=False, control=True
            ).add_to(m)

            points = []
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                loc1 = [p1['lat'], p1['lon']]
                loc2 = [p2['lat'], p2['lon']]
                points.append(loc1)

                # Kira Bearing & Jarak
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg_deg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # Sudut putaran CSS (Sengek ikut garisan)
                text_angle = brg_deg - 90
                if 90 < brg_deg < 270: text_angle -= 180 

                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

                # 3. Gabungkan Teks Senget ke atas Peta
                label_html = f'''
                    <div style="transform: rotate({text_angle}deg); 
                                color: #00FFFF; font-weight: bold; font-size: {size_brg}pt;
                                text-shadow: 1px 1px 2px black; text-align: center;">
                        {decimal_to_dms(brg_deg)}<br>{dist:.3f}m
                    </div>'''
                
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=label_html)).add_to(m)
                
                # Marker Stesen
                stn_html = f'<div style="color:white; font-weight:bold; font-size:{size_stn}pt;">{int(p1["STN"])}</div>'
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_html)).add_to(m)

            # Lukis Poligon Lot
            folium.Polygon(locations=points, color='yellow', weight=3, fill=True, fill_opacity=0.1).add_to(m)

            st.subheader("🗺️ Peta Lot Gabungan (Satelit + Teks Senget)")
            st_folium(m, width=1100, height=600)

        except Exception as e:
            st.error(f"Ralat: {e}")
