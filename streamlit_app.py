import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="PUO - Visualisasi Lot Satelit", layout="wide")

st.markdown("<h2 style='text-align: center;'>🛰️ Paparan Lot Poligon (Satelit di Belakang)</h2>", unsafe_allow_html=True)
st.markdown("---")

default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # Pastikan kolum x dan y wujud (x=lon, y=lat)
    if 'x' in df.columns and 'y' in df.columns:
        df_plot = df.rename(columns={'x': 'lon', 'y': 'lat'})
        
        # Tutup poligon (sambung balik ke stesen 1)
        df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

        # 2. BINA PETA
        fig = go.Figure()

        # Tambah Poligon (Ini dipanggil 'trace')
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'],
            lon=df_poly['lon'],
            mode='lines+markers+text',
            fill="toself",
            fillcolor="rgba(255, 255, 0, 0.4)", # Kuning lutsinar
            marker=dict(size=12, color='red'),
            line=dict(width=3, color='yellow'),
            text=df_poly['STN'],
            textposition="top right",
            name="Lot Sempadan"
        ))

        # 3. KONFIGURASI LAYOUT & LAYER SATELIT
        fig.update_layout(
            mapbox=dict(
                style="white-bg", # Latar belakang kosong supaya tidak ganggu satelit
                layers=[
                    {
                        "below": 'traces', # PENTING: Meletakkan satelit di BELAKANG poligon
                        "sourcetype": "raster",
                        "sourceattribution": "Google Satellite",
                        "source": [
                            # Menggunakan pelayan Google Satellite yang sangat stabil
                            "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                        ]
                    }
                ],
                center=dict(lat=df_plot['lat'].mean(), lon=df_plot['lon'].mean()),
                zoom=19 # Zoom dekat untuk nampak lot
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=700,
            showlegend=False
        )

        # Paparkan Peta
        st.plotly_chart(fig, use_container_width=True)
        
        # Paparkan Data untuk semakan
        with st.expander("Klik untuk lihat data koordinat"):
            st.dataframe(df_plot[['STN', 'lat', 'lon']])
            
    else:
        st.error("Ralat: Fail CSV mesti mempunyai kolum 'x' dan 'y'.")
else:
    st.error("Fail 'data ukur.csv' tidak dijumpai. Sila muat naik ke GitHub.")
