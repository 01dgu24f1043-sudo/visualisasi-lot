import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import json
from folium.plugins import Fullscreen

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "1": {"nama": "Admin", "pwd": "123"},
        "01dgu24f1043": {"nama": "Alif", "pwd": "123"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "456"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI PEMBANTU ---
def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
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
        else: st.error("ID tidak sah")
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
            else: st.error("ID/Password Salah")
        if st.button("Lupa Kata Laluan?"):
            st.session_state["reset_mode"] = True
            st.rerun()
    st.stop()

# --- APLIKASI UTAMA (LOGGED IN) ---

# Sidebar Header
st.sidebar.markdown(f"### 👋 Hi, {st.session_state['user_name']}")
st.sidebar.markdown("---")

st.title("POLITEKNIK UNGKU OMAR")
st.subheader(f"Unit Geomatik - Selamat Datang, {st.session_state['user_name'].upper()}")

# --- SIDEBAR SETTINGS ---
uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

st.sidebar.header("👁️ Kawalan Paparan (On/Off)")
show_stn = st.sidebar.checkbox("Paparkan No Stesen", value=True)
show_brg = st.sidebar.checkbox("Paparkan Bearing/Jarak", value=True)
show_poly = st.sidebar.checkbox("Paparkan Poligon & Luas", value=True)

st.sidebar.header("🛠️ Tetapan Saiz Teks")
size_stn = st.sidebar.slider("Saiz No Stesen", 8, 30, 12)
size_brg = st.sidebar.slider("Saiz Bearing/Jarak", 6, 25, 10)
text_gap = st.sidebar.slider("Keluasan Gap Teks", 20, 70, 35)
epsg_input = st.sidebar.text_input("Kod EPSG", "4390")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
        
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
            attr='Google', name='Google Satellite', max_zoom=22, max_native_zoom=20
        ).add_to(m)
        
        Fullscreen(position="topright").add_to(m)

        points = []
        total_dist = 0
        for i in range(len(df)):
            p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
            loc1 = [p1['lat'], p1['lon']]
            points.append(loc1)

            # Kira Bearing/Jarak
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            total_dist += dist
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Label Bearing/Jarak (Logic On/Off)
            if show_brg:
                t_angle = brg - 90
                if 90 < brg < 270: t_angle -= 180
                h_gap = text_gap / 2
                l_html = f'''<div style="transform: rotate({t_angle}deg); display: flex; flex-direction: column; justify-content: space-between; align-items: center; color: #00FFFF; font-weight: bold; font-size: {size_brg}pt; text-shadow: 1px 1px 2px black; width: 180px; margin-left: -90px; height: {text_gap}px; margin-top: -{h_gap}px; pointer-events: none;">
                    <div style="padding-bottom:2px;">{decimal_to_dms(brg)}</div>
                    <div style="padding-top:2px;">{dist:.3f}m</div>
                </div>'''
                folium.Marker([ (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2 ], icon=folium.DivIcon(html=l_html)).add_to(m)

            # Titik Stesen & Koordinat Popup
            stn_popup = f"<b>STN {int(p1['STN'])}</b><br>E: {p1['E']:.3f}<br>N: {p1['N']:.3f}"
            folium.CircleMarker(loc1, radius=4, color="white", fill=True, fill_color="red", popup=stn_popup).add_to(m)
            
            # Label No Stesen (Logic On/Off)
            if show_stn:
                stn_txt = f'''<div style="color:white; font-weight:bold; font-size:{size_stn}pt; text-shadow: 1px 1px 2px black;">{int(p1["STN"])}</div>'''
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_txt)).add_to(m)

        # Poligon & Luas (Logic On/Off)
        area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
        if show_poly:
            poly_info = f"<b>Info Lot</b><hr>Luas: {area:.3f} m²<br>Perimeter: {total_dist:.3f} m"
            folium.Polygon(locations=points, color='yellow', weight=3, fill=True, fill_opacity=0.15, popup=poly_info).add_to(m)

        # Download Buttons & Info
        st.sidebar.markdown("---")
        st.sidebar.info(f"📐 Luas: {area:.3f} m²\n\n📏 Perimeter: {total_dist:.3f} m")
        geojson = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]}, "properties": {"Luas": area}}]}
        st.sidebar.download_button("📥 Export QGIS (GeoJSON)", data=json.dumps(geojson), file_name="lot_puo.geojson", use_container_width=True)
        
        st_folium(m, width="100%", height=700)

    except Exception as e: st.error(f"Ralat Fail: {e}")

# --- TOLAK LOGOUT KE BAWAH SEKALI ---
st.sidebar.markdown("<br>" * 10, unsafe_allow_html=True) # Mencipta ruang kosong
if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

