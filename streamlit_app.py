import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Visualisasi LOT 11487 - PUO", layout="centered")

# --- HEADER: TAJUK & LOGO ---
col1, col2 = st.columns([1, 2])

logo_path = "politeknik-ungku-umar-seeklogo-removebg-preview.png"

with col1:
    st.markdown("<h1 style='text-align: left; margin-top: 20px;'POLITEKNIK UNGKO OMAR</h1>", unsafe_allow_html=True)

with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
    else:
        st.write("PUO")

st.markdown("---") 

def decimal_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(round((deg - d - m/60) * 3600))
    if s >= 60: s = 0; m += 1
    if m >= 60: m = 0; d += 1
    return f"{d}°{m:02d}'{s:02d}\""

uploaded_file = st.file_uploader("Muat naik fail CSV (E, N)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
            centroid_x, centroid_y = df['E'].mean(), df['N'].mean()
            
            max_n = df['N'].max()
            mid_e = df['E'].mean()

            fig = go.Figure()

            # 1. Plot Poligon
            fig.add_trace(go.Scatter(
                x=df_poly['E'], y=df_poly['N'],
                mode='lines+markers', fill="toself",
                line=dict(color='RoyalBlue', width=2),
                marker=dict(size=8, color='red'),
                name="Sempadan"
            ))

            # 2. Label Tajuk
            fig.add_annotation(
                x=mid_e, y=max_n + 1.2, 
                text="<b>LOT 11487</b>",
                showarrow=False,
                font=dict(size=22, color="black"),
                xref="x", yref="y"
            )

            # 3. Label Bearing & Jarak
            for i in range(len(df_poly)-1):
                x1, y1 = df_poly['E'].iloc[i], df_poly['N'].iloc[i]
                x2, y2 = df_poly['E'].iloc[i+1], df_poly['N'].iloc[i+1]
                
                dx, dy = x2 - x1, y2 - y1
                dist = np.sqrt(dx**2 + dy**2)
                brg_deg = np.degrees(np.arctan2(dx, dy)) % 360
                angle_rad = np.arctan2(dy, dx)
                angle_deg = np.degrees(angle_rad)
                
                display_angle = angle_deg
                if display_angle > 90: display_angle -= 180
                elif display_angle < -90: display_angle += 180

                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                off = 0.35

                fig.add_annotation(
                    x=mid_x - off * np.sin(angle_rad), y=mid_y + off * np.cos(angle_rad),
                    text=f"<b>{decimal_to_dms(brg_deg)}</b>", showarrow=False,
                    textangle=-display_angle, font=dict(size=9, color="black")
                )
                fig.add_annotation(
                    x=mid_x + off * np.sin(angle_rad), y=mid_y - off * np.cos(angle_rad),
                    text=f"<b>{dist:.3f} m</b>", showarrow=False,
                    textangle=-display_angle, font=dict(size=9, color="black")
                )

                # Nombor Stesen
                dx_out, dy_out = x1 - centroid_x, y1 - centroid_y
                mag = np.sqrt(dx_out**2 + dy_out**2)
                label_off = 0.7
                fig.add_annotation(
                    x=x1 + (dx_out/mag)*label_off, y=y1 + (dy_out/mag)*label_off,
                    text=f"{i+1}", showarrow=False,
                    font=dict(size=11, color="red", family="Arial Black"),
                    bgcolor="white", borderpad=2
                )

            # 4. Luas
            area = 0.5 * np.abs(np.dot(df_poly['E'], np.roll(df_poly['N'], 1)) - np.dot(df_poly['N'], np.roll(df_poly['E'], 1)))
            fig.add_annotation(
                x=centroid_x, y=centroid_y, 
                text=f"<b>LUAS<br>{area:.2f} m²</b>",
                showarrow=False, font=dict(size=14, color="red"),
                bgcolor="rgba(255, 255, 255, 0.7)"
            )

            fig.update_layout(
                xaxis=dict(title="Easting (E)", gridcolor='lightgrey'),
                yaxis=dict(title="Northing (N)", gridcolor='lightgrey', scaleanchor="x", scaleratio=1),
                width=800, height=850, plot_bgcolor='white'
            )

            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Selesai! LOT 11487 telah dijana.")
            
    except Exception as e:

        st.error(f"Ralat: {e}")
