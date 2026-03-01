import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="PUO - Satellite Viewer", layout="wide")

# Header Ringkas
st.markdown("<h2 style='text-align: center;'>🛰️ Paparan Satelit Lot Poligon</h2>", unsafe_allow_html=True)

default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # Tukar nama kolum untuk Plotly (x=lon, y=lat)
    df = df.rename(columns={'x': 'lon', 'y': 'lat'})
    
    # Tutup poligon
    df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    # BINA PETA
    fig = go.Figure()

    # 1. Tambah Poligon & Titik
    fig.add_trace(go.Scattermapbox(
        lat=df_poly['lat'],
        lon=df_poly['lon'],
        mode='lines+markers+text',
        fill="toself",
        fillcolor="rgba(0, 255, 255, 0.4)", # Biru Cyan lutsinar
        marker=dict(size=12, color='red'),
        line=dict(width=3, color='yellow'),
        text=df_poly['STN'],
        textposition="top right",
        hoverinfo='text'
    ))

    # 2. KONFIGURASI LAYOUT (Penyelesaian isu putih)
    fig.update_layout(
        mapbox=dict(
            # Kita guna 'open-street-map' sebagai dasar supaya tidak kosong
            style="open-street-map", 
            layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "Esri World Imagery",
                    "source": [
                        # Pelayan alternatif (ArcGIS Online) yang sangat stabil
                        "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ]
                }
            ],
            center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
            zoom=18 # Jika masih putih, cuba kurangkan ke 15
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("Jika peta masih putih: 1. Pastikan internet stabil. 2. Cuba buka di Google Chrome mod 'Incognito'.")

else:
    st.error("Fail 'data ukur.csv' tidak dijumpai.")
