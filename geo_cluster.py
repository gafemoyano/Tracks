from __future__ import division
import numpy as np
from rtree import index
from trajectory import Trajectory
from pymongo import MongoClient
from trip import TripLoader, Trip, TripParser

client = MongoClient()
db = client.trip_db
trip_collection = db.trips
all_trips = TripParser.json_to_object(trip_collection.find())
# globals
trip_max=len(all_trips)
location_list = list(location for trip in all_trips for location in trip.locations)
all_locations = dict([(loc._id, loc) for loc in location_list])

class GeoCluster(object):

	MAX_DISTANCE_ALLOWED = 20 #meters

	def __init__(self):

		self.location_index = index.Index()
		self.clusters = []


	def insert_locations(self):
		for key, _location in all_locations.iteritems():
			coord = [_location.latitude, _location.longitude]

			for _cluster in clusters:
				if self.belongs_in_cluster(location, cluster):
					cluster.add_location()
				else:
					self.split_cluster(cluster)

			self.location_index.add(coord)



	def relative_weight(self, location1, bearing1, location2, bearing2):
		
		

	def split_cluster(self, cluster):
		pass

class Cluster(object):

	def __init__(self):
		self.parent = None
		self.locations = []
		self.id = 0
		self.radius = 0
		self.seed = None

	def add(self, loc):
		self.locations.append(loc)

	def score(self, loc):
		return Trajectory.distance(self.seed.latitude, self.seed.longitude, loc.latitude, loc.longitude)

import sys, getopt, time,os
if __name__ == '__main__':
    
    
    start_time = time.time()
    cluster = GeoCluster()
    cluster.insert_locations()
    
    print "\nClustering completed (in " + str(time.time() - start_time) + " seconds).\n"

'''
1. Iterate locations
2. Create a cluster
3. check if it belongs there

'''
