
# Routing für Rettungsdienste bei Hochwasser


---------------------------------------------------------------------

## Beschreibung:
Dieses Projekt untersucht, wie sich Hochwasser auf die Erreichbarkeit von Rettungsdiensten und Feuerwehr auswirkt. 
Dabei wird analysiert:
- Welche Station unter normalen Bedingungen am schnellsten ist
- Ob sich diese Zuständigkeit bei Hochwasser verändert
Als Grundlage dient das am stärksten betroffene Gebiet innerhalb einer Beispielgemeinde.


Der Analyseworkflow lässt sich in drei Schritten unterteilen:

1.Identifikation des am stärksten betroffenen Überflutungsbereichs und Bestimmung eines Anfahrpunkts für Rettungsdienste/Feuerwehr
Verwendete Skripte: selectOrt_u_Bev.py, target_point.py, find_exit.py


2.Auswahl der nächstgelegenen, innerhalb von 15 min erreichbaren, Krankenhäuser und Feuerwehrstationen
Verwendete Skripte: care_in_puffer03.py


3. Analyse der Fahrtzeitänderungen bei Überflutung. 
Verwendete Skripte: next_care04_2.py, ors_analyse02.py, plots.py

---------------------------------------------------------------------

## Voraussetzung:
	Python >= 3.10
	Internetverbindung (für OpenRouteService API)
	
---------------------------------------------------------------------

## Benötigte Daten:
	Überflutungsflächen:	UEG_SN.shp
	Bevölkerungsdaten:	sachsen_bewohnte_kacheln.gpkg
	Gemeindegrenzen:	gem.shp
	Straßennetz: 		*.geojson

In folgenden Dateien müssen Pfade angepasst werden:
	main.py

---------------------------------------------------------------------

## Installation:
Es müssen noch packages zur Durchführung installiert werden, daher sollte dieser Pfad im einmalig vor der Nutzung im Terminal ausgeführt werden:

pip install geopandas shapely pandas numpy matplotlib contextily pyproj openrouteservice osmnx networkx rtree requests

---------------------------------------------------------------------

## Nutzung
1. Pfade in `main.py` (Zeile 17–20) anpassen 

Im Terminal:
2. cd <Pfad_zum_Projekt>
3. Programm starten: "python .\code\main.py" 

Grundsetzlich wird der Code über den die main.py Datei gesteuert. hier kann unter anderem auch das Untersuchungsgebiet gesetzt werden: z.B. gemeinde_name = "Pirna".

Die Berechnung kann mehrere Minuten dauern.
Zwischenplots müssen geschlossen werden, damit das Programm fortgesetzt wird.

---------------------------------------------------------------------

## Known Issus:
1. Exit-Point-Erkennung unvollständig
Beim Ableiten möglicher Exit-Points aus Überflutungsgebieten zeigt die Visualisierung, dass vermutlich weitere geeignete Punkte existieren. diese werden aktuell jedoch nicht erkannt. Eine genaue Ursache ist noch nicht bekannt. 

2. Wenn ein bewohntes Überflutungsgebiet komplett mit Wasser umgeben ist, kann kein Exit-Point gefunden werden 

3. Routing schlägt teilweise fehl
Das Routing zwischen Exit-Point und Rettungsdienst bzw. Feuerwehr liefert nicht immer eine Route. In diesen Fällen gibt die API von OpenRouteService (ORS) keine gültige Verbindung zurück.
Mögliche Ursachen:
	1. Flutpolygone blockieren unbemerkt kritische Knoten im Bereich der Route
	2. Das gedownloadete Straßennetzwerk stimmt nicht mit dem vom ORS überein, somit liegt der Punkt nicht auf einer erreichbaren Straße

4. Routenänderung ohne sichtbare Flutüberschneidung
In einigen Fällen unterschiedet sich die Route mit Hochwasser von der normalen Route, obwohl das Hochwasser die ursprüngliche Route visuell nicht schneidet.
Die Ursache konnte bislang nicht eindeutig identifiziert werden.

---------------------------------------------------------------------

## Zukünftige Verbesserungen
1. Beheben der bekannten Probleme
	Stabilisierung der Exit-Point-Erkennung sowie der Routing-Robustheit bei großen oder komplexen Hochwasserflächen

2. Fallback-Strategie beim Routing
	Falls kein Routing zu einem Exit-Point möglich ist, soll automatisch ein alternativer Exit-Point getestet werden.

3. Erweiterung des Untersuchung Gebiets
	Einbeziehung weiterer potenziell betroffener Bereiche innerhalb er Gemeinde um eine realistische Einsatzplanung abzubilden

4. Mehrere Anfahrpunkte bei großen Überflutungen
	Für ausgedehnte Hochwasserflächen sollen mehrere geeignete Zugangspunkte bestimmt werden.
	Zusätzlich könnten nächstegelegene Rettungsdienste bzw. Feuerwehren algorithmisch auf Exit-Points verteilt werden, um eine möglichst vollständige 	Abdeckung sicherzustellen.

5. Langfristiges Projektziel
	Entwicklung einer klaren zuständigkeits- und Anfahrtslogik für Hochwasserlagen, sodass bereits im Vorfeld definiert ist:
		1. welche Station zuständig ist
		2. welcher zugangspunkt genutzt wird
		3. wie die Einsatzplanung im Extremfall aussieht

---------------------------------------------------------------------

## Tools
Für das Erstellen des Codes wurde "Perplexity AI" als Unterstützung verwendet.
Die KI half bei Code-Optimierung und Debugging.
Es wurden alle Vorschläge geprüft, angepasst und final validiert.

---------------------------------------------------------------------

## Autoren
Milan Barth
Sascha Wegert

---------------------------------------------------------------------

## Kontakt
milan.barth@stud.uni-heidelberg.de

---------------------------------------------------------------------

## Lizenz
GNU GPL
