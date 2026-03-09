import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- LOGIN SESSION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# (Fungsi login diringkaskan untuk fokus kepada pembaikan peta)
if not st.session_state["logged_in"]:
    st.title("🔐 Log Masuk Sistem PUO")
    u_id = st.text_input("ID Pengguna")
    if st.button("Masuk"):
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = u_id
        st.rerun()
else:
    # --- SIDEBAR SETTINGS ---
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

        # 1. GARISAN LOT
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            line=dict(width=3, color="yellow"),
            marker=dict(size=8, color="red"),
            fill="toself", fillcolor="rgba(255,255,0,0.1)"
        ))

        # 2. BEARING & JARAK (MENGHALA KE POINT TUJUAN)
        if show_brg_dist:
            offset_dist = 0.000012 # Jarak atas/bawah
            
            for i in range(len(df_poly)-1):
                p1 = df_poly.iloc[i]
                p2 = df_poly.iloc[i+1]
                
                # Kira Bearing & Jarak
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # --- TEKNIK MENGHALA KE POINT TUJUAN ---
                # Kita letak label pada 70% perjalanan garisan (bukan tengah 50%)
                ratio = 0.7 
                target_lat = p1['lat'] + (p2['lat'] - p1['lat']) * ratio
                target_lon = p1['lon'] + (p2['lon'] - p1['lon']) * ratio
                
                # Kira Vektor Normal untuk anjakan Atas/Bawah
                d_lat, d_lon = p2['lat'] - p1['lat'], p2['lon'] - p1['lon']
                mag = np.sqrt(d_lat**2 + d_lon**2)
                nx, ny = -d_lat/mag, d_lon/mag
                
                # BEARING (Atas & Menghala ke depan)
                fig.add_trace(go.Scattermapbox(
                    lat=[target_lat + ny * offset_dist],
                    lon=[target_lon + nx * offset_dist],
                    mode="text",
                    text=[f"<b>{decimal_to_dms(brg)}</b>"],
                    textfont=dict(size=size_brg, color="cyan")
                ))
                
                # JARAK (Bawah & Menghala ke depan)
                fig.add_trace(go.Scattermapbox(
                    lat=[target_lat - ny * offset_dist],
                    lon=[target_lon - nx * offset_dist],
                    mode="text",
                    text=[f"{dist:.3f}m"],
                    textfont=dict(size=size_brg, color="white")
                ))

        # 3. LABEL STESEN
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'], mode="markers+text",
                text=df['STN'].astype(str), textposition="top right",
                textfont=dict(size=size_stn, color="yellow")
            ))

        # LAYOUT
        layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]} if show_satellite else []]
        fig.update_layout(
            mapbox=dict(style="white-bg", layers=layers, center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()), zoom=zoom_val),
            uirevision="lock",
            margin={"r":0,"t":0,"l":0,"b":0}, height=700, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['STN','E','N']])
