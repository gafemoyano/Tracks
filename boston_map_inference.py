import time
import math
import sys
import numpy as np
from trajectory import Trajectory
from quadtree import QuadTree
from scipy import signal as sg
from scipy import mgrid, exp
from scipy import stats as st
from itertools import permutations, groupby
from pymongo import MongoClient
from rtree import index
from trip import TripLoader, Trip, TripParser
from collections import namedtuple
from itertools import tee, islice, chain, izip
from map_inference import MapAlgo as mpa

client = MongoClient()
db = client.trip_db
trip_collection = db.trips
all_trips = TripParser.json_to_object(trip_collection.find())
# globals
all_locations = list(location for trip in all_trips for location in trip.locations)
trip_max=len(all_trips)
MAX_DEPTH = 8 #Max recursion inn the quadtree #Should change this to meters


class BostonMap(object):


    def __init__(self, all_trips):
        self.all_trips = all_trips
        self.bounding_box = self._bounding_box(all_locations)
        self.location_index = None    
        self.all_nodes = {}

	def run_algorithm(self):
	        sys.stdout.write("\nRunning map inference algorithm ... ")
	        sys.stdout.flush()
	        self.location_index = self._build_location_index()
	        self._trim_spurious_roads()


	#
    # Initializes the quadtree and adds all the trajectory information
    # 
    def _build_location_index(self):   
        sys.stdout.write("Generating QuadTree location index... ")
        sys.stdout.flush()
        location_index = QuadTree(MAX_DEPTH, self.bounding_box)
        # iterate through all trips

        for trip in self.all_trips:
            #Iterate through all locations
            current_node = None
            #Loop for adding trajectory information
            for previous, location, next in self.previous_and_next(trip.locations):
                current_node = location_index.insert(location)

                # First location 
                if previous is not None and next is not None:
                    #get the node where the next location would fall
                    self.update_trajectory(previous, location, next, current_node)


        location_index.traverse() #Populate leaves[]

        _node_id = 0
        #Hash with all leaves
        for leave in location_index.leaves:
            location = leave._center_of_mass()
            leave.id = (location.latitude, location.longitude)
            self.all_nodes[(location.latitude, location.longitude)] = leave

        return location_index

import sys, getopt, time,os
if __name__ == '__main__':
    
    (opts, args) = getopt.getopt(sys.argv[1:],"n:f:h")
    
    for o,a in opts:
        print o,a
        if o == "-n":
            trip_max = int(a)
        if o == "-f":
            kml_output = a
        if o == "-h":
            print "Usage: python map_inference.py [-n <trip_max>] [-f <filde_name>] [-h]\n"
            exit()
    
    start_time = time.time()
    m = BostonMap(all_trips[:trip_max])
    m.run_algorithm()
    m._segments_to_kml(kml_output)

    # os.chdir("/home/moyano/Projects/CreateTracks/maps/")
    
    print "\nMap inference completed (in " + str(time.time() - start_time) + " seconds).\n"