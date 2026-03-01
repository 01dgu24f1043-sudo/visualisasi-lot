import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="PUO - Visualisasi Lot", layout="wide")

st.title("🛰️ Paparan Lot Poligon")

# 1. BACA FAIL
if os.path.exists("data ukur.csv"):
    df = pd.read_csv("data ukur.csv")
    
    # 2. PASTIKAN DATA DIAMBIL DENGAN BETUL
    # CSV anda: STN, x, y
    # Kita buat dataframe baru khusus untuk plotting
    plot_df = pd.DataFrame()
    plot_df['stn'] = df['STN']
    plot_df['lon'] = df['x'] # Longitude
    plot_df['lat'] = df['y'] # Latitude
    
    # 3. TUTUP POLIGON (PENTING: supaya garisan bersambung balik ke titik asal)
    df_closed = pd.concat([plot_df, plot_df.iloc[[0]]], ignore_index=True)

    # 4. BINA PETA
    fig = go.Figure()

    # Tambah garisan poligon
    fig.add_trace(go.Scattermapbox(
        lat=df_closed['lat'],
        lon=df_closed['lon'],
        mode='lines+markers+text',
        fill="toself",
        fillcolor="rgba(255, 255, 0, 0.3)", # Kuning lutsinar
        line=dict(width=4, color='yellow'),
        marker=dict(size=12, color='red'),
        text=df_closed['stn'],
        textposition="top right"
    ))

    # 5. CONFIGURATION PETA
    fig.update_layout(
        mapbox_style="open-street-map", # Guna ini dulu untuk pastikan poligon muncul
        mapbox=dict(
            center=dict(lat=plot_df['lat'].mean(), lon=plot_df['lon'].mean()),
            zoom=18
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Paparkan data di bawah peta untuk semakan manual
    st.subheader("Semakan Data CSV")
    st.write(df)

else:
    st.error("Fail 'data ukur.csv' tidak dijumpai.")
