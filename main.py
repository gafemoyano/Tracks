from collections import namedtuple
from QuadTree import QuadTree
import os
from rtree import index
from math import radians, cos, sin,atan2,degrees
from Track import Track
Point = namedtuple('Point', ['latitude', 'longitude','timestamp'])
'''
Returns an array of named tuples
in the form of geo_point[latitude,longitude,timestamp]
'''

def load_file(file_name):
    points = []
    if file_name.endswith(".txt"):
        point_file = open(file_name)
        print file_name
        for line in point_file:
            data = line.split(",")
            points.append(Point(float(data[1]),float(data[2]),float(data[3])))
    
    return points

def initial_heading(lon1, lat1, lon2, lat2):
    dlon = radians(lon2-lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    y = sin(dlon)*cos(lat2)
    x = (cos(lat1)*sin(lat2))-(sin(lat1)*cos(lat2)*cos(dlon))
    #normalize
    heading =  (degrees((atan2(y,x)))+360)%360
    return heading

def is_part_of_segment(seg, point):
    last_point = seg[-1]
    previous_point = seg[-2]
    previous_heading =  initial_heading(previous_point.longitude, previous_point.latitude, last_point.longitude,last_point.latitude)
    new_heading = initial_heading(last_point.longitude, last_point.latitude, point.longitude, point.latitude)    
    if abs(previous_heading - new_heading) < 15:
        return True
    else:
        return False
    
def get_segments(points):
    segments = []
    segment = []
    for point in points:
        if  len(segment)<2:
            segment.append(point)
        else:
            if is_part_of_segment(segment,point):
                segment.append(point)
            else:
                segments.append(segment)
                segment = []
                segment.append(point)
                
    segments.append(segment)
    return segments

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

os.chdir("/home/moyano/Projects/CreateTracks/trips/")
all_points = []
tracks = []
for trip in os.listdir("."):
        trip_data = load_file(trip)
        all_points += trip_data
        tracks.append(Track(trip_data))
        
print 100*("Z")
print all_points


#coords =load_file('all_trips.csv')
boundries = max_bounding_rect(all_points)
depth = depth(boundries, 0.00035)
print "Nesting Level: %i" % depth
qtree = QuadTree(depth, boundries)


#Make the QTree
leafs = []
l2 = []
for coord in all_points:
    l = qtree.add_point(coord)
    leafs.append(l)

#Write the output file
test_file = open("test.txt", "w")

print 100*("x")


for leaf in set(leafs):
    point = leaf.geographic_midpoint()
    test_file.write(str(point[0]) + "," + str(point[1]))
    test_file.write("\n")
    
    
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