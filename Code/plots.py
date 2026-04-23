import pandas as pd
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import contextily as cx






def setup_plot_style():
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = '#FFF8E1'
    plt.rcParams['font.size'] = 12




def plot1_betroffene_bevoelkerung(gemeinde_name, gemeinde, gemeinde_bewohnte_kacheln, flood_in_gemeinde, bewohnte_kacheln_in_flood):
    
    plt.style.use('default') 
    fig, ax = plt.subplots(figsize=(12, 9))  

    # Hintergrund: Pastellgelb für Figure 
    fig.patch.set_facecolor('#FFF8E1')  
    ax.set_facecolor('white')  # Plot-Bereich bleibt weiß
    
    # CRS aller Layer auf EPSG:3857 setzen (für OSM)
    gemeinde = gemeinde.to_crs("EPSG:3857")
    gemeinde_bewohnte_kacheln = gemeinde_bewohnte_kacheln.to_crs("EPSG:3857")
    flood_in_gemeinde = flood_in_gemeinde.to_crs("EPSG:3857")
    bewohnte_kacheln_in_flood = bewohnte_kacheln_in_flood.to_crs("EPSG:3857")


    # Plots
    gemeinde.plot(ax=ax, color='lightgray', edgecolor='black', alpha=0.4, linewidth=0.5)
    gemeinde_bewohnte_kacheln.plot(ax=ax, color='#FF9800', alpha=0.5, edgecolor='#F57C00', linewidth=0.5, markersize=15)
    flood_in_gemeinde.plot(ax=ax, color='#2196F3', alpha=0.4, edgecolor='#1976D2', linewidth=0.9)
    bewohnte_kacheln_in_flood.plot(ax=ax, color='#F44336', alpha=0.7, edgecolor='#D32F2F', linewidth=0.5)

    # OSM Hintergrund 
    cx.add_basemap(ax, crs='EPSG:3857', source=cx.providers.OpenStreetMap.Mapnik, 
                zoom='auto', alpha=0.6)  #alpha für Durchsichtigkeit

    ax.set_axis_off()
    ax.set_title(f'Betroffene Bevölkerung in Überschwemmungsgebieten in {gemeinde_name}', 
                fontsize=16, fontweight='bold', pad=-5)

    # Legende (rechts außen)
    legend_elements = [
        Patch(facecolor='lightgray', edgecolor='black', alpha=0.3, label='Gemeindegrenze'),
        Patch(facecolor='#FF9800', alpha=0.5, edgecolor='#F57C00', label='Bewohnte Kacheln'),
        Patch(facecolor='#2196F3', alpha=0.4, edgecolor='#1976D2', label='Überschwemmungsgebiet'),
        Patch(facecolor='#F44336', alpha=0.7, edgecolor='#D32F2F', label='Bewohnte Fläche in Flut')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), 
            frameon=True, fancybox=True, shadow=True, fontsize=12)

    plt.tight_layout()
    plt.show()






def plot2_stärkst_betroffene_cluster(flood_clean, gemeinde_name, gemeinde, bew_clusters, top5):
   
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(13, 9))  # Etwas breiter für Legende

    # Hintergrund 
    fig.patch.set_facecolor('#FFF8E1')  # Pastellgelb außen
    ax.set_facecolor('white')  # Plot weiß

    # Alle Layer in EPSG:3857 für OSM-Hintergrund
    gemeinde = gemeinde.to_crs("EPSG:3857")
    flood_clean = flood_clean.to_crs("EPSG:3857")
    bew_clusters = bew_clusters.to_crs("EPSG:3857")
    top5 = top5.to_crs("EPSG:3857")


    # Plots 
    gemeinde.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.7, alpha=0.3)
    flood_clean.plot(ax=ax, color='#2196F3', alpha=0.4, edgecolor='#1976D2', linewidth=1.2)  # Blau wie Flut in Fig.1
    bew_clusters.plot(ax=ax, color='#FF9800', alpha=0.5, edgecolor='#F57C00', linewidth=0.8)  # Orange wie bewohnte Kacheln

    # Top-5 Punkte
    colors = ["#D32F2F", "#1976D2", "#388E3C", "#F57C00", "#7B1FA2"]  # Rot-Orange-Gradient

    

    for i, (_, row) in enumerate(top5.iterrows()):
        centroid = row.geometry.centroid
        x, y = centroid.x, centroid.y
        ax.plot(x, y, marker="o", color=colors[i], markersize=18, 
                markeredgecolor="black", markeredgewidth=1.5, 
                label=f"Top {i+1}: {row['Einwohner']} Pers.", zorder=10)
        ax.text(x, y, f"{i+1}", ha="center", va="center", fontsize=12, 
                color="white", weight="bold", fontfamily='sans-serif', zorder=11)

    

    minx, miny, maxx, maxy = gemeinde.total_bounds
    dx = maxx - minx
    dy = maxy - miny
    margin = 0.1

    ax.set_xlim(minx - dx*margin, maxx + dx*margin)
    ax.set_ylim(miny - dy*margin, maxy + dy*margin)
   

    # OSM Hintergrund 
    cx.add_basemap(ax, crs='EPSG:3857', source=cx.providers.OpenStreetMap.Mapnik, 
                zoom='auto', alpha=0.7)  #alpha für Durchsichtigkeit

    ax.set_axis_off()
    ax.set_title(f'Hochwasser-Hotspots (Top-5 Bevölkerung) in {gemeinde_name}', 
                fontsize=16, fontweight='bold', pad=-5)

    # Legende rechts außen
    legend_elements = [
        Patch(facecolor='#2196F3', alpha=0.4, edgecolor='#1976D2', label='Überschwemmungsgebiet'),
        Patch(facecolor='#FF9800', alpha=0.5, edgecolor='#F57C00', label='Bewohntes Überschwemmungsgebiet'),
    ] + [plt.Line2D([0], [0], marker='o', color=c, markerfacecolor=c, 
                    markeredgecolor='black', markersize=12, label=f"Top {i+1}: {top5.iloc[i]['Einwohner']} Pers.") 
        for i, c in enumerate(colors)]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), 
            frameon=True, fancybox=True, shadow=True, fontsize=11, ncol=1)

    plt.tight_layout(pad=3.0)
    plt.show()





def plot3_exit_points(poly_plot, roads_plot, target_plot, exit_plot, rand_plot):

    plt.style.use('default')
    minx, miny, maxx, maxy = poly_plot.total_bounds
    fig, ax = plt.subplots(figsize=(10, 8))

    # Hintergrund
    fig.patch.set_facecolor('#FFF8E1')
    ax.set_facecolor('white')

    # Plots
    poly_plot.plot(ax=ax, alpha=0.4, edgecolor="blue", linewidth=1.5)
    roads_plot.plot(ax=ax, color="grey", linewidth=0.5, alpha=0.7)
    target_plot.plot(ax=ax, color="red", markersize=80)
    for p in exit_plot:
        ax.scatter(p.x, p.y, color="blue", s=80, edgecolors="darkblue", linewidth=1.5)
    rand_plot.plot(ax=ax, color="green", markersize=80)

    # Achsen
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_xticklabels([])  # Keine X-Beschriftung
    ax.set_yticklabels([])  # Keine Y-Beschriftung
    ax.spines['bottom'].set_visible(True)    # Rahmen sichtbar
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['left'].set_visible(True)

    
    ax.set_title('Exit Points des am stärksten betroffenen Bereichs', 
                fontsize=16, fontweight='bold', pad=30, loc='center')  # loc='center'

    # Legende rechts
    legend_elements = [
        Patch(facecolor='blue', alpha=0.4, label='Flutpolygon'),
        Line2D([0], [0], color='grey', linewidth=0.5, label='Straßennetz'),
        Line2D([0], [0], marker='o', color='red', markerfacecolor='red', markersize=12, label='Zentroid'),
        Line2D([0], [0], marker='o', color='blue', markerfacecolor='blue', 
            markeredgecolor='darkblue', markersize=10, label='Mögliche Exit Points'),
        Line2D([0], [0], marker='o', color='green', markerfacecolor='green', markersize=12, label='Gewählter Exit Point')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), 
            frameon=True, fancybox=True, shadow=True, fontsize=11)

    plt.tight_layout()
    plt.show()



def plot4_helthcare_fire_stations_in_puffer(iso_m, flood_m, healthcare, fire, center_point, healthcare_filtered, fire_filtered):

   
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 10))

    # Layer in EPSG:3857 für OSM-Hintergrund
    iso_m_3857 = iso_m.to_crs(epsg=3857)
    flood_m_3857 = flood_m.to_crs(epsg=3857)
    healthcare_3857 = healthcare.to_crs(epsg=3857)
    fire_3857 = fire.to_crs(epsg=3857)
    center_point_3857 = center_point.to_crs(epsg=3857)
    healthcare_filtered_3857 = healthcare_filtered.to_crs(epsg=3857)
    fire_filtered_3857 = fire_filtered.to_crs(epsg=3857)

    # Layer in Plot-Reihenfolge: 1. Isochrone, 2. Flut, 3. POIs, 4. Zentrum
    iso_m_3857.plot(ax=ax, facecolor="none", edgecolor="black", linestyle="-", linewidth=1.4, zorder=4)
    flood_m_3857.plot(ax=ax, color="lightblue", alpha=0.8, edgecolor="lightblue", linewidth=1.5, zorder=3)
    healthcare_3857.plot(ax=ax, color="red", markersize=80, edgecolor="pink", zorder=5)
    fire_3857.plot(ax=ax, color="red", markersize=80, marker="^", edgecolor="darkorange", zorder=5)
    healthcare_filtered_3857.plot(ax=ax, color="blue", markersize=100, edgecolor="blue", zorder=6)
    fire_filtered_3857.plot(ax=ax, color="orange", markersize=100, marker="^", edgecolor="orange", zorder=6)
    center_point_3857.plot(ax=ax, color="black", markersize=150, marker="*", edgecolor="white", zorder=6)

    # OSM Hintergrund 
    cx.add_basemap(ax, crs='EPSG:3857', source=cx.providers.OpenStreetMap.Mapnik, 
                zoom='auto', alpha=0.6)  #alpha für Durchsichtigkeit

    # 3. Style
    fig.patch.set_facecolor('#FFF8E1') 
    ax.set_facecolor('white')
    ax.set_axis_off()
    ax.set_title('Rettungsdienste & Feuerwehrstationen im 15-min-Radius', 
                fontsize=16, fontweight='bold', pad=-5, loc='center')

    # 4. Legende RECHTS AUßEN
    ax.legend(handles=[
        Line2D([0], [0], color='black', linestyle='-', linewidth=2, label='15-Minuten-Isochrone'),
        Patch(facecolor='lightblue', alpha=0.5, edgecolor='darkblue', label='Überschwemmung'),
        Line2D([0], [0], marker='o', color='red', markerfacecolor='red', markersize=12, label='Rettungsdienste innerhalb der Flut'),
        Line2D([0], [0], marker='^', color='red', markerfacecolor='red', markersize=14, label='Feuerwachen innerhalb Flut'),
        Line2D([0], [0], marker='*', color='black', markerfacecolor='black', markersize=16, label='Zentrum'),
        Line2D([0], [0], marker='o', color='blue', markerfacecolor='blue', markersize=12, label='Rettungsdienste außerhalb der Flut'),
        Line2D([0], [0], marker='^', color='orange', markerfacecolor='orange', markersize=14, label='Feuerwachen außerhalb Flut')
    ], loc='upper left', bbox_to_anchor=(1.02, 1), frameon=True, fancybox=True, shadow=True, fontsize=11)

    plt.tight_layout(pad=3.0)
    plt.show()




def plot5_vergleichstabelle_erstellen(results_fire):

    # --- Normal ---
    fire_norm = (
        results_fire
        .sort_values("time_no_flood_s")
        [["id","name","time_no_flood_s","dist_no_flood_m"]]
        .reset_index(drop=True)
    )

    fire_norm["time_no_flood_s"] /= 60
    fire_norm["dist_no_flood_m"] /= 1000
    fire_norm["time_no_flood_s"] = fire_norm["time_no_flood_s"].round(1)
    fire_norm["dist_no_flood_m"] = fire_norm["dist_no_flood_m"].round(2)

    fire_norm.insert(0, "Rank", fire_norm.index + 1)
    fire_norm.columns = ["Rank", "ID", "Name", "Dauer (min)", "Distanz (km)"]

    # --- Avoid ---
    fire_avoid = (
        results_fire
        .sort_values("time_with_flood_s")
        [["id","name","time_with_flood_s","dist_with_flood_m"]]
        .reset_index(drop=True)
    )

    fire_avoid["time_with_flood_s"] /= 60
    fire_avoid["dist_with_flood_m"] /= 1000
    fire_avoid["time_with_flood_s"] = fire_avoid["time_with_flood_s"].round(1)
    fire_avoid["dist_with_flood_m"] = fire_avoid["dist_with_flood_m"].round(2)

    fire_avoid.insert(0, "Rank", fire_avoid.index + 1)
    fire_avoid.columns = ["Rank", "ID", "Name", "Dauer (min)", "Distanz (km)"]

    # HTML bauen
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            h2 {{
                margin-top: 40px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 60px;
            }}
            th, td {{
                border: 1px solid #999;
                padding: 6px;
                text-align: center;
            }}
            th {{
                background-color: #e6e6e6;
            }}
        </style>
    </head>
    <body>

        <h2>Top 5 – Normal Routing</h2>
        {fire_norm.to_html(index=False)}

        <h2>Top 5 – Flood Avoid Routing</h2>
        {fire_avoid.to_html(index=False)}

    </body>
    </html>
    """

    return html


#Abschlussabbildung RoutenPlots
def plot_route(ax, route_row, flood_gdf, title, color, normal):
    target_crs = "EPSG:3857"
    stats_lines = []

    ax.set_aspect("equal", adjustable="box")

    name = route_row.get("name", "unbekannt")

    if normal:
        dist = route_row.get("dist_no_flood_m")
        time = route_row.get("time_no_flood_s")
        route = route_row.get("route_normal")
    else:
        dist = route_row.get("dist_with_flood_m")
        time = route_row.get("time_with_flood_s")
        route = route_row.get("route_avoid")

    # --- Infotext kompakt halten ---
    stats_lines.append(f"{name}")

    if dist is not None:
        stats_lines.append(f"Distanz: {dist/1000:.2f} km")
    if time is not None:
        stats_lines.append(f"Dauer: {time/60:.1f} min")

    if not normal:
        delta_d = route_row.get("delta_dist_m")
        delta_t = route_row.get("delta_time_s")

        if delta_d is not None:
            stats_lines.append(f"ΔDistanz: {delta_d/1000:.2f} km")
        if delta_t is not None:
            stats_lines.append(f"ΔZeit: {delta_t/60:.1f} min")

    # --- Flood transformieren ---
    flood_gdf_transformed = None
    if flood_gdf is not None and not flood_gdf.empty:
        if flood_gdf.crs is None:
            flood_gdf = flood_gdf.set_crs("EPSG:4326")
        flood_gdf_transformed = flood_gdf.to_crs(target_crs)

    # --- Route vorbereiten und zeichnen ---
    route_geometry = None

    if isinstance(route, dict) and "features" in route:
        route_gdf = gpd.GeoDataFrame.from_features(route["features"])
        if route_gdf.crs is None:
            route_gdf = route_gdf.set_crs("EPSG:4326")
        route_gdf = route_gdf.to_crs(target_crs)

        for geometry in route_gdf.geometry:
            if geometry.geom_type == "LineString":
                x, y = geometry.xy
                ax.plot(x, y, color=color, linewidth=4, zorder=3)
                route_geometry = geometry
                break

    # --- Flood nur bei Avoid zeichnen ---
    if (not normal) and flood_gdf_transformed is not None:
        flood_gdf_transformed.plot(
            ax=ax,
            color="#9ecae1",
            alpha=0.45,
            edgecolor="#6baed6",
            linewidth=1.2,
            zorder=1
        )

    # --- Start- und Endpunkte + Kartenausschnitt ---
    if route_geometry is not None:
        bounds = route_geometry.bounds  # minx, miny, maxx, maxy

        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2

        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]

        # Falls Route fast nur vertikal oder horizontal verläuft:
        width = max(width, 250)
        height = max(height, 250)

        padding = max(width, height) * 0.18

        ax.set_xlim(center_x - (width / 2 + padding), center_x + (width / 2 + padding))
        ax.set_ylim(center_y - (height / 2 + padding), center_y + (height / 2 + padding))

        start_point = route_geometry.coords[0]
        end_point = route_geometry.coords[-1]

        # Startpunkt
        ax.scatter(
            start_point[0], start_point[1],
            color="#2E8B57",
            s=180,
            marker="^",
            edgecolor="white",
            linewidth=2.5,
            zorder=5
        )

        # Endpunkt
        ax.scatter(
            end_point[0], end_point[1],
            color="#DC143C",
            s=180,
            marker="v",
            edgecolor="white",
            linewidth=2.5,
            zorder=5
        )

        # Labels
        ax.annotate(
            "START",
            xy=(start_point[0], start_point[1]),
            xytext=(6, 0),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color="#2E8B57",
            va="center",
            zorder=6
        )

        ax.annotate(
            "END",
            xy=(end_point[0], end_point[1]),
            xytext=(-6, 0),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color="#DC143C",
            ha="right",
            va="center",
            zorder=6
        )

    # --- Basemap ---
    ctx.add_basemap(
        ax,
        source=ctx.providers.OpenStreetMap.Mapnik,
        crs=target_crs,
        zorder=0,
        alpha=0.9,
        reset_extent=False
    )

    # --- Titel ---
    ax.set_title(title, fontsize=16, pad=12, fontweight="bold")
    ax.set_axis_off()

    # --- Infobox innerhalb der Karte ---
    if stats_lines:
        stats_text = "\n".join(stats_lines)

        ax.text(
            0.03, 0.97, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            va="top",
            ha="left",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor="white",
                edgecolor="0.4",
                alpha=0.92
            ),
            zorder=10
        )

#AbschlussAbbildung        

def make_plots(winner_routes, flood_in_puffer):

    # ---------- FIGUR 1: HEALTHCARE ----------
    fig1, (ax_h_norm, ax_h_avoid) = plt.subplots(
        1, 2,
        figsize=(16, 8),
        constrained_layout=True
    )

    fig1.patch.set_facecolor('#FFF8E1')
    ax_h_norm.set_facecolor('white')
    ax_h_avoid.set_facecolor('white')

    plot_route(
        ax_h_norm,
        winner_routes["healthcare_normal"],
        flood_in_puffer,
        "Rettungsdienste – schnellste Route (ohne Flut)",
        color="#0072B2",
        normal=True
    )

    plot_route(
        ax_h_avoid,
        winner_routes["healthcare_avoid"],
        flood_in_puffer,
        "Rettungsdienste – Route mit Überflutung",
        color="#D55E00",
        normal=False
    )

    fig1.suptitle("Schnellste Routen für Rettungsdiense", fontsize=16, fontweight="bold")

    handles_health = [
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#2E8B57',
               markeredgecolor='white', markersize=10, label='Ausgewählter Rettungsdienst'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='#DC143C',
               markeredgecolor='white', markersize=10, label='Exit point'),
        Line2D([0], [0], color='#0072B2', lw=3, label='Route ohne Flut'),
        Line2D([0], [0], color='#D55E00', lw=3, label='Route mit Flut'),
        Patch(facecolor='#9ecae1', edgecolor='#6baed6', alpha=0.45, label='Überflutungsgebiet')
    ]

    fig1.legend(
        handles=handles_health,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.01),
        ncol=2,
        frameon=True,
        fontsize=10
    )

    # ---------- FIGUR 2: FIRE ----------
    fig2, (ax_f_norm, ax_f_avoid) = plt.subplots(
        1, 2,
        figsize=(16, 8),
        constrained_layout=True
    )

    fig2.patch.set_facecolor('#FFF8E1')
    ax_f_norm.set_facecolor('white')
    ax_f_avoid.set_facecolor('white')

    plot_route(
        ax_f_norm,
        winner_routes["fire_normal"],
        flood_in_puffer,
        "ohne Überflutung",
        color="#0072B2",
        normal=True
    )

    plot_route(
        ax_f_avoid,
        winner_routes["fire_avoid"],
        flood_in_puffer,
        "mit Überflutung",
        color="#D55E00",
        normal=False
    )

    fig2.suptitle("Schnellste Routen für Feuerwehrstationen ", fontsize=16, fontweight="bold")

    handles_fire = [
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#2E8B57',
               markeredgecolor='white', markersize=10, label='Ausgewählte Feuerstation'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='#DC143C',
               markeredgecolor='white', markersize=10, label='Exit point'),
        Line2D([0], [0], color='#0072B2', lw=3, label='Route ohne Überflutung'),
        Line2D([0], [0], color='#D55E00', lw=3, label='Route mit Überflutung'),
        Patch(facecolor='#9ecae1', edgecolor='#6baed6', alpha=0.45, label='Überflutungsgebiet')
    ]

    fig2.legend(
        handles=handles_fire,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.01),
        ncol=2,
        frameon=True,
        fontsize=10
    )

    plt.show()