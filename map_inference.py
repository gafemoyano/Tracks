#
#	Map inference using a quadtree
#
#
import time
import math
import sys
from trajectory import Trajectory
from quadtree import QuadTree
from scipy import signal as sg
from scipy import mgrid, exp
from pymongo import MongoClient
from rtree import index
from trip import TripLoader, Trip, TripParser
from collections import namedtuple
from itertools import tee, islice, chain, izip

client = MongoClient()
db = client.trip_db
trip_collection = db.trips
all_trips = TripParser.json_to_object(trip_collection.find())
# globals
trip_max=len(all_trips)
all_locations = list(location for trip in all_trips for location in trip.locations)
MAX_DEPTH = 8 #Max recursion inn the quadtree #Should change this to meters


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
        self.all_nodes = {}
	
    #distribution
    # Control de flow of the algorithm
    #
    def run_algorithm(self):
        sys.stdout.write("\nRunning map inference algorithm ... ")
        sys.stdout.flush()
        self.location_index = self._build_location_index() # Initialize and populate the quadtree
        #self.canonical_trips = self._find_canonical_trips() # Build Trips with qtree Nodes instead of Locations
        #self._apply_gaussian()
        self._count_patterns()
        self._segments_to_kml()
        #self.skeletonize()
      #  self.canonical_edges = self._find_canonical_edges() # Extract edges from the canonical trips
        #self.trip_edge_index = self._build_trip_edge_index() # Build a geospacial index with all the edges

    def classify_nodes(self):
        thresholds = [2**x for x in range(8, 3, -1)] + range(15, 0, -1)

        for current_threshold in thresholds:
            current_nodes = self.filter_nodes_by_threshold(current_threshold)
            self.save_nodes(current_nodes,threshold)

    def filter_nodes_by_threshold(self, threshold):
        thresholded_nodes = []

        for key in self.all_nodes:
            if self.all_nodes[key].blur_value > threshold:
                thresholded_nodes.add(key)

        return thresholded_nodes

    def save_nodes(self, nodes, threshold):
        
        save_nodes = []
        for current_id in nodes:
            loc = [current_id[0],current_id[1]]
            save_node = {"location": loc,
                         "threshold": threshold,
                         "value": self.all_nodes[current_id].blur_value
            }
            save_nodes.append(save_node)

        node_collection = db.node_collection
        node_collection.insert(save_nodes)


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
        
        # storage for trip _trip_edges
        edges = {} # indexed by trip edge id
        
        # storage for trip edge id
        _trip_edge_id = iterate
        
        # 0 through all trips
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

    def update_trajectory(self, previous, current, next, node):

        #get the total distance traveled
        total_distance = Trajectory.distance(previous.latitude, previous.longitude, current.latitude, current.longitude) + Trajectory.distance(next.latitude, next.longitude, current.latitude, current.longitude)
        
        # If the distance traveled between the three points is more than 15 mts
        if total_distance > 15:
            in_bearing = Trajectory.initial_heading(previous.latitude, previous.longitude, current.latitude, current.longitude)
            out_bearing = Trajectory.initial_heading(current.latitude, current.longitude, next.latitude, next.longitude)

            #Get a cardinal representation of the bearing
            in_direction = Trajectory.direction((in_bearing + 180) % 360)
            out_direction = Trajectory.direction(out_bearing)

            if  (in_direction, out_direction) not in node.trajectories:
                node.trajectories[in_direction,out_direction] = 0

            node.trajectories[in_direction,out_direction] += 1

                    

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

    def _get_road_center_line(self):
        pass




    def _bounding_box(self, locations):
        max_y = max(coord.latitude for coord in locations)
        min_y = min(coord.latitude for coord in locations)
        max_x  = max(coord.longitude for coord in locations)
        min_x = min(coord.longitude for coord in locations)
        rectangle = namedtuple('rectangle', ['x0', 'x1','y0', 'y1'])    
        box = rectangle(min_x -  0.005, max_x +  0.005 , min_y -  0.005, max_y +  0.005)
        return box

    def _write_trips_to_file(self):
        os.chdir("/home/moyano/Projects/Tracks/edges")
        test_file = open("neighbors.txt", "w")
        test_file.write("latitude, longitude")
        # print children
        for k in self.all_nodes.keys():
            p = self.all_nodes[k]._center_of_mass()
            print p
            n = self.location_index.neighbors(p)
            print n
            if n:
                for k,v in n.iteritems():
                    if v.locations:
                        x = v._center_of_mass()
                        print x
                        test_file.write("\n")  
                        test_file.write(str(x.latitude) + "," + str(x.longitude))
            break

    def _write_nodes_to_file(self):
        nodes = self.location_index.leaves
        os.chdir("/home/moyano/Projects/Tracks/edges")
        test_file = open("blurred.txt", "w")
        test_file.write("latitude, longitude, ocurrences")
        # print children
        for node in nodes:
            p = node._center_of_mass()
            count = node.blur_value
            if count > 0:
                test_file.write("\n")  
                test_file.write(str(p.latitude) + "," + str(p.longitude) + "," + str(count))


    def _write_weighted_nodes_to_file(self):
        pass

    def _get_tracks(self):
        pass

    def skeletonize(self, threshold = 250):
        _nodes = self.location_index.leaves
        _selected_nodes = set()

        for _node_key in self.all_nodes.keys():

            if self.all_nodes[_node_key].blur_value > threshold:
                _selected_nodes.add(_node_key)
                self.all_nodes[_node_key].skeleton_value = 1
       
        print len(_selected_nodes)
        print len(self.all_nodes)
        self.thin_nodes(_selected_nodes)
    # Define if a pixel should be removed or not. A pixel is only kept if it  belongs
    # to the skeleton of the image
    # based on "A Fast Parallel Algorithm for Thinning Digital Patterns" by T. Y. ZHANG and C. Y. SUEN



    def thin_nodes(self, nodes):

        sys.stdout.write("\nThinning the nodes in the grid... ")
        sys.stdout.flush()
        # Matrix counting the number of neighbors a given position has
        check_nodes = set()
        
        # For each node check it's neighbors and decide weather they are to be deleted or not
        for key in nodes:
            coord = self.all_nodes[key]._center_of_mass()
            _neighbors = self.location_index.neighbors(coord, False)
            _num_neighbors = 0

            # Count     
            for k,v in _neighbors.items(): 
                if _neighbors[k] is not None and len(_neighbors[k].locations) > 0:
                    _num_neighbors += 1

            # First condition of the thinning algorithm
            if _num_neighbors >= 2 and _num_neighbors <= 6 and self.all_nodes[key].skeleton_value == 1:
                check_nodes.add(key)

        #Iterate over all the check_nodes
        while len(check_nodes) > 0:
            print len(check_nodes)
            s1_nodes = self.first_subiteration(check_nodes)
            s2_nodes = self.second_subiteration(check_nodes.union(s1_nodes))     
            check_nodes = s1_nodes.union(s2_nodes)

            print check_nodes
    
        sys.stdout.write("\nDone... ")
        sys.stdout.flush()
        


    # On this subiteration we remove the south-east boundary points and the north-west cornerpoints 
    def first_subiteration(self, fg_nodes):
        next_nodes = set() 
        zero_nodes = set() #nodes to be deleted from the skeleton

        for _node_id in fg_nodes:
            if self.all_nodes[_node_id].skeleton_value != 1: continue

            # get the center of mass of the node
            _location = self.all_nodes[_node_id]._center_of_mass()

            # query the index for its neighbors
            _neighbors = self.location_index.neighbors(_location, False)
            
            print "|" + str(_neighbors['nw'].skeleton_value) + "|" + str(_neighbors['n'].skeleton_value) + "|" + str(_neighbors['ne'].skeleton_value)
            print "|" + str(_neighbors['w'].skeleton_value )+ "|" + str(self.all_nodes[_node_id].skeleton_value) + "|" +str( _neighbors['e'].skeleton_value)
            print "|" + str(_neighbors['sw'].skeleton_value) + "|" + str(_neighbors['s'].skeleton_value) + "|" + str(_neighbors['se'].skeleton_value)
            print "-"*20
            # Count
            _num_neighbors = 0     
            for k,v in _neighbors.items(): 
                if _neighbors[k] is not None and len(_neighbors[k].locations) > 0:
                    _num_neighbors += 1
            # if these conditions are satisfied then the the node isn't part of the skeleton

            nes = _neighbors['n'].skeleton_value * _neighbors['e'].skeleton_value * _neighbors['s'].skeleton_value        
            esw = _neighbors['e'].skeleton_value * _neighbors['s'].skeleton_value * _neighbors['w'].skeleton_value
            # the number of non zero neighbors is beteween 2 and 6
            if (_num_neighbors >= 2 and _num_neighbors <= 6 and nes == 0 and esw == 0):
                # there is exactly one pair of 01 neighbors
                if self._zero_one_neighbors(_neighbors) == 1:
                    zero_nodes.add(_node_id)

                    for k in _neighbors.keys():
                        if _neighbors[k].skeleton_value == 1:
                            next_nodes.add(_neighbors[k].id)
        # set the skeleton_value to 0 if needed
        for _id in zero_nodes:
            self.all_nodes[_id].skeleton_value = 0
            print _id

        return next_nodes


    def second_subiteration(self,fg_nodes):
        next_nodes = set() 
        zero_nodes = set() #nodes to be deleted from the skeleton

        for _node_id in fg_nodes:
            if self.all_nodes[_node_id].skeleton_value != 1: continue
            # get the center of mass of the node
            _location = self.all_nodes[_node_id]._center_of_mass()
            # query the index for its neighbors
            _neighbors = self.location_index.neighbors(_location, False)
            
            # Count
            _num_neighbors = 0     
            for k,v in _neighbors.items(): 
                if _neighbors[k] is not None and len(_neighbors[k].locations) > 0:
                    _num_neighbors += 1

            # if these conditions are satisfied then the the node isn't part of the skeleton

            # the number of non zero neighbors is beteween 2 and 6
            _new = _neighbors['n'].skeleton_value * _neighbors['e'].skeleton_value * _neighbors['w'].skeleton_value
            nsw = _neighbors['n'].skeleton_value * _neighbors['s'].skeleton_value * _neighbors['w'].skeleton_value
            
            if _num_neighbors >= 2 and _num_neighbors <= 6 and _new == 0 and nsw == 0:     
                # there is exactly one pair of 01 neighbors
                if self._zero_one_neighbors(_neighbors) == 1:
                    zero_nodes.add(_node_id)
                    
                    for k in _neighbors.keys():
                        if _neighbors[k].skeleton_value == 1:
                            next_nodes.add(_neighbors[k].id)
        
        # set the skeleton_value to 0 if needed
        for _id in zero_nodes:
            self.all_nodes[_id].skeleton_value = 0
            print _id
        return next_nodes


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
            return len(node.locations)*kernel_value
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

    # Returns the number of 01 pairs
    def _zero_one_neighbors(self, _neighbors):
        _sum = 0

        if  _neighbors['n'].skeleton_value == 0 and _neighbors['ne'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['ne'].skeleton_value == 0 and _neighbors['e'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['e'].skeleton_value == 0 and _neighbors['se'].skeleton_value == 1:
            _sum += 1
        
        if  _neighbors['se'].skeleton_value == 0 and _neighbors['s'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['s'].skeleton_value == 0 and _neighbors['sw'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['sw'].skeleton_value == 0 and _neighbors['w'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['w'].skeleton_value == 0 and _neighbors['nw'].skeleton_value == 1:
            _sum += 1

        if  _neighbors['nw'].skeleton_value == 0 and _neighbors['n'].skeleton_value == 1:
            _sum += 1

        return _sum

    def _segments_to_kml(self, output = "segments_2.kml"):
        _file = open(output,"w")
        #Header
        _file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        _file.write( "<kml xmlns='http://www.opengis.net/kml/2.2'>\n")
        _file.write(  "<Document>\n")

        #Line Style)
        _file.write(  "<Style id='myStyle'>\n")
        _file.write(      "<LineStyle>\n")
        _file.write(        "<color>7f00ff00</color>\n")
        _file.write(        "<width>4</width>\n")
        _file.write(      "</LineStyle>\n")
        _file.write(      "<PolyStyle>\n")
        _file.write(        "<color>7f00ff00</color>\n")
        _file.write(      "</PolyStyle>\n")
        _file.write(  "</Style>\n")
       
               #Line Style)
        _file.write(  "<Style id='myStyle2'>\n")
        _file.write(      "<LineStyle>\n")
        _file.write(        "<color>ffff0000</color>\n")
        _file.write(        "<width>4</width>\n")
        _file.write(      "</LineStyle>\n")
        _file.write(      "<PolyStyle>\n")
        _file.write(        "<color>ff0000ff</color>\n")
        _file.write(      "</PolyStyle>\n")
        _file.write(  "</Style>\n")

        sys.stdout.write("\nWriting output to kml ... ")
        sys.stdout.flush()
        i = 0
        for key in self.all_nodes:
            
            if len(self.all_nodes[key].locations) > 0:
                _trajs = self.all_nodes[key].trajectories
                _neighbors = self.location_index.neighbors(self.all_nodes[key]._center_of_mass())
                for t in _trajs:
                    #Threshold
                    if _trajs[t] > 2:
                        _in = _neighbors[t[0]]
                        _out = _neighbors[t[1]]
                        _file.write( "<Placemark>\n")
                        _file.write( "<name>" + str(key) + "</name>\n")

                        _file.write( "<styleUrl>#myStyle2</styleUrl>\n")
                    # else:
                    #     _file.write( "<styleUrl>#myStyle</styleUrl>\n")
                        _file.write( "<LineString>\n")
                        _file.write(  "<altitudeMode>relative</altitudeMode>\n")
                        _file.write(  "<coordinates>\n")
                        _file.write(      str(_in._center_of_mass().longitude) + "," + str(_in._center_of_mass().latitude) + "\n")
                        _file.write(      str(self.all_nodes[key]._center_of_mass().longitude) + "," + str(self.all_nodes[key]._center_of_mass().latitude) + "\n")
                        _file.write(      str(_out._center_of_mass().longitude) + "," + str(_out._center_of_mass().latitude) + "\n")
                        _file.write(   "</coordinates>\n")
                        _file.write(  "</LineString>\n")
                        _file.write( "</Placemark>\n")
                        _file.write( "<weight>\n")
                        _file.write( str(t) + ":::" + str(_trajs[t]) + "\n")
                        _file.write( "</weight>\n")

        #Close tags
        _file.write(  "</Document>\n")       
        _file.write( "</kml>\n")
        _file.close()

        sys.stdout.write("\nDone ... ")
        sys.stdout.flush()


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

    # Stablish a certainty value
    def _certainty_value(self, _min, _max, node_id):
        _weight = self.all_nodes[node_id].blur_value
        _percent = (_weight/_max)

        if _weight < _min:
            return 0

        elif 0.8 < _percent <= 1:
            return 1
        
        elif 0.7 < _percent <= 0.8:
            return 0.8
        
        elif 0.6 < _percent <= 0.7:
            return 0.7
        
        elif 0.5 < _percent <= 0.6:
            return 0.6
        
        elif 0.4 < _percent <= 0.5:
            return 0.5
        
        elif 0.3 < _percent <= 0.4:
            return 0.4
        
        elif 0.2 < _percent <= 0.3:
            return 0.3
        
        elif 0.15 < _percent <= 0.2:
            return 0.2

        elif 0.10 < _percent <= 0.15:
            return 0.15

        elif 0.05 < _percent <= 0.10:
            return 0.01

        elif 0.05 < _percent <= 0.10:
            return 0.05

        elif 0.03 < _percent <= 0.05:
            return 0.03

        elif 0.02 < _percent <= 0.03:
            return 0.02

        elif 0.01 < _percent <= 0.02:
            return 0.01

    def previous_and_next(self, some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return izip(prevs, items, nexts)

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
    m._write_trips_to_file()
    m._write_nodes_to_file()
    # os.chdir("/home/moyano/Projects/CreateTracks/maps/")
    # m._segments_to_kml("kml_output.kml")
    
    print "\nMap inference completed (in " + str(time.time() - start_time) + " seconds).\n"