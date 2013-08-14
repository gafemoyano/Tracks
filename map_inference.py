#
#	Map inference using a quadtree
#
#
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

client = MongoClient()
db = client.trip_db
trip_collection = db.trips
all_trips = TripParser.json_to_object(trip_collection.find().limit(1))
# globals
trip_max=len(all_trips)
location_list = list(location for trip in all_trips for location in trip.locations)
all_locations = dict([(loc._id, loc) for loc in location_list])

MAX_DEPTH = 8 #Max recursion inn the quadtree #Should change this to meters

class Edge:
    def __init__(self, id, in_node, out_node):
        self.id = id
        self.in_node = in_node
        self.out_node = out_node


class MapAlgo(object):

    def __init__(self, all_trips):
        self.all_trips = all_trips
        self.all_locations = all_locations
        self.trip_edges = self._find_all_trip_edges()
        self.bounding_box = self._bounding_box(self.all_locations)
        self.location_index = None    
        self.canonical_edges = {}
        self.pattern_edges = []
        self.all_nodes = {}
	
    #distribution
    # Control de flow of the algorithm
    #
    def run_algorithm(self):
        sys.stdout.write("\nRunning map inference algorithm ... ")
        sys.stdout.flush()
        self.location_index = self._build_dynamic_location_index() # Initialize and populate the quadtree
        #self.canonical_trips = self._find_canonical_trips() # Build Trips with qtree Nodes instead of Locations
        #self._apply_gaussian()
        #self._print_pattern_ocurrences()
        self.look_for_patterns() #identify directional patterns on each quadtree cell
        self.trim_patterns() #Remove patterns that aren't statistically significant
        self.get_road_segments()
    
    def _bounding_box(self, locations):
        """
        Given a list of GPS (latitude, longitude) locations values
        find the max and min value. 
        Return a rectangle element with those values plus an arbitrary delta
        """
        max_y = max(coord.latitude for coord in locations.itervalues())
        min_y = min(coord.latitude for coord in locations.itervalues())
        max_x  = max(coord.longitude for coord in locations.itervalues())
        min_x = min(coord.longitude for coord in locations.itervalues())
        rectangle = namedtuple('rectangle', ['x0', 'x1','y0', 'y1'])    
        box = rectangle(min_x -  0.005, max_x +  0.005 , min_y -  0.005, max_y +  0.005)
        return box
    #
    # Initializes the quadtree and adds all the trajectory information
    # 
    def _build_location_index(self):   
        sys.stdout.write("Generating QuadTree location index... ")
        sys.stdout.flush()
        location_index = QuadTree(self.bounding_box)
        # iterate through all trips

        for trip in self.all_trips:
            #Iterate through all locations
            current_cell = None
            #Loop for adding trajectory information
            for previous, location, next in self.previous_and_next(trip.locations):
                current_cell = location_index.insert(location)

                # First location 
                if previous is not None and next is not None:
                    #get the node where the next location would fall
                    self.update_trajectory(previous, location, next, current_cell)


        location_index.traverse() #Populate leaves[]

        _node_id = 0
        #Hash with all leaves
        for leave in location_index.leaves:
            location = leave._center_of_mass()
            leave.id = (location.latitude, location.longitude)
            self.all_nodes[(location.latitude, location.longitude)] = leave

        return location_index


    def _build_dynamic_location_index(self):
        """
        Initialize a quadtree index and insert
        all the stored locations 
        """   
        sys.stdout.write("Generating QuadTree location index...\n ")
        sys.stdout.flush()
        location_index = QuadTree(self.bounding_box)
        # iterate through all trips

        for trip in self.all_trips:
            #Iterate through all locations
            current_cell = None
            #Loop for adding trajectory information
            for location in trip.locations:
                current_cell = location_index.insert(location)

        location_index.traverse() #Populate leaves[]

        _node_id = 0
        #Store a reference to all the quadtree LEAF cells
        for cell in location_index.leaves:
            location = cell._center_of_mass()
            cell.id = (location.latitude, location.longitude)
            self.all_nodes[(location.latitude, location.longitude)] = cell
        
        sys.stdout.write("Done...\n ")
        sys.stdout.flush()
        
        return location_index



    def look_for_patterns(self):
        """
        Traverse all the LEAF cells on the tree and identify all
        the patterns
        """
        sys.stdout.write("Finding trace patterns...\n ")
        sys.stdout.flush()

        #Iterate every cell on the quadtree
        for k in self.all_nodes.keys():

            for location in self.all_nodes[k].locations:

                if location.prev_location and location.next_location:
                    previous = self.all_locations[location.prev_location]
                    next = self.all_locations[location.next_location]

                    self._identify_pattern(previous, location, next, self.all_nodes[k])

        sys.stdout.write("Done...\n ")
        sys.stdout.flush()


    def _identify_pattern(self, previous, current, next, cell):

        """
        Given three consecutive locations(from the same trace) identify a pair of numbers
        indicating the source_cell and the destination_cell relative the the following diagram
        where current would be 'x'.
        |---|---|---|  
        | 0 | 1 | 2 |
        |---|---|---|
        | 3 | x | 4 |
        |---|---|---|
        | 5 | 6 | 7 |
        |---|---|---|

        If a pattern is found then the current position is added to a list in the patterns dictionary
        """

        #get the total distance traveled
        total_distance = Trajectory.distance(previous.latitude, previous.longitude, current.latitude, current.longitude) + Trajectory.distance(next.latitude, next.longitude, current.latitude, current.longitude)
        in_speed = Trajectory.velocity(previous.latitude, previous.longitude, current.latitude, current.longitude, previous.time, current.time)
        out_speed = Trajectory.velocity(current.latitude, current.longitude, next.latitude, next.longitude, current.time, next.time)
        # If the distance traveled between the three points is moer than 15 mts
        if total_distance > 3 and in_speed < 30 and out_speed < 30:
            in_bearing = Trajectory.initial_heading(previous.latitude, previous.longitude, current.latitude, current.longitude)
            out_bearing = Trajectory.initial_heading(current.latitude, current.longitude, next.latitude, next.longitude)

            #Get a cardinal representation of the bearing
            in_direction = Trajectory.direction((in_bearing + 180) % 360) #reverse the bearing to get the incoming direction
            out_direction = Trajectory.direction(out_bearing)

            #Create a new key on the dictionary if the pattern hasn't been encountered before
            if  (in_direction, out_direction) not in cell.patterns:
                cell.patterns[in_direction,out_direction] = []

            cell.patterns[in_direction,out_direction].append(current)

                                


    def trim_patterns(self):
        """
        For each cell take a list of every pattern identified and it's number
        of ocurrances. 

        Select only those whose number of occurrence is relevant
        and store them on the significant_pattern dictionary of the respective cell
        """
        sys.stdout.write("Filtering non-relevant patterns...\n ")
        sys.stdout.flush()

        for k in self.all_nodes.keys():
            if len(self.all_nodes[k].patterns)>0:
                sig_patterns = self._get_significant_patterns(k)

                for _tuple in sig_patterns:
                    self.all_nodes[k].significant_patterns[_tuple[0]] = self.all_nodes[k].patterns[_tuple[0]]
                
        sys.stdout.write("Done...\n ")
        sys.stdout.flush()

   
    def _get_significant_patterns(self, key, critical_value = 0.51):
        
        """
        Given a certain cell run a T-test over all the patterns found and
        return only those that are statistically significant
        """     
        #Get all the patterns of the current cell and sorted by number of ocurrences


        temp_sort = sorted(self.all_nodes[key].patterns.iteritems(), key = lambda t: len(t[1]), reverse = True)
        sorted_patterns = []

        # Make a list of (key,value) tuples where the value is the the number of locations and the key is the pattern
        for t in temp_sort:
            sorted_patterns.append((t[0],len(t[1])))

        _current_group = []

        #If there's only one pattern then return it and skip the rest
        if len(sorted_patterns) == 1:
            _current_group =  sorted_patterns

        else:
            #Each tuple is in the form (Pattern, Number of Ocurrences)
            for _tuple in sorted_patterns:
                #If the list is empty the first pattern is added
                if not _current_group:
                    _current_group.append(_tuple)

                else:
                    #create a copy of the current list
                    test_group = list(_current_group)
                    # Add the next pattern
                    test_group.append(_tuple)
                    #Test if the new set is statistically diferent from
                    
                    #The list should be sorted on descending order.
                    #They are also turned into sets
                    l1 = sorted(list(set([x[1] for x in _current_group])), reverse = True)
                    l2 = sorted(list(set([x[1] for x in test_group])), reverse = True)
                    
                    #When two patterns in a row have the same number of ocurrences [8,7,5,4,4] => [8,7,5,4]
                    #the last value is removed. This makes sure that the same test
                    #is being run for each pattern with the same value.
                    if len(l1)>= 2 and l1[-1] == l2[-1]:
                        l1.pop()


                    (t, p_value) = st.ttest_ind(l1, l2, equal_var = False) 

                
                    if p_value >= critical_value:
                        break
                    else:
                        _current_group.append(_tuple)

            #Removing the last pattern added
            final_patterns = set([x[1] for x in _current_group])
            _significant_patterns =[]
            if len(final_patterns) > 1:
         
                # while _current_group[-1][1] == last_pattern:
                #     _current_group.pop()
                temp_list = sorted(list(set([x[1] for x in _current_group])), reverse = True)
                median = np.median(temp_list)

                for x in _current_group:
                    if x[1] > median:
                        _significant_patterns.append(x)
        
                if _significant_patterns:
                    _current_group = _significant_patterns

        return _current_group

    def get_road_segments(self):
        """
        Traverse all the cells and look for pattern similarities that would
        allow two cells to be linked thus creating a road segment.
        If a segment is found add it to an index.
        """

        for k in self.all_nodes.keys():

            if len(self.all_nodes[k].significant_patterns)>0:
                new_segments = self._pattern_intersection(k)

    def _pattern_intersection(self, key):
        """
        regarde la cellule voisine pointee par le pattern. Si l'intersection des 
        traces associees a ce pattern avec l'un des patterns de la cellule pointee, 
        alors on peut lier les 2 points d'equilibre (Center of Mass) des 2 patterns 
        pour obtenir un segment du chemin.
        """

        for pattern, locs in self.all_nodes[key].significant_patterns.iteritems():
            print "source"
            print list(self.all_nodes[key].significant_patterns.iterkeys())

            direction_out = pattern[1]

            dest_cell = self.location_index.neighbor_on_direction(self.all_nodes[key]._center_of_mass(),direction_out)
            print dest_cell._center_of_mass()
            print self.all_nodes[key]._center_of_mass()
            for l in locs:
                print l.latitude, l.longitude
            
            #Get the geographical midpoint of the locations assosiated with the current pattern in the target cell
            # target_locations = [self.all_locations[loc.next_location] for loc in locations]
            # target_midpoint = Trajectory.center_of_mass(target_locations)
            # print target_midpoint
            # #print locations
            # #Get the geographical midpoint of the locations assosiatedwith the current pattern in the current cell
            # current_midpoint = Trajectory.center_of_mass(locations)
           
            # #Find the cell where this average location would be located
            # destination_cell = self.location_index.containing_node(target_midpoint)
            # print destination_cell._center_of_mass()
            # print "dest"
            # print list(destination_cell.significant_patterns.iterkeys())

            # all_dest_in =  [dp[0] for dp in destination_cell.significant_patterns.iterkeys()]
            
            # if Trajectory.reverse_direction(source_out) in all_dest_in:
            #     self.pattern_edges.append((current_midpoint, target_midpoint))



    #----------------------------------------------------
    # Stuff I tried before adn I'm not currently using
    #----------------------------------------------------   


    #   Store all canonical trip edges in a RTree index    
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
        
        sys.stdout.write("\nDone. ")
        sys.stdout.flush()
        
        # return all trip edges
        return trip_edges


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

    #----------------------------------------------------
    # Image Processing Algorithms
    #----------------------------------------------------
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

    #-----------------------------------------
    # Text Output Algorithms
    #----------------------------------------

    def _print_pattern_ocurrences(self, output = 'ocurrences.txt'):
            #Create a hash with all the possible patterns that are stored in the quadtree
            sys.stdout.write("\nCounting the number of patters... ")
            sys.stdout.flush()
            ocurrences = {}

            for key in self.all_nodes:
                if len(self.all_nodes[key].locations) > 0:
                    _trajectories = self.all_nodes[key].trajectories 
                    for pattern in _trajectories:
                        if not pattern in ocurrences:
                            ocurrences[pattern] = 0
                        ocurrences[pattern] += _trajectories[pattern]

            sys.stdout.write("\nWriting " + output + "... ")
            sys.stdout.flush()
            os.chdir("/home/moyano/Projects/Tracks/graphics/")
            
            _file = open(output,"w")
            _file.write("Pattern: Ocurrences\n")
            
            sorted_ocurrences = sorted(ocurrences.iteritems(), key = lambda t: t[1])
            for pattern in sorted_ocurrences:
                _file.write(str(pattern[0]) + ": " + str(pattern[1]) + "\n")
            _file.close()

            _file = open('ocurrences_npatterns.csv',"w")
            _file.write("Ocurrences: Times: Patterns\n")

            for key, group in groupby(sorted_ocurrences, lambda x: x[1]):
                    patterns = []

                    for p in group:
                        patterns.append(p[0])

                    _file.write(str(key) + ': '+ str(len(patterns)) + ': ' +str(patterns))
                    _file.write("\n")
            _file.close()

            _file = open('ocr_pattrn.csv',"w")
            _file.write("Ocurrences: Patterns\n")
            _max_x = max(ocurrences[k] for k in ocurrences.keys())

            for x in range(0,_max_x):
                counter = 0
                for k in ocurrences.keys():
                    if ocurrences[k] <= x:
                        counter += 1

                _file.write(str(x) + ": " + str(counter)) 
                _file.write("\n")

            _file.close()

            _file = open('o_p_2.csv',"w")
            _file.write("Ocurrences: Patterns\n")

            for key, group in groupby(sorted_ocurrences, lambda x: x[1]):
                    counter = 0
                    for k in ocurrences.keys():
                        if ocurrences[k] <= key:
                            counter += 1

                    _file.write(str(key) + ': ' +str(counter))
                    _file.write("\n")
            _file.close()

    def _segments_to_kml(self, output = "default.kml", density = 2):
        os.chdir("/home/moyano/Projects/Tracks/kml/")

        sys.stdout.write("\nWriting output to kml ... ")
        sys.stdout.flush()

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


        for key in self.all_nodes:
            
            if len(self.all_nodes[key].locations) > 0:
                _trajs = self.all_nodes[key].patterns
                _ntrajs = self.all_nodes[key].significant_patterns
                _neighbors = self.location_index.neighbors(self.all_nodes[key]._center_of_mass())
                for t in _trajs:
                    #Threshold
                    if _trajs[t] > density:
                        #print _neighbors
                        _in = _neighbors[t[0]]
                        _out = _neighbors[t[1]]
                        _file.write( "<Placemark>\n")
                        _file.write( "<name>" + str(key) + "</name>\n")
                        if t == ('3','4') or t == ('6', '1'):
                            _file.write( "<styleUrl>#myStyle</styleUrl>\n")
                        else:
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
    

    def _edges_to_kml(self, output = "default.kml"):

        os.chdir("/home/moyano/Projects/Tracks/kml/")

        sys.stdout.write("\nWriting output to kml ... ")
        sys.stdout.flush()

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

        count = 0
        for edge in self.pattern_edges:
            count +=1
            _in = edge[0]
            _out = edge[1]

            _file.write( "<Placemark>\n")
            _file.write( "<name>" + str(count) + "</name>\n")
            _file.write( "<styleUrl>#myStyle</styleUrl>\n")
            _file.write( "<LineString>\n")
            _file.write(  "<altitudeMode>relative</altitudeMode>\n")
            _file.write(  "<coordinates>\n")
            _file.write(      str(_in.longitude) + "," + str(_in.latitude) + "\n")
            _file.write(      str(_out.longitude) + "," + str(_out.latitude) + "\n")
            _file.write(   "</coordinates>\n")
            _file.write(  "</LineString>\n")
            _file.write( "</Placemark>\n")

        #Close tags
        _file.write(  "</Document>\n")       
        _file.write( "</kml>\n")
        _file.close()

        sys.stdout.write("\nDone ... ")
        sys.stdout.flush()
    def _write_nodes_to_file(self):

        nodes = self.location_index.leaves

        os.chdir("/home/moyano/Projects/Tracks/edges")

        test_file = open("blurred.txt", "w")

        test_file.write("latitude, longitude, ocurrences")

        # print children

        for node in nodes:

            p = node._center_of_mass()

            count = len(node.locations)

            if count > 0:

                test_file.write("\n")  

                test_file.write(str(p.latitude) + "," + str(p.longitude) + "," + str(count))

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
    #-----------------------------------------
    # Misc and Helpers
    #----------------------------------------

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
    
    (opts, args) = getopt.getopt(sys.argv[1:],"n:f:h")
    
    for o,a in opts:
        print o,a
        if o == "-n":
            trip_max = int(a)
        if o == "-f":
            kml_output = a
        if o == "-h":
            print "Usage: python map_inference.py [-n <trip_max>] [-f <file_name>] [-h]\n"
            exit()
    
    start_time = time.time()
    m = MapAlgo(all_trips[:trip_max])
    m.run_algorithm()
    #m._segments_to_kml(kml_output)
    m._edges_to_kml(kml_output)
    m._write_nodes_to_file()
    # os.chdir("/home/moyano/Projects/CreateTracks/maps/")
    
    print "\nMap inference completed (in " + str(time.time() - start_time) + " seconds).\n"