import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- FUNGSI KATA LALUAN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.title("🔒 Log Masuk Sistem")
            pwd = st.text_input("Masukkan Kata Laluan:", type="password")
            if st.button("Masuk"):
                if pwd == "puo123": # <--- TUKAR PASSWORD DI SINI
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Kata laluan salah!")
        return False
    return True

if check_password():
    # --- SIDEBAR: TETAPAN ---
    st.sidebar.header("⚙️ Tetapan Peta")
    
    epsg_code = st.sidebar.text_input("Kod EPSG (Cth Cassini Perak: 4390):", value="4326")
    zoom_margin = st.sidebar.slider("🔍 Zum Keluar (Margin Meter):", 0, 100, 20)
    
    st.sidebar.subheader("🏷️ Tetapan Label")
    show_stn = st.sidebar.checkbox("Label Stesen", value=True)
    show_brg_dist = st.sidebar.checkbox("Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Label Luas", value=True)

    # --- FUNGSI DMS ---
    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    # --- LOADING DATA ---
    default_file = "data ukur.csv"
    if os.path.exists(default_file):
        df = pd.read_csv(default_file)
        
        # Penukaran Koordinat jika bukan 4326
        if epsg_code != "4326":
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['x'].values, df['y'].values)
                df['lon'], df['lat'] = lon, lat
            except Exception as e:
                st.error(f"Ralat EPSG: {e}")
                df['lon'], df['lat'] = df['x'], df['y']
        else:
            df['lon'], df['lat'] = df['x'], df['y']

        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        # 2. BINA PETA
        fig = go.Figure()

        # Trace Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.2)",
            line=dict(width=3, color='yellow'),
            marker=dict(size=10, color='red'),
            hoverinfo='none'
        ))

        # 3. LABEL LOGIK
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text', text=df['STN'],
                textposition="top right",
                textfont=dict(size=14, color="white")
            ))

        if show_brg_dist:
            for i in range(len(df_poly)-1):
                p1 = df_poly.iloc[i]
                p2 = df_poly.iloc[i+1]
                mid_lat, mid_lon = (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2
                
                # Kira Bearing/Jarak (Cartesian simple untuk label)
                dx, dy = p2['x'] - p1['x'], p2['y'] - p1['y']
                dist = np.sqrt(dx**2 + dy**2)
                brg = np.degrees(np.arctan2(dx, dy)) % 360
                
                fig.add_annotation(
                    xref="x", yref="y", lat=mid_lat, lon=mid_lon,
                    text=f"{decimal_to_dms(brg)}<br>{dist:.2f}m",
                    showarrow=False, font=dict(color="cyan", size=10),
                    bgcolor="rgba(0,0,0,0.5)"
                )

        if show_area:
            area = 0.5 * np.abs(np.dot(df['x'], np.roll(df['y'], 1)) - np.dot(df['y'], np.roll(df['x'], 1)))
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {area:.2f} m²"],
                textfont=dict(size=16, color="yellow", family="Arial Black")
            ))

        # 4. LAYOUT
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[{"below": 'traces', "sourcetype": "raster",
                         "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}],
                center=dict(lat=center_lat, lon=center_lon),
                zoom=19
            ),
            margin={"r":0,"t":0,"l":0,"b":0}, height=800, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Fail 'data ukur.csv' tidak dijumpai.")
