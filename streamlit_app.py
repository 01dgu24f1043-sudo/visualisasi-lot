# --- PROSES GEOJSON UNTUK AUTOMATIK DI QGIS ---
        features_for_geojson = []

        # 1. Garisan Sempadan (Untuk paparan Bearing & Jarak)
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            brg = np.degrees(np.arctan2(dE, dN)) % 360
            
            features_for_geojson.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]},
                "properties": {
                    "Label_Sempadan": f"{decimal_to_dms(brg)}\n{dist:.3f}m",
                    "Jenis": "Sempadan"
                }
            })

        # 2. Titik Stesen (Untuk paparan No Stesen)
        for i, row in df.iterrows():
            features_for_geojson.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row['lon'], row['lat']]},
                "properties": {
                    "Label_Stesen": f"STN {int(row['STN'])}",
                    "Jenis": "Stesen"
                }
            })

        # 3. Poligon (Untuk paparan Luas di tengah)
        features_for_geojson.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]},
            "properties": {
                "Label_Luas": f"LUAS: {area:.3f} m²",
                "Jenis": "Lot"
            }
        })
