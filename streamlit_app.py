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
    epsg_input = st.sidebar.text_input("Kod EPSG (Cth Cassini Perak: 4390):", value="4390")
    zoom_val = st.sidebar.slider("🔍 Tahap Zoom:", 10, 22, 20)
    
    st.sidebar.subheader("🏷️ Tetapan Label")
    show_stn = st.sidebar.checkbox("Label Stesen", value=True)
    show_brg = st.sidebar.checkbox("Label Bearing (Atas Garisan)", value=True)
    show_dist = st.sidebar.checkbox("Label Jarak (Bawah Garisan)", value=True)
    show_area = st.sidebar.checkbox("Label Luas", value=True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    # --- PEMPROSESAN DATA ---
    file_path = "point.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip() # Bersihkan nama kolum

        # 2. TRANSFORMASI KOORDINAT (METER -> WGS84)
        try:
            # Transformer dari Cassini/RSO ke WGS84
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lon'], df['lat'] = lon, lat
        except Exception as e:
            st.sidebar.error(f"Ralat EPSG: {e}")
            df['lon'], df['lat'] = 0.0, 0.0

        # Tutup poligon
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        # 3. BINA VISUALISASI
        fig = go.Figure()

        # Lukisan Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.15)",
            line=dict(width=3, color='yellow'),
            marker=dict(size=8, color='red'),
            name="Sempadan"
        ))

        # OFFSET LOGIK UNTUK BEARING & JARAK
        # Kita gunakan offset kecil dalam darjah (anggaran 1.5 meter)
        offset_val = 0.000015 

        for i in range(len(df_poly)-1):
            p1 = df_poly.iloc[i]
            p2 = df_poly.iloc[i+1]
            
            # Pengiraan Geometrik Dasar (Meter)
            dE = p2['E'] - p1['E']
            dN = p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Titik Tengah (WGS84)
            mid_lat = (p1['lat'] + p2['lat']) / 2
            mid_lon = (p1['lon'] + p2['lon']) / 2
            
            # Vector Normal untuk Offset (Pegang Teks Atas/Bawah)
            # Menghitung arah tegak lurus terhadap garisan
            norm = np.sqrt(dE**2 + dN**2)
            if norm != 0:
                off_lon = (-dN / norm) * offset_val
                off_lat = (dE / norm) * offset_val
            else:
                off_lon, off_lat = 0, 0

            # Label Bearing (Atas - Offset Positif)
            if show_brg:
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat + off_lat], lon=[mid_lon + off_lon],
                    mode='text', text=[decimal_to_dms(brg)],
                    textfont=dict(size=11, color="cyan", family="Arial Black")
                ))

            # Label Jarak (Bawah - Offset Negatif)
            if show_dist:
                fig.add_trace(go.Scattermapbox(
                    lat=[mid_lat - off_lat], lon=[mid_lon - off_lon],
                    mode='text', text=[f"{dist:.3f}m"],
                    textfont=dict(size=10, color="yellow", family="Arial")
                ))

        # Label Stesen
        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text', text=df['STN'].astype(str),
                textposition="top right",
                textfont=dict(size=14, color="white", family="Arial Black")
            ))

        # Label Luas
        if show_area:
            # Shoelace formula untuk meter
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {area:.2f} m²"],
                textfont=dict(size=18, color="yellow", family="Arial Black")
            ))

        # 4. LAYOUT PETA
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
        st.write("### 📋 Data Lot (Meter)")
        st.dataframe(df[['STN', 'E', 'N']])
    else:
        st.error("Fail 'point.csv' tidak dijumpai dalam direktori.")
