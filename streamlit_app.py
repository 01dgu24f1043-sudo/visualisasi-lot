import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="PUO - Visualisasi Lot", layout="wide")

st.markdown("<h2 style='text-align: center;'>🛰️ Paparan Lot Poligon (WGS84)</h2>", unsafe_allow_html=True)
st.markdown("---")

default_file = "data ukur.csv"

if os.path.exists(default_file):
    df = pd.read_csv(default_file)
    
    # Memastikan kolum x dan y wujud
    if 'x' in df.columns and 'y' in df.columns:
        # PENTING: Penukaran nama kolum
        df_plot = df.rename(columns={'x': 'lon', 'y': 'lat'})
        
        # Tutup poligon
        df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

        # 2. BINA PETA (Guna Mapbox Built-in Style)
        fig = go.Figure()

        # Tambah Poligon
        fig.add_trace(go.Scattermapbox(
            lat=df_poly['lat'],
            lon=df_poly['lon'],
            mode='lines+markers+text',
            fill="toself",
            fillcolor="rgba(0, 255, 255, 0.3)", # Biru lutsinar
            marker=dict(size=12, color='red'),
            line=dict(width=3, color='yellow'),
            text=df_poly['STN'],
            textposition="top right",
            hoverinfo='text+lat+lon'
        ))

        # 3. SETTING MAPBOX (Pilihan yang paling stabil)
        fig.update_layout(
            # 'open-street-map' adalah yang paling stabil dan tidak akan putih
            # Jika anda mahu satelit, guna 'stamen-terrain' atau 'carto-positron'
            mapbox_style="open-street-map", 
            mapbox=dict(
                center=dict(lat=df_plot['lat'].mean(), lon=df_plot['lon'].mean()),
                zoom=18
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Paparkan Data di bawah peta (Backup jika peta gagal)
        st.write("### 📋 Semakan Data Koordinat")
        st.dataframe(df_plot)
        
    else:
        st.error("Ralat: Pastikan fail CSV mempunyai kolum 'x' dan 'y'.")
else:
    st.error("Fail 'data ukur.csv' tidak dijumpai. Sila muat naik ke GitHub.")

# --- SELESAIKAN ISU PUTIH ---
st.info("""
**Jika skrin masih putih, ini langkah terakhir:**
1. **Refresh Browser**: Tekan Ctrl+F5 (Windows) atau Cmd+Shift+R (Mac).
2. **Uji di Telefon**: Cuba buka link aplikasi anda di telefon pintar. Jika di telefon muncul, bermakna WiFi/Computer anda yang menyekat imej tersebut.
3. **Cek Fail CSV**: Pastikan tiada baris kosong di dalam fail CSV anda.
""")
