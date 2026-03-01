import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="PUO - Visualisasi Lot WGS84", layout="wide")

st.markdown("<h2 style='text-align: center;'>🛰️ Paparan Satelit Lot Poligon</h2>", unsafe_allow_html=True)
st.markdown("---")

# --- PEMPROSESAN DATA ---
default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # Pastikan kolum x (lon) dan y (lat) wujud
    if 'x' in df.columns and 'y' in df.columns:
        # Kita namakan semula kolum untuk Plotly
        df_plot = df.rename(columns={'x': 'lon', 'y': 'lat'})
        
        # Tutup poligon
        df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

        # 2. BINA VISUALISASI
        fig = go.Figure()

        # Tambah Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'],
            lon=df_poly['lon'],
            mode='lines+markers+text',
            fill="toself",
            fillcolor="rgba(0, 255, 255, 0.3)", # Biru cyan lutsinar
            marker=dict(size=12, color='red'),
            line=dict(width=3, color='yellow'),
            text=df_poly['STN'],
            textposition="top right",
            hoverinfo='text+lat+lon'
        ))

        # 3. KONFIGURASI MAPBOX (VERSI STABIL)
        # Kita gunakan style 'open-street-map' sebagai base jika satelit gagal
        # Kemudian kita tindih dengan layer satelit yang berbeza (Mapbox/Stamen)
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "Google Satellite",
                        "source": [
                            # Guna server Google sebagai alternatif terakhir (sangat stabil)
                            "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
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
        
        # JADUAL DATA (Untuk rujukan jika peta tidak muncul)
        st.write("### 📋 Data Koordinat")
        st.dataframe(df_plot[['STN', 'lat', 'lon']])
        
    else:
        st.error("Ralat: Pastikan fail CSV mempunyai kolum 'x' dan 'y'.")
else:
    st.error("Fail 'data ukur.csv' tidak dijumpai. Sila muat naik ke GitHub.")

st.info("💡 **Tips Jika Putih:** Cuba zoom out (kecilkan peta) atau guna pelayar web lain (seperti Firefox/Edge).")
