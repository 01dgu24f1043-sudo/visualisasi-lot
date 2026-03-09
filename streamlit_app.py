import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from pyproj import Transformer

st.set_page_config(page_title="Sistem Lot Geomatik PUO", layout="wide")

# USER LOGIN
USER_CREDENTIALS = {
    "01dgu24f1043": "12345",
    "01dgu24f1013": "Nafiz0921",
    "pensyarah": "jka123"
}

def login_page():
    col_l,col_m,col_r = st.columns([1,1,1])

    with col_m:

        st.markdown("<h2 style='text-align:center;'>🔐 Sistem Survey Lot PUO</h2>",unsafe_allow_html=True)

        tab1,tab2 = st.tabs(["Log Masuk","Lupa Kata Laluan"])

        with tab1:

            user_id = st.text_input("ID Pengguna")
            user_pwd = st.text_input("Kata Laluan",type="password")

            if st.button("Masuk",use_container_width=True):

                if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id]==user_pwd:

                    st.session_state["logged_in"]=True
                    st.session_state["user_id"]=user_id
                    st.rerun()

                else:

                    st.error("ID atau Kata Laluan salah")

        with tab2:

            forgot_id = st.text_input("Masukkan ID Pengguna")

            if st.button("Semak Password"):

                if forgot_id in USER_CREDENTIALS:

                    st.warning(f"Kata laluan: {USER_CREDENTIALS[forgot_id]}")

                else:

                    st.error("ID tidak ditemui")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"]=False

if not st.session_state["logged_in"]:

    login_page()

else:

    logo_path="politeknik-ungku-umar-seeklogo-removebg-preview.png"

    col1,col2,col3 = st.columns([1,4,1.5])

    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path,width=120)

    with col2:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader("Jabatan Kejuruteraan Awam - Unit Geomatik")

    with col3:
        st.markdown(f"""
        <div style="background-color:#f0f2f6;padding:10px;border-radius:10px;border-left:5px solid red;margin-top:20px;">
        <p>Selamat Datang</p>
        <h3>HI {st.session_state['user_id']}</h3>
        </div>
        """,unsafe_allow_html=True)

    st.markdown("---")

    st.sidebar.header("Fail Data")

    uploaded_file = st.sidebar.file_uploader("Upload CSV",type=["csv"])

    st.sidebar.header("Tetapan Peta")

    show_satellite = st.sidebar.checkbox("Layer Satellite",True)
    zoom_val = st.sidebar.slider("Zoom",15,22,19)

    st.sidebar.subheader("Saiz Tulisan")

    size_stn = st.sidebar.slider("No Stesen",10,30,14)
    size_brg = st.sidebar.slider("Bearing",8,25,11)
    size_area = st.sidebar.slider("Luas",15,40,20)

    st.sidebar.subheader("Paparan Label")

    show_stn = st.sidebar.checkbox("Papar Stesen",True)
    show_brg_dist = st.sidebar.checkbox("Papar Bearing & Jarak",True)
    show_area = st.sidebar.checkbox("Papar Luas",True)

    def decimal_to_dms(deg):

        d=int(deg)
        m=int((deg-d)*60)
        s=int(round((deg-d-m/60)*3600))

        if s>=60:
            s=0
            m+=1

        return f"{d}°{m:02d}'{s:02d}\""

    if uploaded_file is not None:

        try:

            df = pd.read_csv(uploaded_file)

            df.columns = df.columns.str.strip().str.upper()

            epsg_input = st.sidebar.text_input("Kod EPSG","4390")

            transformer = Transformer.from_crs(f"EPSG:{epsg_input}","EPSG:4326",always_xy=True)

            lon,lat = transformer.transform(df['E'].values,df['N'].values)

            df['lon']=lon
            df['lat']=lat

            df_poly = pd.concat([df,df.iloc[[0]]],ignore_index=True)

            fig = go.Figure()

            # POLYGON
            fig.add_trace(go.Scattermapbox(

                lat=df_poly['lat'],
                lon=df_poly['lon'],

                mode='lines+markers',

                fill="toself",
                fillcolor="rgba(255,255,0,0.1)",

                line=dict(width=3,color="yellow"),
                marker=dict(size=8,color="red")

            ))

            # STATION LABEL
            if show_stn:

                fig.add_trace(go.Scattermapbox(

                    lat=df['lat'],
                    lon=df['lon'],

                    mode="text",

                    text=df['STN'].astype(str),

                    textposition="top right",

                    textfont=dict(
                        size=size_stn,
                        color="white"
                    )

                ))

            # ======================
            # BEARING + DISTANCE
            # ======================

            if show_brg_dist:

                offset = 0.000015

                for i in range(len(df_poly)-1):

                    p1 = df_poly.iloc[i]
                    p2 = df_poly.iloc[i+1]

                    dE = p2['E'] - p1['E']
                    dN = p2['N'] - p1['N']

                    dist = np.sqrt(dE**2 + dN**2)

                    brg = np.degrees(np.arctan2(dE, dN)) % 360

                    mid_lat = (p1['lat'] + p2['lat']) / 2
                    mid_lon = (p1['lon'] + p2['lon']) / 2

                    dx = p2['lon'] - p1['lon']
                    dy = p2['lat'] - p1['lat']

                    length = np.sqrt(dx**2 + dy**2)

                    nx = -dy / length
                    ny = dx / length

                    lat_brg = mid_lat + ny * offset
                    lon_brg = mid_lon + nx * offset

                    lat_dist = mid_lat - ny * offset
                    lon_dist = mid_lon - nx * offset

                    angle = np.degrees(np.arctan2(dy, dx))

                    if angle > 90 or angle < -90:
                        angle += 180

                    # BEARING
                    fig.add_trace(go.Scattermapbox(

                        lat=[lat_brg],
                        lon=[lon_brg],

                        mode="text",

                        text=[decimal_to_dms(brg)],

                        textfont=dict(
                            size=size_brg,
                            color="cyan"
                        ),

                        textangle=angle,
                        textposition="middle center"

                    ))

                    # DISTANCE
                    fig.add_trace(go.Scattermapbox(

                        lat=[lat_dist],
                        lon=[lon_dist],

                        mode="text",

                        text=[f"{dist:.3f} m"],

                        textfont=dict(
                            size=size_brg,
                            color="cyan"
                        ),

                        textangle=angle,
                        textposition="middle center"

                    ))

            # AREA
            if show_area:

                area = 0.5*np.abs(
                    np.dot(df['E'],np.roll(df['N'],1))
                    -
                    np.dot(df['N'],np.roll(df['E'],1))
                )

                fig.add_trace(go.Scattermapbox(

                    lat=[df['lat'].mean()],
                    lon=[df['lon'].mean()],

                    mode="text",

                    text=[f"LUAS<br>{area:.2f} m²"],

                    textfont=dict(
                        size=size_area,
                        color="yellow"
                    )

                ))

            layers=[]

            if show_satellite:

                layers=[{

                    "below":'traces',
                    "sourcetype":"raster",

                    "source":[
                    "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                    ]

                }]

            fig.update_layout(

                mapbox=dict(

                    style="white-bg",
                    layers=layers,

                    center=dict(
                        lat=df['lat'].mean(),
                        lon=df['lon'].mean()
                    ),

                    zoom=zoom_val

                ),

                margin={"r":0,"t":0,"l":0,"b":0},

                height=750,
                showlegend=False

            )

            st.plotly_chart(fig,use_container_width=True)

            # COORDINATE TABLE
            st.subheader("Jadual Koordinat Lot")

            table_df = df[['STN','E','N']].copy()

            table_df['E']=table_df['E'].round(3)
            table_df['N']=table_df['N'].round(3)

            st.dataframe(table_df,use_container_width=True)

            csv = table_df.to_csv(index=False).encode('utf-8')

            st.download_button(
                "Download Coordinate Table",
                csv,
                "coordinate_lot.csv",
                "text/csv"
            )

            if st.sidebar.button("Log Keluar"):

                st.session_state["logged_in"]=False
                st.rerun()

        except Exception as e:

            st.error(f"Ralat: {e}")
