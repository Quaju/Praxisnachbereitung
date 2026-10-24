# Struktur
- das Projekt hat ein Backend
    - Templates
    - Webapp
    - API
- die DB
    - Initialisierungsskript
- die MQTT Konfiguration
    - wird vom Broker gelesen
# Formularverarbeitung
- Die Formulare werden an die API übergeben
- Werden mithilfe von den Datenmodellen in Python Objekte umgewandelt
- Die Objekte werden dann für die Parametrisierung der SQL Queries genutzt
# Templates
- Template Response in der die Daten enstprechend eingesetzt werden
# CRUD flows
- Create
    - post Funktion
    - entsprechende create Klassen
- Update
    - update Funktion
    - entsprechende Update Klassen
- Delete
    - delete Funktion
    - Post request auf den Delete Pfad