import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Visualisasi Satelit LOT 11487 - PUO", layout="wide")

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
            <p style='font-size: 1.2em;'>Jabatan Kejuruteraan Geomatik - Sistem Lot Poligon (Satelit Overlay)</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.markdown("---")

# --- FUNGSI TRANSFORMASI (CONTOH) ---
# Koordinat local (m) ditukar ke Lat/Lon untuk paparan peta
def transform_to_latlon(df):
    # Titik rujukan (Anchor point) - Contoh lokasi di PUO
    ref_lat = 4.5888 
    ref_lon = 101.0437
    
    # 1 darjah latitud ~ 111,320 meter
    # 1 darjah longitud ~ 111,320 * cos(lat) meter
    df['lat'] = ref_lat + (df['N'] - 1000) / 111320
    df['lon'] = ref_lon + (df['E'] - 1000) / (111320 * np.cos(np.radians(ref_lat)))
    return df

# --- LOADING DATA ---
default_file = "data ukur.csv"
df = None

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    df = transform_to_latlon(df)
    # Tutup poligon (stesen akhir balik ke stesen awal)
    df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
else:
    st.error(f"Fail '{default_file}' tidak dijumpai!")

if df is not None:
    # 2. BINA PETA MENGGUNAKAN GRAPH OBJECTS
    fig = go.Figure()

    # Tambah Garisan Poligon & Titik
    fig.add_trace(go.Scattermapbox(
        lat=df_poly['lat'],
        lon=df_poly['lon'],
        mode='lines+markers+text',
        fill="toself",
        fillcolor="rgba(255, 0, 0, 0.2)", # Merah lutsinar
        marker=dict(size=10, color='red'),
        line=dict(width=3, color='yellow'),
        text=df_poly['STN'],
        textposition="top right",
        name="Sempadan Lot"
    ))

    # Konfigurasi Layout Mapbox (Satelit)
    fig.update_layout(
        mapbox=dict(
            style="white-bg", # Kita guna layer custom di bawah
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
            zoom=18
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=700,
        showlegend=False
    )

    # Paparkan Peta
    st.plotly_chart(fig, use_container_width=True)
    
    # Info Tambahan
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Data Koordinat (Converted)")
        st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']])
    with c2:
        area = 0.5 * np.abs(np.dot(df_poly['E'], np.roll(df_poly['N'], 1)) - np.dot(df_poly['N'], np.roll(df_poly['E'], 1)))
        st.metric("Luas Anggaran", f"{area:.3f} m²")
        st.info("Nota: Kedudukan satelit adalah anggaran berdasarkan titik rujukan (Anchor Point).")

