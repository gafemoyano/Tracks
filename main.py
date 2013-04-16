from __future__ import division
from collections import namedtuple
from QuadTree import QuadTree
from itertools import tee, izip
import os
from rtree import index
from math import radians, cos, sin,atan2,degrees
from Track import Track
from Trip import Trip
from Segment import Segment
from _abcoll import Sequence
Point = namedtuple('Point', ['latitude', 'longitude','timestamp'])
'''
Returns an array of named tuples
in the form of geo_point[latitude,longitude,timestamp]
'''

def load_file(file_name):
    points = []
    if file_name.endswith(".txt") and not file_name.startswith("."):
        try:
            point_file = open(file_name)
            for line in point_file:
                data = line.split(",")
                points.append(Point(float(data[1]),float(data[2]),float(data[3])))
        except Exception:
            print "Error loading File: "
            print file_name
    return points


'''
TEMP Function
this function does not take into account the fact that
max boundries would be different according to the geographical
cuadrant given than coordinates and latitudes change sign
'''
def max_bounding_rect(coordinates):
    max_y = max(coord.latitude for coord in coordinates)
    min_y = min(coord.latitude for coord in coordinates)
    max_x = max(coord.longitude for coord in coordinates)
    min_x = min(coord.longitude for coord in coordinates)
    rectangle = namedtuple('rectangle', ['x0', 'x1','y0', 'y1'])    
    #x0 = [min_x,min_y]
    #x1 = [max_x,min_y]
    #y0 = [min_x, max_y]
    #y1 = [max_x,max_y]
    rec = rectangle(min_x, max_x, min_y, max_y)
    print "Max Grid Size: " 
    print rec
    return rec
               
def depth(rect, distance):
    
    max_lenght = abs (rect.x1 - rect.x0)
    max_height =  abs(rect.y1 - rect.y0)
    leaf_lenght = max_lenght
    leaf_height = max_height
    l_depth = 0
    h_depth = 0
    flag= False
    
    while not flag:
        if leaf_lenght/2 >= distance:
            leaf_lenght = leaf_lenght/2
            l_depth  += 1
        else:
            flag = True
            
        if leaf_height/2 >= distance:
            leaf_height = leaf_lenght/2
            h_depth  += 1
        else:
            flag =  True
        
    depth = min(l_depth, h_depth)
    return depth

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def extract_routes(tracks):
    candidates = []
    similar = []
    treshold = 25
    print "Total tracks %i:" % len(tracks)
    
    #Iterate though tracks for grouping them by similarity
    for t in tracks:
        #t.corners()
        #If #the track matches a group then it's added to it
        unique = True
        for group in similar:
            if group_similarity(t,group):
                unique = False
                break
        #If no group is similar to it, create a new one
        if unique:
            similar.append([t])
        
    print "Groups of similar tracks %i:" % len(similar)
    #Else the track must form a new group containing itself
    routes = []
    for group in similar:
        nodes = []
        for track in group:
            for n in track.nodes:
                nodes.append(n) 

        route = list(set(nodes))
        routes.append(route)

        if len(group)>treshold:
            print len(route)
            candidates.append(group)
        
    print "Possible Routes %i: and %i" % (len(candidates), len(routes))       
    
    cluster = []
    # for r1 in routes:
    #     for r2 in routes:
    #         # if merge_routes(r1,r2):
    #         #     pass
                
    os.chdir("/home/moyano/Projects/CreateTracks/Candidates")
    for i,c in enumerate(candidates):
        f = open("candidate"+str(i)+".txt", 'w')
        #print "candidate"+str(i)
        for track in c:
            #print track.name
            for node in track.nodes:
                p = node._center_of_mass()
                f.write(str(p.latitude) + "," + str(p.longitude))
                f.write('\n')
                
    return candidates

def routes(self, qtree):


#Adds a track to a given group if it's similar
#to more than 80% of it's current members
def group_similarity(track, track_group):
    count = 0

    for t in track_group:
        if track.compare(t):
            count += 1
            
    if count/len(track_group) >= 0.6:
        track_group.append(track)
        return True
    else:
        return False     

#Load all files and initilize Simple Tracks
os.chdir("/home/moyano/Projects/CreateTracks/trips/")
all_points = []
#tracks = []
for trip in os.listdir("."):
        trip_data = load_file(trip)
        all_points += trip_data
        #tracks.append(Track(trip_data))
        
print 100*("x")


#coords =load_file('all_trips.csv')
boundries = max_bounding_rect(all_points)
depth = depth(boundries, 0.00035)
print "Nesting Level: %i" % depth
qtree = QuadTree(5, boundries)

#print "there are %i tracks" % len(tracks)


#Make the QTree
for coord in all_points:
    l = qtree.add_point(coord)

#Canonical Trips
trips = []

for trip in os.listdir("."):
    if not trip.startswith('.'):
        gps_data = load_file(trip)
        trips.append(load_trip(gps_data))
        if not nodes:
            print trip
            break
        
        canonical_trips.append(Trip(nodes,trip))

def load_trip(gps_data):
    nodes = [] 
    
    for gps_point in gps_data:
        nodes.append(qtree.canonical_point(p))

    #tracks.append(Track(canonical_points))
extract_routes(canonical_trips)
#Write the output file
# os.chdir("/home/moyano/Projects/CreateTracks/")
# test_file = open("test.txt", "w")
# unique = set(leafs)
# for node in unique:
#     p = node._center_of_mass()
#     test_file.write(str(p.latitude) + "," + str(p.longitude))
#     test_file.write("\n")

    
'''
tree = index.Index()
tree.insert(0, (boundries.left,boundries.bottom, boundries.right,boundries.top))
segments = get_segments(coords)



index = 0
for segment in segments:
    s = Segment(segment)
    tree.insert(index,max_bounding_rect(segment), s)
    index +=1
    
print tree
print [n.object for n in tree.intersection(max_bounding_rect(coords), objects=True)]
'''