import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import io

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "01dgu24f1043": {"nama": "Ahmad", "pwd": "12345"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "Nafiz0921"},
        "pensyarah": {"nama": "Dr. Surveyor", "pwd": "jka123"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI PEMBANTU ---
def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- FUNGSI LOGIN ---
def login_page():
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

# --- LOGIK UTAMA ---
if not st.session_state["logged_in"]:
    login_page()
else:
    if st.sidebar.button("🚪 Log Keluar"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("POLITEKNIK UNGKU OMAR")
    st.subheader(f"Unit Geomatik - Selamat Datang, {st.session_state['user_name'].upper()}")
    st.markdown("---")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

    st.sidebar.header("🛠️ Tetapan Paparan")
    size_stn = st.sidebar.slider("Saiz No Stesen", 8, 20, 10)
    size_brg = st.sidebar.slider("Saiz Teks (Bearing/Jarak)", 6, 15, 9)
    # Slider untuk jarak teks dari garisan (Gap Control)
    text_gap = st.sidebar.slider("Jarak Teks (Gap)", 30, 60, 46) 
    epsg_input = st.sidebar.text_input("Kod EPSG (Semenanjung: 4390)", "4390")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            # 1. Transformasi Koordinat
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            
            # 2. Bina Peta Folium (Super Zoom)
            center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
            
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google', name='Google Satellite', overlay=False, control=True,
                max_zoom=22, max_native_zoom=20
            ).add_to(m)

            points = []
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                loc1, loc2 = [p1['lat'], p1['lon']], [p2['lat'], p2['lon']]
                points.append(loc1)

                # Kira Bearing & Jarak
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg_deg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # Sudut putaran CSS
                text_angle = brg_deg - 90
                if 90 < brg_deg < 270: text_angle -= 180 

                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

                # 3. Label Bearing (ATAS) & Jarak (BAWAH) dengan "No-Touch Gap"
                # margin-top mestilah separuh daripada text_gap untuk center
                half_gap = text_gap / 2
                
                label_html = f'''
                    <div style="transform: rotate({text_angle}deg); 
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                                color: #00FFFF; 
                                font-weight: bold; 
                                font-size: {size_brg}pt;
                                text-shadow: 1px 1px 3px black; 
                                text-align: center;
                                width: 160px; 
                                margin-left: -80px;
                                pointer-events: none;
                                height: {text_gap}px; 
                                margin-top: -{half_gap}px;
                                ">
                        <div style="white-space: nowrap;">{decimal_to_dms(brg_deg)}</div>
                        <div style="white-space: nowrap;">{dist:.3f}m</div>
                    </div>'''
                
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=label_html)).add_to(m)
                
                # Label No Stesen
                stn_html = f'''<div style="color:white; font-weight:bold; font-size:{size_stn}pt; 
                                text-shadow: 1px 1px 2px black; pointer-events: none;">{int(p1["STN"])}</div>'''
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_html)).add_to(m)

            # 4. Lukis Poligon
            folium.Polygon(locations=points, color='yellow', weight=2, fill=True, fill_color='yellow', fill_opacity=0.15).add_to(m)

            st.subheader("🗺️ Peta Lot Gabungan (Clean Label Design)")
            st_folium(m, width="100%", height=700)

            # Info Luas
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            st.success(f"📐 **Luas Lot:** {area:.3f} m² | {(area/4046.856):.4f} Ekar")

        except Exception as e:
            st.error(f"Ralat: {e}. Semak kolum STN, E, N dalam fail CSV anda.")
    else:
        st.info("Sila muat naik fail CSV untuk melihat paparan lot.")
