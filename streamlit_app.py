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

# --- HALAMAN LOGIN ---
if not st.session_state["logged_in"]:
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
        if st.button("Batal"):
            st.session_state["reset_mode"] = False
            st.rerun()
    else:
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
                else: st.error("ID/Password Salah")
            if st.button("Lupa Kata Laluan?"):
                st.session_state["reset_mode"] = True
                st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("politeknik-ungku-umar-seeklogo-removebg-preview.png", use_container_width=True)
    except:
        st.warning("⚠️ Logo tidak dijumpai.")
    
    st.markdown(f"<h3 style='text-align:center;'>👋 Hi, {st.session_state['user_name']}</h3>", unsafe_allow_html=True)
    st.divider()

    uploaded_file = st.file_uploader("📂 Upload CSV (STN, E, N)", type=["csv"])

    st.header("👁️ Kawalan Paparan")
    show_satellite = st.toggle("Paparkan Imej Satelit", value=True)
    show_stn = st.checkbox("Paparkan No Stesen", value=True)
    show_brg = st.checkbox("Paparkan Bearing/Jarak", value=True)
    show_poly = st.checkbox("Paparkan Poligon & Luas", value=True)

    st.header("🎨 Warna Poligon")
    poly_color = st.color_picker("Pilih Warna Sempadan", "#00FFFF")
    fill_color = st.color_picker("Pilih Warna Isi", "#00FFFF")
    fill_opac = st.slider("Kepekatan Warna Isi", 0.0, 1.0, 0.3)

    st.header("🛠️ Tetapan Teks")
    size_stn = st.slider("Saiz No Stesen", 8, 30, 14)
    size_brg = st.slider("Saiz Bearing/Jarak", 6, 25, 10)
    text_gap = st.slider("Keluasan Gap Teks", 20, 100, 45)
    epsg_input = st.text_input("Kod EPSG (cth: 4390)", "4390")

    st.divider()
    if st.button("🚪 Log Keluar", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- HEADER UTAMA ---
st.markdown("<h1 style='text-align:center;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#555;'>Unit Geomatik - Sistem Visualisasi Lot</h3>", unsafe_allow_html=True)
st.divider()

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
        
        if show_satellite:
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                             attr='Google', name='Google Satellite', max_zoom=22, max_native_zoom=20).add_to(m)
        else:
            folium.TileLayer('OpenStreetMap').add_to(m)
        
        Fullscreen(position="topright").add_to(m)

        points = []
        total_dist = 0
        
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            loc1 = [p1['lat'], p1['lon']]
            points.append(loc1)

            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            total_dist += dist
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Marker Titik Koordinat
            stn_info = f"<b>STESEN {int(p1['STN'])}</b><hr>N: {p1['N']:.3f}<br>E: {p1['E']:.3f}"
            folium.CircleMarker(
                location=loc1, radius=6, color='red', fill=True, fill_color='yellow',
                popup=folium.Popup(stn_info, max_width=150),
                tooltip=f"Stesen {int(p1['STN'])}",
                z_index_offset=1000 
            ).add_to(m)

            if show_stn:
                stn_txt = f'<div style="color:white; font-weight:bold; font-size:{size_stn}pt; text-shadow: 2px 2px 3px black; pointer-events:none;">{int(p1["STN"])}</div>'
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_txt, icon_anchor=(-10, 10))).add_to(m)

            if show_brg:
                calc_angle = brg - 90
                if 90 < brg < 270: calc_angle -= 180
                l_html = f'''<div style="transform: rotate({calc_angle}deg); display: flex; flex-direction: column; justify-content: space-between; align-items: center; color: #00FFFF; font-weight: bold; font-size: {size_brg}pt; text-shadow: 2px 2px 4px black; width: 200px; margin-left: -100px; height: {text_gap}px; margin-top: -{text_gap/2}px; pointer-events: none; text-align: center;">
                            <div>{decimal_to_dms(brg)}</div><div style="color: #FFD700;">{dist:.3f}m</div></div>'''
                folium.Marker([(p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2], icon=folium.DivIcon(html=l_html)).add_to(m)

        # --- POLIGON DENGAN INFO LUAS & PERIMETER ---
        area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
        
        if show_poly:
            # Format HTML untuk Popup Poligon
            poly_popup_html = f"""
                <div style="font-family: Arial; font-size: 13px; width: 160px;">
                    <h4 style="margin-bottom: 5px; color: #333;">Info Lot</h4>
                    <hr style="margin: 5px 0;">
                    <b>📐 Luas:</b> {area:.3f} m²<br>
                    <b>📏 Perimeter:</b> {total_dist:.3f} m
                </div>
            """
            
            folium.Polygon(
                locations=points, 
                color=poly_color, 
                weight=3, 
                fill=True, 
                fill_color=fill_color, 
                fill_opacity=fill_opac, 
                popup=folium.Popup(poly_popup_html, max_width=200)
            ).add_to(m)

        # Info Sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Analisis Lot")
        st.sidebar.success(f"📐 Luas: **{area:.3f} m²**")
        st.sidebar.info(f"📏 Perimeter: **{total_dist:.3f} m**")
        
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]},
                "properties": {"Luas_m2": area, "Perimeter_m": total_dist}
            }]
        }
        st.sidebar.download_button("📥 Export GeoJSON", data=json.dumps(geojson_data), file_name="lot_puo.geojson", use_container_width=True)
        
        st_folium(m, width="100%", height=700, returned_objects=[])

    except Exception as e: st.error(f"Ralat: {e}")
else:
    st.info("Sila muat naik fail CSV untuk memulakan.")
