# WlanThermoInitialstate
Schnittstelle vom WlanThermo zu Initiatlstate

dieses Script erzeugt eine Datei zum Zwischenspeichern der letzten Daten welche an Initialstate gesendet wurden.

# Commandlineparameter:
Daten nicht senden
/nc       keine CPU-Daten senden
/np       keine Pitmasterdaten senden

Daten zwingend senden
/ft       Zusatzwerte der Kanaele senden (min/max)        
/fa       Datei wird gelöscht und Daten werden neu gesendet.

löschen der Zwischenspeicher Datei
/dT       die Temporaere Datei wird gelöscht,
          beim nächsten Aufruf findet automatisch ein INIT statt.
          Es werden auch keine Daten gesendet.

/eC=Path_to_file  
          External Credentials BenutzerDaten von externer Datei laden


# Config Einstellungen:
Achtung Strings "" eingeben
[Initialstate]                Credentials
BUCKET_NAME = xxxxxxxxxxxxxxxx          
BUCKET_KEY = xxxxxxxxxxxxxxxx
ACCESS_KEY = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

[Local]
Temp_File = /home/pi/WTdata.json       Pfad zum Zwischenspeicher

[Options]
notSendCPU = FALSE              keine CPU-Daten senden
notSendPit = FALSE              keine Pitmasterdaten senden

[WlanThermo]
URL = http://localhost/app.php  Pfad zum WlanThermo, falls das Script nicht lokal ausgeführt wird


# ---------- depencies -----------------------
run the following command to aktivate ISStreamer for Inital State:
\curl -sSL https://get.initialstate.com/python -o - | sudo bash
at console

# run cyclic as cron job
crontab -e
ad:
* * * * * /usr/bin/python ./WlanThermoInitialstate.py
                           ad your path here
