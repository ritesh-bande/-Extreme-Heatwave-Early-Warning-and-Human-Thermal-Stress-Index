import urllib.request, json, urllib.parse
query = '[out:json];area["name"="Nagpur"]->.a;relation["admin_level"="9"](area.a);out geom;'
url = 'https://overpass-api.de/api/interpreter?data=' + urllib.parse.quote(query)
try:
    req = urllib.request.urlopen(url)
    data = json.loads(req.read())
    print(f'Found {len(data.get("elements", []))} elements')
except Exception as e:
    print(e)
