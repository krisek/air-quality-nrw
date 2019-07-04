from app import app

import requests
from requests.packages import urllib3
import re
import json
from flask import Response

def getData():

  r = requests.get('https://www.lanuv.nrw.de/fileadmin/lanuv/luft/immissionen/aktluftqual/eu_luft_akt.htm', headers={'Content-type': 'application/json'})
  
  
  levels = {
    
    'eins': {'value': 1, 'color':'#3399FF'},
    'zwei': {'value': 2, 'color': '#66CCFF'},
    'drei': {'value': 3, 'color':'#99FFFF'},
    'vier': {'value': 4, 'color':'#FFFF99'},
    'fuenf': {'value': 5, 'color':'#FF9933'},
    'sechs': {'value': 6, 'color':'#FE0000'}
  }
  
  characters = {
    '&uuml;': 'ü',
    '&ouml;': 'ö',
    '&auml;': 'ä',
    '&szlig;': 'ß' 
  }
  
  air_map = {}
  
  #print(r.text)
  pout = False
  for line in r.text.split('\n'):
    if(pout and re.search('<!--Ende Platzhalter' ,line)):
      pout = False
    if pout:
      elems = line.split('<td')
      for elem in elems:
        #print(elem)
        elem = elem.replace('>','')
      record_raw = {}
      record_raw_comp = {}
      try:
        record_raw = {
            'sensor': elems[1].replace('>',''),
            'code': elems[2],
            'o3': elems[3],
            'so2': elems[4],
            'no2': elems[5],
            'pm10': elems[6]
          }
        #print(record_raw)
      except:
        pass
        #print(line)
      record_raw_comp['code'] = record_raw.get('code', '')
      for key in record_raw:
        #print(key)
        #clean HTML
        record_raw[key]=record_raw[key].replace('>','').replace('</td>','').replace('</td','').replace('</tr','')
        #manage missing measurement
        record_raw[key]=record_raw[key].replace(' class="strich"-<span class="ns"Strich - derzeit kein Wert</span', '-')
        #manage no sensor
        if record_raw[key] == "&nbsp;":
          record_raw_comp[key] = 'n/a'
        #extract level
        matchObj = re.search('\s*class=\"(.*)"\s*', record_raw[key], re.M|re.I)
        if matchObj:
          record_raw_comp[key + '_level'] = matchObj.group(1)
          record_raw_comp[key] = re.sub('\s*class=\"(.*)\"\s*' ,'', record_raw[key])
          if record_raw_comp[key + '_level'] in levels:
            record_raw_comp[key + '_level'] = levels[record_raw_comp[key + '_level']]
        #clean code TODO - check with clean HTML
        if key == 'code':
          record_raw_comp['code'] = record_raw['code'].replace('</td>', '')
        #clean sensor name
        if key == 'sensor':
          record_raw_comp[key] = record_raw[key]
          for char in characters:
            record_raw_comp[key] = record_raw_comp[key].replace(char, characters[char])
      
      #merge back data
      record = {**record_raw, **record_raw_comp}
      #print(record)
      #print(record_raw_comp)
      
      #map data
      if 'code' in record and record['code'] != '':
        air_map[record['code']] = record
      #nothing more to do with the line
    #check end of data
    if(re.search('Aktive-Stationen', line)):
      pout = True
  
  return air_map    

    
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  path = path.upper()
  air_map = getData()
  if path in air_map:
      return Response(json.dumps(air_map[path]), mimetype='application/json')
      
  else:
      return Response(json.dumps(air_map), mimetype='application/json')
