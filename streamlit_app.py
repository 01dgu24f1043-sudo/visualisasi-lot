import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

# --- CONFIG ---
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- LOGIN SYSTEM ---
USER_CREDENTIALS = {"01dgu24f1043": "12345", "01dgu24f1013": "Nafiz0921", "pensyarah": "jka123"}
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.subheader("🔐 Log Masuk Sistem")
        u_id = st.text_input("ID Pengguna")
        u_pw = st.text_input("Kata Laluan", type="password")
        if st.button("Masuk", use_container_width=True):
            if u_id in USER_CREDENTIALS and USER_CREDENTIALS[u_id] == u_pw:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = u_id
                st.rerun()
            else: st.error("ID atau Kata Laluan Salah")
else:
    # --- SIDEBAR ---
    st.sidebar.header("Tetapan")
    uploaded_file = st.sidebar.file_uploader("Muat Naik CSV", type=["csv"])
    show_satellite = st.sidebar.checkbox("Paparan Satelit", True)
    zoom_val = st.sidebar.slider("Zoom", 15, 22, 19)
    size_brg = st.sidebar.slider("Saiz Teks", 8, 25, 11)
    
    show_stn = st.sidebar.checkbox("Papar Stesen", True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", True)

    def decimal_to_dms(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        # CRS Transformation
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # Guna Scattermap (BUKAN Scattermapbox) untuk sokongan 'angle'
        fig = go.Figure()

        # 1. Garisan Sempadan
        fig.add_trace(go.Scattermap(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            line=dict(width=3, color="yellow"),
            marker=dict(size=8, color="red"),
            fill="toself", fillcolor="rgba(255, 255, 0, 0.1)"
        ))

        # 2. Bearing & Jarak (Berpusing Selari Garisan)
        if show_brg_dist:
            offset_val = 0.000015
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                
                # Kira Bearing & Jarak
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # Kira Sudut untuk Rotation (Sisi kanan menghala ke point tujuan)
                # Dalam Plotly Map, 0 darjah adalah tegak. Kita perlu adjust.
                angle_deg = np.degrees(np.arctan2(p2['lon'] - p1['lon'], p2['lat'] - p1['lat']))
                
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                
                # Normal vector untuk offset Atas/Bawah
                d_lat, d_lon = p2['lat'] - p1['lat'], p2['lon'] - p1['lon']
                mag = np.sqrt(d_lat**2 + d_lon**2)
                nx, ny = -d_lat/mag, d_lon/mag

                # Plot Bearing (Atas)
                fig.add_trace(go.Scattermap(
                    lat=[mid_lat + ny * offset_val], lon=[mid_lon + nx * offset_val],
                    mode="text", text=[decimal_to_dms(brg)],
                    textfont=dict(size=size_brg, color="cyan"),
                    marker=dict(angle=angle_deg - 90) # Pusingkan teks
                ))

                # Plot Jarak (Bawah)
                fig.add_trace(go.Scattermap(
                    lat=[mid_lat - ny * offset_val], lon=[mid_lon - nx * offset_val],
                    mode="text", text=[f"{dist:.3f}m"],
                    textfont=dict(size=size_brg, color="white"),
                    marker=dict(angle=angle_deg - 90) # Pusingkan teks
                ))

        # --- LAYOUT ---
        fig.update_layout(
            map=dict(
                style="satellite-streets" if show_satellite else "streets",
                center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
                zoom=zoom_val
            ),
            uirevision="constant",
            margin={"r":0,"t":0,"l":0,"b":0}, height=750, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['STN','E','N']], use_container_width=True)
