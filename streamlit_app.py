import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA (Simulasi) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "01dgu24f1043": {"nama": "Ahmad", "pwd": "12345"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "Nafiz0921"},
        "pensyarah": {"nama": "Dr. Surveyor", "pwd": "jka123"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI LOGIN & RESET ---
def login_page():
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        
        with tab1:
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
        
        with tab2:
            reset_id = st.text_input("Masukkan ID untuk Reset")
            new_pwd = st.text_input("Kata Laluan Baru", type="password")
            if st.button("Simpan Password Baru"):
                if reset_id in st.session_state["user_db"]:
                    st.session_state["user_db"][reset_id]["pwd"] = new_pwd
                    st.success(f"Kata laluan untuk {reset_id} telah dikemaskini!")
                else:
                    st.error("ID tidak ditemui")

# --- LOGIK UTAMA ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # Logout button di sidebar paling atas
    if st.sidebar.button("🚪 Log Keluar"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- HEADER ---
    logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png"
    col1, col2, col3 = st.columns([1, 4, 1.5])
    with col1:
        if os.path.exists(logo_path): st.image(logo_path, width=120)
    with col2:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader("Jabatan Kejuruteraan Awam - Unit Geomatik")
    with col3:
        # Paparan HI [NAMA]
        nama_user = st.session_state.get('user_name', 'USER').upper()
        st.markdown(f"""
            <div style='background-color:#f0f2f6;padding:10px;border-radius:10px;border-left:5px solid red;'>
            Selamat Datang<h3>HI {nama_user}</h3>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Mesti ada STN, E, N)", type=["csv"])

    st.sidebar.header("⚙️ Tetapan Paparan")
    size_stn = st.sidebar.slider("Saiz No Stesen", 10, 40, 15)
    size_brg = st.sidebar.slider("Saiz Bearing/Jarak", 8, 30, 12)
    size_area = st.sidebar.slider("Saiz Luas (Tengah)", 15, 60, 25)
    
    # Gantikan baris 88 asal dengan ini:
    show_satellite = st.sidebar.checkbox("🌏 Buka Layer Satelit", True)

    def decimal_to_dms(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            # Transformasi Koordinat
            epsg_input = st.sidebar.text_input("Kod EPSG (Contoh: 4390)", "4390")
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

            # Hitung Luas & Perimeter
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            perimeter = 0
            for i in range(len(df_poly)-1):
                dE = df_poly.iloc[i+1]['E'] - df_poly.iloc[i]['E']
                dN = df_poly.iloc[i+1]['N'] - df_poly.iloc[i]['N']
                perimeter += np.sqrt(dE**2 + dN**2)

            fig = go.Figure()

            # 1. POLYGON (Hover keluar Perimeter & Luas)
            fig.add_trace(go.Scattermapbox(
                lat=df_poly['lat'], lon=df_poly['lon'],
                mode='lines',
                fill="toself", fillcolor="rgba(255,255,0,0.1)",
                line=dict(width=4, color="yellow"),
                hoverinfo="text",
                text=f"MAKLUMAT LOT:<br>Luas: {area:.3f} m²<br>Perimeter: {perimeter:.3f} m"
            ))

            # --- 2. STESEN (Label N & E Statik) ---
            if show_stn:
                # Membina label teks: No Stesen, N, dan E secara menegak
                label_n_e = [
                    f"<b>{row['STN']}</b><br>N: {row['N']:.3f}<br>E: {row['E']:.3f}" 
                    for _, row in df.iterrows()
                ]
                
                fig.add_trace(go.Scattermapbox(
                    lat=df['lat'], lon=df['lon'],
                    mode='markers+text',
                    marker=dict(size=10, color="red"),
                    text=label_n_e, # Menggunakan label N & E yang baru dibina
                    textposition="top right",
                    textfont=dict(size=size_stn, color="white", family="Arial Black"),
                    hoverinfo="text",
                    hovertext=[f"STN: {s}" for s in df['STN']]
                ))

            # 3. BEARING & JARAK
            offset_dist = 0.000015
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg = np.degrees(np.arctan2(dE, dN)) % 360
                
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat], lon=[mid_lon],
                    mode="text",
                    text=[f"{decimal_to_dms(brg)}<br>{dist:.3f}m"],
                    textfont=dict(size=size_brg, color="cyan"),
                    hoverinfo='skip'
                ))

            # 4. TEKS LUAS DI TENGAH
            fig.add_trace(go.Scattermapbox(
                lat=[df['lat'].mean()], lon=[df['lon'].mean()],
                mode="text",
                text=[f"LUAS<br>{area:.2f} m²"],
                textfont=dict(size=size_area, color="yellow"),
                hoverinfo='skip'
            ))

            # LAYOUT & FULLSCREEN SUPPORT
            layers = []
            if show_satellite:
                layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]

            fig.update_layout(
                mapbox=dict(style="white-bg", layers=layers, center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()), zoom=zoom_val),
                margin={"r":0,"t":0,"l":0,"b":0}, height=700, showlegend=False,
                dragmode="pan" # Default pan untuk senang gerak peta
            )

            # Paparkan Peta
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

            # --- EKSPORT QGIS (GEOJSON) ---
            features = [{
                "type": "Feature",
                "properties": {"Luas": area, "Perimeter": perimeter},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[ [r['lon'], r['lat']] for _, r in df_poly.iterrows() ]]
                }
            }]
            geojson_data = json.dumps({"type": "FeatureCollection", "features": features})
            
            st.sidebar.download_button(
                label="📥 Export ke QGIS (GeoJSON)",
                data=geojson_data,
                file_name="lot_geomatik.geojson",
                mime="application/json"
            )

            st.subheader("Jadual Data")
            st.dataframe(df[['STN','E','N','lat','lon']], use_container_width=True)

        except Exception as e:
            st.error(f"Sila pastikan format CSV betul (STN, E, N). Ralat: {e}")


