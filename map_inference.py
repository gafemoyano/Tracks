#
#	Map inference using a quadtree
#
#
import time
import math
import sys
from quadtree import QuadTree
from pymongo import MongoClient
from rtree import index
from trip import TripLoader, Trip, TripParser
from collections import namedtuple

client = MongoClient()
db = client.trip_db
trip_collection = db.trips
all_trips = TripParser.json_to_object(trip_collection.find())
# globals
trip_max=len(all_trips)
all_locations = list(location for trip in all_trips for location in trip.locations)
MAX_DEPTH = 6 #Max recursion inn the quadtree


class Edge:
    def __init__(self, id, in_node, out_node):
        self.id = id
        self.in_node = in_node
        self.out_node = out_node


class MapAlgo(object):

    def __init__(self, all_trips):
        self.all_trips = all_trips
        self.trip_edges = self._find_all_trip_edges()
        self.bounding_box = self._bounding_box(all_locations)
        self.location_index = None    
        self.trip_edge_index = None
        self.canonical_trips = []
        self.canonical_edges = {}
	
    #
    # Control de flow of the algorithm
    #
    def run_algorithm(self):
        sys.stdout.write("\nRunning map inference algorithm ... ")
        sys.stdout.flush()
        self.location_index = self._build_location_index() # Initialize and populate the quadtree
        self.canonical_trips = self._find_canonical_trips() # Build Trips with qtree Nodes instead of Locations
        self.canonical_edges = self._find_canonical_edges() # Extract edges from the canonical trips
        self.trip_edge_index = self._build_trip_edge_index() # Build a geospacial index with all the edges
    #
    # by James P. Biagioni (jbiagi1@uic.edu) 
    #
    def _find_all_trip_edges(self):
        sys.stdout.write("\nFinding all trip edges ... ")
        sys.stdout.flush()
        
        # storage for trip edges
        trip_edges = {} # indexed by trip edge id
        
        # storage for trip edge id
        trip_edge_id = 0
        
        # iterate through all trips
        for trip in self.all_trips:
            
            # iterate through all trip locations
            for i in range(1, len(trip.locations)):
                
                # store current edge
                trip_edges[trip_edge_id] = Edge(trip_edge_id, trip.locations[i-1], trip.locations[i])
                
                # increment trip edge id
                trip_edge_id += 1
        
        print "done."
        
        # return all trip edges
        return trip_edges

    def _find_canonical_edges(self):
        sys.stdout.write("\nFinding canonical trip edges ... ")
        sys.stdout.flush()
        
        # storage for trip edges
        _trip_edges = {} # indexed by trip edge id
        
        # storage for trip edge id
        _trip_edge_id = 0
        
        # iterate through all trips
        for trip in self.canonical_trips:
            
            # iterate through all trip locations
            for i in range(1, len(trip.locations)):
                
                # store current edge
                _trip_edges[_trip_edge_id] = Edge(_trip_edge_id, trip.locations[i-1], trip.locations[i])
                
                # increment trip edge id
                _trip_edge_id += 1
        
        print "done."
        
        # return all trip edges
        return _trip_edges

    #
    #  Transforms all the trip locations to their containing
    #  node in the trip_index
    #
    def _find_canonical_trips(self):
        sys.stdout.write("\nCreating Canonical Trips ... ")
        sys.stdout.flush()
        trips = []

        for trip in self.all_trips:
            canonical_trip = Trip()
            
            for _location in trip.locations:
                location_node = self.location_index.containing_node(_location)
                canonical_trip.add_location(location_node)

            trips.append(canonical_trip)

        return trips

    def _build_location_index(self):   
        sys.stdout.write("Generating QuadTree location index... ")
        sys.stdout.flush()
        location_index = QuadTree(MAX_DEPTH, self.bounding_box)
        location_index.traverse() #Populate leaves[]

        # iterate through all trips
        for trip in self.all_trips:

            #Iterate through all locations
            for location in trip.locations:
                location_index.insert(location)                

        return location_index

    #
    #   Store all canonical trip edges in a RTree index
    #
    def _build_trip_edge_index(self):
        sys.stdout.write("\nBuilding trip edge index for map inference algorithm... ")
        sys.stdout.flush()
        edge_index = index.Index()

        # iterate through all trip edges

        for trip_edge in self.canonical_edges.values():

            #Get a Point(latitude, longitude) touple
            in_location = trip_edge.in_node._center_of_mass() 
            out_location = trip_edge.out_node._center_of_mass() 
            
            # determine the bounding box of the edge
            trip_edge_minx = min(in_location.longitude, out_location.longitude)
            trip_edge_miny = min(in_location.latitude, out_location.latitude)
            trip_edge_maxx = max(in_location.longitude, out_location.longitude)
            trip_edge_maxy = max(in_location.latitude, out_location.latitude)                        

            #insert into index
            edge_index.insert(trip_edge.id, (trip_edge_minx, trip_edge_miny, trip_edge_maxx, trip_edge_maxy))
        
        return edge_index

    def _get_road_segments(self, treshold=0):
        pass

    def _bounding_box(self, locations):
        max_y = max(coord.latitude for coord in locations)
        min_y = min(coord.latitude for coord in locations)
        max_x = max(coord.longitude for coord in locations)
        min_x = min(coord.longitude for coord in locations)
        rectangle = namedtuple('rectangle', ['x0', 'x1','y0', 'y1'])    
        box = rectangle(min_x, max_x, min_y, max_y)
        return box

    def _write_trips_to_file(self):
        pass

    def _write_nodes_to_file(self):
        pass

    def _write_weighted_nodes_to_file(self):
        pass

    def _get_tracks(self):
        



import sys, getopt, time
if __name__ == '__main__':
    
    (opts, args) = getopt.getopt(sys.argv[1:],"n:h")
    
    for o,a in opts:
        if o == "-n":
            trip_max = int(a)
        if o == "-h":
            print "Usage: python map_inference.py [-n <trip_max>] [-h]\n"
            exit()
    
    start_time = time.time()
    m = MapAlgo(all_trips[:trip_max])
    m.run_algorithm()
    
    print "\nMap inference completed (in " + str(time.time() - start_time) + " seconds).\n"