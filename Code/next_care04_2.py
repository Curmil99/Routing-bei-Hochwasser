import geopandas as gpd
import pyproj

from shapely.geometry import (
    LineString, 
    Point, 
    mapping, 
    shape
)

from shapely.ops import unary_union
from shapely.validation import make_valid

import ors_analyse02 as ors_analyse


 
def next_care_route_analysis(target_point, flood_in_puffer, healthcare):

    results = []

    # CRS-Transformer
    proj_to_wgs = pyproj.Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
    proj_to_utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)

    if flood_in_puffer.crs != "EPSG:25833":
        flood_in_puffer = flood_in_puffer.to_crs("EPSG:25833")


    # Hochwasser-Union einmalig für contains()
    flood_union = None
    if not flood_in_puffer.empty:
        flood_union = make_valid(unary_union(flood_in_puffer.geometry)).buffer(0)


    #Iteriere über alle Kliniken / Krankenhäuser
    for _, row in healthcare.iterrows():

         # Startpunkt ist Krankenhaus / Klinik
        start_m = row.geometry.centroid
        start_point_utm = start_m  # in EPSG:25833
        start_lon, start_lat = proj_to_wgs.transform(start_point_utm.x, start_point_utm.y)
        start = (start_lon, start_lat)

        # Endpunkt
        end = target_point
        end_x, end_y = proj_to_utm.transform(end[0], end[1])
        end_point_utm = Point(end_x, end_y)

        

        print("Start:", start)
        print("End:", end)

        
        #Wenn Klinik/Krankenhaus im Hochwasser liegt, wird es übersprungen
        if flood_union.contains(start_point_utm):
            print(f"❌ Startpunkt {start_m} liegt im Hochwasser – übersprungen.")
            continue

        
        if flood_in_puffer.empty:
            print("KEINE gültigen Polygone gefunden!")
            flood_simple = None

        else:

            # Vereinfachen
            flood_simple = flood_union.simplify(20)

            # Analyse
            bounds = flood_simple.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            area = flood_simple.area

            print("\n=== FLOOD ANALYSE ===")
            print(f"Breite: {width:.0f} m")
            print(f"Höhe:  {height:.0f} m")
            print(f"Fläche: {area:.0f} m²")


                
            flood_geometry = None  # <- initialisieren, damit sie immer existiert

            if flood_union:
                # Jetzt beschneide das Hochwasser auf den Bereich um die neue Route
                luftlinie = LineString([start_point_utm, end_point_utm])
                
                puffer_um_luftlinie = luftlinie.buffer(3000)

               # print("Route CRS:", puffer_um_luftlinie.crs)
                print("Flood CRS:", flood_in_puffer.crs)
                print("Flood Bounds:", flood_in_puffer.total_bounds)
                    
                flood_beschnitten = flood_union.intersection(puffer_um_luftlinie)

                


                print("Flood beschnitten leer?", flood_beschnitten.is_empty)
                print("Start UTM:", start_point_utm)
                print("End UTM:", end_point_utm)


                if not flood_beschnitten.is_empty:

                    # Validieren
                    flood_clean = make_valid(flood_beschnitten)

                    # Vereinfachen 
                    flood_simple = flood_clean.simplify(20, preserve_topology=True)

                    flood_simple = make_valid(flood_simple).buffer(0)

                    # Falls GeometryCollection → nur Polygone behalten
                    if flood_simple.geom_type == "GeometryCollection":
                        polys = [g for g in flood_simple.geoms if g.geom_type in ["Polygon","MultiPolygon"]]
                        if polys:
                            flood_simple = unary_union(polys)
                        else:
                            flood_simple = None

                    
                    # Konvertiere zu WGS84 und mapping
                    print("VALID:", flood_simple.is_valid, "TYPE:", flood_simple.geom_type)
                    
                    if flood_simple is not None and not flood_simple.is_empty and flood_simple.is_valid:
                        # Transformieren nach WGS84
                        flood_simple_4326 = gpd.GeoSeries([flood_simple], crs="EPSG:25833").to_crs("EPSG:4326").geometry.iloc[0]
                        print("Flood GeoJSON bounds:", shape(flood_simple_4326).bounds)


                        # Sicherstellen, dass es ein Polygon oder MultiPolygon ist
                        if flood_simple_4326.geom_type in ["Polygon", "MultiPolygon"]:
                            flood_geometry = mapping(flood_simple_4326)
                            print(f"✅ Flood Geometrie erstellt: {flood_simple_4326.geom_type}")
                        else:
                            print(f"❌ Flood-Geom ist {flood_simple_4326.geom_type}, wird nicht verwendet")
                            flood_geometry = None


            '''

            #Kurzer Plot, des Start, End und des Hochwasserbereichs (debug)
            fig, ax = plt.subplots(figsize=(6,6))

            # Flood plotten 
            if flood_geometry is not None:
                flood_shape = shape(flood_geometry)
                gpd.GeoSeries([flood_shape], crs="EPSG:4326").plot(ax=ax)

            # Start plotten
            ax.scatter(start_neu[0], start_neu[1])
            ax.text(start_neu[0], start_neu[1], "Start")

            # End plotten
            ax.scatter(end[0], end[1])
            ax.text(end[0], end[1], "End")

            ax.set_title("Debug: Start / End / Flood")
            plt.show()

            '''

            result = ors_analyse.berechne_route_mit_vermeidung(
                    start, 
                    end, 
                    flood_geometry
                )
            



            summary_normal = result["summary_normal"]
            summary_avoid = result["summary_avoid"]

            # Berechnung der Distanzdifferenz (nur wenn für beide eine Route gefunden wurde)
            dist_normal = summary_normal.get("distance")
            dist_avoid = summary_avoid.get("distance")

            if dist_normal is not None and dist_avoid is not None:
                delta_dist = dist_avoid - dist_normal
            else:
                delta_dist = None

            # Berechnung der Zeitdifferenz (nur wenn für beide eine Route gefunden wurde)
            time_normal = summary_normal.get("duration")
            time_avoid = summary_avoid.get("duration")
            if time_normal is not None and time_avoid is not None:
                delta_time = time_avoid - time_normal
            else:
                delta_time = None

            results.append({
                "id": row.name[1],
                "route_normal": result["route_normal"],
                "route_avoid": result["route_avoid"],
                "name": row.get("name", "unbekannt"),
                "dist_no_flood_m": summary_normal["distance"],
                "time_no_flood_s": summary_normal["duration"],
                "dist_with_flood_m": summary_avoid["distance"],
                "time_with_flood_s": summary_avoid["duration"],
                "delta_dist_m": delta_dist,
                "delta_time_s": delta_time,
            })



    # NACH der Schleife
    results_df = gpd.GeoDataFrame(results)

    if not results_df.empty:
        results_df.sort_values("delta_dist_m", ascending=False, inplace=True)

    return results_df












            