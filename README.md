# Praxisnachbereitung
## Arbeitsablauf
csv datei import Ausleihe, Geräte und Mitarbeiter
Fehlerhafte Daten entfernt sowie die Datentypen und Überschriften geprüft
Zusammenführung von Geräte und Ausleihe mit einem Inner Join
daraufhin wurden die Mitarbeitern ergänzt und damit eine Gesamttabelle erstellt.
Es wurde der Gesamtwert nicht im Einsatz befindlicher Geräte ermittelt indem alle mit abgabedatum erfasst wurden.
Alle Ausleihen mit dem typen Laptop gefiltert.
Pivottabelle erstellt mit allen Gerätetypen und ihrer jeweiligen Anzahl und ein Säulendiagramm erstellt.
Hinzufügung des Standortes und ein gestapeltes Säulendiagramm erstellt 
Export der gesamttabelle als CSV

## Probleme
WÄhrungsdarstellung aufgrund von regionalen Unterschieden. Lösung mit Abfrage als Gebietsschema

## Erkenntnisse
Excel kann erstaunlich pingelig sein