import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import json
from folium.plugins import Fullscreen

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA & KATA LALUAN ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "1": {"nama": "Admin", "pwd": "123"},
        "01dgu24f1043": {"nama": "Ahmad", "pwd": "123"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "456"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI PEMBANTU ---
def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- HALAMAN LUPA PASSWORD ---
def reset_password_page():
    st.markdown("### 🔑 Set Semula Kata Laluan")
    uid = st.text_input("Masukkan ID anda untuk set semula")
    new_pwd = st.text_input("Kata Laluan Baru", type="password")
    if st.button("Simpan Kata Laluan Baru"):
        if uid in st.session_state["user_db"]:
            st.session_state["user_db"][uid]["pwd"] = new_pwd
            st.success("Kata laluan berjaya disimpan! Sila log masuk semula.")
            st.session_state["reset_mode"] = False
            st.rerun()
        else:
            st.error("ID tidak dijumpai")
    if st.button("Kembali ke Login"):
        st.session_state["reset_mode"] = False
        st.rerun()

# --- HALAMAN LOGIN ---
def login_page():
    if st.session_state.get("reset_mode", False):
        reset_password_page()
        return

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
        
        if st.button("Lupa Kata Laluan?"):
            st.session_state["reset_mode"] = True
            st.rerun()

# --- LOGIK UTAMA ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # Sidebar
    st.sidebar.markdown(f"### 👋 Hi, {st.session_state['user_name']}")
    if st.sidebar.button("🚪 Log Keluar"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("POLITEKNIK UNGKU OMAR")
    st.subheader(f"Unit Geomatik - Selamat Datang, {st.session_state['user_name'].upper()}")
    st.markdown("---")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

    st.sidebar.header("🛠️ Tetapan Saiz Teks")
    size_stn = st.sidebar.slider("Saiz No Stesen", 8, 30, 12)
    size_brg = st.sidebar.slider("Saiz Bearing/Jarak", 6, 25, 10)
    size_area = st.sidebar.slider("Saiz Teks Luas", 10, 40, 18)
    text_gap = st.sidebar.slider("Keluasan Gap Teks", 20, 70, 35)
    epsg_input = st.sidebar.text_input("Kod EPSG (RSO Malaya: 4390)", "4390")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            # 1. Transformasi Koordinat
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            
            # 2. Bina Peta Folium
            center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22, tiles=None)
            
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google', name='Google Satellite', overlay=False, control=True,
                max_zoom=22, max_native_zoom=20
            ).add_to(m)

            Fullscreen(position="topright", title="Skrin Penuh", title_cancel="Keluar").add_to(m)

            points = []
            features = []
            total_perimeter = 0

            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                loc1 = [p1['lat'], p1['lon']]
                points.append(loc1)

                # Kira Bearing & Jarak
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                total_perimeter += dist
                brg_deg = np.degrees(np.arctan2(dE, dN)) % 360
                
                text_angle = brg_deg - 90
                if 90 < brg_deg < 270: text_angle -= 180 

                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

                # 3. Label Bearing & Jarak (Gap Precision)
                half_gap = text_gap / 2
                label_html = f'''
                    <div style="transform: rotate({text_angle}deg); display: flex; flex-direction: column; justify-content: space-between; align-items: center; color: #00FFFF; font-weight: bold; font-size: {size_brg}pt; text-shadow: 1px 1px 2px black; text-align: center; width: 180px; margin-left: -90px; pointer-events: none; height: {text_gap}px; margin-top: -{half_gap}px;">
                        <div style="white-space: nowrap; line-height: 1; padding-bottom: 2px;">{decimal_to_dms(brg_deg)}</div>
                        <div style="white-space: nowrap; line-height: 1; padding-top: 2px;">{dist:.3f}m</div>
                    </div>'''
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=label_html)).add_to(m)
                
                # 4. Point Stesen (Klik untuk Koordinat)
                stn_popup = f"<b>Stesen: {int(p1['STN'])}</b><br>E: {p1['E']:.3f}<br>N: {p1['N']:.3f}"
                folium.CircleMarker(
                    location=loc1, radius=4, color="white", fill=True, fill_color="red", popup=stn_popup
                ).add_to(m)

                stn_html = f'''<div style="color:white; font-weight:bold; font-size:{size_stn}pt; text-shadow: 1px 1px 2px black;">{int(p1["STN"])}</div>'''
                folium.Marker(loc1, icon=folium.DivIcon(html=stn_html, icon_anchor=(0,0))).add_to(m)

            # 5. Luas (Shoelace Formula)
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            
            # Poligon Info (Klik untuk Luas & Perimeter)
            poly_popup = f"<b>Maklumat Lot</b><hr>Luas: {area:.3f} m²<br>Perimeter: {total_perimeter:.3f} m"
            folium.Polygon(
                locations=points, color='yellow', weight=3, fill=True, fill_opacity=0.15, popup=poly_popup
            ).add_to(m)

            # Paparan Luas di Sidebar & Peta
            st.sidebar.markdown("---")
            st.sidebar.write(f"📐 **Luas:** {area:.3f} m²")
            st.sidebar.write(f"📏 **Perimeter:** {total_perimeter:.3f} m")

            # 6. Button Export GeoJSON (QGIS)
            geojson_data = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]},
                    "properties": {"Luas_m2": area, "Perimeter_m": total_perimeter}
                }]
            }
            st.sidebar.download_button(
                label="📥 Export ke QGIS (GeoJSON)",
                data=json.dumps(geojson_data),
                file_name="lot_geomatik.geojson",
                mime="application/json"
            )

            st_folium(m, width="100%", height=700)

        except Exception as e:
            st.error(f"Sila semak fail CSV. Ralat: {e}")
