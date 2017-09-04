import sys
import os
import urllib2
import json
import mmap, codecs
from ISStreamer.Streamer import Streamer

# --------- User Settings ---------
BUCKET_NAME = "xxxxxxxxxxxxxxxx"
BUCKET_KEY = "xxxxxxxxxxxxxxxx"
ACCESS_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ---------- depencies -----------------------
# run the following command to aktivate ISStreamer for Inital State:
# \curl -sSL https://get.initialstate.com/python -o - | sudo bash
# at console

# run cyclic as cron job
# crontab -e
# ad:
# * * * * * /usr/bin/python ./WlanThermoInitialstate.py
#                           ad your path here

# ---------- getting Data -----------------------
def read_loc_json():
	try: #pruefen der Datei und lesen des Inhaltes
		with open('./WTdata.json') as f:    
			data= json.load(f)
	except IOError: # Wenn die Datei nicht vorhanden ist
		print('File not exists!') # Meldung ausgeben
		return[]	# leeres dict zurueckgeben
	f.close()
	return data
		
def write_loc_json(data):
	# write a simple example file
	with open('./WTdata.json', 'w') as f:
		json.dump(data, codecs.getwriter('utf-8')(f), ensure_ascii=False)	
	f.close()
	
def get_values():
    api_conditions_url = "http://localhost/app.php"
    try:
        f = urllib2.urlopen(api_conditions_url)
    except:
        print "Failed to get conditions"
        return []
    json_conditions = f.read()
    f.close()
    return json.loads(json_conditions)

def main():
	# -------------- WlanThermo --------------
	#neue Daten lesen
	values = get_values()
	
	#alte Daten von file lesen
	values_old = read_loc_json()
	
	# pruefen auf inhalt
	force_new_data = ('temp_unit' not in values_old)
	
	
	force_data = len(sys.argv) > 1
	
	# Manipulieren einzelner Werte
	values['cpu_load'] = round(values['cpu_load'],2)
	if values['temp_unit'] == 'celsius':
		values['temp_unit'] = "C"
	else:
		values['temp_unit'] = "F"

	print('force: ' + str(force_data))	
	#erneute Pruefung der aktualdaten zur weiteren ausfuehrung
	if ('temp_unit' not in values):
		print "Error! Wlanthermo app.php reading failed!"
		exit()
	else:
		# init ISStreamer
		streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)

		# Variablen durcharbeiten 
		for x in values:  #alle Basis Elemente durcharbeiten
			if (x == 'pit' or x == 'pit2'): #pitmaster signale
				for y in values[x]:
					new_data = False
					if force_new_data:
						new_data = True
					elif force_data:
						if str(y) == 'setpoint':
							new_data = True
					else:
						new_data= not (values[x][y] == values_old[x][y])
					
					if 'timestamp' in y:
						new_data = False
					
					if new_data:
						#print(str(x) + '_' + str(y) + ': ' + str(values[x][y]))
						name = str(x) + '_' + str(y)
						value = values[x][y]
						streamer.log(name, value)
						
			elif (x == 'channel'):  #alle Temperatur Kanaele durcharbeiten
				for y in values[x]:
					for z in values[x][y]:
						new_data = False
						if force_new_data:
							new_data = True
						elif force_data:
							if (values[x][y]['state'] == 'ok'):
								if str(z)[:4] == 'temp':
									new_data = True
						else:
							new_data= not (values[x][y][z] == values_old[x][y][z])
				
						if new_data:
							#print(str(x)[:2] + str('0'+ y)[:2] + '_' + str(z) + ': ' + str(values[x][y][z]))
							name = str(x)[:2] + str('0'+ y)[:2] + '_' + str(z)
							value = values[x][y][z]
							streamer.log(name, value)
				
			else:  # alle anderen Signale
				new_data = False
				if force_new_data:
					new_data = True
				elif (x == 'timestamp'):
					new_data = False
				else:
					new_data= not (values[x] == values_old[x])
				
				if new_data:
						#print(str(x) + ': ' + str(values[x]))
						name = str(x)
						value = values[x]
						streamer.log(name, value)
						
	print('done')
	try:
		streamer.flush()
	except Exception:
		print('Daten senden nicht moeglich!')
		exit() # hier wird abgebrochen, damit der Zischenspeicher mit Initialstate synchron bleibt.
		
	# schreiben der lokalen Datei
	write_loc_json(values)
	

if __name__ == "__main__":
    main()