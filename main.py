from __future__ import division
import os
import sys
import heatmap
from quadtree import QuadTree
from itertools import tee, izip
from rtree import index
from trip import TripLoader
from Segment import Segment

all_trips = TripLoader.get_all_trips("trips/")
trip_max=len(all_trips)

def main():
        #Load all files and initilize Simple Tracks
    os.chdir("/home/moyano/Projects/CreateTracks/trips/")
    all_points = []
    for trip in os.listdir("."):
            trip_data = load_file(trip)
            all_points += trip_data
            #tracks.append(Track(trip_data))
            

    boundries = max_bounding_rect(all_points)
   # depth = depth(boundries, 0.00035)
    #print "Nesting Level: %i" % depth
    qtree = QuadTree(6, boundries)
    #Make the QTree
    for coord in all_points:
        qtree.add_point(coord)
    qtree.traverse()
    nodes = qtree.leaves

    #Load Trips
     trips = []
     for trip in os.listdir("."):
        if not trip.startswith('.'):
             gps_data = load_file(trip)
             trips.append(Trip(gps_data,trip))

    routes(trips, qtree)

    #Weighted Points
    os.chdir("/home/moyano/Projects/CreateTracks/edges")
    test_file = open("edges.txt", "w")
    test_file.write("latitude, longitude, ocurrences, color")
    # print children
    for node in nodes:
        p = node._center_of_mass()
        count = len(node.items)
        if count > 2:
            test_file.write("\n")  
            test_file.write(str(p.latitude) + "," + str(p.longitude) + "," + str(count) + "," + get_color(count))

    #All points
    os.chdir("/home/moyano/Projects/CreateTracks/edges")
    test_file = open("edges2.csv", "w")
    test_file.write("latitude, longitude")
    test_file.write("#")  
    # print children
    xpoints = []
    for node in nodes:
        p = node._center_of_mass()
        count = len(node.items)
        if count > 100:

            for _ in xrange(count):
                xpoints.append((p.latitude, p.longitude))
                test_file.write(str(p.latitude) + ", " + str(p.longitude))
                test_file.write("#")  

                            
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
def write_files

def routes(trips, qtree):
    candidates = []

    for trip in trips:
        _new = True
        
        for route in candidates:
            if continuation(route, trip):
            _new = False
            break 

        if _new:
            candidates.append(trip)

#Return true if
def continuation(route, trip):
    #Area being all the neighbors of the node including itself
    end_area = route.nodes[-1].neighbors
    start_area = trip.nodes[0].neighbors
    result = []

    for node in end_area:
        if node in start_area:
            result.append(node)

    if result:
        route.append(trip)

    return False if not result else True

#Returns a list without repeated elements
def unique(_list):
    _temp = list(set(_list))
    return _temp    


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
#Returns de n,s,w,e or a combination of these    
def get_direction(node1, node2):
    neighbors = node1._neighbors()

    for location, neighbor in neighbors.iteritems():
        if neighbor is node2:
            return location
    else :
        print "not consecutive neighbors"
        return None

def load_trip(gps_data, trip):
    nodes = [] 
    direction = ""
    
    for gps_point in gps_data:
        actual = qtree.containing_node(gps_point)
        #Add  the first point to an empty list
        if not nodes:
            nodes.append(actual)
        #Ignore points that are mapped to the same grid
        elif actual is nodes[-1]:
            pass
        #The second point should set the direction variable
        elif direction is None:
            last = nodes[-1]
            nodes.append(actual)
            direction = get_direction(actual, last)
        else:
            last = nodes[-1]
            new_direction = get_direction(actual,last)
            if new_direction == direction:
                nodes[-1] = actual
            else:
                direction = new_direction
                nodes.append(actual)

    return Trip(nodes,trip)

def get_color(count):
    if count <= 100:
        return "small_blue"
    elif count > 100 and count <= 150:
        return "ylw_blank"
    elif count > 150 and count <= 200:
        return "wht_blank"
    elif count > 200 and count <= 250:
        return "red_blank"
    elif count > 250 and count <= 300:
        return "purple_blank"
    elif count > 300 and count <= 350:
        return "pink_blank"
    elif count > 350 and count <= 400:
        return "pink_blank"        
    elif count > 400 and count <= 450:
        return "orange_blank"
    elif count > 450 and count <= 500:
        return "ltblu_blank"
    elif count > 500 and count <= 550:
        return "grn_blank"        
    elif count > 550 and count <= 650:
        return "blu_blank"     
    elif count > 650 and count <= 750:
        return "ylw_stars"
    else:
        return "wht_stars"    
        

def to_png(data, area):
    os.chdir("/home/moyano/Projects/CreateTracks/maps/")
    hm = heatmap.Heatmap()
    img = hm.heatmap(data)
    img.saveKML("map.kml")    


if __name__ == "__main__":
    sys.exit(main())
 

#extract_routes(canonical_trips)
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