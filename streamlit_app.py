import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Satelit Overlay - PUO", layout="wide")

# --- FUNGSI PENUKARAN KOORDINAT (SIMPLIFIED) ---
# Nota: Ini adalah anggaran kasar untuk demonstrasi. 
# Dalam kerja ukur sebenar, anda perlu rumus "Coordinate Transformation".
def transform_to_latlon(df):
    # Titik rujukan (Contoh: Pintu masuk PUO)
    ref_lat = 4.5888 
    ref_lon = 101.0437
    
    # Anggaran kasar: 1 darjah latitud ~ 111,000 meter
    df['lat'] = ref_lat + (df['N'] - 1000) / 111000
    df['lon'] = ref_lon + (df['E'] - 1000) / (111000 * 0.99) # Kosinus latitud
    return df

# --- LOADING DATA ---
default_file = "point.csv"
if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    df = transform_to_latlon(df) # Tukar ke Lat/Lon
    
    # Tutup poligon
    df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    st.title("🛰️ Overlay Poligon pada Imej Satelit")

    # 2. Mencipta Mapbox Plot
    fig = px.scatter_mapbox(
        df_poly, 
        lat="lat", 
        lon="lon", 
        hover_name="STN",
        zoom=17, 
        height=600
    )

    # Tambah garisan poligon
    fig.update_traces(mode='lines+markers', line=dict(width=3, color='red'))

    # Set gaya satelit
    # Anda boleh guna 'white-bg' + 'vancouver-canadian-cities-satellite' 
    # atau daftar Mapbox Token untuk 'satellite-streets'
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattr": "Esri World Imagery",
                "source": [
                    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                ]
            }
        ],
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.info("Nota: Koordinat telah ditukar secara simulasi dari format tempatan ke Lat/Lon untuk paparan peta.")
else:
    st.error("Fail data tidak dijumpai.")
