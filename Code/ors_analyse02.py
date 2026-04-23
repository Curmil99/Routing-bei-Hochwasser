import openrouteservice
import geopandas as gpd
from openrouteservice.exceptions import ApiError, Timeout


from shapely.geometry import shape
import geopandas as gpd
import os




client = openrouteservice.Client(key="5b3ce3597851110001cf6248346b32c2ca1f40439e45e94385175436",timeout=120) 


def berechne_route_mit_vermeidung(start, end, flood_mp):

    coords = [start, end]

    
    # ROUTE NORMAL
    try:
        route_normal = client.directions(
            coordinates=coords,
            profile='driving-car',
            preference='shortest',
            extra_info=['waytype', 'waycategory', 'osmid'],
            format='geojson'
        )

        summary_normal = {
            "distance": route_normal['features'][0]['properties']['summary']['distance'],
            "duration": route_normal['features'][0]['properties']['summary']['duration']
        }

        print(f'Normal: {summary_normal["distance"]:.0f} m, {summary_normal["duration"]:.0f} s')

       

    except (ApiError, Timeout) as e:
        print("⚠️ Keine Normalroute gefunden:", e)

        route_normal = None
        summary_normal = {"distance": None, "duration": None}


   
    # ROUTE MIT VERMEIDUNG
    if flood_mp is not None:

        try:
            route_avoid = client.directions(
                coordinates=coords,
                profile='driving-car',
                preference='shortest',
                options={'avoid_polygons': flood_mp},
                format='geojson'
            )

            summary_avoid = {
                "distance": route_avoid['features'][0]['properties']['summary']['distance'],
                "duration": route_avoid['features'][0]['properties']['summary']['duration']
            }

            print(f'Vermeidung: {summary_avoid["distance"]:.0f} m, {summary_avoid["duration"]:.0f} s')

        except (ApiError, Timeout) as e:
            print("⚠️ Keine Vermeidungsroute gefunden:", e)

            route_avoid = None
            summary_avoid = {"distance": None, "duration": None}

    else:
        print('ℹ️ Keine Hochwasserdaten vorhanden, verwende Normalroute')

        route_avoid = route_normal
        summary_avoid = summary_normal

    

    
    return {
        "summary_normal": summary_normal,
        "summary_avoid": summary_avoid,
        "route_normal": route_normal,
        "route_avoid": route_avoid
    }





# Funktion zum Speichern der Routen pro Startpunkt
# wird am Ende der main.py aufgerufen, um die Routen als GeoPackage zu speichern, damit diese in QGIS weiterverwendet werden können

def save_routes_per_start(results_df, export_folder, prefix):
    for _, row in results_df.iterrows():
        route_features = []

        # NORMAL
        if row["route_normal"] is not None:
            geom_normal = shape(row["route_normal"]["features"][0]["geometry"])
            start_x, start_y = list(geom_normal.coords)[0]

            route_features.append({
                "route_type": "normal",
                "name": row.get("name", "unbekannt"),
                "dist_m": row.get("dist_no_flood_m"),
                "time_s": row.get("time_no_flood_s"),
                "geometry": geom_normal
            })
        else:
            start_x, start_y = None, None

        # AVOID
        if row["route_avoid"] is not None:
            geom_avoid = shape(row["route_avoid"]["features"][0]["geometry"])

            # Falls normal nicht existiert, Start aus avoid holen
            if start_x is None or start_y is None:
                start_x, start_y = list(geom_avoid.coords)[0]

            route_features.append({
                "route_type": "avoid",
                "name": row.get("name", "unbekannt"),
                "dist_m": row.get("dist_with_flood_m"),
                "time_s": row.get("time_with_flood_s"),
                "geometry": geom_avoid
            })

        # Nur speichern, wenn mindestens eine Route vorhanden ist
        if route_features:
            gdf = gpd.GeoDataFrame(route_features, geometry="geometry", crs="EPSG:4326")

            # Dateiname nach Startkoordinate
            start_x_str = str(round(start_x, 6)).replace(".", "_")
            start_y_str = str(round(start_y, 6)).replace(".", "_")

            out_path = os.path.join(
                export_folder,
                f"{prefix}_id_{row.get('id', 'x')}_start_{start_x_str}_{start_y_str}.gpkg"
            )

            gdf.to_file(out_path, driver="GPKG")
            print(f"✅ Route gespeichert: {out_path}")












