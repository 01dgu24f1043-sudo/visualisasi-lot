# --- LABEL BEARING & JARAK (LOGIK PUTARAN 180°) ---
            if show_brg:
                # 1. Kira sudut asas untuk orientasi teks (Bearing - 90 darjah)
                calc_angle = brg - 90
                
                # 2. LOGIK PUSING 180: Jika bearing antara 90° hingga 270°
                # Teks akan dipusingkan 180° supaya TIDAK TERBALIK bila dibaca,
                # tetapi nilai teks (299° atau 119°) TETAP KEKAL sama.
                if 90 < brg < 270:
                    calc_angle -= 180 
                
                h_gap = text_gap / 2
                
                # HTML untuk paparan teks yang dinamik
                l_html = f'''
                <div style="
                    transform: rotate({calc_angle}deg); 
                    display: flex; 
                    flex-direction: column; 
                    justify-content: space-between; 
                    align-items: center; 
                    color: #00FFFF; 
                    font-weight: bold; 
                    font-size: {size_brg}pt; 
                    text-shadow: 2px 2px 4px black; 
                    width: 200px; 
                    margin-left: -100px; 
                    height: {text_gap}px; 
                    margin-top: -{h_gap}px; 
                    pointer-events: none; 
                    text-align: center;">
                    
                    <div>{decimal_to_dms(brg)}</div>
                    <div style="color: #FFD700;">{dist:.3f}m</div>
                </div>
                '''
                
                mid_point = [(p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2]
                folium.Marker(mid_point, icon=folium.DivIcon(html=l_html)).add_to(m)
