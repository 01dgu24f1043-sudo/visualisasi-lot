import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Geod

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
    st.sidebar.header("⚙️ Tetapan Peta")
    zoom_val = st.sidebar.slider("🔍 Tahap Zoom:", 10, 22, 20)
    
    st.sidebar.subheader("🏷️ Tetapan Label")
    show_stn = st.sidebar.checkbox("Label Stesen", value=True)
    show_data = st.sidebar.checkbox("Label Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Label Luas", value=True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if os.path.exists("point.csv"):
        df = pd.read_csv("point.csv")
        df['lon'] = df['x']
        df['lat'] = df['y']
        
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        fig = go.Figure()

        # 1. LUKIS POLIGON
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.1)",
            line=dict(width=2, color='yellow'),
            marker=dict(size=8, color='red'),
            hoverinfo='none'
        ))

        geod = Geod(ellps="WGS84")

        # 2. LABEL STESEN
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text', text=df['STN'].astype(str),
                textposition="top center",
                textfont=dict(size=13, color="white", family="Arial Black")
            ))

        # 3. BEARING & JARAK (DENGAN ROTASI)
        if show_data:
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                
                # Kira Bearing & Jarak Sebenar (Geodetik)
                fwd_az, back_az, dist = geod.inv(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
                brg = fwd_az % 360
                
                # Titik Tengah untuk Label
                mid_lat = (p1['lat'] + p2['lat']) / 2
                mid_lon = (p1['lon'] + p2['lon']) / 2
                
                # Kira Sudut Rotasi (Skrin)
                # Kita guna beza koordinat mudah untuk dapatkan angle visual
                d_lon = p2['lon'] - p1['lon']
                d_lat = p2['lat'] - p1['lat']
                angle = np.degrees(np.arctan2(d_lat, d_lon))
                
                # Adjust supaya teks tidak terbalik (upside down)
                if angle > 90: angle -= 180
                elif angle < -90: angle += 180

                # Tambah Label Bearing (Atas Garisan) & Jarak (Bawah Garisan)
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat], lon=[mid_lon],
                    mode='text',
                    text=[f"{decimal_to_dms(brg)}<br>{dist:.2f}m"],
                    textfont=dict(size=11, color="cyan", family="Arial Black"),
                    hoverinfo='none'
                ))

        # 4. LABEL LUAS
        if show_area:
            lons, lats = df['lon'].tolist(), df['lat'].tolist()
            area_m2, perim = geod.polygon_area_perimeter(lons, lats)
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {abs(area_m2):.2f} m²"],
                textfont=dict(size=16, color="yellow", family="Arial Black")
            ))

        # 5. LAYOUT
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
            margin={"r":0,"t":0,"l":0,"b":0}, height=800, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Fail 'data ukur.csv' tidak dijumpai.")

