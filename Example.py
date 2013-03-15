from math import radians, sin, cos, asin, sqrt, pi, atan2
import numpy as np
import itertools

earth_radius_miles = 3956.0

def haversine(point1, point2):
    """Gives the distance between two points on earth.
    """
    lat1, lon1 = (radians(coord) for coord in point1)
    lat2, lon2 = (radians(coord) for coord in point2)
    dlat, dlon = (lat2 - lat1, lon2 - lon1)
    a = sin(dlat/2.0)**2 + cos(lat1) * cos(lat2) * sin(dlon/2.0)**2
    great_circle_distance = 2 * asin(min(1,sqrt(a)))
    d = earth_radius_miles * great_circle_distance
    return d

def dumb(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2
    d = abs((lat2 - lat1) + (lon2 - lon1))
    return d

def get_shortest_in(needle, haystack):
    """needle is a single (lat,long) tuple.
        haystack is a numpy array to find the point in
        that has the shortest distance to needle
    """
    dlat = np.radians(haystack[:,0]) - radians(needle[0])
    dlon = np.radians(haystack[:,1]) - radians(needle[1])
    a = np.square(np.sin(dlat/2.0)) + cos(radians(needle[0])) * np.cos(np.radians(haystack[:,0])) * np.square(np.sin(dlon/2.0))
    great_circle_distance = 2 * np.arcsin(np.minimum(np.sqrt(a), np.repeat(1, len(a))))
    d = earth_radius_miles * great_circle_distance
    return np.min(d)


x = (37.160316546736745, -78.75)
y = (39.095962936305476, -121.2890625)

def dohaversine():
    for i in xrange(100000):
        haversine(x,y)

def dodumb():
    for i in xrange(100000):
        dumb(x,y)

lots = np.array(list(itertools.repeat(y, 100000)))
def donumpy():
    get_shortest_in(x, lots)

from timeit import Timer
print 'haversine distance =', haversine(x,y), 'time =',
print Timer("dohaversine()", "from __main__ import dohaversine").timeit(100)
print 'dumb distance =', dumb(x,y), 'time =',
print Timer("dodumb()", "from __main__ import dodumb").timeit(100)
print 'numpy distance =', get_shortest_in(x, lots), 'time =',
print Timer("donumpy()", "from __main__ import donumpy").timeit(100)