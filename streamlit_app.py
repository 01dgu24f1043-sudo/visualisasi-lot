import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- HEADER (LOGO & TAJUK) ---
logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png"
col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.info("Logo PUO")
with col2:
    st.title("POLITEKNIK UNGKU OMAR")
    st.subheader("Jabatan Kejuruteraan Awam - Unit Geomatik")

st.markdown("---")

# --- KATA LALUAN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.info("Sila log masuk.")
            pwd = st.text_input("Kata Laluan:", type="password")
            if st.button("Masuk"):
                if pwd == "puo123":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Salah!")
        return False
    return True

if check_password():
    # --- SIDEBAR ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Muat Naik CSV (STN, E, N)", type=["csv"])
    
    st.sidebar.header("⚙️ Tetapan Peta")
    show_satellite = st.sidebar.checkbox("🌏 Layer Satelit", value=True)
    epsg_input = st.sidebar.text_input("Kod EPSG:", value="4390")
    zoom_val = st.sidebar.slider("🔍 Zoom:", 15, 22, 20)
    
    st.sidebar.subheader("🌐 Tetapan Grid")
    show_grid = st.sidebar.checkbox("Papar Grid X & Y", value=True)
    grid_spacing = st.sidebar.number_input("Sela Grid (Meter):", min_value=1, max_value=500, value=20)
    
    st.sidebar.subheader("🏷️ Label")
    show_stn = st.sidebar.checkbox("No. Stesen", value=True)
    show_brg_dist = st.sidebar.checkbox("Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Luas Lot", value=True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            if not {'STN', 'E', 'N'}.issubset(df.columns):
                st.error("Kolum STN, E, N diperlukan!")
            else:
                # Transformasi
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['E'].values, df['N'].values)
                df['lon'], df['lat'] = lon, lat
                df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

                # --- PLOT PETA ---
                fig = go.Figure()

                # Lukis Grid
                if show_grid:
                    min_e, max_e = df['E'].min() - 40, df['E'].max() + 40
                    min_n, max_n = df['N'].min() - 40, df['N'].max() + 40
                    
                    for x in np.arange(np.floor(min_e/grid_spacing)*grid_spacing, max_e, grid_spacing):
                        glons, glats = transformer.transform([x, x], [min_n, max_n])
                        fig.add_trace(go.Scattermapbox(lat=glats, lon=glons, mode='lines', line=dict(width=1, color='rgba(200,200,200,0.4)'), hoverinfo='none', showlegend=False))
                    
                    for y in np.arange(np.floor(min_n/grid_spacing)*grid_spacing, max_n, grid_spacing):
                        glons, glats = transformer.transform([min_e, max_e], [y, y])
                        fig.add_trace(go.Scattermapbox(lat=glats, lon=glons, mode='lines', line=dict(width=1, color='rgba(200,200,200,0.4)'), hoverinfo='none', showlegend=False))

                # Lukis Lot
                fig.add_trace(go.Scattermapbox(lat=df_poly['lat'], lon=df_poly['lon'], mode='lines+markers', fill="toself", fillcolor="rgba(255, 255, 0, 0.1)", line=dict(width=3, color='yellow'), marker=dict(size=8, color='red')))

                # Label Bearing/Jarak
                if show_brg_dist:
                    for i in range(len(df_poly)-1):
                        p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                        dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                        brg = np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) % 360
                        fig.add_trace(go.Scattermapbox(lat=[(p1['lat']+p2['lat'])/2], lon=[(p1['lon']+p2['lon'])/2], mode='text', text=[f"<b>{decimal_to_dms(brg)}</b><br>{dist:.3f}m"], textfont=dict(size=11, color="cyan")))

                # Label STN & Luas
                if show_stn:
                    fig.add_trace(go.Scattermapbox(lat=df['lat'], lon=df['lon'], mode='text', text=df['STN'].astype(str), textposition="top right", textfont=dict(size=14, color="white")))

                if show_area:
                    area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
                    fig.add_trace(go.Scattermapbox(lat=[center_lat], lon=[center_lon], mode='text', text=[f"<b>LUAS: {area:.2f} m²</b>"], textfont=dict(size=16, color="yellow")))

                fig.update_layout(mapbox=dict(style="white-bg" if not show_satellite else "satellite", layers=[{"sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]} if show_satellite else {}], center=dict(lat=center_lat, lon=center_lon), zoom=zoom_val), margin={"r":0,"t":0,"l":0,"b":0}, height=700, showlegend=False)

                st.plotly_chart(fig, use_container_width=True)

                # --- KEMBALIKAN JADUAL DATA ---
                st.markdown("### 📋 Jadual Koordinat & Data Lot")
                col_tab1, col_tab2 = st.columns([2, 1])
                
                with col_tab1:
                    # Menambah kolum Lat/Lon ke jadual untuk rujukan QGIS
                    st.dataframe(df[['STN', 'E', 'N', 'lon', 'lat']], use_container_width=True)
                
                with col_tab2:
                    st.info(f"**Ringkasan Lot:**\n\n* Bilangan Titik: {len(df)}\n* Kod EPSG: {epsg_input}\n* Luas: {area:.3f} m²")

                # Eksport GeoJSON
                st.sidebar.download_button("Download GeoJSON", data=json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[r['lon'], r['lat']] for i, r in df_poly.iterrows()]]}}]}), file_name="lot_puo.geojson")

        except Exception as e:
            st.error(f"Ralat: {e}")
