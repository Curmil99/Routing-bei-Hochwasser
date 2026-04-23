import osmnx as ox
import openrouteservice as ors
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import os
from shapely.geometry import shape
import plots as my_plots

 
def helth_and_fire_in_puffer(coordinates, flood_gdf, gemeinde_name):

    #ORS API
    client = ors.Client(key="5b3ce3597851110001cf6248346b32c2ca1f40439e45e94385175436") 

    #Koordinaten in die richtige Reihenfolge für ORS bringen
    center = (coordinates[1], coordinates[0])

    #Grenzen von Flood auf Gemeinde auflösen (bestht aus mehreren Polyognen)
    flood_clean = (
        flood_gdf              
        .dissolve()                     #Grenzen zwischen den Kacheln auflösen
        .explode(index_parts=False)     #Macht MultiPolygone zu jeweils einzelnen
        .reset_index(drop=True)         #Macht neuen Index
    )
    
    flood_gdf = flood_clean
    

    #Berechne Isochone um Zentroidpunkt
    iso = client.isochrones(
        locations=[[coordinates[0], coordinates[1]]],  # lon, lat
        profile="driving-car",
        range=[900],  # Sekunden
    )

    iso_poly = shape(iso["features"][0]["geometry"])

    #Isochrone in ein GeoDataFrame umwandeln (mit gleichem CRS wie flood_gdf)
    iso_gdf = gpd.GeoDataFrame(
        {'geometry': [iso_poly]}, 
        crs= "EPSG:4326" 
    )

    iso_gdf = iso_gdf.to_crs(flood_gdf.crs)


    # Flood-Daten auf Isochrone zuschneiden
    flood_in_puffer = gpd.clip(flood_gdf, iso_gdf)

    radius_min = 900 / 60
    print(f"✅ {len(flood_in_puffer)} Flood-Flächen in {radius_min}-Minuten-Isochrone geschnitten")

    
    
        

    #POIS, nach denen gefiltert werden soll
    tags1 = {"amenity": [ "fire_station"]}
    tags2 = {"emergency": ["ambulance_station"]}
    tags = {**tags1, **tags2}  # Beide Tag-Dictionaries zusammenführen
    

   

    pois = ox.features_from_polygon(
        iso_poly,
        tags=tags
    ).to_crs("EPSG:4326")





    #POIS und Flut in richtige Koordinaten umwandeln
    pois_m = pois.to_crs("EPSG:25833")      # UTM Zone 32N (für Rhein-Neckar korrekt)
    flood_m = flood_in_puffer.to_crs("EPSG:25833")
    



    # Zentrum als einzelner Shapely Point (direkt in metrischem CRS)
    center_geom = gpd.GeoSeries(
        [Point(coordinates[0], coordinates[1])], 
        crs="EPSG:4326"
    ).to_crs("EPSG:25833").iloc[0]

    pois_m["dist_to_center_m"] = pois_m.geometry.distance(center_geom)
  



    healthcare  = pois_m[pois_m["emergency"].isin(["ambulance_station"])].copy()
    fire        = pois_m[pois_m["amenity"].isin(["fire_station"])].copy()

    print(pois_m[["amenity", "dist_to_center_m"]].head(10))

    print(f"Anzahl Rettungsdienste: {len(healthcare)} und Distanz zum Hochwasser in Metern: {healthcare['dist_to_center_m'].min()}")

    print(f"Anzahl Feuerwachen: {len(fire)} und Distanz zum Hochwasser in Metern: {fire['dist_to_center_m'].min()}")


    #Alle Gemontrien von Feuerwehrstationen/Krankenhäusern werden, falls nötig, in Punktgeometiren umgewandelt. Es wird der zentroid gewählt
    healthcare["geometry"] = healthcare.geometry.apply(lambda g: g.centroid if g.geom_type != "Point" else g)

    fire["geometry"] = fire.geometry.apply(lambda g: g.centroid if g.geom_type != "Point" else g)

    flood_gdf = flood_in_puffer.to_crs("EPSG:25833")
    healthcare = healthcare.to_crs("EPSG:25833")
    fire = fire.to_crs("EPSG:25833")

    flood_outer = flood_gdf.unary_union

    #Filtere die Punkte, die innerhalb der Flut liegen heraus
    healthcare_filtered = healthcare[
        ~healthcare.geometry.within(flood_outer)
    ]

    fire_filtered = fire[
        ~fire.geometry.within(flood_outer)
    ]




    healthcare_sorted = (
        healthcare_filtered
        .sort_values("dist_to_center_m", ascending=True)
        .head(5)
    )

    fire_sorted = (
        fire_filtered
        .sort_values("dist_to_center_m", ascending=True)
        .head(5)
    )

    healthcare_sorted.to_crs("EPSG:4326")
    fire_sorted.to_crs("EPSG:4326")





    center_point = gpd.GeoSeries(
        [Point(center[1], center[0])],
        crs="EPSG:4326"
    ).to_crs("EPSG:25833")


    

    iso_m = iso_gdf.to_crs("EPSG:25833")
    flood_m = flood_in_puffer.to_crs("EPSG:25833")
    pois_m = pois.to_crs("EPSG:25833")


    my_plots.plot4_helthcare_fire_stations_in_puffer(iso_m, flood_m, healthcare, fire, center_point, healthcare_filtered, fire_filtered)


    return healthcare_sorted, fire_sorted, flood_in_puffer, iso_gdf

    


    # ============================================
    # EXPORT DER POI-DATEN FÜR QGIS
    # ============================================

    #"/" und "\" durch "_" ersetzt, damit es keine Probleme mit Ordnernamen gibt
    gemeinde_name = gemeinde_name.replace("/", "_").replace("\\", "_")
    
    export_folder = rf"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Ergebnisse\{gemeinde_name}"
    os.makedirs(export_folder, exist_ok=True)

    # Koordinaten für den Dateinamen sichern
    coord_str = f"{coordinates[0]:.4f}_{coordinates[1]:.4f}".replace('.', '_')


    # Krankenhäuser/Kliniken
    healthcare_path = os.path.join(export_folder, f"healthcare_{coord_str}_15min.gpkg")
    healthcare.to_crs("EPSG:4326").to_file(healthcare_path, driver='GPKG')
    print(f"✅ Krankenhäuser/Kliniken gespeichert: {healthcare_path}")

    # Feuerwachen 
    fire_path = os.path.join(export_folder, f"fire_stations_{coord_str}_15min.gpkg")
    fire.to_crs("EPSG:4326").to_file(fire_path, driver='GPKG')
    print(f"✅ Feuerwachen gespeichert: {fire_path}")


    #Die Auf den Puffer zusammengeschnittene Flut
    flood_mit_puffer_path = os.path.join(export_folder, f"flood_mit_puffer_{gemeinde_name}.gpkg")
    flood_in_puffer.to_file(flood_mit_puffer_path, driver='GPKG')
    print(f"✅ Flut mit Puffer gespeichert: {flood_mit_puffer_path}")

    #Die Isochone
    isochrone_path = os.path.join(export_folder, f"isochrone_10min_{coord_str}.gpkg")
    iso_gdf.to_file(isochrone_path, driver='GPKG')
    print(f"✅ 10-Minuten-Isochrone gespeichert: {isochrone_path}")
        

    # 7. Center-Punkt
    center_point_wgs84 = center_point.to_crs("EPSG:4326")
    center_path = os.path.join(export_folder, f"center_point_{coord_str}.gpkg")
    center_point_wgs84.to_file(center_path, driver='GPKG')
    print(f"✅ Center-Punkt gespeichert: {center_path}")



    print(f"\n🎉 Alle POI-Daten exportiert nach: {export_folder}")




    

