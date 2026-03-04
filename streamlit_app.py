import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- SIMULASI DATA PENGGUNA ---
# Dalam sistem sebenar, ini biasanya diambil dari database
USER_CREDENTIALS = {
    "admin1": "puo123",
    "pelajar": "geomatik2024",
    "pensyarah": "jka123"
}

# --- FUNGSI LOGIN & FORGOT PASSWORD ---
def login_page():
    # Menggunakan container untuk mencantikkan paparan tengah
    col_l, col_m, col_r = st.columns([1, 1, 1])
    
    with col_m:
        st.markdown("<h2 style='text-align: center;'>SISTEM LOGIN</h2>", unsafe_allow_html=True)
        
        # Menu pilihan antara Login atau Lupa Password
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        
        with tab1:
            user_id = st.text_input("ID Pengguna")
            user_pwd = st.text_input("Kata Laluan", type="password")
            
            if st.button("Masuk", use_container_width=True):
                if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == user_pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.success("Log masuk berjaya!")
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah!")
        
        with tab2:
            st.info("Sila masukkan ID anda untuk mendapatkan bantuan kata laluan.")
            forgot_id = st.text_input("Masukkan ID Pengguna anda")
            if st.button("Semak Password"):
                if forgot_id in USER_CREDENTIALS:
                    # Simulasi: Dalam realiti, hantar emel. Di sini kita paparkan hint.
                    st.warning(f"Kata laluan untuk ID {forgot_id} adalah: {USER_CREDENTIALS[forgot_id]}")
                else:
                    st.error("ID tidak ditemui dalam sistem.")

# --- INISIALISASI SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIK HALAMAN ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # Jika sudah login, paparkan butang Logout di sidebar
    if st.sidebar.button("Log Keluar (Logout)"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- HEADER (LOGO & TAJUK) ---
    logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png"
    col1, col2 = st.columns([1, 5])
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.info("Logo PUO")
    with col2:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader(f"Unit Geomatik - Selamat Datang, {st.session_state['user_id']}")

    st.markdown("---")

    # --- KOD UTAMA GEOMATIK ANDA BERMULA DI SINI ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Muat Naik Fail CSV (STN, E, N)", type=["csv"])
    
    # Tetapan Peta
    st.sidebar.header("⚙️ Tetapan Peta")
    show_satellite = st.sidebar.checkbox("🌏 Buka Layer Satelit (On/Off)", value=True)
    epsg_input = st.sidebar.text_input("Kod EPSG:", value="4390")
    zoom_val = st.sidebar.slider("🔍 Zum:", 15, 22, 20)
    
    # Tetapan Label
    st.sidebar.subheader("🏷️ Tetapan Label")
    show_stn = st.sidebar.checkbox("Papar Label Stesen (STN)", value=True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", value=True)
    show_area = st.sidebar.checkbox("Papar Label Luas Lot", value=True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s = 0; m += 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            if not {'STN', 'E', 'N'}.issubset(df.columns):
                st.error("Kolum STN, E, N diperlukan!")
            else:
                # Transformasi
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['E'].values, df['N'].values)
                df['lon'], df['lat'] = lon, lat
                
                df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                center_lat, center_lon = df['lat'].mean(), df['lon'].mean()

                # Bina Peta
                fig = go.Figure()
                fig.add_trace(go.Scattermapbox(
                    lat=df_poly['lat'], lon=df_poly['lon'],
                    mode='lines+markers', fill="toself",
                    fillcolor="rgba(255, 255, 0, 0.15)",
                    line=dict(width=3, color='yellow'),
                    marker=dict(size=8, color='red'),
                    name="Sempadan"
                ))

                # Label Bearing & Jarak (Sentiasa Muncul)
                if show_brg_dist:
                    for i in range(len(df_poly)-1):
                        p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                        dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                        brg = np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) % 360
                        fig.add_trace(go.Scattermapbox(
                            lat=[(p1['lat']+p2['lat'])/2], lon=[(p1['lon']+p2['lon'])/2],
                            mode='text', text=[f"<b>{decimal_to_dms(brg)}</b><br>{dist:.3f}m"],
                            textfont=dict(size=12, color="cyan", family="Arial Black")
                        ))

                if show_stn:
                    fig.add_trace(go.Scattermapbox(
                        lat=df['lat'], lon=df['lon'], mode='text', 
                        text=df['STN'].astype(str), textposition="top right",
                        textfont=dict(size=14, color="white", family="Arial Black")
                    ))

                if show_area:
                    area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
                    fig.add_trace(go.Scattermapbox(
                        lat=[center_lat], lon=[center_lon], mode='text', 
                        text=[f"<b>LUAS: {area:.2f} m²</b>"],
                        textfont=dict(size=18, color="yellow", family="Arial Black")
                    ))

                # Style & Satelit
                mapbox_style = "white-bg"
                layers = []
                if show_satellite:
                    layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]
                
                fig.update_layout(
                    mapbox=dict(style=mapbox_style, layers=layers, center=dict(lat=center_lat, lon=center_lon), zoom=zoom_val),
                    margin={"r":0,"t":0,"l":0,"b":0}, height=700, showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)
                st.write("### 📊 Jadual Data")
                st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)

        except Exception as e:
            st.error(f"Ralat: {e}")
