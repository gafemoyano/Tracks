import sys
from pymongo import MongoClient
from trip import TripLoader
from bson.objectid import ObjectId

def get_trips_from_files(path):
	all_trips = TripLoader.get_all_trips(path)
	new_trips = []
	#iterate through all trips
	sys.stdout.write("\nRetrieving trips from text files... ")

	for trip in all_trips:
		print trip
		print "\n"
		#create JSON type object
		t = {"num_locations": trip.num_locations,
			 "start_time": trip.start_time,
			 "end_time": trip.end_time,
			 "time_span": trip.time_span,
			 "locations": []
		}

		#iterate all locations 
		new_locations = []
		for l in trip.locations:
			new_location = {
							"_id": ObjectId(),
							"longitude": l.longitude,
							"latitude": l.latitude,
							"time": l.time
			}
			new_locations.append(new_location)

		#insert locations onto trip hash
		t["locations"] = new_locations
		print "\n"
		new_trips.append(t)

	#Insert trips into database
	sys.stdout.write("\nTrips loaded onto memory... ")
	return new_trips


if __name__ == '__main__':
	sys.stdout.write("\nInstantiating database... ")

	client = MongoClient()
	db = client["trip_db"]
	trip_collection = db.trips
	#Drop the current table
	trip_collection.drop()
	#Load trips from files
	trips = get_trips_from_files("trips/")

	sys.stdout.write("\nInserting objects into database... ")
	trip_collection.insert(trips)


