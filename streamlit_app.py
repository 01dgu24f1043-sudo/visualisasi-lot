import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- KREDENTIAL LOGIN ---
USER_CREDENTIALS = {
    "01dgu24f1043": "12345",
    "01dgu24f1013": "Nafiz0921",
    "pensyarah": "jka123"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login_page():
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        with tab1:
            u_id = st.text_input("ID Pengguna")
            u_pw = st.text_input("Kata Laluan", type="password")
            if st.button("Masuk", use_container_width=True):
                if u_id in USER_CREDENTIALS and USER_CREDENTIALS[u_id] == u_pw:
                    st.session_state["logged_in"], st.session_state["user_id"] = True, u_id
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah")
        with tab2:
            forgot_id = st.text_input("Masukkan ID Pengguna")
            if st.button("Semak Password"):
                if forgot_id in USER_CREDENTIALS:
                    st.info(f"Kata laluan: {USER_CREDENTIALS[forgot_id]}")
                else:
                    st.error("ID tidak ditemui")

if not st.session_state["logged_in"]:
    login_page()
else:
    # --- HEADER DASHBOARD ---
    col1, col2, col3 = st.columns([1, 4, 1.5])
    with col1:
        if os.path.exists("politeknik-ungku-umar-seeklogo-removebg-preview.png"):
            st.image("politeknik-ungku-umar-seeklogo-removebg-preview.png", width=120)
    with col2:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader("Jabatan Kejuruteraan Awam - Unit Geomatik")
    with col3:
        st.markdown(f"<div style='background-color:#f0f2f6;padding:10px;border-radius:10px;border-left:5px solid red;'>Selamat Datang<br><h3>HI {st.session_state['user_id']}</h3></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- SIDEBAR & TETAPAN ---
    st.sidebar.header("Konfigurasi")
    uploaded_file = st.sidebar.file_uploader("Muat Naik CSV", type=["csv"])
    
    with st.sidebar.expander("Tetapan Visual", expanded=True):
        show_satellite = st.checkbox("Paparan Satelit", True)
        zoom_val = st.slider("Zoom", 10, 22, 19)
        size_stn = st.slider("Saiz No Stesen", 10, 30, 14)
        size_brg = st.slider("Saiz Bearing/Jarak", 8, 25, 11)
        size_area = st.slider("Saiz Teks Luas", 15, 40, 25)

    show_stn = st.sidebar.checkbox("Papar Stesen", True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak", True)
    show_area = st.sidebar.checkbox("Papar Luas", True)

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(round((deg - d - m/60) * 3600))
        if s >= 60: s, m = 0, m + 1
        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()
            
            epsg_input = st.sidebar.text_input("Kod EPSG", "4390")
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

            fig = go.Figure()

            # LUKISAN POLIGON (Sempadan Lot)
            fig.add_trace(go.Scattermapbox(
                lat=df_poly['lat'], lon=df_poly['lon'],
                mode='lines+markers',
                fill="toself", fillcolor="rgba(255, 255, 0, 0.1)",
                line=dict(width=3, color="yellow"),
                marker=dict(size=8, color="red"),
                below="''" # Memastikan line di atas satelit
            ))

            # LABEL BEARING & JARAK (Dinamik & Berpusing)
            if show_brg_dist:
                offset_val = 0.000018
                for i in range(len(df_poly)-1):
                    p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                    dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                    dist, brg = np.sqrt(dE**2 + dN**2), np.degrees(np.arctan2(dE, dN)) % 360
                    
                    # Sudut visual untuk textangle
                    angle = np.degrees(np.arctan2(p2['lat'] - p1['lat'], p2['lon'] - p1['lon']))
                    if angle > 90: angle -= 180
                    elif angle < -90: angle += 180
                    
                    # Vektor normal untuk offset Atas/Bawah
                    mag = np.sqrt((p2['lon']-p1['lon'])**2 + (p2['lat']-p1['lat'])**2)
                    nx, ny = -(p2['lat']-p1['lat'])/mag, (p2['lon']-p1['lon'])/mag
                    mid_lat, mid_lon = (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2

                    # Bearing (Atas Garisan)
                    fig.add_trace(go.Scattermapbox(
                        lat=[mid_lat + ny * offset_val], lon=[mid_lon + nx * offset_val],
                        mode="text", text=[decimal_to_dms(brg)],
                        textfont=dict(size=size_brg, color="cyan"), textangle=-angle
                    ))
                    # Jarak (Bawah Garisan)
                    fig.add_trace(go.Scattermapbox(
                        lat=[mid_lat - ny * offset_val], lon=[mid_lon - nx * offset_val],
                        mode="text", text=[f"{dist:.3f} m"],
                        textfont=dict(size=size_brg, color="white"), textangle=-angle
                    ))

            # PAPARAN LUAS & STESEN
            if show_area:
                area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
                fig.add_trace(go.Scattermapbox(
                    lat=[df['lat'].mean()], lon=[df['lon'].mean()],
                    mode="text", text=[f"LUAS<br>{area:.2f} m²"],
                    textfont=dict(size=size_area, color="yellow", family="Arial Black")
                ))

            # LAYOUT & PETA
            layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]} if show_satellite else []]
            
            fig.update_layout(
                mapbox=dict(style="white-bg", layers=layers, center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()), zoom=zoom_val),
                uirevision="PUO_GEOMATIK", # Tetapan uirevision mengikut dokumentasi
                margin={"r":0,"t":0,"l":0,"b":0}, height=750, showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # JADUAL DATA
            st.subheader("Jadual Koordinat Lot")
            st.dataframe(df[['STN','E','N']], use_container_width=True)
            
            if st.sidebar.button("Log Keluar", type="primary"):
                st.session_state["logged_in"] = False
                st.rerun()

        except Exception as e:
            st.error(f"Ralat: {e}")
