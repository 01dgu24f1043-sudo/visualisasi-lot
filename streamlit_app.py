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
    # PENTING: Untuk data anda, pastikan EPSG adalah 4390 (Perak)
    epsg_input = st.sidebar.text_input("Kod EPSG (Perak: 4390):", value="4390")
    zoom_val = st.sidebar.slider("🔍 Tahap Zoom:", 10, 22, 19)
    
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

    # --- PEMPROSESAN DATA ---
    file_path = "point.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

        # TRANSFORMASI KOORDINAT (Cassini -> WGS84)
        try:
            # Gunakan transformer untuk tukar E,N ke Lat,Lon
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lon'], df['lat'] = lon, lat
        except Exception as e:
            st.error(f"Ralat Pertukaran Koordinat: {e}")

        # Tutup poligon (sambung balik ke stesen asal)
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        # 2. BINA PETA
        fig = go.Figure()

        # LUKIS POLIGON (GARISAN KUNING)
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'], lon=df_poly['lon'],
            mode='lines+markers',
            fill="toself", fillcolor="rgba(255, 255, 0, 0.2)",
            line=dict(width=4, color='yellow'),
            marker=dict(size=10, color='red'),
            name="Sempadan"
        ))

        # 3. LABEL BEARING, JARAK & STESEN
        # Offset untuk memisahkan teks supaya tidak bertindih
        offset_val = 0.000015 

        for i in range(len(df_poly)-1):
            p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
            
            # Kira Bearing & Jarak (Guna unit meter E, N)
            dE = p2['E'] - p1['E']
            dN = p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # Titik tengah garisan (Lat/Lon)
            m_lat, m_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

            if show_data:
                # Label Bearing (Cyan - Atas sedikit)
                fig.add_trace(go.Scattermapbox(
                    lat=[m_lat + offset_val], lon=[m_lon],
                    mode='text', text=[decimal_to_dms(brg)],
                    textfont=dict(size=12, color="cyan", family="Arial Black")
                ))
                # Label Jarak (Yellow - Bawah sedikit)
                fig.add_trace(go.Scattermapbox(
                    lat=[m_lat - offset_val], lon=[m_lon],
                    mode='text', text=[f"{dist:.3f}m"],
                    textfont=dict(size=11, color="yellow", family="Arial")
                ))

        if show_stn:
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text', text=df['STN'].astype(str),
                textposition="top right",
                textfont=dict(size=14, color="white", family="Arial Black")
            ))

        # 4. LUAS (Formula Shoelace Meter)
        if show_area:
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            fig.add_trace(go.Scattermapbox(
                lat=[center_lat], lon=[center_lon],
                mode='text', text=[f"LUAS: {area:.2f} m²"],
                textfont=dict(size=18, color="yellow", family="Arial Black")
            ))

        # 5. LAYOUT & GOOGLE SATELLITE
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]
                }],
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom_val
            ),
            margin={"r":0,"t":0,"l":0,"b":0}, height=800, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Papar jadual data di bawah peta untuk semakan
        st.write("### 📋 Semakan Data Meter (point.csv)")
        st.dataframe(df[['STN', 'E', 'N']])
        
    else:
        st.error("Fail 'point.csv' tidak dijumpai. Sila pastikan fail ada di GitHub.")
