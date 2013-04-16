from __future__ import division
import numpy as np
from collections import namedtuple
from math import radians, cos, sin, asin, sqrt,atan2,degrees
Point = namedtuple('Point', 'latitude, longitude')
class QuadTree(object):

    """An implementation of a quad-tree.
        Inserts geographical points at the leaves
    """
    LEAF = 2
    BRANCH = 1
    ROOT = 0

    def __init__(self, depth, bounding_rect, parent = None):
        """Creates a quad-tree.

        @param depth:
            The maximum recursion depth.
            
        @param bounding_rect:
            The bounding rectangle of all of the items in the quad-tree. For
            internal use only.
        """
        #Set box attributes       
        self.x0, self.x1, self.y0, self.y1 = bounding_rect        
        cx = self.cx = (self.x0 + self.x1) * 0.5
        cy = self.cy = (self.y0 + self.y1) * 0.5
        
        #Stop recursion at maximum depth
        depth -= 1
        if depth == 0:
            self.type = QuadTree.LEAF
            self.items = []
            self.parent = parent
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

    def add_point(self, coord):

        if(self.type == QuadTree.LEAF):
            self.items.append(coord)        
            return self
        
        if self.nw._contains(coord.latitude, coord.longitude):           
            return self.nw.add_point(coord)
            
        if self.ne._contains(coord.latitude, coord.longitude):
            return self.ne.add_point(coord)
            
        if self.sw._contains(coord.latitude, coord.longitude):
            return self.sw.add_point(coord)
            
        if self.se._contains(coord.latitude, coord.longitude):
            return self.se.add_point(coord)
            

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
                if len(node.items) > max_items: 
                    max_items = len(node.items)
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
    def neighbors(self, coord, include_self=True):
        if self.type == QuadTree.ROOT:
            node = self.containing_node(coord)
            #neighbors = {'nw': None, 'n': None, 'ne': None, 'w': None, 'x': None, 'e': None,'sw': None, 's': None, 'se': None }
            neighbors =[]
            #find the lenght of the node's boinding box
            delta_x = node.x1 - node.x0
            delta_y = node.y1 - node.y0
            cm = node._center_of_mass

            # Find w and e
            for tlon in (node.cx - delta_x, node.cx + delta_x):
                if tlon >= self.x0 and tlon <= self.x1:
                    p = Point(node.cy, tlon)
                    neighbors.append(self.containing_node(p))

            # Find nw, n and ne
            tlat = node.cy + delta_y
            if not tlat > self.y1:

                for tlon in (node.cx - delta_x, node.cx, node.cx + delta_x):
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors.append(self.containing_node(p))
            # Find sw, s and se
            tlat = node.cy - delta_y
            if tlat >= self.y0:

                for tlon in (node.cx - delta_x, node.cx, node.cx + delta_x):
                    if tlon >= self.x0 and tlon <= self.x1:
                        p = Point(tlat,tlon)
                        neighbors.append(self.containing_node(p))

            if include_self:
                neighbors.append(node)

            return neighbors
    
    """ #######################################
    INSTANCE METHODS
    ###################################### """     

    def _neighbors(self, include_self):
        root = self._get_root()
        neighbors = []
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
            lat = np.mean([coord.latitude for coord in self.items])
            lon = np.mean([coord.longitude for coord in self.items])     
            return Point(lat,lon)
            
    #Returnsthe geographical center of all the items in the node
    #Returns a Point topule [latitude,longitude]
    def _geographic_midpoint(self):
        #List with all the points transformed to [[lat,lon],[lat,lon]....]
        
        rad_points = [Point(radians(coord.latitude),radians(coord.longitude)) for coord in self.items]   
        
        #Converting to cartesian coordinates
        x_coords = [cos(coord.latitude)*cos(coord.longitude) for coord in rad_points]
        y_coords = [cos(coord.latitude)*sin(coord.longitude) for coord in rad_points]
        z_coords = [sin(coord.latitude) for coord in rad_points]
      
        #Since the locations are to be weighted equally
        total_weight = len(self.items)
        
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