from __future__ import division
from math import radians, cos, sin, atan2, degrees

import os
class Trip(object):
    
    def __init__(self, grid, name = None):
        self.nodes = []
        self.name = name
        for node in grid:
            if self.nodes:
                if self.nodes[-1] != node:
                    self.nodes.append(node)
            else:
                self.nodes.append(node)

    def compare(self,other):

        #Direction

        #Lenght
        
        #Similarity

        self_len = len(self.nodes)
        other_len = len(other.nodes)
        #print self_len, other_len
        if self_len > other_len:
            temp_set = set(other.nodes)
            intersection = temp_set.intersection(self.nodes) 
            ratio =  len(intersection)/self_len
        else:
            temp_set = set(self.nodes)
            intersection = temp_set.intersection(other.nodes) 
            ratio =  len(intersection)/other_len
        
        return True if ratio > 0.7 else False
    
    
    def corners(self):
        segments = self.get_segments(self.nodes)
        if len(segments)>2:
            corners = []
            #Add the first point
            corners.append(segments[0][0])
            for s in segments:
                #Add the last point in each segment
                corners.append(s[-1])
        print "#"*10                
        # print  [(corner.latitude, corner.longitude) for corner in corners]
        return corners

    def is_part_of_segment(self, seg, point):
        last_point = seg[-1]
        previous_point = seg[-2]
        previous_heading =  self.initial_heading(previous_point.longitude, previous_point.latitude, last_point.longitude,last_point.latitude)
        new_heading = self.initial_heading(last_point.longitude, last_point.latitude, point.longitude, point.latitude)    
        if abs(previous_heading - new_heading) < 70:
            return True
        else:
            return False
    
    def get_segments(self, nodes):
        segments = []
        segment = []
        for n in nodes:
            point = n._center_of_mass()
            if  len(segment)<2:
                segment.append(point)
            else:
                if self.is_part_of_segment(segment,point):
                    segment.append(point)
                else:
                    segments.append(segment)
                    segment = []
                    segment.append(point)
                    
        segments.append(segment)
        return segments

    def initial_heading(self,lon1, lat1, lon2, lat2):
        dlon = radians(lon2-lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        y = sin(dlon)*cos(lat2)
        x = (cos(lat1)*sin(lat2))-(sin(lat1)*cos(lat2)*cos(dlon))
        #normalize
        heading =  (degrees((atan2(y,x)))+360)%360
        return heading

    def __eq__(self,other):
        pass
        