import collections
import sys
import numpy as np
from math import radians, cos, sin, asin, sqrt,atan2,degrees,fmod,pi
from Tree import Tree as Tree
from collections import namedtuple
Point = namedtuple('Point', 'latitude, longitude')

class Trajectory:

    @staticmethod
    def is_part_of_segment(seg, point):
        last_point = seg[-1]
        previous_point = seg[-2]
        previous_heading =  initial_heading(previous_point.longitude, previous_point.latitude, last_point.longitude,last_point.latitude)
        new_heading = initial_heading(last_point.longitude, last_point.latitude, point.longitude, point.latitude)    
        if abs(previous_heading - new_heading) < 15:
            print "former dir: %f" % previous_heading
            print "new dir: %f" % new_heading
            print "delta: %f" % (previous_heading - new_heading)
            return True
        else:
            return False
    @staticmethod
    def initial_heading(lat1, lon1, lat2, lon2):
        dlon = radians(lon2-lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        y = sin(dlon)*cos(lat2)
        x = (cos(lat1)*sin(lat2))-(sin(lat1)*cos(lat2)*cos(dlon))
        #normalize
        heading =  (degrees((atan2(y,x)))+360)%360
        return heading
    @staticmethod
    def final_heading(lat1, lon1, lat2, lon2):
        heading = initial_heading(lon2,lat2,lon1,lat1)
        final_heading = (heading+180)%360
        print final_heading
   

    @staticmethod
    def velocity(lat1, lon1, lat2, lon2, t1, t2):
        """Given two locations and their unix timestamps
        returns the average speed in m/s"""
        d = Trajectory.distance(lat1, lon1, lat2, lon2)
        t = (t2 - t1)
        return d/t

    @staticmethod
    def distance(lat1, lon1, lat2, lon2):
        dlat= radians(lat2-lat1)
        dlon = radians(lon2-lon1)
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        a = (sin(dlat/2)**2) + (sin(dlon/2)**2*cos(lat1_rad)*cos(lat2_rad))
        c = 2*atan2(sqrt(a),sqrt(1-a))
        d = 6371*c #earth radius in km
        return d*1000 #convert to meters
    #
    # Returns the destination point given distance and bearing from a start point. Formula adapted from: http://www.movable-type.co.uk/scripts/latlong.html
    #
    @staticmethod
    def destination_point(a_lat, a_lon, bearing, distance):
        angular_distance = (distance/6371000.0) # meters
        bearing = radians(bearing)
        
        a_lat = radians(a_lat)
        a_lon = radians(a_lon)
        
        b_lat = asin(sin(a_lat) * cos(angular_distance) + cos(a_lat) * sin(angular_distance) * cos(bearing))
        b_lon = a_lon + atan2(sin(bearing) * sin(angular_distance) * cos(a_lat), cos(angular_distance) - sin(a_lat) * sin(b_lat))
        
        b_lon = fmod((b_lon + (3 * pi)), (2 * pi)) - pi
        
        return Point(degrees(b_lat), degrees(b_lon))  
    
    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        km = 6367 * c
        return km 

    @staticmethod
    def center_of_mass(locations):
        lat = np.mean([coord.latitude for coord in locations])
        lon = np.mean([coord.longitude for coord in locations]) 
        return Point(lat,lon)

    @staticmethod
    def direction(heading):
        """
        Maps a given angle to a number.
        """

        _dir = ''
        if (heading > 337.5 and heading < 360) or (heading >= 0 and heading <= 22.5):
            _dir = '1'

        elif heading > 22.5 and heading <= 67.5:
            _dir = '2'

        elif heading > 67.5 and heading <= 112.5:
            _dir = '4'

        elif heading > 112.5 and heading <= 157.5:
            _dir = '7'

        elif heading > 157.5 and heading <= 202.5:
            _dir = '6'

        elif heading > 202.5 and heading <= 247.5:
            _dir = '5' 

        elif heading > 247.5 and heading <= 292.5:
            _dir = '3'

        elif heading > 292.5 and heading <= 337.5:
            _dir = '0'

        if not _dir:
            print 'nope'
            print heading
            sys.exit(0)
        return _dir


    @staticmethod
    def bearing(_dir):
        """
        Maps a given angle to a number.
        """

        bearing = -1

        if _dir == '1':
            bearing = 0

        elif _dir == '2':
            bearing = 45

        elif _dir == '4':
            bearing = 90

        elif _dir == '7':
            bearing = 135

        elif _dir == '6':
            bearing = 180

        elif _dir == '5':
            bearing = 225 

        elif _dir == '3':
            bearing = 270

        elif _dir == '0':
            bearing = 315

        if  bearing == -1:
            print 'nope'
            print heading
            sys.exit(0)
        return bearing

    @staticmethod
    def reverse_direction(_dir):
        """
        0=>7, 1=>6, 
        map
        |---|---|---|  
        | 0 | 1 | 2 |
        |---|---|---|
        | 3 | x | 4 |
        |---|---|---|
        | 5 | 6 | 7 |
        |---|---|---|
        to:
        |---|---|---|  
        | 7 | 6 | 5 |
        |---|---|---|
        | 4 | x | 3 |
        |---|---|---|
        | 2 | 1 | 0 |
        |---|---|---|
        """
        rev = ''
        if _dir == '0':
            rev = '7'
        elif _dir == '1':
            rev = '6'
        elif _dir == '2':
            rev = '5'
        elif _dir == '3':
            rev = '4'
        elif _dir == '4':
            rev = '3'
        elif _dir == '5':
            rev = '2'
        elif _dir == '6':
            rev = '1'
        elif _dir == '7':
            rev = '0'

        return rev