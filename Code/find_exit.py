import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.ops import split
import plots as my_plots
import sys

def cut_roads_by_flood(roads, flood):

    boundary = flood.boundary
    cut_segments = []

    roads = roads[roads.geometry.type.isin(["LineString","MultiLineString"])]
    roads = roads.explode(index_parts=False)

    for _, row in roads.iterrows():
        geom = row.geometry

        if not geom.intersects(flood):
            cut_segments.append((geom, False))  # komplett trocken
            continue

        parts = split(geom, boundary)

        for part in parts.geoms:
            inside = part.within(flood)
            cut_segments.append((part, inside))

    return cut_segments





def build_graph(segments):

    G = nx.Graph()

    def node_from_xy(x, y):
        return (round(x,6), round(y,6))

    for seg in segments:

        # Nur echte Linien behalten
        if not isinstance(seg, LineString):
            continue
        if len(seg.coords) < 2:
            continue

        x1, y1 = seg.coords[0]
        x2, y2 = seg.coords[-1]

        start = node_from_xy(x1, y1)
        end   = node_from_xy(x2, y2)

        G.add_edge(start, end, geometry=seg)

    return G





def find_true_exitpoints(cut_segments, largest_nodes):

    exits = []

    def node(x,y):
        return (round(x,6), round(y,6))

    for seg, inside in cut_segments:

        # nur trockene Linien betrachten
        if inside:
            continue
        if not isinstance(seg, LineString):
            continue
        if len(seg.coords) < 2:
            continue

        x1,y1 = seg.coords[0]
        x2,y2 = seg.coords[-1]

        start_node = node(x1,y1)
        end_node   = node(x2,y2)

        # Segment gehört zur großen trockenen Komponente?
        if start_node in largest_nodes or end_node in largest_nodes:
            exits.append(Point(x1,y1))
            exits.append(Point(x2,y2))

    return exits





def snap_point_to_accessible_road(roads, flood):
    cut = cut_roads_by_flood(roads, flood)

    dry_segments = [g for g, inside in cut if not inside]

    G = build_graph(dry_segments)

    components = list(nx.connected_components(G))
    largest_nodes = max(components, key=len)

    exit_points = find_true_exitpoints(cut, largest_nodes)

    boundary = flood.boundary

    #5 Meter Toleranz, damit Punkte nahe der Grenze nicht verloren gehen
    tol = 5 

    exit_points = [p for p in exit_points if p.distance(boundary) < tol]    


    return exit_points






def find_exit_point(zentroid, poly_utm, roads_gdf):


        
        # Zentroid nach UTM transformieren
    zentroid_utm = (
        gpd.GeoSeries([zentroid], crs="EPSG:4326")
        .to_crs("EPSG:25833")
        .iloc[0]
    )


    #Roads in UTM transformieren
    roads_gdf = roads_gdf.set_crs("EPSG:4326", allow_override=True)
    roads_gdf = roads_gdf.to_crs("EPSG:32633")

    # Exit-Punkte auf aus betroffenem Bereich
    exit_points = snap_point_to_accessible_road(roads_gdf, poly_utm)

    # Distanz jedes Exit-Punkts zum Original randpunkt_utm messen
    distances = [(pt, pt.distance(zentroid_utm)) for pt in exit_points]

    # Nach Distanz sortieren (nächster zuerst)
    distances.sort(key=lambda x: x[1])

    # Punkt mit geringster Distanz zum Zentorid als neuen randpunkt_utm setzen
    try:
        randpunkt_utm = distances[0][0]  # geometry des nächsten Points
        # ... Rest deines Codes nach dieser Zeile
    except IndexError:
        print("\n❌ KEIN AUSGANG MÖGLICH!")
        print("Keine trockene Straße führt aus dem bewohnten Überflutungsgebiet.")
        print("Das Gebiet ist vollständig umschlossen – auch außen rum alles überflutet.")
        print("Exit-Point-Berechnung abgebrochen.")
        sys.exit(1)  
    
    # Alles zurück nach WGS84 transformieren fürs Plotten
    poly_plot = (
        gpd.GeoSeries([poly_utm], crs="EPSG:25833")
        .to_crs("EPSG:4326")
    )

    roads_plot = roads_gdf.to_crs("EPSG:4326")  # oder poly_plot.crs

    exit_plot = (
        gpd.GeoSeries(exit_points, crs="EPSG:25833")
        .to_crs("EPSG:4326")
    )

    target_plot = (
        gpd.GeoSeries([zentroid_utm], crs="EPSG:25833")
        .to_crs("EPSG:4326")
    )

    rand_plot = (
        gpd.GeoSeries([randpunkt_utm], crs="EPSG:25833")
        .to_crs("EPSG:4326")
    )

    my_plots.plot3_exit_points(poly_plot, roads_plot, target_plot, exit_plot, rand_plot)



    # Randpunkt (UTM) → GeoSeries mit CRS
    rand_utm_series = gpd.GeoSeries([randpunkt_utm], crs="EPSG:25833")

    # → zurück nach WGS84
    rand_wgs = rand_utm_series.to_crs("EPSG:4326").iloc[0]

    # → wieder in ORS-Format bringen
    target_point = [rand_wgs.x, rand_wgs.y]

    return target_point
