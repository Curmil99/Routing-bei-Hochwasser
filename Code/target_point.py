import os
import geopandas as gpd
import matplotlib.pyplot as plt
from pyproj import Transformer
import plots as my_plots
    


def find_worst_affected_areas(bewohnte_kacheln_in_flood, flood_gdf, gemeinde_name, gemeinde):
    """
    Löse die Kanten zwischen den bevölkerungskachel auf und gebe die Top-5 der neuen geclusterten Polygonen zurück. 
    Nach Bevölkerungszahl sortiert
    """
 

    ziel_crs = "EPSG:25833"
    gemeinde = gemeinde.to_crs(ziel_crs)
    flood_gdf = flood_gdf.to_crs(ziel_crs)
    bewohnte_kacheln_in_flood = bewohnte_kacheln_in_flood.to_crs(ziel_crs)


    # 1. alles vereinigen
    merged = bewohnte_kacheln_in_flood.unary_union

    # 2.kleine Lücken zwischen Kacheln schließen 
    merged = merged.buffer(5).buffer(-5)

    # 3. In Einzelcluster zerlegen
    clusters_geom = (
        gpd.GeoDataFrame(geometry=[merged], crs=bewohnte_kacheln_in_flood.crs)
        .explode(index_parts=False)
        .reset_index(drop=True)
    )

    clusters_geom["cluster_id"] = clusters_geom.index

    
    #Original-Kacheln den Clustern zuordnen 
    #welche Kachel schneidet sich mit einem von den neuen Polygonen -> bekommt die ID von dem Polygon
    kacheln_mit_cluster = gpd.sjoin(
        bewohnte_kacheln_in_flood,
        clusters_geom,
        how="left",
        predicate="intersects"
    )


    # Einwohner pro Cluster summieren
    bew_clusters = (
        kacheln_mit_cluster
        .groupby("cluster_id", as_index=False)      #Es wird nach zugeordnetem Polygon gruppiert
        .agg({"Einwohner": "sum"})                  #Es werden die Einwohner der einzelen Gruppen/Polygone aufsummiert
        .merge(clusters_geom, on="cluster_id")      
    )

    bew_clusters = gpd.GeoDataFrame(bew_clusters, geometry="geometry", crs=clusters_geom.crs)   
    bew_clusters["centroid"] = bew_clusters.geometry.centroid               #Für jedes Polygonwird der geografische Zentroid berechnet

    
    # sortieren der Polygone anhand der Einwohneranzahl
    top5 = bew_clusters.sort_values("Einwohner", ascending=False).head(5)

    #Für Ausgabe des betroffenen Bevölkerungpolygons
    polygons_top5 = list(top5.geometry)



    #------------------------------------------------------------------
    # Ab hier Debbugging, Visualisierung und Export der Daten für QGIS
    #------------------------------------------------------------------


    #Grenzen von Flood auflösen (nur für spätere Darstellung)
    flood_clean = (
        flood_gdf              
        .pipe(gpd.clip, gemeinde)       #Zuschneiden der Flut auf die Gemeinde
        .dissolve()                     #Grenzen zwischen den Kacheln auflösen
        .explode(index_parts=False)     #Macht MultiPolygone zu jeweils einzelnen
        .reset_index(drop=True)         #Macht neuen Index
    )

    my_plots.plot2_stärkst_betroffene_cluster(flood_clean, gemeinde_name, gemeinde, bew_clusters, top5)
    


    print(f"✅ {len(bewohnte_kacheln_in_flood)} Raster → {len(bew_clusters)} Cluster")
    print("Top-5 Einwohner:", top5["Einwohner"].tolist())


    # Centroids in neues Koordinatensystem transformeieren
    top5['centroid'] = top5.geometry.centroid
    transformer = Transformer.from_crs(ziel_crs, 'EPSG:4326', always_xy=True)

    # ORS‑Format: [[lon1, lat1], [lon2, lat2], ...]
    ors_coordinates = []
    for idx, row in top5.iterrows():
        lon, lat = transformer.transform(row['centroid'].x, row['centroid'].y)
        ors_coordinates.append([lon, lat])
        print(f"Top {idx+1}: {row['Einwohner']:.0f} Pers. → ORS: [{lon:.6f}, {lat:.6f}]")

    print("\n📍 ORS‑Koordinaten (kopierbar):")
    print(ors_coordinates)


    return ors_coordinates, polygons_top5


    # ============================================
    # EXPORT DER POI-DATEN FÜR QGIS
    # ============================================ 
    
    #"/" und "\" durch "_" ersetzt, damit es keine Probleme mit Ordnernamen gibt
    gemeinde_name = gemeinde_name.replace("/", "_").replace("\\", "_")

    # Export-Ordner erstellen
    export_folder = rf"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Ergebnisse\{gemeinde_name}"
    os.makedirs(export_folder, exist_ok=True)

    # 1. Bewohnte Cluster - nur die Haupt-Geometry-Spalte beibehalten
    # Zuerst sicherstellen, dass wir nur eine Geometry-Spalte haben
    bew_clusters_clean = bew_clusters.copy()
    if 'centroid' in bew_clusters_clean.columns:
        # Die centroid-Spalte ist auch eine Geometry-Spalte, müssen wir entfernen
        bew_clusters_clean = bew_clusters_clean.drop(columns=['centroid'])
        
    # Explizit als GeoDataFrame mit geometry-Spalte definieren
    bew_clusters_clean = gpd.GeoDataFrame(bew_clusters_clean, geometry='geometry', crs=ziel_crs)

    bew_clusters_path = os.path.join(export_folder, f"bewohnte_cluster_{gemeinde_name}.gpkg")
    bew_clusters_clean.to_file(bew_clusters_path, driver='GPKG')
    print(f"✅ Bewohnte Cluster gespeichert: {bew_clusters_path}")

    # 3. Top-5 Centroids als Punkte
    # Hier müssen wir sicherstellen, dass die centroid-Spalte die Geometry ist
    top5_centroids = gpd.GeoDataFrame(
        top5[['Einwohner']].reset_index(drop=True),
        geometry=top5['centroid'].values,
        crs=ziel_crs
    )

    centroids_path = os.path.join(export_folder, f"top5_centroids_{gemeinde_name}.gpkg")
    top5_centroids.to_file(centroids_path, driver='GPKG')
    print(f"✅ Top-5 Centroids gespeichert: {centroids_path}")

  


    
