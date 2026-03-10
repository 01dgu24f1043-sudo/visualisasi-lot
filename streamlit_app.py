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

# --- DATABASE PENGGUNA (SIMULASI) ---
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
    if s >= 60: 
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- HALAMAN RESET PASSWORD ---
if st.session_state.get("reset_mode", False):
    st.markdown("### 🔑 Set Semula Kata Laluan")
    uid = st.text_input("ID untuk set semula")
    new_pwd = st.text_input("Kata Laluan Baru", type="password")
    if st.button("Simpan"):
        if uid in st.session_state["user_db"]:
            st.session_state["user_db"][uid]["pwd"] = new_pwd
            st.success("Berjaya! Sila log masuk.")
            st.session_state["reset_mode"] = False
            st.rerun()
        else: 
            st.error("ID tidak sah")
    if st.button("Batal"):
        st.session_state["reset_mode"] = False
        st.rerun()
    st.stop()

# --- HALAMAN LOGIN ---
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
                st.error("ID/Password Salah")
        if st.button("Lupa Kata Laluan?"):
            st.session_state["reset_mode"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR (LOGO DI ATAS SEKALI) ---
with st.sidebar:
    try:
        # Logo PUO diletakkan di sini
        st.image("politeknik-ungku-umar-seeklogo-removebg-preview.png", use_container_width=True)
    except:
        st.warning("⚠️ Fail logo tidak dijumpai dalam direktori.")
    
    st.markdown(f"<h3 style='text-align:center;'>👋 Hi, {st.session_state['user_name']}</h3>", unsafe_allow_html=True)
    st.divider()

    uploaded_file = st.file_uploader("📂 Upload CSV (STN, E, N)", type=["csv"])

    st.header("👁️ Kawalan Paparan")
    show_satellite = st.toggle("Paparkan Imej Satelit", value=True)
    show_stn = st.checkbox("Paparkan No Stesen", value=True)
    show_brg = st.checkbox("Paparkan Bearing/Jarak", value=True)
    show_poly = st.checkbox("Paparkan Poligon & Luas", value=True)

    st.header("🛠️ Tetapan Teks")
    size_stn = st.slider("Saiz No Stesen", 8, 30, 12)
    size_brg = st.slider("Saiz Bearing/Jarak", 6, 25, 10)
    text_gap = st.slider("Keluasan Gap Teks", 20, 100, 45)
    epsg_input = st.text_input("Kod EPSG (cth: 4390)", "4390")

    st.divider()
    if st.button("🚪 Log Keluar", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- HEADER HALAMAN UTAMA ---
st.markdown("""
    <div style="text-align: center;">
        <h1 style='margin-bottom: 0px;'>POLITEKNIK UNGKU OMAR</h1>
        <h3 style='margin-top: 0px; color: #555;'>Unit Geomatik - Sistem Visualisasi Lot</h3>
    </div>
""", unsafe_allow_html=True)
st.divider()

# --- LOGIK PEMPROSESAN DATA & PETA ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        # Semakan lajur wajib
        if not {'STN', 'E', 'N'}.issubset(df.columns):
            st.error("Ralat: Fail CSV mesti mempunyai lajur STN, E, dan N.")
            st.stop()

        # Penukaran Koordinat (Projected -> WGS84)
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
        
        # Cipta Peta Folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
        
        if show_satellite:
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                attr='Google Satellite', name='Google Satellite', max_zoom=22, max_native_zoom=20
            ).add_to(m)
        else:
            folium.TileLayer('OpenStreetMap', name='Peta Dasar').add_to(m)
        
        Fullscreen(position="topright").add_to(m)

        points = []
        total_dist = 0
        
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            loc1 = [p1['lat'], p1['lon']]
            loc2 = [p2['lat'], p2['lon']]
            points.append(loc1)

            # Pengiraan Bearing & Jarak (Satah)
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            total_dist += dist
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Marker Stesen
            stn_info = f"<b>STESEN {int(p1['STN'])}</b><br>N: {p1['N']:.3f}<br>E: {p1['E']:.3f}"
            folium.CircleMarker(
                location=loc1, radius=5, color='red', fill=True, fill_color='white',
                popup=folium.Popup(stn_info, max_width=200)
            ).add_to(m)

            # Label No Stesen
            if show_stn:
                stn_txt = f'''<div style="color:white; font-weight:bold; font-size:{size_stn}pt; text-shadow: 2px 2px 3px black; pointer-events:none;">{int(p1["STN"])}</div>'''
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_txt, icon_anchor=(0,0))).add_to(m)

            # Label Bearing & Jarak
            if show_brg:
                calc_angle = brg - 90
                if 90 < brg < 270:
                    calc_angle -= 180 # Supaya teks tidak terbalik
                
                h_gap = text_gap / 2
                l_html = f'''<div style="transform: rotate({calc_angle}deg); display: flex; flex-direction: column; justify-content: space-between; align-items: center; color: #00FFFF; font-weight: bold; font-size: {size_brg}pt; text-shadow: 2px 2px 4px black; width: 200px; margin-left: -100px; height: {text_gap}px; margin-top: -{h_gap}px; pointer-events: none; text-align: center;">
                    <div style="padding-bottom:2px;">{decimal_to_dms(brg)}</div>
                    <div style="padding-top:2px; color: #FFD700;">{dist:.3f}m</div>
                </div>'''
                
                mid_point = [(p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2]
                folium.Marker(mid_point, icon=folium.DivIcon(html=l_html)).add_to(m)

        # Pengiraan Luas (Formula Shoelace)
        area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
        
        if show_poly:
            poly_info = f"<b>INFO LOT</b><hr>Luas: {area:.3f} m²<br>Perimeter: {total_dist:.3f} m"
            folium.Polygon(
                locations=points, color='yellow', weight=3, fill=True, 
                fill_opacity=0.15, popup=folium.Popup(poly_info, max_width=200)
            ).add_to(m)

        # Ringkasan di Sidebar
        st.sidebar.markdown("### 📊 Ringkasan Lot")
        st.sidebar.success(f"📐 Luas: {area:.3f} m²")
        st.sidebar.info(f"📏 Perimeter: {total_dist:.3f} m")
        
        # Export GeoJSON
        geojson = {
            "type": "FeatureCollection", 
            "features": [{
                "type": "Feature", 
                "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]}, 
                "properties": {"Luas": area, "Perimeter": total_dist}
            }]
        }
        st.sidebar.download_button("📥 Export ke QGIS (GeoJSON)", data=json.dumps(geojson), file_name="lot_puo.geojson", use_container_width=True)
        
        # Papar Peta
        st_folium(m, width="100%", height=700)

    except Exception as e: 
        st.error(f"Ralat Pemprosesan: {e}")
else:
    st.info("👋 Selamat Datang! Sila muat naik fail CSV di sidebar untuk mula memaparkan lot ukur.")
