import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- HEADER ---
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

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.info("Sila log masuk untuk mengakses data pemetaan.")
            pwd = st.text_input("Masukkan Kata Laluan:", type="password")
            if st.button("Masuk"):
                if pwd == "puo123":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Kata laluan salah!")
        return False
    return True

if check_password():
    # --- SIDEBAR ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Muat Naik Fail CSV Anda (STN, E, N)", type=["csv"])
    
    st.sidebar.header("⚙️ Tetapan Peta")
    show_satellite = st.sidebar.checkbox("🌏 Buka Layer Satelit (On/Off)", value=True)
    epsg_input = st.sidebar.text_input("Kod EPSG (Cth: 4390, 3386):", value="4390")
    zoom_val = st.sidebar.slider("🔍 Zoom:", 15, 22, 20)
    
    # TAMBAHAN: Checkbox Grid
    st.sidebar.subheader("🌐 Tetapan Grid")
    show_grid = st.sidebar.checkbox("Papar Grid X & Y", value=True)
    grid_spacing = st.sidebar.number_input("Sela Grid (Meter):", min_value=5, max_value=500, value=20)
    
    st.sidebar.subheader("🏷️ Tetapan Label Lot")
    show_stn = st.sidebar.checkbox("Papar Label Stesen (STN)", value=True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Papar Label Luas Lot", value=True)

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
                st.error("Fail CSV tidak lengkap!")
            else:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['E'].values, df['N'].values)
                df['lon'], df['lat'] = lon, lat

                df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

                fig = go.Figure()

                # --- 1. LOGIK PEMBINAAN GRID X & Y ---
                if show_grid:
                    # Tentukan julat grid berdasarkan koordinat E & N
                    min_e, max_e = df['E'].min() - 50, df['E'].max() + 50
                    min_n, max_n = df['N'].min() - 50, df['N'].max() + 50
                    
                    # Garisan Vertical (X / Easting)
                    for x in np.arange(np.floor(min_e/grid_spacing)*grid_spacing, max_e, grid_spacing):
                        lons, lats = transformer.transform([x, x], [min_n, max_n])
                        fig.add_trace(go.Scattermapbox(
                            lat=lats, lon=lons, mode='lines',
                            line=dict(width=1, color='rgba(255, 255, 255, 0.3)'),
                            hoverinfo='none', showlegend=False
                        ))
                        # Label Nilai X
                        fig.add_trace(go.Scattermapbox(
                            lat=[lats[0]], lon=[lons[0]], mode='text',
                            text=[f"E:{x:.0f}"], textfont=dict(size=9, color="white"),
                            showlegend=False
                        ))

                    # Garisan Horizontal (Y / Northing)
                    for y in np.arange(np.floor(min_n/grid_spacing)*grid_spacing, max_n, grid_spacing):
                        lons, lats = transformer.transform([min_e, max_e], [y, y])
                        fig.add_trace(go.Scattermapbox(
                            lat=lats, lon=lons, mode='lines',
                            line=dict(width=1, color='rgba(255, 255, 255, 0.3)'),
                            hoverinfo='none', showlegend=False
                        ))
                        # Label Nilai Y
                        fig.add_trace(go.Scattermapbox(
                            lat=[lats[0]], lon=[lons[0]], mode='text',
                            text=[f"N:{y:.0f}"], textfont=dict(size=9, color="white"),
                            textposition="middle right", showlegend=False
                        ))

                # --- 2. LUKIS LOT ---
                fig.add_trace(go.Scattermapbox(
                    lat=df_poly['lat'], lon=df_poly['lon'],
                    mode='lines+markers',
                    fill="toself", fillcolor="rgba(255, 255, 0, 0.15)",
                    line=dict(width=3, color='yellow'),
                    marker=dict(size=8, color='red'),
                    name="Lot"
                ))

                # --- 3. LABEL LOT ---
                if show_brg_dist:
                    for i in range(len(df_poly)-1):
                        p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                        dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                        dist = np.sqrt(dE**2 + dN**2)
                        brg = np.degrees(np.arctan2(dE, dN)) % 360
                        m_lat, m_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                        fig.add_trace(go.Scattermapbox(
                            lat=[m_lat], lon=[m_lon], mode='text',
                            text=[f"<b>{decimal_to_dms(brg)}</b><br>{dist:.3f}m"],
                            textfont=dict(size=12, color="cyan", family="Arial Black"),
                            showlegend=False
                        ))

                if show_stn:
                    fig.add_trace(go.Scattermapbox(
                        lat=df['lat'], lon=df['lon'], mode='text', 
                        text=df['STN'].astype(str), textposition="top right",
                        textfont=dict(size=14, color="white", family="Arial Black"),
                        showlegend=False
                    ))

                if show_area:
                    area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
                    fig.add_trace(go.Scattermapbox(
                        lat=[center_lat], lon=[center_lon], mode='text', 
                        text=[f"<b>LUAS:<br>{area:.2f} m²</b>"],
                        textfont=dict(size=18, color="yellow", family="Arial Black"),
                        showlegend=False
                    ))

                # LAYOUT
                mapbox_style = "white-bg"
                layers = []
                if show_satellite:
                    layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]
                else:
                    mapbox_style = "carto-positron"

                fig.update_layout(
                    mapbox=dict(style=mapbox_style, layers=layers, center=dict(lat=center_lat, lon=center_lon), zoom=zoom_val),
                    margin={"r":0,"t":0,"l":0,"b":0}, height=800, showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # --- EKSPORT ---
                st.sidebar.subheader("📤 Eksport Data")
                st.sidebar.download_button(
                    label="Download GeoJSON",
                    data=json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[r['lon'], r['lat']] for i, r in df_poly.iterrows()]]}}]}),
                    file_name="lot.geojson", mime="application/json"
                )

        except Exception as e:
            st.error(f"Ralat: {e}")
    else:
        st.info("Sila muat naik fail CSV.")
