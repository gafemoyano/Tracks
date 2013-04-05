from __future__ import division
class GTrack(object):
    
    def __init__(self, grid, name = None):
        self.nodes = []
        self.name = name
        for node in grid:
            if node not in self.nodes:
                self.nodes.append(node)
                
                
    def compare(self,other):
        self_len = len(self.nodes)
        other_len = len(other.nodes)
        #print self_len, other_len
        if self_len > other_len:
            temp_set = set(other.nodes)
            intersection = temp_set.intersection(self.nodes) 
            ratio =  len(intersection)/self_len
        else:
            temp_set = set(self.nodes)
            intersection = temp_set.intersection(other.nodes) 
            ratio =  len(intersection)/other_len
        
        return True if ratio > 0.8 else False
    
    def __eq__(self,other):
        pass
        