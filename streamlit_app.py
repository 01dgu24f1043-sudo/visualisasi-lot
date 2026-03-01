import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="PUO - Visualisasi Lot WGS84", layout="wide")

# --- HEADER: TAJUK & LOGO ---
col1, col2 = st.columns([1, 4])
logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png" 

with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)
    else:
        st.write("### PUO")

with col2:
    st.markdown("## JABATAN KEJURUTERAAN GEOMATIK")
    st.markdown("#### Sistem Visualisasi Lot Poligon (WGS84)")

st.markdown("---")

# --- PEMPROSESAN DATA ---
default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # PENTING: Menyelaraskan nama kolum (CSV anda guna x dan y)
    # x = Longitude, y = Latitude
    if 'x' in df.columns and 'y' in df.columns:
        df_plot = df.copy()
        df_plot = df_plot.rename(columns={'x': 'lon', 'y': 'lat'})
        
        # Menutup poligon
        df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

        # 2. BINA VISUALISASI MAPBOX
        fig = go.Figure()

        # Tambah Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'],
            lon=df_poly['lon'],
            mode='lines+markers+text',
            fill="toself",
            fillcolor="rgba(255, 255, 0, 0.3)", # Kuning Lutsinar
            marker=dict(size=10, color='red'),
            line=dict(width=3, color='yellow'),
            text=df_poly['STN'],
            textposition="top right",
            hoverinfo='text+lat+lon'
        ))

        # 3. SETTING PETA (Satelit)
        fig.update_layout(
            mapbox=dict(
                style="white-bg", 
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "Esri World Imagery",
                        "source": [
                            "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        ]
                    }
                ],
                center=dict(lat=df_plot['lat'].mean(), lon=df_plot['lon'].mean()),
                zoom=18
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=700,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Info Tambahan di bawah peta
        st.success(f"📍 Lokasi dikesan di Muar, Johor (WGS84)")
        
        # Kira Luas (Geodetik Ringkas)
        # Kerana koordinat sangat kecil, kita guna pengiraan Cartesian sementara
        area = 0.5 * np.abs(np.dot(df_plot['lon'], np.roll(df_plot['lat'], 1)) - np.dot(df_plot['lat'], np.roll(df_plot['lon'], 1)))
        # Nota: Untuk luas sebenar dalam m2 bagi WGS84, perlu rumus Haversine/Vincenty
        
    else:
        st.error("Ralat: Kolum 'x' dan 'y' tidak dijumpai dalam CSV. Sila semak format fail anda.")
else:
    st.warning("Sila pastikan fail 'data ukur.csv' telah dimuat naik ke dalam GitHub repository anda.")
