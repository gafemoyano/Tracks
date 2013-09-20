from __future__ import division
import numpy as np
from collections import namedtuple
from itertools import permutations
from trajectory import Trajectory
from math import radians, cos, sin, asin, sqrt,atan2,degrees
Point = namedtuple('Point', 'latitude, longitude')
directions = ["n","e","w","s","ne","nw","se","sw"]
t_list = list(permutations(directions,2))
trajectories = {}
for _dir in t_list:
    trajectories[_dir] = 0

class QuadTree(object):

    """An implementation of a quad-tree.
        Inserts Locations at the leaves
    """
    LEAF = 2
    BRANCH = 1
    ROOT = 0
    MAX_LOCATIONS = 1
    MIN_CELL_SIZE = 30 #meters height
    DYNAMIC = False
    DELTA = 0.0000000000001
    leaves = []


    def __init__(self, depth, bounding_rect, parent = None):
        """Creates a quadtree with a fixed
            recursion depth

        @param depth:
            The maximum recursion depth.
            
        @param bounding_rect:
            The bounding rectangle of all of the locations in the quad-tree. For
            internal use only.
        """
        #Set box attributes       
        self.x0, self.x1, self.y0, self.y1 = bounding_rect        
        cx = self.cx = (self.x0 + self.x1) * 0.5
        cy = self.cy = (self.y0 + self.y1) * 0.5
        
        #Stop recursion at maximum depth
        depth -= 1
        if depth == 0:
            self.type = QuadTree.LEAF       #Type constant
            self.locations = []     #Holds all the locations inserted on the index
            self.parent = parent    #reference to the parent node
            self.blur_value = 0     #holds the gaussian blur value
            self.id = -1        #node id
            self.skeleton_value = 0   #Indicates if the node is part of the skeleton, is set to true when a location is added
            self.significant_patterns = {}
            self.patterns = {}
            return
        elif parent is None:
            self.type = QuadTree.ROOT
        else:
            self.type = QuadTree.BRANCH
            self.parent = parent
        
        #Initialize children recursively
        
        self.nw = QuadTree(depth, (self.x0, cx, cy, self.y1), self)
        self.ne = QuadTree(depth, (cx, self.x1, cy, self.y1), self)
        self.se = QuadTree(depth, (cx, self.x1, self.y0, cy), self)
        self.sw = QuadTree(depth, (self.x0, cx, self.y0, cy), self)
    

    def __init__(self, bounding_rect, parent = None):
        """Initializes a location index. New  cells are
        created when a max number of locations per cell is reached.

        @param bounding_rect:
            The bounding rectangle of all of the locations in the quad-tree. For
            internal use only.
        """
        QuadTree.DYNAMIC = True
        #Set box attributes       
        self.x0, self.x1, self.y0, self.y1 = bounding_rect        
        cx = self.cx = (self.x0 + self.x1) * 0.5
        cy = self.cy = (self.y0 + self.y1) * 0.5

        #Initialize the Root
        if parent is None:
            self.type = QuadTree.ROOT
            self.nw = QuadTree((self.x0, cx, cy, self.y1), self)
            self.ne = QuadTree((cx, self.x1, cy, self.y1), self)
            self.se = QuadTree((cx, self.x1, self.y0, cy), self)
            self.sw = QuadTree((self.x0, cx, self.y0, cy), self)
        else:
            self.type = QuadTree.LEAF       #Type constant
            self.locations = []     #Holds all the locations inserted on the index
            self.parent = parent    #reference to the parent node
            self.blur_value = 0     #holds the gaussian blur value
            self.id = -1        #node id
            self.skeleton_value = 0   #Indicates if the node is part of the skeleton, is set to true when a location is added
            self.significant_patterns = {}
            self.patterns = {}

    #Adds a point to the root where it belongs and returns the geographical
    #center of the node as the most Representative Point

    """ #######################################
    CLASS METHODS
    ###################################### """ 

    def insert(self, coord):

        if(self.type == QuadTree.LEAF):
            self.locations.append(coord)
            cell_size = Trajectory.distance(self.y0, self.x0, self.y1, self.x1)/2
            #Conditions that must be met in order to subdivde the current cell
            if QuadTree.DYNAMIC and len(self.locations) > QuadTree.MAX_LOCATIONS and cell_size >= QuadTree.MIN_CELL_SIZE:
                self.subdivide()
                
            return self
        
        if self.nw._contains(coord.latitude, coord.longitude):           
            return self.nw.insert(coord)
            
        if self.ne._contains(coord.latitude, coord.longitude):
            return self.ne.insert(coord)
            
        if self.sw._contains(coord.latitude, coord.longitude):
            return self.sw.insert(coord)
            
        if self.se._contains(coord.latitude, coord.longitude):
            return self.se.insert(coord)
            


    def subdivide(self):
        """
        Divides the current cell and inserts all the locations
        into the respective children
        """

        self.type = QuadTree.BRANCH

        #Unset the leaf attributes (Should probably handle this better)

        self.blur_value = None
        self.id = None
        self.skeleton_value = None
        self.significant_patterns = None
        self.patterns = None

        cx = self.cx = (self.x0 + self.x1) * 0.5
        cy = self.cy = (self.y0 + self.y1) * 0.5
        #Creating the children
        self.nw = QuadTree((self.x0, cx, cy, self.y1), self)
        self.ne = QuadTree((cx, self.x1, cy, self.y1), self)
        self.se = QuadTree((cx, self.x1, self.y0, cy), self)
        self.sw = QuadTree((self.x0, cx, self.y0, cy), self)

        #Insert the locations into the new cells
        for coord in self.locations:

            if self.nw._contains(coord.latitude, coord.longitude):           
                self.nw.locations.append(coord)
                
            if self.ne._contains(coord.latitude, coord.longitude):
                self.ne.locations.append(coord)
                
            if self.sw._contains(coord.latitude, coord.longitude):
                self.sw.locations.append(coord)
                
            if self.se._contains(coord.latitude, coord.longitude):
                self.se.locations.append(coord)



    #Returns the center of mass of the leaf where the point would be placed
    #in the tree. Returns the original timestamp of the coordiante
    def canonical_point(self, coord):
        if(self.type == QuadTree.LEAF):
            neighbors = self._neighbors(coord)
            # print neighbors
            significant_node = None
            max_items = 0
            #The node with the highest number of poitns is the most significant
            for node in neighbors:
                if len(node.locations) > max_items: 
                    max_items = len(node.locations)
                    significant_node = node 
            
            return significant_node
        
        if self.nw._contains(coord.latitude, coord.longitude):           
            return self.nw.canonical_point(coord)
            
        if self.ne._contains(coord.latitude, coord.longitude):
            return self.ne.canonical_point(coord)
            
        if self.sw._contains(coord.latitude, coord.longitude):
            return self.sw.canonical_point(coord)
            
        if self.se._contains(coord.latitude, coord.longitude):
            return self.se.canonical_point(coord)
        

    def containing_node(self, coord):
        if(self.type == QuadTree.LEAF):
            return self 
        
        if self.nw._contains(coord.latitude, coord.longitude):           
            return self.nw.containing_node(coord)
            
        if self.ne._contains(coord.latitude, coord.longitude):
            return self.ne.containing_node(coord)
            
        if self.sw._contains(coord.latitude, coord.longitude):
            return self.sw.containing_node(coord)
            
        if self.se._contains(coord.latitude, coord.longitude):
            return self.se.containing_node(coord)
    
    # I'm not sure this works if the point is exactly at one of the
    # borders
    # Returns a list with the neighboring nodes and itself at the end

    def neighbors(self, coord, include_self=False):
        """
        Finds the neighbors of the cell 'x'
        Returns a hash where the value is a reference to a neighbor cell and the key is the number
        representing the relative position to 'x' according to the diagram.
        |---|---|---|
        | 0 | 1 | 2 |
        |---|---|---|
        | 3 | x | 4 |
        |---|---|---|
        | 5 | 6 | 7 |
        |---|---|---|
        """
        if self.type == QuadTree.ROOT:
            node = self.containing_node(coord)
            if include_self:
                neighbors = {'0': None, '1': None, '2': None, '3': None, '4': None, '5': None,'6': None, '7': None, 'x': None }
            else:
                neighbors = {'0': None, '1': None, '2': None, '3': None, '4': None,'5': None, '6': None, '7': None }
            #find the lenght of the node's bounding box
            delta_x = node.x1 - node.x0
            delta_y = node.y1 - node.y0
            cm = node._center_of_mass
            
            # Shift the position on the x axis by a given delta. This will give a new
            # location guaranteed to fall on the cell to the right (4) and to the left (3)
            # Then query the quadtree for those cells
            lons = {'3': node.cx - delta_x, '4': node.cx + delta_x}
            
            for location, tlon in lons.iteritems():
                if tlon >= self.x0 and tlon <= self.x1:
                    p = Point(node.cy, tlon)
                    neighbors[location] = self.containing_node(p)

            # Shift the position on the y axis by adding a delta.
            # Repeat the previous step to find the upper neigbhors (1,2,3)
            tlat = node.cy + delta_y
            if not tlat > self.y1:
                lons = {'0': node.cx - delta_x,'1': node.cx, '2': node.cx + delta_x}
                
                for location, tlon in lons.iteritems():
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors[location] = self.containing_node(p)

            # Shift the position on the y axis by substracting a delta.
            # Find the bottom neigbhors (5,6,7)
            tlat = node.cy - delta_y
            if tlat >= self.y0:
                lons = {'5': node.cx - delta_x,'6': node.cx, '7': node.cx + delta_x}
                
                for location, tlon in lons.iteritems():
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors[location] = self.containing_node(p)

            if include_self:
                neighbors['x'] = node

            return neighbors

    def neighbor_on_direction(self, coord, _dir):

        if self.type == QuadTree.ROOT:
            node = self.containing_node(coord)

            delta_x = (node.x1 - node.x0)/2  +QuadTree.DELTA
            delta_y = (node.y1 - node.y0)/2 + QuadTree.DELTA
            
            distance = Trajectory.distance(node.cy, node.cx, node.cy + delta_y, node.cx + delta_x)
            cm = node._center()
            bearing = Trajectory.bearing(_dir)
            dest_point = Trajectory.destination_point(cm.latitude, cm.longitude, bearing, distance) 
            return self.containing_node(dest_point)
    
    def neighbor_on_direction_from_cm(self, coord, _dir):
        """
        Parting from the center of mass
        """
        if self.type == QuadTree.ROOT:
            node = self.containing_node(coord)
            com = self._center_of_mass()
            delta_x = (node.x1 - node.x0)/2  +QuadTree.DELTA
            delta_y = (node.y1 - node.y0)/2 + QuadTree.DELTA
            
            distance = Trajectory.distance(node.cy, node.cx, node.cy + delta_y, node.cx + delta_x)
            cm = node._center()
            bearing = Trajectory.bearing(_dir)
            dest_point = Trajectory.destination_point(cm.latitude, cm.longitude, bearing, distance) 
            return self.containing_node(dest_point)
            
    def traverse(self, count = 0):
        if(self.type == QuadTree.LEAF):

            if self.locations:
                self.leaves.append(self)

        else:
            self.nw.traverse()
            self.ne.traverse()
            self.sw.traverse()
            self.se.traverse()

    def patterns_by_in_direction(self, direction):
        "Returns the key of the patterns that have the given direction as in ekey"        
        _patterns = []

        for p in self.significant_patterns.iterkeys():
            if p[0] is direction:
                _patterns.append(p)

        return _patterns
        
    def out_patterns_by_out_direction(self, direction):
        "Returns the key of the patterns that have the given direction as in key"        
        _patterns = []
        
        for p in self.significant_patterns.iterkeys():
            if p[1] == direction:
                _patterns.append(p)

        return _patterns

    """ #######################################
     METHODS
    ###################################### """     

    def _neighbors(self, include_self=False):
        root = self._get_root()
        neighbors = {}
        neighbors = root.neighbors(self._center_of_mass(), include_self)
        return neighbors

    def _get_root(self):
        if self.type == QuadTree.ROOT:
            return self
        else:
            return self.parent._get_root()

                #Returns true if a given lat,lon point lies within the boundries
    #of the node
    def _contains(self, lat, lon):
        if lat >= self.y0 and lat <= self.y1 and lon >= self.x0 and lon <= self.x1:
            return True
        return False
        
    
    #Returns the aritmetic average of all the coordinates stored in the node
    #Format (longitude, latitude)
    def _center_of_mass(self):
        if self.type != QuadTree.LEAF:
            return None
        else:
            if self.locations:
                lat = np.mean([coord.latitude for coord in self.locations])
                lon = np.mean([coord.longitude for coord in self.locations])     
            else:
                lat = (self.y0 + self.y1)/2
                lon = (self.x0 + self.x1)/2
                print "warning"*20
            return Point(lat,lon)
    
    def _center(self):
        lat = (self.y0 + self.y1)/2
        lon = (self.x0 + self.x1)/2
        return Point(lat,lon)
    #Returnsthe geographical center of all the locations in the node
    #Returns a Point topule [latitude,longitude]
    def _geographic_midpoint(self):
        #List with all the points transformed to [[lat,lon],[lat,lon]....]
        
        rad_points = [Point(radians(coord.latitude),radians(coord.longitude)) for coord in self.locations]   
        
        #Converting to cartesian coordinates
        x_coords = [cos(coord.latitude)*cos(coord.longitude) for coord in rad_points]
        y_coords = [cos(coord.latitude)*sin(coord.longitude) for coord in rad_points]
        z_coords = [sin(coord.latitude) for coord in rad_points]
      
        #Since the locations are to be weighted equally
        total_weight = len(self.locations)
        
        #Calculate the average
        x = sum(x_coords)/total_weight
        y = sum(y_coords)/total_weight
        z = sum(z_coords)/total_weight
        
        # Transform to lat, lon values and convert to degrees
        lon = degrees(atan2(y, x)) 
        hyp = sqrt(x**2 + y**2)
        lat = degrees(atan2(z, hyp)) 
        
        #return a point
        return Point(lat,lon)


