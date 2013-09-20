from __future__ import division
from random import choice
from math import sqrt
import sys


class Cluster(object):

	def __init__(self, seed):
		self.locations = []
		self.center = seed
		self.radius = 0


	def add_location(self, location):
		self.locations.append(location)
		self.radius = seed.distance(location)

	def score(self, location):
		return 1

class ClusterSplit:
	
	@staticmethod
	def pick_seeds(points, n):
		random_list = random.shuffle(points)
		return random_list[:n]
	
	@staticmethod
	def build_clusters(points, seeds):
		clusters = [Cluster(s) for s in seeds]
		print clusters
		sys.exit(0)
		for p in points:
			#calculate scores for each cluster
			candidates = [(c,c.score(p)) for c in clusters]
			
			#select the cluster with the best score
			best_candidate = min([_c[1] for _c in candidates])

			best_candidate.add_location(p)

	@staticmethod
	def score_clusters(clusters):
		cluster.foldLeft()
	
	@staticmethod
	def compare_clusters(score, solution, points):
		seeds = [c.center for c in solution]
		candidates = ClusterSplit.build_clusters(poitns, seeds)
		candidate_score = ClusterSplit.score_clusters(candidates)

		if candidate_score < score:
			return ClusterSplit.compare_clusters(candidate_score, candidates, points) 
		else:
			return solution
	
	@staticmethod
	def split(points, seeds):
		solution = ClusterSplit.build_clusters(points, seeds)
		score = ClusterSplit.score_clusters(solution)
		ClusterSplit.compare_clusters(self, score, solution, points)



class Tree(object):

	def __init__(self):
		self.root = None


	def insert(self, point):
		pass
	
	def filter(self, predicate):
		pass


	def fold_left(self, acc, f):
		pass

class Node(Tree):

	def __init__(self, nodes):
		self.nodes = nodes
		print nodes
		self.center = nodes[0].center

	def insert(self, point):
		# returns a list of tuples -> [(distance, node)]
		distances = [(n.center.distance(point),n) for n in self.nodes]
		#gets the tuple with minimum distance
		closest = min(distances, key = lambda x:x[0])
		
		#create a copy
		new_nodes = self.nodes[:]
		#Insert point into respective cluster.
		new_nodes.insert(self.nodes.index(closest[1]), closest[1].insert(point))
		

		print new_nodes
		return Node(new_nodes)

class Leaf(Tree):

	def __init__(self, max_radius, points):
		self.points = points
		self.max_radius = max_radius
		self.center = points[0]

	def insert(self, point):
		_points = self.points[:]
		_points.append(point)
		
		if point.distance(self.center) < self.max_radius:
			return Leaf(self.max_radius, _points)

		else:
			clusters = ClusterSplit.split(_points, [point, self.center])
			new_nodes = []

			sys.exit(0)
			for c in clusters:
				new_leaf = [Leaf(self.max_radius, c.points)]
				print "x"*10
				print new_leaf
				new_leaves.append(Node(new_leaf))



from pymongo import MongoClient
from trip import TripLoader, Trip, TripParser

if __name__ == '__main__':
	client = MongoClient()
	db = client.trip_db

	#Get locations
	trip_collection = db.trips
	all_trips = TripParser.json_to_object(trip_collection.find())
	locations = list(location for trip in all_trips for location in trip.locations)
	
	l = Leaf(10, [locations.pop()])
	tree = Node([l])
	for l in locations:
		tree.insert(l)
    


