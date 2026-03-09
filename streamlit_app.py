import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- LOGIN & SESSION STATE ---
USER_CREDENTIALS = {"01dgu24f1043": "12345", "01dgu24f1013": "Nafiz0921", "pensyarah": "jka123"}
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # (Bahagian login dikekalkan seperti asal anda)
    u_id = st.sidebar.text_input("ID Pengguna")
    u_pw = st.sidebar.text_input("Kata Laluan", type="password")
    if st.sidebar.button("Masuk"):
        if u_id in USER_CREDENTIALS and USER_CREDENTIALS[u_id] == u_pw:
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = u_id
            st.rerun()
else:
    # --- HEADER & SIDEBAR ---
    st.title("POLITEKNIK UNGKU OMAR - Geomatik")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    show_satellite = st.sidebar.checkbox("Layer Satellite", True)
    zoom_val = st.sidebar.slider("Zoom", 15, 22, 19)
    size_brg = st.sidebar.slider("Saiz Teks", 8, 25, 11)

    def decimal_to_dms(deg):
        d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        # Transformasi Koordinat
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        fig = go.Figure()

        # 1. LUKIS SEMPADAN (LINE)
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.1)",
            line=dict(width=3, color="yellow"),
            marker=dict(size=8, color="red")
        ))

        # 2. SISTEM LABEL TANPA TEXTANGLE (OFFSET MANUFAIL)
        # Kita guna vektor normal untuk tolak teks keluar dari garisan
        lat_brg_list, lon_brg_list, text_brg_list = [], [], []
        lat_dist_list, lon_dist_list, text_dist_list = [], [], []

        offset = 0.000015 # Jarak anjakan teks

        for i in range(len(df_poly)-1):
            p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
            
            # Kira Bearing & Jarak
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist_val = np.sqrt(dE**2 + dN**2)
            brg_val = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Titik Tengah
            mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
            
            # Kira arah "Normal" (Serenjang dengan garisan)
            d_lat, d_lon = p2['lat'] - p1['lat'], p2['lon'] - p1['lon']
            length = np.sqrt(d_lat**2 + d_lon**2)
            
            if length != 0:
                nx, ny = -d_lat / length, d_lon / length
                
                # BEARING - Kita letak di lokasi Midpoint + Offset
                lat_brg_list.append(mid_lat + ny * offset)
                lon_brg_list.append(mid_lon + nx * offset)
                text_brg_list.append(f"<b>{decimal_to_dms(brg_val)}</b>")
                
                # JARAK - Kita letak di lokasi Midpoint - Offset
                lat_dist_list.append(mid_lat - ny * offset)
                lon_dist_list.append(mid_lon - nx * offset)
                text_dist_list.append(f"{dist_val:.3f}m")

        # Masukkan label Bearing (Warna Cyan)
        fig.add_trace(go.Scattermapbox(
            lat=lat_brg_list, lon=lon_brg_list,
            mode="text", text=text_brg_list,
            textfont=dict(size=size_brg, color="cyan"),
            name="Bearing"
        ))

        # Masukkan label Jarak (Warna Putih)
        fig.add_trace(go.Scattermapbox(
            lat=lat_dist_list, lon=lon_dist_list,
            mode="text", text=text_dist_list,
            textfont=dict(size=size_brg, color="white"),
            name="Jarak"
        ))

        # 3. LAYOUT PETA
        layers = []
        if show_satellite:
            layers = [{"below": 'traces', "sourcetype": "raster", 
                       "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]

        fig.update_layout(
            mapbox=dict(
                style="white-bg", layers=layers,
                center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
                zoom=zoom_val
            ),
            uirevision="lock", # Mengekalkan zoom semasa slider diubah
            margin={"r":0,"t":0,"l":0,"b":0}, height=750, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['STN','E','N']])
