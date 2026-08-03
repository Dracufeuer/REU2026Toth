import math
import sortedcontainers as sc
from itertools import islice


def transform(point, theta, cone_i):
    a = cone_i * theta
    x = point[0]
    y = point[1]
    u = (math.sin(a + theta) * x - math.cos(a + theta)*y) / math.sin(theta)
    v = (math.cos(a)*y - math.sin(a)*x) / math.sin(theta)
    return u, v

class Node:
    __slots__ = ['u', 'point', 'secondary', 'left', 'right']
    def __init__(self, point, secondary, left=None, right=None):
        self.point = point #  (u,v,x,y)
        self.secondary = secondary # stores (u,v,x,y) pairs of the children and self below
        self.left = left
        self.right = right


def consider(candidate, best, formula):
    if candidate is not None and (best is None or formula(best[0] + best[1], candidate[0] + candidate[1])):
        return candidate
    return best


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
        root = Node(arr[mid], sc.SortedList(arr, key=lambda p: p[1]))

        root.left = self.build(arr[:mid])
        root.right = self.build(arr[mid+1:])

        return root
    def add_node(self, point):
        trans_point = transform(point, self.theta, self.cone_i)
        self.node_list.append((trans_point[0], trans_point[1], point[0], point[1]))
        self.tree = self.build(self.node_list)

    def query(self, u0, v0):
        smallest = None # This is used for the first quadrant cone best point
        biggest = None # This is used for the third quadrant cone best point

        def recurse(node):
            nonlocal smallest
            nonlocal biggest

            # end of the tree
            if node is None:
                return

            # main cone query
            if node.point[0] > u0:

                if node.point[1] >= v0:
                    smallest = consider(node.point, smallest, lambda a, b: a > b)
                if node.right is not None:
                    sl_left = node.right.secondary.bisect_left(v0)
                    smallest = consider(min(islice(node.right.secondary, sl_left, None),
                                 key=lambda p: p[0] + p[1],
                                 default=None), smallest, lambda a, b: a > b)
                # this part is to recurse for the opposite cone
                recurse(node.left)
            # opposite cone query
            elif node.point[0] < u0:
                if node.point[1] <= v0:
                    biggest = consider(node.point, biggest, lambda a, b: a < b)
                if node.left is not None:
                    sl_right = node.left.secondary.bisect_right(v0)
                    biggest = consider(max(islice(node.left.secondary, 0, sl_right),
                                           key=lambda p: p[0] + p[1],
                                          default=None), biggest, lambda a, b: a < b)
                # this part is to recurse for the main cone
                recurse(node.right)

            # happens only when node u == u0
            # we do not include u == u0 since that is on the counter-clockwise wall.
            else:
                if node.right is not None:
                    sl_left = node.right.secondary.bisect_left(v0)
                    smallest = consider(min(islice(node.right.secondary, sl_left, None),
                                            key=lambda p: p[0] + p[1],
                                            default=None), smallest, lambda a, b: a > b)
                if node.left is not None:
                    sl_right = node.left.secondary.bisect_right(v0)
                    biggest = consider(max(islice(node.left.secondary, 0, sl_right),
                                           key=lambda p: p[0] + p[1],
                                           default=None), biggest, lambda a, b: a < b)
        recurse(self.tree)
        return smallest, biggest
