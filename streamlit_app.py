import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="PUO Geomatik - Satellite Overlay", layout="wide")

# --- FUNGSI PENUKARAN KOORDINAT (CASSINI/LOCAL TO WGS84) ---
def transform_to_latlon(df):
    """
    Menukarkan koordinat meter (E, N) kepada Latitud/Longitud.
    Titik Rujukan: STN 5 (999.99, 1000.00) diletakkan di PUO.
    """
    # Koordinat Lat/Lon SEBENAR untuk PUO (Stesen 5)
    ref_lat = 4.588825  
    ref_lon = 101.043690
    
    # Rujukan asalan dalam CSV (E=1000, N=1000)
    origin_e = 1000.0
    origin_n = 1000.0
    
    # Faktor penukaran kasar (meter ke darjah)
    lat_per_meter = 1 / 111320
    lon_per_meter = 1 / (111320 * np.cos(np.radians(ref_lat)))
    
    df['lat'] = ref_lat + (df['N'] - origin_n) * lat_per_meter
    df['lon'] = ref_lon + (df['E'] - origin_e) * lon_per_meter
    return df

# --- CARI FAIL CSV ---
default_file = "point.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    df = transform_to_latlon(df)
    df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    st.title("🛰️ Paparan Satelit Lot Poligon")

    # 2. BINA PETA (Guna Mapbox Layer)
    fig = go.Figure()

    # Tambah Poligon
    fig.add_trace(go.Scattermapbox(
        lat=df_poly['lat'],
        lon=df_poly['lon'],
        mode='lines+markers+text',
        fill="toself",
        fillcolor="rgba(0, 255, 255, 0.3)", # Biru cyan lutsinar
        marker=dict(size=12, color='yellow'),
        line=dict(width=3, color='yellow'),
        text=df_poly['STN'],
        textposition="top center",
        hoverinfo='text'
    ))

    # 3. CONFIGURATION MAPBOX & SATELIT
    fig.update_layout(
        mapbox=dict(
            style="white-bg", # Mesti guna white-bg jika guna layer raster
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
            zoom=18 # Dekatkan zoom supaya nampak bangunan
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=700,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    st.success("Satelit berjaya dimuatkan dengan koordinat transformasi.")
    
else:
    st.error(f"Fail '{default_file}' tidak dijumpai. Sila pastikan fail CSV ada dalam folder yang sama.")
