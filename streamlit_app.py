import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# ... (Kekalkan bahagian Login & Header asal anda) ...

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()

        # 1. Transformasi Koordinat
        epsg_input = st.sidebar.text_input("Kod EPSG", "4390")
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        
        # Titik tengah untuk zoom peta
        center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

        # 2. Bina Peta Folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)
        
        # Tambah Layer Satelit Google
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google Satelit',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # 3. Lukis Garisan Lot & Teks Berotasi
        points = []
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)] # Titik seterusnya (loop balik ke asal)
            
            loc1 = [p1['lat'], p1['lon']]
            loc2 = [p2['lat'], p2['lon']]
            points.append(loc1)

            # Kira Bearing & Jarak
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            brg_deg = np.degrees(np.arctan2(dE, dN)) % 360
            
            # SUDUT TEKS: Kita guna CSS Rotation
            # Folium membolehkan kita letak DivIcon yang boleh di-rotate
            text_angle = brg_deg - 90
            if 90 < brg_deg < 270: text_angle -= 180 # Supaya tak terbalik

            mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2

            # Tambah Label (Bearing & Jarak) yang SENGET
            label_html = f'''
                <div style="transform: rotate({text_angle}deg); 
                            white-space: nowrap; 
                            color: yellow; 
                            font-weight: bold; 
                            font-size: {size_brg}pt;
                            text-shadow: 1px 1px 2px black;">
                    {decimal_to_dms(brg_deg)}<br>{dist:.3f}m
                </div>'''
            
            folium.Marker(
                [mid_lat, mid_lon],
                icon=folium.DivIcon(html=label_html)
            ).add_to(m)

            # Tambah Nombor Stesen
            folium.Marker(
                loc1,
                icon=folium.DivIcon(html=f'<b style="color:white; font-size:{size_stn}pt;">{int(p1["STN"])}</b>')
            ).add_to(m)

        # Lukis Poligon
        folium.Polygon(
            locations=points,
            color='yellow',
            weight=3,
            fill=True,
            fill_color='yellow',
            fill_opacity=0.1
        ).add_to(m)

        # 4. Paparkan Peta Gabungan
        st.subheader("🗺️ Peta Lot Terintegrasi (Satelit + Teks Senget)")
        st_folium(m, width="100%", height=600)

    except Exception as e:
        st.error(f"Ralat: {e}")
