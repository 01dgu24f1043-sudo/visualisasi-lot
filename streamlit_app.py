import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
try:
    from pyproj import Transformer
except ImportError:
    st.error("Sila tambah 'pyproj' dalam fail requirements.txt di GitHub")

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Cassini Perak", layout="wide")

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
    epsg_code = st.sidebar.text_input("Kod EPSG (Cth Perak: 4390):", value="4390")
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
    if os.path.exists("point.csv"):
        df = pd.read_csv("point.csv")
        
        # TUKAR x -> E, y -> N untuk paparan
        df = df.rename(columns={'x': 'E', 'y': 'N'})
        
        # TRANSFORMASI KOORDINAT (CASSINI TO WGS84)
        try:
            # Transformer dari Cassini (EPSG:4390) ke WGS84 (EPSG:4326)
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            # Dalam pyproj, always_xy=True bermaksud (East, North) -> (Lon, Lat)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lon'], df['lat'] = lon, lat
        except Exception as e:
            st.sidebar.error(f"Ralat Transformasi: {e}")
            # Fallback jika gagal (anggap data sudah lat/lon)
            df['lon'], df['lat'] = df['E'], df['N']

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

        # Trace 3: Bearing & Jarak
        if show_brg_dist:
            lats_mid, lons_mid, texts_mid = [], [], []
            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                lats_mid.append((p1['lat'] + p2['lat']) / 2)
                lons_mid.append((p1['lon'] + p2['lon']) / 2)
                
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                brg = np.degrees(np.arctan2(dE, dN)) % 360
                texts_mid.append(f"<b>{decimal_to_dms(brg)}<br>{dist:.2f}m</b>")
            
            fig.add_trace(go.Scattermapbox(
                lat=lats_mid, lon=lons_mid,
                mode='text', text=texts_mid,
                textfont=dict(size=10, color="cyan")
            ))

        # Trace 4: Luas
        if show_area:
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {area:.2f} m²"],
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
        
        st.write("### 📋 Data Koordinat (Cassini Perak)")
        st.dataframe(df[['STN', 'N', 'E', 'lat', 'lon']])
    else:
        st.error("Fail 'data ukur.csv' tidak dijumpai.")
