import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Membaca data
if os.path.exists("data ukur.csv"):
    df = pd.read_csv("data ukur.csv")
    
    # 1. Tukar koordinat ke format yang betul
    # x = lon (102.52...), y = lat (2.10...)
    df_plot = df.rename(columns={'x': 'lon', 'y': 'lat'})
    
    # 2. Tutup poligon
    df_poly = pd.concat([df_plot, df_plot.iloc[[0]]], ignore_index=True)

    fig = go.Figure()

    # 3. Lukis Poligon (Guna Scattermapbox)
    fig.add_trace(go.Scattermapbox(
        lat=df_poly['lat'],
        lon=df_poly['lon'],
        mode='lines+markers',
        fill="toself",
        fillcolor="rgba(255, 255, 0, 0.4)", # Kuning terang
        line=dict(width=4, color='red'),    # Garisan merah tebal
        marker=dict(size=10),
        text=df_poly['STN']
    ))

    # 4. Layout
    fig.update_layout(
        mapbox=dict(
            style="white-bg", # Mesti 'white-bg' untuk layer custom
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }],
            center=dict(lat=df_plot['lat'].mean(), lon=df_plot['lon'].mean()),
            zoom=19
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
