import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Visualisasi Lot WGS84", layout="wide")

st.markdown("<h2 style='text-align: center;'>🛰️ Sistem Lot Poligon (WGS84)</h2>", unsafe_allow_html=True)
st.markdown("---")

# --- PEMPROSESAN DATA ---
default_file = "data ukur.csv"

if os.path.exists(default_file):
    # Membaca fail CSV
    df = pd.read_csv(default_file)
    
    # 2. Penyelarasan Kolum (PENTING!)
    # Kita tukar 'x' kepada 'lon' dan 'y' kepada 'lat'
    if 'x' in df.columns and 'y' in df.columns:
        df_plot = df.rename(columns={'x': 'lon', 'y': 'lat'})
        
        # Menutup poligon (sambung titik terakhir ke titik pertama)
        df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

        # 3. BINA VISUALISASI MAPBOX
        fig = go.Figure()

        # Tambah Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'],
            lon=df_poly['lon'],
            mode='lines+markers+text',
            fill="toself",
            fillcolor="rgba(0, 255, 255, 0.3)", # Isi biru lutsinar
            marker=dict(size=10, color='red'),
            line=dict(width=3, color='yellow'),
            text=df_poly['STN'],
            textposition="top right",
            hoverinfo='text+lat+lon'
        ))

        # 4. SETTING PETA SATELIT (VERSI PALING STABIL)
        fig.update_layout(
            mapbox=dict(
                style="white-bg", 
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "Google Satellite",
                        "source": [
                            # Menggunakan pelayan Google Satellite Hybrid
                            "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                        ]
                    }
                ],
                # Fokuskan peta pada purata koordinat anda
                center=dict(lat=df_plot['lat'].mean(), lon=df_plot['lon'].mean()),
                zoom=18 
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=700,
            showlegend=False
        )

        # Paparkan Peta
        st.plotly_chart(fig, use_container_width=True)
        
        # Paparkan Jadual Data di bawah untuk semakan
        st.write("### 📋 Data Koordinat Terkini")
        st.dataframe(df_plot[['STN', 'lat', 'lon']])
        
    else:
        st.error("Ralat: Kolum 'x' dan 'y' tidak dijumpai. Sila pastikan fail CSV anda mempunyai tajuk kolum yang betul.")
else:
    st.error(f"Fail '{default_file}' tidak dijumpai. Sila muat naik fail tersebut ke GitHub repository anda.")

st.info("💡 **Tips:** Jika peta masih putih, cuba 'zoom out' atau 'refresh' pelayar web anda.")
