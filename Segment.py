from collections import namedtuple

class Segment(object):
    
    '''
    must receive an array of points which will have the values
    for latitude, longitude and a timestamp
    'geo_point', ['latitude', 'longitude','timestamp']
    '''
    def __init__(self, points):
        self.points = []
        Point = namedtuple('Point', 'latitude, longitude, timestamp')
        for point in points:
            p = Point(point.latitude, point.longitude, point.timestamp)
            self.points.append(p)
    