from rtree import index
import collections

class RtreePoints(object):
    
    
    def __init__(self,data):
        self.index = index.Index()
        self.points = self.load_file(data)
        
        
    def load_file(self, file_name):
        points = []
        point_file = open(file_name)
        geo_point = collections.namedtuple('geo_point', ['latitude', 'longitude','timestamp'])
        
        for line in point_file:
            data = line.split(",")
            points.append(geo_point(float(data[1]),float(data[2]),float(data[3])))
    
    def add_points(self, points):        
        _i = 0
        for point in points:
            coordinates = [point.latitude, point.longitude]
            self.index.add(_i, coordinates)
            _i += 1