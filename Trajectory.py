import collections
from math import radians, cos, sin, asin, sqrt,atan2,degrees
from Tree import Tree as Tree

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
    
def initial_heading(lon1, lat1, lon2, lat2):
    dlon = radians(lon2-lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    y = sin(dlon)*cos(lat2)
    x = (cos(lat1)*sin(lat2))-(sin(lat1)*cos(lat2)*cos(dlon))
    #normalize
    heading =  (degrees((atan2(y,x)))+360)%360
    return heading

def final_heading(lon1, lat1, lon2, lat2):
    heading = initial_heading(lon2,lat2,lon1,lat1)
    final_heading = (heading+180)%360
    print final_heading
    
def calculate_distance(lon1, lat1, lon2, lat2):
    dlat= radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    a = (sin(dlat/2)**2) + (sin(dlon/2)**2*cos(lat1_rad)*cos(lat2_rad))
    c = 2*atan2(sqrt(a),sqrt(1-a))
    d = 6371*c
    print d
    

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
    print km 
    
def time_interval(t1,t2):
    return t2-t1

def add_segment(seg,track):
    if not track:
        track = Tree(seg)
    else:
        pass

point_file = open('trip_0.txt')
geo_point = collections.namedtuple('geo_point', ['latitude', 'longitude','timestamp'])
points = []
segments = []
track = None
#load points as touples into a list
for line in point_file:
    data = line.split(",")
    points.append(geo_point(float(data[1]),float(data[2]),float(data[3])))

segment = []
for point in points:
    if  len(segment)<2:
        segment.append(point)
    else:
        if is_part_of_segment(segment,point):
            segment.append(point)
            add_segment(segment,track)
        else:
            segments.append(segment)
            segment = []
            segment.append(point)
            
segments.append(segment)
        
root = Tree(segments[0])
node = Tree(segments[1])
root.addChild(node)
print root.data
print len(segments)
    

def initialize_segment(point1,point2):
    pass

def initialize_trajectory(self):
    pass
    
def calculate_velocity():
    pass


    
#calculate_distance(41.879176,-87.649627,41.879172,-87.649875)
#haversine(41.879176,-87.649627,41.879172,-87.649875)
#initial_heading(41.879176,-87.649627,41.879172,-87.649875)
#final_heading(41.879176,-87.649627,41.879172,-87.649875)
