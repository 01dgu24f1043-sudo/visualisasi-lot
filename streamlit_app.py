import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

# --- PERSAPAN ASAS ---
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI LOGIN ---
if not st.session_state["logged_in"]:
    st.title("🔐 Log Masuk Sistem PUO")
    u_id = st.text_input("ID Pengguna")
    if st.button("Masuk"):
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = u_id
        st.rerun()
else:
    # --- SIDEBAR (KEKKALKAN SEMUA SETTING) ---
    st.sidebar.header("Tetapan Peta")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    show_satellite = st.sidebar.checkbox("Layer Satellite", True)
    zoom_val = st.sidebar.slider("Zoom", 15, 22, 19)
    
    st.sidebar.subheader("Saiz Tulisan")
    size_stn = st.sidebar.slider("No Stesen", 10, 30, 14)
    size_brg = st.sidebar.slider("Bearing & Jarak", 8, 25, 11)
    
    show_stn = st.sidebar.checkbox("Papar Stesen", True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", True)

    def decimal_to_dms(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        fig = go.Figure()

        # 1. LUKIS GARISAN LOT
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            line=dict(width=3, color="yellow"),
            marker=dict(size=8, color="red"),
            fill="toself", fillcolor="rgba(255,255,0,0.1)"
        ))

        # 2. BEARING & JARAK (ROTASI SELARI GARISAN)
        if show_brg_dist:
            offset_val = 0.000012 
            
            for i in range(len(df_poly)-1):
                p1 = df_poly.iloc[i]
                p2 = df_poly.iloc[i+1]
                
                # Kira Bearing & Jarak Satah
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # Kira Sudut Rotasi (Visual Lat/Lon)
                d_lat = p2['lat'] - p1['lat']
                d_lon = p2['lon'] - p1['lon']
                angle = np.degrees(np.arctan2(d_lat, d_lon))
                
                # Normalkan sudut supaya teks tidak terbalik (sentiasa dari kiri ke kanan)
                display_angle = angle
                if display_angle > 90: display_angle -= 180
                elif display_angle < -90: display_angle += 180
                
                # Vektor Normal untuk anjakan Atas/Bawah
                mag = np.sqrt(d_lat**2 + d_lon**2)
                nx, ny = -d_lat/mag, d_lon/mag
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

                # BEARING (Tengah, Atas, Berpusing)
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat + ny * offset_val],
                    lon=[mid_lon + nx * offset_val],
                    mode="text",
                    text=[decimal_to_dms(brg)],
                    textfont=dict(size=size_brg, color="cyan"),
                    textangle=-display_angle # Memusingkan teks mengikut garisan
                ))
                
                # JARAK (Tengah, Bawah, Berpusing)
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat - ny * offset_val],
                    lon=[mid_lon - nx * offset_val],
                    mode="text",
                    text=[f"{dist:.3f}m"],
                    textfont=dict(size=size_brg, color="white"),
                    textangle=-display_angle # Memusingkan teks mengikut garisan
                ))

        # 3. LABEL STESEN
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'], mode="text",
                text=df['STN'].astype(str), textposition="top right",
                textfont=dict(size=size_stn, color="yellow")
            ))

        # --- LAYOUT PETA ---
        layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]} if show_satellite else []]
        fig.update_layout(
            mapbox=dict(style="white-bg", layers=layers, center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()), zoom=zoom_val),
            uirevision="constant", # Zoom takkan reset
            margin={"r":0,"t":0,"l":0,"b":0}, height=700, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['STN','E','N']])
