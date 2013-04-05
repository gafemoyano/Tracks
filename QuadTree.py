from __future__ import division
import numpy as np
from collections import namedtuple
from math import radians, cos, sin, asin, sqrt,atan2,degrees
Point = namedtuple('Point', 'latitude, longitude')
class QuadTree(object):

    """An implementation of a quad-tree.
        Inserts geographical points at the leaves
    """
    LEAF = 1
    NODE = 0
    def __init__(self, depth, bounding_rect):
        """Creates a quad-tree.
 
        @param items:
            A sequence of items to store in the quad-tree. Note that these
            items must possess left, top, right and bottom attributes.
            
        @param depth:
            The maximum recursion depth.
            
        @param bounding_rect:
            The bounding rectangle of all of the items in the quad-tree. For
            internal use only.
        """
        # The sub-quadrants are empty to start with.
        
        #Rect center
        self.type = QuadTree.NODE
        self.x0, self.x1, self.y0, self.y1 = bounding_rect
        cx = self.cx = (self.x0 + self.x1) * 0.5
        cy = self.cy = (self.y0 + self.y1) * 0.5
        
                #Stop recursion at maximum depth
        depth -= 1
        if depth == 0:
            self.type = QuadTree.LEAF
            self.items = []
            return
        
        #Initialize children recursively       
        self.nw = QuadTree(depth, (self.x0, cx, cy, self.y1))
        self.ne = QuadTree(depth, (cx, self.x1, cy, self.y1))
        self.se = QuadTree(depth, (cx, self.x1, self.y0, cy))
        self.sw = QuadTree(depth, (self.x0, cx, self.y0, cy))
    
    #Adds a point to the root where it belongs and returns the geographical
    #center of the node as the most Representative Point
    def add_point(self, coord):

        if(self.type == QuadTree.LEAF):
            self.items.append(coord)        
            return self
        
        if self.nw.contains(coord.latitude, coord.longitude):           
            return self.nw.add_point(coord)
            
        if self.ne.contains(coord.latitude, coord.longitude):
            return self.ne.add_point(coord)
            
        if self.sw.contains(coord.latitude, coord.longitude):
            return self.sw.add_point(coord)
            
        if self.se.contains(coord.latitude, coord.longitude):
            return self.se.add_point(coord)
            
    #Returns true if a given lat,lon point lies within the boundries
    #of the node
    def contains(self, lat, lon):
        if lat >= self.y0 and lat <= self.y1 and lon >= self.x0 and lon <= self.x1:
            return True
        return False
        
    
    #Returns the aritmetic average of all the coordinates stored in the node
    #Format (longitude, latitude)
    def center_of_mass(self):
        if self.type != QuadTree.LEAF:
            return None
        else:
            lat = np.mean([coord.latitude for coord in self.items])
            lon = np.mean([coord.longitude for coord in self.items])     
            return Point(lat,lon)
            
    #Returnsthe geographical center of all the items in the node
    #Returns a Point topule [latitude,longitude]
    def geographic_midpoint(self):
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
    #Returns the center of mass of the leaf where the point would be placed
    #in the tree. Returns the original timestamp of the coordiante
    def canonical_point(self, coord):
        if(self.type == QuadTree.LEAF):
            return self.center_of_mass() 
        
        if self.nw.contains(coord.latitude, coord.longitude):           
            return self.nw.canonical_point(coord)
            
        if self.ne.contains(coord.latitude, coord.longitude):
            return self.ne.canonical_point(coord)
            
        if self.sw.contains(coord.latitude, coord.longitude):
            return self.sw.canonical_point(coord)
            
        if self.se.contains(coord.latitude, coord.longitude):
            return self.se.canonical_point(coord)
    
    def print_grid(self):
        grid = set()
        if self.type == QuadTree.LEAF:
            if self.items:
                print self.center_of_mass()
                grid |= set(self.center_of_mass())

        else:
            grid |=(self.nw.print_grid())
            grid |= (self.ne.print_grid())
            grid |= (self.sw.print_grid())
            grid |= (self.se.print_grid())
        
        return grid
                