#
#	Map inference using a quadtree
#
#
import time
import math
import sys
from quadtree import QuadTree
from scipy import signal as sg
from scipy import mgrid, exp
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
MAX_DEPTH = 9 #Max recursion inn the quadtree


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
        self._apply_gaussian()
      #  self.canonical_edges = self._find_canonical_edges() # Extract edges from the canonical trips
        #self.trip_edge_index = self._build_trip_edge_index() # Build a geospacial index with all the edges
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
                
                # store current edge_index
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
        # iterate through all trips
        for trip in self.all_trips:

            #Iterate through all locations
            for location in trip.locations:
                location_index.insert(location)

        location_index.traverse() #Populate leaves[]
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
            trip_edge_minx = min(in_location.longitude ,out_location.longitude) 
            trip_edge_miny = min(in_location.latitude, out_location.latitude)
            trip_edge_maxx = max(in_location.longitude, out_location.longitude)
            trip_edge_maxy = max(in_location.latitude, out_location.latitude)                        

            #insert into index
            edge_index.insert(trip_edge.id, (trip_edge_minx, trip_edge_miny, trip_edge_maxx, trip_edge_maxy))
        
        return edge_index

    def _get_road_segments(self, treshold=0):
        # so basically what i am going to do here is something like this..
        # try to get the road segments that repete the most
        # hmm and
        # ok so lets get all the segments clasiffied and paint them

        # for edge in canonical_edges:
        #     _in = edge.in_node
        #     _out = edge.uot_node
        pass    

    def _get_road_center_line():
        pass

    def _bounding_box(self, locations):
        max_y = max(coord.latitude for coord in locations)
        min_y = min(coord.latitude for coord in locations)
        max_x  = max(coord.longitude for coord in locations)
        min_x = min(coord.longitude for coord in locations)
        rectangle = namedtuple('rectangle', ['x0', 'x1','y0', 'y1'])    
        box = rectangle(min_x, max_x, min_y, max_y)
        return box

    def _write_trips_to_file(self):
        pass

    def _write_nodes_to_file(self):
        nodes = self.location_index.leaves
        os.chdir("/home/moyano/Projects/CreateTracks/edges")
        test_file = open("edges.txt", "w")
        test_file.write("latitude, longitude, ocurrences")
        # print children
        for node in nodes:
            p = node._center_of_mass()
            count = node.blur_value
            if count > 2:
                test_file.write("\n")  
                test_file.write(str(p.latitude) + "," + str(p.longitude) + "," + str(count))


    def _write_weighted_nodes_to_file(self):
        pass

    def _get_tracks(self):
        pass

    def _apply_gaussian(self):
        _kernel = self.gauss_kernel(1)
        _nodes = self.location_index.leaves 
        sys.stdout.write("\nApplying gaussian filter to the grid... ")
        sys.stdout.flush()
        for _node in _nodes:
            coord = _node._center_of_mass()
            _neighbors = self.location_index.neighbors(coord, True)
            _node.blur_value = self._convolve(_neighbors, _kernel)

        sys.stdout.write("\nDone... ")
        sys.stdout.flush()

    # Multiplies the neigbhbors of x by a gaussian matrix
    # And returns the weighted average
    def _convolve(self, _neighbors, _kernel):
        value = 0
        value += self._multiply(_neighbors['nw'],_kernel[0][0])
        value += self._multiply(_neighbors['n'],_kernel[0][1])
        value += self._multiply(_neighbors['ne'],_kernel[0][2])
        value += self._multiply(_neighbors['w'],_kernel[1][0])
        value += self._multiply(_neighbors['x'],_kernel[1][1])
        value += self._multiply(_neighbors['e'],_kernel[1][2])
        value += self._multiply(_neighbors['sw'],_kernel[2][0])
        value += self._multiply(_neighbors['s'],_kernel[2][1])
        value += self._multiply(_neighbors['sw'],_kernel[2][2])
        return value

    def _multiply(self, node, kernel_value):

        if node:
            return len(node.leaves)*kernel_value
        else:
            return 0
    # I don't even know why the quadtree returns a hash
    def _neighbor_matrix(self, _dict):
        matrix = []

        line1 = []
        line1.append(len(_dict['nw']))
        line1.append(len(_dict['n']))
        line1.append(len(_dict['ne']))
        matrix.append(line1)
        line2 = []
        line2.append(len(_dict['w']))
        line2.append(len(_dict['x']))
        line2.append(len(_dict['e']))
        matrix.append(line2)

        line3 = []
        line3.append(len(_dict['sw']))
        line3.append(len(_dict['s']))
        line3.append(len(_dict['se']))
        matrix.append(line3)

        return matrix

    def _segments_to_kml(self, output):
        #Header
        kml = "<?xml version='1.0' encoding='UTF-8'?>"
        kml += "<kml xmlns='http://www.opengis.net/kml/2.2'>"
        kml +=  "<Document>"

        #Line Style
        kml +=  "<Style id='myStyle'>"
        kml +=      "<LineStyle>"
        kml +=        "<color>7f00ff00</color>"
        kml +=        "<width>4</width>"
        kml +=      "</LineStyle>"
        kml +=      "<PolyStyle>"
        kml +=        "<color>7f00ff00</color>"
        kml +=      "</PolyStyle>"
        kml +=  "</Style>"


        for key in self.canonical_edges:
            
            edge = self.canonical_edges[key]
            _in = edge.in_node._center_of_mass()
            _out = edge.out_node._center_of_mass()

            kml += "<Placemark>"
            kml += "<name>" + str(key) + "</name>"
            kml += "<styleUrl>#myStyle</styleUrl>"
            kml += "<LineString>"
            kml +=  "<altitudeMode>relative</altitudeMode>"
            kml +=  "<coordinates>"
            kml +=      str(_in.longitude) + "," + str(_in.latitude) 
            kml +=      str(_out.longitude) + "," + str(_out.latitude)
            kml +=   "</coordinates>"
            kml +=  "</LineString>"
            kml += "</Placemark>"

        #Close tags
        kml +=  "</Document>"       
        kml += "</kml>"

        _file = open(output,"w")
        _file.write(kml)
        _file.close()

    def get_color(self,count):
        if count <= 100:
            return "small_blue"
        elif count > 100 and count <= 150:
            return "ylw_blank"
        elif count > 150 and count <= 200:
            return "wht_blank"
        elif count > 200 and count <= 250:
            return "red_blank"
        elif count > 250 and count <= 300:
            return "purple_blank"
        elif count > 300 and count <= 350:
            return "pink_blank"
        elif count > 350 and count <= 400:
            return "pink_blank"        
        elif count > 400 and count <= 450:
            return "orange_blank"
        elif count > 450 and count <= 500:
            return "ltblu_blank"
        elif count > 500 and count <= 550:
            return "grn_blank"        
        elif count > 550 and count <= 650:
            return "blu_blank"     
        elif count > 650 and count <= 750:
            return "ylw_stars"
        else:
            return "wht_stars" 

    def gauss_kernel(self, size, sizey=None):
        """ Returns a normalized 2D gauss kernel array for convolutions """
        size = int(size)    
        if not sizey:
            sizey = size
        else:
            sizey = int(sizey)               
        #print size, sizey    
        x, y = mgrid[-size:size+1, -sizey:sizey+1]
        g = exp(-(x**2/float(size)+y**2/float(sizey)))
        return g / g.sum()

import sys, getopt, time,os
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
    m._write_nodes_to_file()
    # os.chdir("/home/moyano/Projects/CreateTracks/maps/")
    # m._segments_to_kml("kml_output.kml")
    
    print "\nMap inference completed (in " + str(time.time() - start_time) + " seconds).\n"