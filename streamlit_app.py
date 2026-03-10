# Sediakan senarai feature untuk GeoJSON
features = []

# TAMBAH TITIK STESEN
for i, row in df.iterrows():
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [row['lon'], row['lat']]},
        "properties": {
            "Stesen": f"STN {int(row['STN'])}",
            "N": row['N'],
            "E": row['E'],
            "Jenis": "Titik Stesen"
        }
    })

# TAMBAH POLIGON (LUAS)
features.append({
    "type": "Feature",
    "geometry": {
        "type": "Polygon", 
        "coordinates": [[ [p[1], p[0]] for p in points ] + [[points[0][1], points[0][0]]]]
    },
    "properties": {
        "Luas_m2": round(area, 3),
        "Perimeter": round(total_dist, 3),
        "Jenis": "Sempadan Lot"
    }
})

geojson_data = {
    "type": "FeatureCollection",
    "features": features
}
