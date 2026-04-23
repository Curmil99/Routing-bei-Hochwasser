import geopandas as gpd
import matplotlib.pyplot as plt
import os
import plots as my_plots


def floodedArea_u_Bev(gemeinde_name, flood_gdf, gemeinde, zensus_gpkg_path): 

 
    # CRS prüfen/auf metrisches setzen 
    if gemeinde.crs != 'EPSG:25833':
        gemeinde = gemeinde.to_crs('EPSG:25833')  # UTM Zone 33N, passend für Sachsen
    if flood_gdf.crs != 'EPSG:25833':
        flood_gdf = flood_gdf.to_crs('EPSG:25833')


    #selctiere den überfluteten Bereich in der Gemeinde
    flood_in_gemeinde = gpd.clip(flood_gdf, gemeinde)


    #umrechnen in km²
    flood_area_km2 = flood_in_gemeinde.geometry.area.sum() / 1e6

    # Ausgabe: Flächen prüfen
    print(f"Anzahl Flood-Features in Gemeinde: {len(flood_in_gemeinde)}")
    print(f"Überschwemmungsfläche in Gemeinde: {flood_area_km2:.2f} km²")


    #Betroffene Bevölkerung berechnen:

    #Laden der Bevölkerungsdaten in Form von Rasterdaten
    deutschland_bewohnte_kacheln = gpd.read_file(zensus_gpkg_path)


    #zuschneiden auf die ausgewählte Gemeinde
    gemeinde_bewohnte_kacheln = gpd.clip(deutschland_bewohnte_kacheln, gemeinde)


    #Fläche der bewohnten Kacheln berechnen**
    bewohnte_flaeche_km2 = gemeinde_bewohnte_kacheln.geometry.area.sum() / 1e6  



    #seltectieren der von der Flut betroffenen Kacheln mittels Intersection
    #-> es wird auch der Wert von einer geschnittenen Kachle komplett übernommen, auch wenn es in den grafiken nur als halbe kachel angezeigt wird
    bewohnte_kacheln_in_flood = gpd.overlay(
        gemeinde_bewohnte_kacheln,
        flood_in_gemeinde,
        how="intersection"
    )


    # Falls Kacheln mehrfach gezählt werden (wegen mehrfacher Überlappung mit mehreren Polygonen), dann werden diese Duplikate entfernt
    bewohnte_kacheln_in_flood = bewohnte_kacheln_in_flood.drop_duplicates()

    # Fläche der bewohnten Kacheln berechnen
    bewohnte_flaeche_überflutungsfläche_km2 = bewohnte_kacheln_in_flood.geometry.area.sum() / 1e6  

    # Bevölkerung innerhalb der Überflutungsfläche
    gesamtbevoelkerung_flooded_area = bewohnte_kacheln_in_flood['Einwohner'].sum()

    # Gesamtbevölkerung der Gemeinde
    gesamtbevoelkerung_gemeinde = gemeinde_bewohnte_kacheln['Einwohner'].sum()
    print (f"🏠 Bewohnte Fläche in {gemeinde_name}: {bewohnte_flaeche_km2:.2f} km²")
    print (f"🟢 Bewohnte Fläche innerhalb der Überflutungsfläche: {bewohnte_flaeche_überflutungsfläche_km2:.2f} km²")
    print (f"👥 Gesamtbevölkerung in {gemeinde_name}: {gesamtbevoelkerung_gemeinde}")
    print (f"🧑‍🤝‍🧑 Bevölkerung innerhalb der Überflutungsfläche: {gesamtbevoelkerung_flooded_area}")



    my_plots.plot1_betroffene_bevoelkerung(gemeinde_name, gemeinde, gemeinde_bewohnte_kacheln, flood_in_gemeinde, bewohnte_kacheln_in_flood)

    return bewohnte_kacheln_in_flood

    # ============================================
    # EXPORT DER POI-DATEN FÜR QGIS
    # ============================================
    # Hier werden die Zwischenergbinsse als Dateien exportiert, damit diese in QGis für beispielsweis Karten, weiterverwendet werden können
    
    # Export-Ordner erstellen

    #"/"" und "\" durch "_" ersetzt, damit es keine Probleme mit Ordnernamen gibt
    gemeinde_name = gemeinde_name.replace("/", "_").replace("\\", "_")

    export_folder = rf"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Ergebnisse\{gemeinde_name}"
    os.makedirs(export_folder, exist_ok=True)

    # 1. Bewohnte Kacheln in der Gemeinde
    bewohnte_kacheln_path = os.path.join(export_folder, f"bewohnte_kacheln_{gemeinde_name}.gpkg")
    gemeinde_bewohnte_kacheln.to_file(bewohnte_kacheln_path, driver='GPKG')
    print(f"✅ Bewohnte Kacheln gespeichert: {bewohnte_kacheln_path}")

    # 2. Bewohnte Kacheln in der Flut (in Gemeinde)
    bewohnte_kacheln_in_flood_path = os.path.join(export_folder, f"bewohnte_kacheln_flood_{gemeinde_name}.gpkg")
    bewohnte_kacheln_in_flood.to_file(bewohnte_kacheln_in_flood_path, driver='GPKG')
    print(f"✅ Bewohnte Kacheln in Flut gespeichert: {bewohnte_kacheln_in_flood_path}")

    # 3. Gemeinde-Grenze
    gemeinde_path = os.path.join(export_folder, f"gemeinde_{gemeinde_name}.gpkg")
    gemeinde.to_file(gemeinde_path, driver='GPKG')
    print(f"✅ Gemeinde-Grenze gespeichert: {gemeinde_path}")

    # 4. Flut in der Gemeinde
    flood_in_gemeinde_path = os.path.join(export_folder, f"flood_in_gemeinde_{gemeinde_name}.gpkg")
    flood_in_gemeinde.to_file(flood_in_gemeinde_path, driver='GPKG')
    print(f"✅ Flut in Gemeinde gespeichert: {flood_in_gemeinde_path}")


    print(f"\n🎉 Alle Daten wurden exportiert nach: {export_folder}")


    