import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Geod # Gunakan Geod untuk jarak/bearing tepat pada glob

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik", layout="wide")

# --- FUNGSI KATA LALUAN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.title("🔒 Log Masuk")
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
    st.sidebar.header("⚙️ Tetapan Peta")
    # Memandangkan data anda 102.52, 2.10, ia ADALAH 4326 (WGS84)
    epsg_code = st.sidebar.text_input("Kod EPSG (Data WGS84 gunakan 4326):", value="4326")
    zoom_val = st.sidebar.slider("🔍 Tahap Zoom:", 10, 22, 19)
    
    st.sidebar.subheader("🏷️ Tetapan Label")
    show_stn = st.sidebar.checkbox("Label Stesen", value=True)
    show_brg_dist = st.sidebar.checkbox("Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Label Luas", value=True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    # --- LOADING DATA ---
    if os.path.exists("data ukur.csv"):
        df = pd.read_csv("data ukur.csv")
        
        # Penamaan semula untuk paparan (x=E, y=N)
        df = df.rename(columns={'x': 'E', 'y': 'N'})
        
        # Koordinat untuk Plotly (Lon/Lat)
        df['lon'] = df['E']
        df['lat'] = df['N']

        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        # 2. BINA PETA
        fig = go.Figure()

        # Trace 1: Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.2)",
            line=dict(width=3, color='yellow'),
            marker=dict(size=10, color='red'),
            name="Sempadan"
        ))

        # Trace 2: Label Stesen
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text', text=df['STN'].astype(str),
                textposition="top right",
                textfont=dict(size=14, color="white")
            ))

        # Trace 3: Bearing & Jarak (Guna Geod untuk koordinat darjah)
        if show_brg_dist:
            geod = Geod(ellps="WGS84")
            lats_mid, lons_mid, texts_mid = [], [], []
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                
                # Kira Bearing & Jarak Geodetik (tepat untuk Lat/Lon)
                # fwd_azimuth adalah bearing dari p1 ke p2
                fwd_azimuth, back_azimuth, distance = geod.inv(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
                
                brg = fwd_azimuth % 360
                
                lats_mid.append((p1['lat'] + p2['lat']) / 2)
                lons_mid.append((p1['lon'] + p2['lon']) / 2)
                texts_mid.append(f"<b>{decimal_to_dms(brg)}<br>{distance:.2f}m</b>")
            
            fig.add_trace(go.Scattermapbox(
                lat=lats_mid, lon=lons_mid,
                mode='text', text=texts_mid,
                textfont=dict(size=11, color="cyan")
            ))

        # Trace 4: Luas (Guna formula Geodetik untuk WGS84)
        if show_area:
            geod = Geod(ellps="WGS84")
            area_m2, perimeter = geod.geometry_area_perimeter(df['lon'], df['lat'])
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {abs(area_m2):.2f} m²"],
                textfont=dict(size=18, color="yellow", family="Arial Black")
            ))

        # 3. LAYOUT
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[{
                    "below": 'traces', "sourcetype": "raster",
                    "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]
                }],
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom_val
            ),
            margin={"r":0,"t":0,"l":0,"b":0}, height=750, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        st.write("### 📋 Data Koordinat (N, E)")
        st.dataframe(df[['STN', 'N', 'E']])
    else:
        st.error("Fail 'data ukur.csv' tidak dijumpai.")
