import urllib2
import sys,time
import xml.etree.ElementTree as etree
from pymongo import MongoClient

def get_feed_data(vehicles, time = 0):
	url = 'http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=mbta&t=' + str(time)
	_file = urllib2.urlopen(url)
	_data = _file.read()
	_file.close
	root = etree.fromstring(_data)
	items = root.findall('vehicle')

	for item in items:
		attrs = item.attrib

		vehicle = list(vehicles.find({'_id': attrs['id']}).limit(1))

		if not vehicle:
		#If there isn't a vehicle with the obtained id
			new_vehicle = {"_id": attrs['id'],
					   "route": attrs['routeTag'],
					   "locations": [],
			}
			vehicles.insert(new_vehicle)

		loc =  [{"latitude": attrs['lat'],
				"longitude": attrs['lon']		
			}]

		vehicles.update( { '_id': attrs['id'] }, {'$pushAll': { 'locations': loc}});
		
		t = root.findall('lastTime')[0].attrib['time']
		return t

if __name__ == '__main__':
	sys.stdout.write("Instantiating database... \n")

	client = MongoClient()
	db = client["boston_bus_db"]
	vehicles = db.vehicles

	sys.stdout.write("Inserting objects into database...\n ")
	last_time = 0
	while(True):
		last_time = get_feed_data(vehicles, last_time)
		time.sleep(10)
		print last_time