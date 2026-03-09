import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "01dgu24f1043": {"nama": "Ahmad", "pwd": "12345"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "Nafiz0921"},
        "pensyarah": {"nama": "Dr. Surveyor", "pwd": "jka123"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    return f"{d}°{m:02d}'{s:02d}\""

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
                st.session_state["user_id"] = user_id
                st.session_state["user_name"] = db[user_id]["nama"]
                st.rerun()
            else:
                st.error("ID atau Kata Laluan salah")
else:
    if st.sidebar.button("🚪 Log Keluar"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("POLITEKNIK UNGKU OMAR")
    st.subheader(f"Unit Geomatik - Selamat Datang, {st.session_state['user_name'].upper()}")
    
    uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])
    size_stn = st.sidebar.slider("Saiz No Stesen", 8, 20, 10)
    size_brg = st.sidebar.slider("Saiz Teks", 6, 15, 9)
    # Kita kunci gap supaya tak sentuh
    text_gap_val = st.sidebar.slider("Jarak Teks (Gap)", 35, 60, 42)
    epsg_input = st.sidebar.text_input("Kod EPSG", "4390")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            
            center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite', max_zoom=22, max_native_zoom=20).add_to(m)

            points = []
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                points.append([p1['lat'], p1['lon']])
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist, brg_deg = np.sqrt(dE**2 + dN**2), np.degrees(np.arctan2(dE, dN)) % 360
                text_angle = brg_deg - 90
                if 90 < brg_deg < 270: text_angle -= 180 
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

                half_gap = text_gap_val / 2
                label_html = f'''
                    <div style="transform: rotate({text_angle}deg); display: flex; flex-direction: column; justify-content: space-between; align-items: center; color: #00FFFF; font-weight: bold; font-size: {size_brg}pt; text-shadow: 1px 1px 2px black; text-align: center; width: 160px; margin-left: -80px; pointer-events: none; height: {text_gap_val}px; margin-top: -{half_gap}px;">
                        <div style="white-space: nowrap; line-height: 1; margin-bottom: 6px;">{decimal_to_dms(brg_deg)}</div>
                        <div style="white-space: nowrap; line-height: 1; margin-top: 6px;">{dist:.3f}m</div>
                    </div>'''
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=label_html)).add_to(m)
                folium.Marker([p1['lat'], p1['lon']], icon=folium.DivIcon(html=f'<div style="color:white; font-weight:bold; font-size:{size_stn}pt; text-shadow: 1px 1px 2px black;">{int(p1["STN"])}</div>')).add_to(m)

            folium.Polygon(locations=points, color='yellow', weight=2, fill=True, fill_opacity=0.1).add_to(m)
            st_folium(m, width="100%", height=700)
        except Exception as e:
            st.error(f"Ralat: {e}")
