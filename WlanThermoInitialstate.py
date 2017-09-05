#!/usr/bin/python
# coding=utf-8

import sys
import os
import urllib2
import json
import mmap, codecs
import ConfigParser
from ISStreamer.Streamer import Streamer

# ---------- getting Data -----------------------
def read_loc_json(jsonPath):
	try: #pruefen der Datei und lesen des Inhaltes
		with open(jsonPath) as f:
			data= json.load(f)
	except IOError: # Wenn die Datei nicht vorhanden ist
		print('File not exists!') # Meldung ausgeben
		return[]	# leeres dict zurueckgeben
	f.close()
	return data

def write_loc_json(data, filepath):
	# schreiben der Datendatei
	with open(filepath, 'w') as f:
		json.dump(data, codecs.getwriter('utf-8')(f), ensure_ascii=False)
	f.close()

def delete_loc_json(filepath):
	## if file exists, delete it ##
	if os.path.isfile(filepath):
		os.remove(filepath)
	else:    ## Show an error ##
		print("Error: %s file not found" % myfile)
		exit()

def get_values(WL_URL):
    api_conditions_url = str(WL_URL)
    try:
		 f = urllib2.urlopen(api_conditions_url)
    except:
        print "Failed to get conditions"
        return []
    json_conditions = f.read()
    f.close()
    return json.loads(json_conditions)

def main():
	# --------- local Path ---------
	configPath = './WlanThermoInitialstate.cfg'

	# --------- local Tags ---------
	force_data = False
	NoSendCPU = False
	NoSendPit = False
	delTemp= False
	bExit = False

	# -------------- Kommandozeilen Parameter --------------
	for x in range(1, len(sys.argv)):
		if sys.argv[x] == '/dT' or sys.argv[x] == '/fa' :
			delTemp = True
			bExit = sys.argv[x] == '/dT'
		elif sys.argv[x] == '/ft':
			force_data = True
		elif sys.argv[x] == '/nc':
			NoSendCPU = True
		elif sys.argv[x] == '/np':
			NoSendPit = True
		elif '/eC' == sys.argv[x][:3]:
			arg = sys.argv[x]
			cfgpath= arg.split('=')
			if os.path.isfile(cfgpath[1]):
				configPath=cfgpath[1]
			else:
				print('Parameter /eC File %s not exists!' % cfgpath[1])
		else:
			print('Wrong Parameter %s in Commandline' % sys.argv[x])
			exit()

	# -------------- Konfiguration --------------
	cfg = ConfigParser.ConfigParser()
	cfg.read(configPath)
	myfile = cfg.get('Local','Temp_File')
	s = cfg.get('Options','notSendCPU')
	sendCPU = (s.upper() != 'TRUE') and not NoSendCPU
	s = cfg.get('Options','notSendPit')
	sendPit = (s.upper() != 'TRUE') and not NoSendPit
	BUCKET_NAME = cfg.get('Initialstate','BUCKET_NAME')
	BUCKET_KEY = cfg.get('Initialstate','BUCKET_KEY')
	ACCESS_KEY = cfg.get('Initialstate','ACCESS_KEY')
	WlanThermoURL = cfg.get('WlanThermo','URL')

	# -------------- Löschen der Temporaeren Datei --------------
	if delTemp:
		delete_loc_json(myfile)
		if bExit:
			exit()

	# -------------- WlanThermo --------------
	#neue Daten lesen
	values = get_values(WlanThermoURL)

	# -------------- alte Daten von file lesen --------------
	values_old = read_loc_json(myfile)

	# -------------- pruefen auf inhalt --------------
	force_new_data = ('temp_unit' not in values_old)

	# -------------- Manipulieren einzelner Werte --------------
	values['cpu_load'] = round(values['cpu_load'],2)
	if values['temp_unit'] == 'celsius':
		values['temp_unit'] = "C"
	else:
		values['temp_unit'] = "F"

	#erneute Pruefung der aktualdaten zur weiteren ausfuehrung
	if ('temp_unit' not in values):
		print "Error! Wlanthermo app.php reading failed!"
		exit()
	else:
		# init ISStreamer
		streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)

		# Variablen durcharbeiten
		for x in values:  #alle Basis Elemente durcharbeiten
			if ('pit' == str(x)[:3]): #pitmaster signale
				if sendPit:
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
							name = str(x)[:2] + str('0'+ y)[:2] + '_' + str(z)
							value = values[x][y][z]
							streamer.log(name, value)
			elif ('cpu' == str(x)[:3]):
				if sendCPU:
					new_data = False
					if force_new_data:
						new_data = True
					else:
						new_data= not (values[x] == values_old[x])

					if new_data:
						name = str(x)
						value = values[x]
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
						name = str(x)
						value = values[x]
						streamer.log(name, value)

	try:
		streamer.flush()
	except Exception:
		print('Daten senden nicht moeglich!')
		exit() # hier wird abgebrochen, damit der Zischenspeicher mit Initialstate synchron bleibt.

	# schreiben der lokalen Datei
	write_loc_json(values, myfile)

if __name__ == "__main__":
    main()
