from __future__ import division
import numpy as np
from collections import namedtuple
from itertools import permutations
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
    leaves = []


    def __init__(self, depth, bounding_rect, parent = None):
        """Creates a quad-tree.

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
            self.trajectories = trajectories
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
    
    #Adds a point to the root where it belongs and returns the geographical
    #center of the node as the most Representative Point

    """ #######################################
    CLASS METHODS
    ###################################### """ 

    def insert(self, coord):

        if(self.type == QuadTree.LEAF):
            self.locations.append(coord)       
            return self
        
        if self.nw._contains(coord.latitude, coord.longitude):           
            return self.nw.insert(coord)
            
        if self.ne._contains(coord.latitude, coord.longitude):
            return self.ne.insert(coord)
            
        if self.sw._contains(coord.latitude, coord.longitude):
            return self.sw.insert(coord)
            
        if self.se._contains(coord.latitude, coord.longitude):
            return self.se.insert(coord)
            

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
    """
    |---|---|---|
    |nw | n |ne |
    |---|---|---|
    | w | x | e |
    |---|---|---|
    |sw | s |se |
    |---|---|---|
    """
    def neighbors(self, coord, include_self=False):
        if self.type == QuadTree.ROOT:
            node = self.containing_node(coord)
            if include_self:
                neighbors = {'nw': None, 'n': None, 'ne': None, 'w': None, 'x': None, 'e': None,'sw': None, 's': None, 'se': None }
            else:
                neighbors = {'nw': None, 'n': None, 'ne': None, 'w': None, 'e': None,'sw': None, 's': None, 'se': None }
            #find the lenght of the node's boinding box
            delta_x = node.x1 - node.x0
            delta_y = node.y1 - node.y0
            cm = node._center_of_mass
            
            # Find w and e
            lons = {'w': node.cx - delta_x, 'e': node.cx + delta_x}
            
            for location, tlon in lons.iteritems():
                if tlon >= self.x0 and tlon <= self.x1:
                    p = Point(node.cy, tlon)
                    neighbors[location] = self.containing_node(p)

            # Find nw, n and ne
            tlat = node.cy + delta_y
            if not tlat > self.y1:
                lons = {'nw': node.cx - delta_x,'n': node.cx, 'ne': node.cx + delta_x}
                
                for location, tlon in lons.iteritems():
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors[location] = self.containing_node(p)

            # Find sw, s and se
            tlat = node.cy - delta_y
            if tlat >= self.y0:
                lons = {'sw': node.cx - delta_x,'s': node.cx, 'se': node.cx + delta_x}
                
                for location, tlon in lons.iteritems():
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors[location] = self.containing_node(p)

            if include_self:
                neighbors['x'] = node

            return neighbors

    def cleanse(self):
        pass
    
    def traverse(self, count = 0):
        if(self.type == QuadTree.LEAF):

            if self.locations:
                self.leaves.append(self)

        else:
            self.nw.traverse()
            self.ne.traverse()
            self.sw.traverse()
            self.se.traverse()
        

    """ #######################################
    INSTANCE METHODS
    ###################################### """     

    def _neighbors(self, include_self=False):
        root = self._get_root()
        neighbors = {}
        neighbors = root.neighbors(self._center_of_mass())
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
            lat = np.mean([coord.latitude for coord in self.locations])
            lon = np.mean([coord.longitude for coord in self.locations])     
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


