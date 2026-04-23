import webbrowser
import os
import geopandas as gpd
from shapely.geometry import Point

import care_in_puffer03 as care
import find_exit as find_exit
import next_care04_2 as next_care
import selectOrt_u_Bev as selectOrt
import target_point as target_point

# Plots 
import plots as my_plots
import ors_analyse02 as ors_analyse


# Daten laden
roads_gdf = gpd.read_file(r'C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\Straßennetzwerk_Pirna_Hohenhein_Königstein.geojson')
flood_gdf = gpd.read_file( r"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\Überschwemmungsfläche Sächsische Schweiz\Daten\UEG_SN.shp")
gemeinde_gdf = gpd.read_file(r"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\Verwaltungsgrenzen Sachsen\gem.shp")
zensus_gpkg_path = r'C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\sachsen_bewohnte_kacheln.gpkg'


gemeinde_name = "Pirna"  # Hier den Namen der Gemeinde eingeben, z.B. "Pirna"


gemeinde = gemeinde_gdf[gemeinde_gdf["ORTSNAME"] == gemeinde_name]
if gemeinde.empty:
    raise ValueError(f"Keine Gemeinde '{gemeinde_name}' gefunden.")



#----------------------------------------------------------------------------------
#Hier wird die betroffene Bevölkerung im Überflutunsbereich selectiert
#Rückgabe der Funktion ist: die Bewohnte bereiche innerhalb des überflutungsgebiets
#----------------------------------------------------------------------------------
bewohnte_kacheln_in_flood = selectOrt.floodedArea_u_Bev(gemeinde_name, flood_gdf, gemeinde, zensus_gpkg_path)




#----------------------------------------------------------------------------------
# Diese Funktion gibt die fünf am stärksten betroffenen Bereiche zurück
#----------------------------------------------------------------------------------
top5_coordinates, top5_polygones = target_point.find_worst_affected_areas(bewohnte_kacheln_in_flood, flood_gdf, gemeinde_name, gemeinde)


# Zentroid des betroffensetn bereichs
zentroid = Point(top5_coordinates[0])
# Polygone des betroffensten Bereichs
poly_utm = top5_polygones[0]




#----------------------------------------------------------------------------------
#In dieser Funktion werden die Straßenausgänge aus dem Flutbereich detektiert. 
# Es wird der Straßenausgang zurückgegeben, der am nächsten zum Zentroid liegt.
#----------------------------------------------------------------------------------
exit_point = find_exit.find_exit_point(zentroid, poly_utm, roads_gdf)   




#----------------------------------------------------------------------------------
# Diese Funktion gibt 5 Rettungsdienste und 5 Feuerwehrstationen in Punktkoordinaten zurück, 
# die innerhlab von 15 min am nächsten vom "target_point"/Point P entfernt liegen
#----------------------------------------------------------------------------------
print(exit_point)
healthcare, fire, flood_in_puffer, iso_gdf = care.helth_and_fire_in_puffer(exit_point, flood_gdf, gemeinde_name)


#----------------------------------------------------------------------------------
# In den nächsten beiden Funktionen wird die Route mit und ohne überflutung für die 
# 10 Rettungsdienste/Feuerwehrstationen berechnet.
# Results_helthcare ist eine Map, die für jede Route folgende Informationen enthällt:
#       "id": idx,
#       "route_normal": result["route_normal"],
#       "route_avoid": result["route_avoid"],
#       "name": row.get("name", "unbekannt"),
#       "dist_no_flood_m": summary_normal["distance"],
#       "time_no_flood_s": summary_normal["duration"],
#       "dist_with_flood_m": summary_avoid["distance"],
#       "time_with_flood_s": summary_avoid["duration"],
#       "delta_dist_m": summary_avoid["distance"] - summary_normal["distance"],
#       "delta_time_s": summary_avoid["duration"] - summary_normal["duration"],
#----------------------------------------------------------------------------------       

print("Analysiere Routen zu Healthcare...")
results_healthcare = next_care.next_care_route_analysis(
    exit_point,
    flood_in_puffer,    
    healthcare
)

print("Analysiere Routen zu Fire Stations...")
results_fire = next_care.next_care_route_analysis(
    exit_point,
    flood_in_puffer,
    fire
)

#----------------------------------------------------------------------------------
#Hier wird eine Tabelle der maximal fünf Rettungsdienste/Feuerwehr in html gemacht. 
#Anahnd dieser sind die  Fahrtzeit anschaulicher und nicht nur auf die schnellste Anfahrstation reduziert. 
#----------------------------------------------------------------------------------


html_fire = my_plots.plot5_vergleichstabelle_erstellen(results_fire)
html_healthcare = my_plots.plot5_vergleichstabelle_erstellen(results_healthcare)


with open("fire_table.html", "w", encoding="utf-8") as f:
    f.write(html_fire)
with open("healthcare_table.html", "w", encoding="utf-8") as f:
    f.write(html_healthcare)


webbrowser.open("fire_table.html")
webbrowser.open("healthcare_table.html")


# Beste Route nach Distanz (ohne Hindernis)
# results bleibt eine Liste von dicts
best_healthcare_normal = results_healthcare.loc[results_healthcare["time_no_flood_s"].idxmin()]
best_healthcare_avoid  = results_healthcare.loc[results_healthcare["time_with_flood_s"].idxmin()]

best_fire_normal = results_fire.loc[results_fire["time_no_flood_s"].idxmin()]
best_fire_avoid  = results_fire.loc[results_fire["time_with_flood_s"].idxmin()]




winner_routes = {
    "healthcare_normal": best_healthcare_normal,
    "healthcare_avoid": best_healthcare_avoid,
    "fire_normal": best_fire_normal,
    "fire_avoid": best_fire_avoid
}


my_plots.make_plots(winner_routes, flood_in_puffer)


#------------------------------------------------------------------
# Export der Ergebnisse für QGIS
#------------------------------------------------------------------
# export_folder = rf"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Ergebnisse\{gemeinde_name}"


# os.makedirs(export_folder, exist_ok=True)

# ors_analyse.save_routes_per_start(results_fire, export_folder, "fire")
# ors_analyse.save_routes_per_start(results_healthcare, export_folder, "healthcare")

# flood_in_puffer_path = os.path.join(export_folder, f"flood_in_puffer_{gemeinde_name}.gpkg")
# flood_in_puffer.to_file(flood_in_puffer_path, driver='GPKG')
# print(f"✅ Flut in Puffer gespeichert: {flood_in_puffer_path}")