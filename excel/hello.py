import csv
with open("C:/Users/juliu/PraxisNach/Praxisnachbereitung/excel/Gesamt_Bereinigt.csv", newline='') as file:
    reader = csv.reader(file, delimiter= ";")
    for row in reader:
        print(", ".join(row))