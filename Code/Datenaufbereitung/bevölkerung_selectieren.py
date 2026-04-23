import geopandas as gpd
import pandas as pd
from shapely import box


#Ort, an welchem die vorprozessierte Datei mit den bewohnten Kacheln gespeichert werden soll
output_gpkg = r"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\sachsen_bewohnte_kacheln.gpkg"


#Input
gemeinde_shp_path = r"C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\Verwaltungsgrenzen Sachsen\gem.shp"
gemeinde_gdf = gpd.read_file(gemeinde_shp_path)

zensus_df = pd.read_csv(
        r'C:\Users\milan\OneDrive\Dokumente\Studium\Master\1. Semester\FOSSGIS\fossgiss_abschlussprojekt\Daten\Zensus2022_Bevoelkerungszahl_100m-Gitter.csv',
        delimiter=';'
    )

# Zensusdaten als GeoDataFrame (EPSG:3035)
zensus_gdf = gpd.GeoDataFrame(
        zensus_df, 
        geometry=gpd.GeoSeries.from_xy(zensus_df['x_mp_100m'], zensus_df['y_mp_100m']),
        crs="EPSG:3035"
    )

zensus_gdf = zensus_gdf.to_crs("EPSG:25833")


# Kacheln in bewohnte Raster umwandeln
zensus_gdf["geometry"] = zensus_gdf.apply(
    lambda row: box(row.geometry.x - 50, row.geometry.y - 50,
                    row.geometry.x + 50, row.geometry.y + 50),
    axis=1
)


# Umwandeln in GeoDataFrame mit Polygonen
raster_gdf = gpd.GeoDataFrame(zensus_gdf, geometry='geometry', crs="EPSG:25833")

 # Alle bewohnten Rasterzellen filtern
bewohnte_kacheln_gdf = raster_gdf[raster_gdf['Einwohner'] > 0]

# Alle Kacheln innerhalb der Gemeinde filtern
bewohnte_kacheln = gpd.clip(bewohnte_kacheln_gdf, gemeinde_gdf)

gesamtbevoelkerung_gemeinde = bewohnte_kacheln['Einwohner'].sum()

print (f"👥 Gesamtbevölkerung in Sachsen: {gesamtbevoelkerung_gemeinde}")


#Index zurücksetzen und unnötige Spalten entfernen
bewohnte_kacheln_clean = bewohnte_kacheln.reset_index(drop=True)



# Exportiere als GeoPackage
bewohnte_kacheln_clean.to_file(
    output_gpkg, 
    driver='GPKG', 
    layer='bewohnte_zellen_100m',
    encoding='UTF-8'  # Für deutsche Umlaute
)

print(f"✅ {len(bewohnte_kacheln_clean)} bewohnte Kacheln exportiert nach: {output_gpkg}")
print(f"📊 CRS: {bewohnte_kacheln_clean.crs}")
print(f"🗺️  Ausdehnung: {bewohnte_kacheln_clean.total_bounds}")


