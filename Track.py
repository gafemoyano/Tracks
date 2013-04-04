from Segment import Segment
from math import radians, cos, sin, atan2, degrees
class Track(object):
    """
    Representation of a Track. A track must be a collection
    of road segments close to each other
    """
    
    def __init__(self, points):
        self.segments = []
        for seg in self.get_segments(points):
            self.segments.append(Segment(seg))
    def compare(self,track):
        pass
    
    def add_segment(self,segment):
        pass
    
    
    def is_part_of_segment(self,seg, point):
        last_point = seg[-1]
        previous_point = seg[-2]
        previous_heading =  self.initial_heading(previous_point.longitude, previous_point.latitude, last_point.longitude,last_point.latitude)
        new_heading = self.initial_heading(last_point.longitude, last_point.latitude, point.longitude, point.latitude)    
        if abs(previous_heading - new_heading) < 15:
            return True
        else:
            return False
    
    def get_segments(self, points):
        segments = []
        _segment = []
        for point in points:
            if  len(_segment)<2:
                _segment.append(point)
            else:
                if self.is_part_of_segment(_segment,point):
                    _segment.append(point)
                else:
                    segments.append(_segment)
                    _segment = []
                    _segment.append(point)
                    
        segments.append(_segment)
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
    