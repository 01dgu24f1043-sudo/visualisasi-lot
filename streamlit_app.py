import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- USER LOGIN ---
USER_CREDENTIALS = {
    "01dgu24f1043": "12345",
    "01dgu24f1013": "Nafiz0921",
    "pensyarah": "jka123"
}

def login_page():
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        
        with tab1:
            user_id = st.text_input("ID Pengguna")
            user_pwd = st.text_input("Kata Laluan", type="password")
            if st.button("Masuk", use_container_width=True):
                if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == user_pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah")
        
        with tab2:
            forgot_id = st.text_input("Masukkan ID Pengguna")
            if st.button("Semak Password"):
                if forgot_id in USER_CREDENTIALS:
                    st.info(f"Kata laluan anda: {USER_CREDENTIALS[forgot_id]}")
                else:
                    st.error("ID tidak ditemui")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    # --- DASHBOARD HEADER ---
    logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png"
    col1, col2, col3 = st.columns([1, 4, 1.5])
    
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=120)
    with col2:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader("Jabatan Kejuruteraan Awam - Unit Geomatik")
    with col3:
        st.markdown(f"""
            <div style="background-color:#f0f2f6;padding:10px;border-radius:10px;border-left:5px solid #ff4b4b;">
                <small>Selamat Datang,</small>
                <h4 style="margin:0;">{st.session_state['user_id']}</h4>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Log Keluar", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    st.markdown("---")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.header("📂 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (E, N, STN)", type=["csv"])
    
    epsg_input = st.sidebar.text_input("Kod EPSG (e.g. 4390 for Cassini)", "4390")

    st.sidebar.header("🗺️ Tetapan Peta")
    show_satellite = st.sidebar.checkbox("Layer Satellite", True)
    zoom_val = st.sidebar.slider("Zoom Level", 10, 22, 18)

    st.sidebar.subheader("📏 Saiz Tulisan")
    size_stn = st.sidebar.slider("No Stesen", 10, 30, 14)
    size_brg = st.sidebar.slider("Bearing/Jarak", 8, 25, 10)
    size_area = st.sidebar.slider("Luas", 15, 40, 22)

    st.sidebar.subheader("👁️ Paparan")
    show_stn = st.sidebar.checkbox("Papar Stesen", True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", True)
    show_area = st.sidebar.checkbox("Papar Luas", True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        if m >= 60: m = 0; d += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()
            
            # Validation
            if not all(col in df.columns for col in ['E', 'N', 'STN']):
                st.error("Fail CSV mesti mempunyai kolum: E, N, dan STN")
                st.stop()

            # Transformation
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lon'], df['lat'] = lon, lat

            # Close the polygon loop
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

            fig = go.Figure()

            # 1. DRAW POLYGON
            fig.add_trace(go.Scattermapbox(
                lat=df_poly['lat'], lon=df_poly['lon'],
                mode='lines+markers',
                fill="toself",
                fillcolor="rgba(255, 255, 0, 0.15)",
                line=dict(width=3, color="yellow"),
                marker=dict(size=10, color="red"),
                name="Lot Boundary"
            ))

            # 2. STATION LABELS
            if show_stn:
                fig.add_trace(go.Scattermapbox(
                    lat=df['lat'], lon=df['lon'],
                    mode="text",
                    text=df['STN'].astype(str),
                    textposition="top right",
                    textfont=dict(size=size_stn, color="white"),
                    name="Stations"
                ))

            # 3. BEARING & DISTANCE LABELS
            if show_brg_dist:
                offset = 0.00002 # Adjust based on zoom
                for i in range(len(df_poly)-1):
                    p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                    
                    # Math for Bearing/Distance
                    dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                    dist = np.sqrt(dE**2 + dN**2)
                    brg = np.degrees(np.arctan2(dE, dN)) % 360
                    
                    # Midpoint for label
                    mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                    
                    label_text = f"{decimal_to_dms(brg)}<br>{dist:.3f}m"
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=[mid_lat], lon=[mid_lon],
                        mode="text",
                        text=[label_text],
                        textfont=dict(size=size_brg, color="cyan"),
                        name="Measurements"
                    ))

            # 4. AREA CALCULATION
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            if show_area:
                fig.add_trace(go.Scattermapbox(
                    lat=[df['lat'].mean()], lon=[df['lon'].mean()],
                    mode="text",
                    text=[f"LUAS<br>{area:.2f} m²"],
                    textfont=dict(size=size_area, color="yellow", family="Arial Black"),
                    name="Area"
                ))

            # --- MAP LAYOUT ---
            layers = []
            if show_satellite:
                layers = [{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]
                }]

            fig.update_layout(
                mapbox=dict(
                    style="white-bg",
                    layers=layers,
                    center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
                    zoom=zoom_val,
                ),
                # uirevision preserves zoom/pan state when sliders change
                uirevision=True, 
                margin={"r":0,"t":0,"l":0,"b":0},
                height=700,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- DATA TABLE ---
            st.subheader("📊 Jadual Koordinat & Analisis")
            col_a, col_b = st.columns([2,1])
            
            with col_a:
                table_df = df[['STN','E','N']].copy()
                st.dataframe(table_df.style.format({"E": "{:.3f}", "N": "{:.3f}"}), use_container_width=True)
            
            with col_b:
                st.metric("Total Perimeter", f"{dist:.3f} m") # Note: This shows last dist, could be summed
                st.metric("Total Area", f"{area:.2f} m²")
                csv = table_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "lot_coordinates.csv", "text/csv")

        except Exception as e:
            st.error(f"⚠️ Ralat Pemprosesan: {e}")
    else:
        st.info("Sila muat naik fail CSV di bahagian sidebar untuk memulakan.")
