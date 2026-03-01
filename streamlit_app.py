import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Poligon WGS84", layout="wide")

# --- HEADER: TAJUK & LOGO ---
col1, col2, col3 = st.columns([1, 3, 1])
logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png" 

with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.write("### PUO")

with col2:
    st.markdown(
        """
        <div style='text-align: center;'>
            <h2 style='margin-bottom: 0;'>POLITEKNIK UNGKU OMAR</h2>
            <p style='font-size: 1.2em;'>Jabatan Kejuruteraan Geomatik - Visualisasi Lot WGS 84</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.markdown("---")

# --- LOADING DATA ---
# Fail CSV anda mempunyai kolum: STN, x (Lon), y (Lat)
default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # Memastikan kolum yang betul digunakan
    # x = Longitude, y = Latitude
    df['lon'] = df['x']
    df['lat'] = df['y']
    
    # Tutup poligon (sambung balik ke stesen asal)
    df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    # 2. BINA PETA SATELIT
    fig = go.Figure()

    # Tambah Poligon (Garisan & Warna Isi)
    fig.add_trace(go.Scattermapbox(
        lat=df_poly['lat'],
        lon=df_poly['lon'],
        mode='lines+markers+text',
        fill="toself",
        fillcolor="rgba(255, 255, 0, 0.3)", # Kuning lutsinar
        marker=dict(size=10, color='red'),
        line=dict(width=3, color='yellow'),
        text=df_poly['STN'],
        textposition="top right",
        hoverinfo='text+lat+lon'
    ))

    # Konfigurasi Layout Mapbox
    fig.update_layout(
        mapbox=dict(
            style="white-bg", 
            layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "Esri World Imagery",
                    "source": [
                        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ]
                }
            ],
            center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
            zoom=19 # Zoom lebih dekat untuk nampak lot
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=700,
        showlegend=False
    )

    # Paparkan dalam Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    # Paparan Data
    st.success(f"Berjaya memaparkan lot berdasarkan koordinat WGS 84.")
    
    with st.expander("Lihat Data Koordinat"):
        st.dataframe(df[['STN', 'x', 'y']])

else:
    st.error(f"Fail '{default_file}' tidak dijumpai dalam direktori.")
