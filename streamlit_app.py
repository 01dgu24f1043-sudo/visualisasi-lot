import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- LOGIN LOGIC (Ringkasan) ---
USER_CREDENTIALS = {"01dgu24f1043": "12345", "01dgu24f1013": "Nafiz0921", "pensyarah": "jka123"}
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # (Borang login anda di sini...)
    user_id = st.sidebar.text_input("ID Pengguna")
    user_pwd = st.sidebar.text_input("Kata Laluan", type="password")
    if st.sidebar.button("Masuk"):
        if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == user_pwd:
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user_id
            st.rerun()
else:
    # --- HEADER ---
    st.title(f"Sistem Lot Geomatik - HI {st.session_state['user_id']}")
    st.markdown("---")

    # --- SIDEBAR: KAWALAN SAIZ (KEPERLUAN ANDA) ---
    st.sidebar.header("📏 Tetapan Saiz Label")
    size_stn = st.sidebar.slider("Saiz No. Stesen (Kuning/Putih):", 8, 30, 15)
    size_brg = st.sidebar.slider("Saiz Bearing & Jarak (Cyan):", 8, 25, 12)
    size_area = st.sidebar.slider("Saiz Luas (Tengah Lot):", 15, 40, 22)
    
    st.sidebar.header("⚙️ Tetapan Peta")
    zoom_val = st.sidebar.slider("Zum Peta:", 15, 22, 19)
    show_satellite = st.sidebar.checkbox("🌏 Buka Layer Satelit", value=True)

    # --- UPLOAD FAIL ---
    uploaded_file = st.sidebar.file_uploader("Muat Naik CSV (STN, E, N)", type=["csv"])

    def decimal_to_dms(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()
            
            # Transformasi Koordinat (Gunakan 4390 sebagai default)
            epsg_input = "4390" 
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lon'], df['lat'] = lon, lat
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

            fig = go.Figure()

            # 1. TRACE SEMPADAN & FILL (Kuning)
            fig.add_trace(go.Scattermapbox(
                lat=df_poly['lat'], lon=df_poly['lon'],
                mode='lines+markers',
                fill="toself", fillcolor="rgba(255, 255, 0, 0.15)",
                line=dict(width=3, color='yellow'),
                marker=dict(size=10, color='red'),
                hoverinfo='none' # Matikan hover box
            ))

            # 2. LABEL NO STESEN (SENTIASA MUNCUL)
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text',
                text=df['STN'].astype(str),
                textposition="top center",
                textfont=dict(size=size_stn, color="yellow", family="Arial Black"),
                hoverinfo='none'
            ))

            # 3. LABEL BEARING & JARAK (SENTIASA MUNCUL PADA SETIAP GARISAN)
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                brg = np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) % 360
                
                fig.add_trace(go.Scattermapbox(
                    lat=[(p1['lat'] + p2['lat']) / 2],
                    lon=[(p1['lon'] + p2['lon']) / 2],
                    mode='text',
                    text=[f"<b>{decimal_to_dms(brg)}</b><br>{dist:.3f}m"],
                    textfont=dict(size=size_brg, color="cyan", family="Arial Black"),
                    hoverinfo='none'
                ))

            # 4. LABEL LUAS (SENTIASA MUNCUL DI TENGAH)
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            fig.add_trace(go.Scattermapbox(
                lat=[df['lat'].mean()], lon=[df['lon'].mean()],
                mode='text',
                text=[f"<b>LUAS:<br>{area:.2f} m²</b>"],
                textfont=dict(size=size_area, color="white", family="Arial Black"),
                hoverinfo='none'
            ))

            # LAYOUT SETTINGS
            layers = []
            if show_satellite:
                layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]

            fig.update_layout(
                mapbox=dict(
                    style="white-bg",
                    layers=layers,
                    center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
                    zoom=zoom_val
                ),
                margin={"r":0,"t":0,"l":0,"b":0},
                height=800,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Sila pastikan format CSV betul (STN, E, N). Ralat: {e}")
