import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer
import io

# ... (Kekalkan kod login dan sidebar anda yang sedia ada) ...

if uploaded_file:
    try:
        # --- PROSES DATA ---
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        # Transformasi Koordinat (Kekalkan EPSG anda)
        epsg_input = st.sidebar.text_input("Kod EPSG", "4390")
        transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # --- BAHAGIAN 1: PETA INTERAKTIF (PLOTLY) ---
        # (Kekalkan kod Plotly anda di sini untuk paparan Satelit)
        
        st.markdown("---")
        st.subheader("🖋️ Pelan Ukur Geomatik (Teks Berotasi)")

        # --- BAHAGIAN 2: MATPLOTLIB (UNTUK TEKS SENGET) ---
        fig_mpl, ax = plt.subplots(figsize=(10, 10))
        
        # Plot garisan lot
        ax.plot(df_poly['E'], df_poly['N'], color='black', linewidth=2, marker='o', markerfacecolor='red')

        for i in range(len(df_poly)-1):
            p1, p2 = df_poly.iloc[i], df_poly.iloc[i+1]
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            
            # Kira Bearing & Sudut Putaran
            angle_rad = np.arctan2(dE, dN)
            brg_deg = np.degrees(angle_rad) % 360
            
            # Sudut teks: Matplotlib guna sudut dari paksi-X (horizontal)
            # Kita tukar bearing (dari North) ke sudut Matematik
            mpl_angle = 90 - brg_deg 
            
            # Pastikan teks tidak terbalik (sentiasa boleh dibaca dari bawah/kanan)
            if mpl_angle > 90: mpl_angle -= 180
            if mpl_angle < -90: mpl_angle += 180

            # Titik tengah untuk letak teks
            mid_E, mid_N = (p1['E'] + p2['E'])/2, (p1['N'] + p2['N'])/2
            
            # Label Bearing & Jarak (SENGET IKUT GARISAN)
            label = f"{decimal_to_dms(brg_deg)}\n{dist:.3f}m"
            ax.text(mid_E, mid_N, label, 
                    fontsize=size_brg, 
                    color='blue',
                    rotation=mpl_angle, 
                    ha='center', va='bottom',
                    rotation_mode='anchor')
            
            # Label No Stesen
            ax.text(p1['E'], p1['N'], f"  {p1['STN']}", fontsize=size_stn, fontweight='bold')

        # Label Luas di tengah
        area = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
        ax.text(df['E'].mean(), df['N'].mean(), f"LUAS\n{area:.2f} m²", 
                fontsize=size_area, color='red', ha='center', fontweight='bold', alpha=0.3)

        ax.set_aspect('equal', adjustable='box')
        ax.axis('off') # Buang grid/axis supaya nampak macam pelan betul
        
        st.pyplot(fig_mpl)

        # --- BUTTON DOWNLOAD IMEJ ---
        buf = io.BytesIO()
        fig_mpl.savefig(buf, format="png", dpi=300)
        st.download_button(
            label="🖼️ Simpan Pelan Sebagai PNG",
            data=buf.getvalue(),
            file_name="pelan_geomatik_puo.png",
            mime="image/png"
        )

    except Exception as e:
        st.error(f"Ralat teknikal: {e}")
