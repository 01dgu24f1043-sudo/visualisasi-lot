import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
import matplotlib.pyplot as plt
from pyproj import Transformer
import io

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# --- DATABASE PENGGUNA (Simulasi) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "01dgu24f1043": {"nama": "Ahmad", "pwd": "12345"},
        "01dgu24f1013": {"nama": "Nafiz", "pwd": "Nafiz0921"},
        "pensyarah": {"nama": "Dr. Surveyor", "pwd": "jka123"}
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- FUNGSI PEMBANTU ---
def decimal_to_dms(deg):
    d = int(deg); m = int((deg - d) * 60); s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    return f"{d}°{m:02d}'{s:02d}\""

# --- FUNGSI LOGIN ---
def login_page():
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        with tab1:
            user_id = st.text_input("ID Pengguna")
            user_pwd = st.text_input("Kata Laluan", type="password")
            if st.button("Masuk", use_container_width=True):
                db = st.session_state["user_db"]
                if user_id in db and db[user_id]["pwd"] == user_pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.session_state["user_name"] = db[user_id]["nama"]
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah")

# --- LOGIK UTAMA ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # Sidebar Logout
    if st.sidebar.button("🚪 Log Keluar"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- HEADER ---
    st.title("POLITEKNIK UNGKU OMAR")
    st.subheader(f"Selamat Datang, {st.session_state['user_name'].upper()}")
    st.markdown("---")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.header("📁 Fail Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

    st.sidebar.header("🛠️ Tetapan Paparan")
    size_stn = st.sidebar.slider("Saiz No Stesen", 8, 25, 12)
    size_brg = st.sidebar.slider("Saiz Bearing/Jarak", 6, 20, 9)
    size_area = st.sidebar.slider("Saiz Luas", 10, 40, 20)
    epsg_input = st.sidebar.text_input("Kod EPSG (Semenanjung: 4390)", "4390")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.upper()

            # 1. Transformasi Koordinat untuk Plotly
            transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

            # 2. Pengiraan Luas & Perimeter
            area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            
            # --- PAPARAN PETA SATELIT (PLOTLY) ---
            st.subheader("🌍 Paparan Satelit (Interaktif)")
            fig = go.Figure()
            fig.add_trace(go.Scattermapbox(
                lat=df_poly['lat'], lon=df_poly['lon'],
                mode='lines+markers',
                fill="toself", fillcolor="rgba(255,255,0,0.1)",
                line=dict(width=3, color="yellow"),
                text=df_poly['STN']
            ))
            fig.update_layout(
                mapbox=dict(style="white-bg", 
                            layers=[{"below": 'traces', "sourcetype": "raster", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}],
                            center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()), zoom=18),
                margin={"r":0,"t":0,"l":0,"b":0}, height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- PAPARAN PELAN TEKNIKAL (MATPLOTLIB - TEKS SENGET) ---
            st.markdown("---")
            st.subheader("🖋️ Pelan Ukur Digital (Teks Berotasi)")
            
            

            fig_mpl, ax = plt.subplots(figsize=(10, 10))
            ax.plot(df_poly['E'], df_poly['N'], color='black', linewidth=1.5, marker='o', markersize=4, markerfacecolor='red')

            for i in range(len(df_poly)-1):
                p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                
                # Kira Bearing & Sudut Putaran Teks
                brg_deg = np.degrees(np.arctan2(dE, dN)) % 360
                
                # Sudut Matematik (Matplotlib guna 0 di timur, kaunter-jam)
                # Kita pusingkan teks supaya selari dengan garisan
                mpl_angle = 90 - brg_deg 
                if mpl_angle > 90: mpl_angle -= 180
                elif mpl_angle < -90: mpl_angle += 180

                mid_E, mid_N = (p1['E'] + p2['E'])/2, (p1['N'] + p2['N'])/2
                
                # Label Bearing/Jarak (SENGET)
                ax.text(mid_E, mid_N, f"{decimal_to_dms(brg_deg)}\n{dist:.3f}m", 
                        fontsize=size_brg, color='blue', rotation=mpl_angle, 
                        ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
                
                # Label No Stesen
                ax.text(p1['E'], p1['N'], f" {int(p1['STN'])}", fontsize=size_stn, fontweight='bold', color='black')

            # Label Luas di tengah
            ax.text(df['E'].mean(), df['N'].mean(), f"LUAS\n{area:.2f} m²", 
                    fontsize=size_area, color='red', ha='center', fontweight='bold', alpha=0.3)

            ax.set_aspect('equal')
            ax.axis('off')
            st.pyplot(fig_mpl)

            # Button Simpan
            buf = io.BytesIO()
            fig_mpl.savefig(buf, format="png", dpi=300)
            st.download_button("📥 Muat Turun Pelan (PNG)", data=buf.getvalue(), file_name="pelan_lot.png", mime="image/png")

        except Exception as e:
            st.error(f"Sila semak format fail anda. Ralat: {e}")

    else:
        st.info("Sila muat naik fail CSV untuk bermula.")
