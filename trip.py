#
# 
# This module is a modification of the location.py module:
# Location-related classes for simplification of GPS traces.
# by James P. Biagioni (jbiagi1@uic.edu), University of Illinois at Chicago
# Available at:
# http://www.cs.uic.edu/pub/Bits/Software/gis12_mapinference.tar.gz
#

from __future__ import division
from math import radians, cos, sin, atan2, degrees
from itertools import tee, islice, chain, izip
import os

class Location:
    def __init__(self, latitude, longitude, time):
        self._id = None
        self.latitude = latitude
        self.longitude = longitude
        self.time = time
        self.prev_location = None
        self.next_location = None
        self.trace_id = None

class Trip(object):
    
    def __init__(self):
        self.locations = []
    
    def add_location(self, bus_location):
        self.locations.append(bus_location)
    
    @property
    def num_locations(self):
        return len(self.locations)
    
    @property
    def start_time(self):
        return self.locations[0].time
    
    @property
    def end_time(self):
        return self.locations[-1].time
    
    @property
    def time_span(self):
        return (self.locations[-1].time - self.locations[0].time)


    def compare(self,other):
        self_len = len(self.locations)
        other_len = len(other.locations)
        #print self_len, other_len
        if self_len > other_len:
            temp_set = set(other.locations)
            intersection = temp_set.intersection(self.locations) 
            ratio =  len(intersection)/self_len
        else:
            temp_set = set(self.locations)
            intersection = temp_set.intersection(other.locations) 
            ratio =  len(intersection)/other_len
        
        return True if ratio > 0.7 else False
    
    
    def corners(self):
        segments = self.get_segments(self.locations)
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
    
    def get_segments(self, locations):
        segments = []
        segment = []
        for n in locations:
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

class TripLoader:
    
    @staticmethod
    def get_all_trips(trips_path):
        
        # storage for all trips
        all_trips = []
        
        # get trip filenames
        trip_filenames = os.listdir(trips_path)
        
        # iterate through all trip filenames
        for trip_filename in trip_filenames:
            
            # if filename starts with "trip_"
            if (trip_filename.startswith("trip_") is True):
                
                # load trip from file
                curr_trip = TripLoader.load_trip_from_file(trips_path + trip_filename)
                
                # add trip to all_trips list
                all_trips.append(curr_trip)
        
        # return all trips
        return all_trips
    
    @staticmethod
    def load_trip_from_file(trip_filename):
        
        # create new trip object
        new_trip = Trip()
        
        # create new trip locations dictionary
        new_trip_locations = {} # indexed by location id
        
        # open trip file
        trip_file = open(trip_filename, 'r')
        
        # read through trip file, a line at a time
        for trip_location in trip_file:
            
            # parse out location elements
            location_elements = trip_location.strip('\n').split(',')
            
            # create new location object
            new_location = Location(float(location_elements[1]), float(location_elements[2]), float(location_elements[3]))           
            
            # add new location to trip
            new_trip.add_location(new_location)
        
        # close trip file
        trip_file.close()
        
        # return new trip
        return new_trip

class TripParser:

    @staticmethod
    def json_to_object(trips):
        all_trips = []

        for trip in trips:
            new_trip = Trip()
            
            locations = trip['locations']

            for previous, location, next in TripParser.previous_and_next(locations):
            
                new_location = Location(location['latitude'], location['longitude'], location['time'])
                #add location to trip
                new_location._id = location['_id']

                if previous:
                    new_location.prev_location = previous['_id']

                if next:
                    new_location.next_location = next['_id']

                new_location.trace_id = trip['_id']
                
                new_trip.add_location(new_location)

            all_trips.append(new_trip)

        return all_trips

    @staticmethod
    def previous_and_next(some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return izip(prevs, items, nexts)
