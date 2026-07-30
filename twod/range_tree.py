import math
import sortedcontainers as sc
from networkx.algorithms.coloring.greedy_coloring import strategy_largest_first


def transform(point, theta, cone_i):
    a = cone_i * theta
    x = point[0]
    y = point[1]
    u = (math.sin(a + theta) * x - math.cos(a + theta)*y) / math.sin(theta)
    v = (math.cos(a)*y - math.sin(a)*x) / math.sin(theta)
    return u, v

class Node:
    __slots__ = ['u', 'point', 'secondary', 'left', 'right']
    def __init__(self, u, point, secondary, left=None, right=None):
        self.u = u
        self.point = point # the original (x,y) before transform
        self.secondary = secondary # stores (u,v,x,y) pairs of the children and self below
        self.left = left
        self.right = right

class RangeTree:
    def __init__(self, cone_i, theta, node_list = None):
        self.node_list = node_list if node_list is not None else sc.SortedList(key=lambda p: p[0])
        self.cone_i = cone_i
        self.theta = theta
        self.tree = self.build(self.node_list)

    def build(self, arr):
        if not arr:
            return None
        mid = len(arr) // 2
        root = Node(arr[mid][0], arr[mid], sc.SortedList(arr, key=lambda p: p[1]))

        root.left = self.build(arr[:mid])
        root.right = self.build(arr[mid+1:])

        return root
    def add_node(self, point):
        trans_point = transform(point, self.theta, self.cone_i)
        self.node_list.append((trans_point[0], trans_point[1], point[0], point[1]))
        self.tree = self.build(self.node_list)

