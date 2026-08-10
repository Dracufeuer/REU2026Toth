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
    __slots__ = [ 'point', 'secondary', 'left', 'right', 'parent', 'balance']
    def __init__(self, point, secondary, left=None, right=None, parent=None):
        self.point = point #  (u,v,x,y) TODO Change it to (u,v, point_index)
        self.secondary = secondary # stores the root of the tree of InnerNode's
        self.left = left
        self.right = right
        self.parent = parent
        self.balance = 0

class InnerNode:
    __slots__ = ['point', 'biggest', 'smallest', 'left', 'right', 'parent', 'balance']
    def __init__(self, point, left=None, right=None, parent=None):
        self.point = point #  (u,v,x,y) TODO Change it to (u,v, point_index)
        self.biggest = (point[0] + point[1], self.point[3]) # (u+v, point_index)
        self.smallest = (point[0] + point[1], self.point[3]) # (u+v, point_index)
        self.left = left
        self.right = right
        self.parent = parent
        self.balance = 0


def consider(candidate, best, compare):
    if candidate is not None and (best is None or compare(best[0] + best[1], candidate[0] + candidate[1])):
        return candidate
    return best


def add_inner_node(root, node):
    while root is not None:
        #This is to update the parents and grandparents of the newly inserted node
        if root.biggest < node.biggest:
            root.biggest = node.biggest
        if root.smallest > node.smallest:
            root.smallest = node.smallest


        if node.point[1] >= root.point[1]:
            if root.right is not None:
                root = root.right
            else:
                #TODO: back propagate the updates to balance
                node.parent = root
                root.right = node
                root = None
        else:
            if root.left is not None:
                root = root.left
            else:
                #TODO: back propagate the updates to balance
                node.parent = root
                root.left = node
                root = None


class RangeTree:
    def __init__(self, cone_i, theta, node_list = None):
        self.node_list = node_list if node_list is not None else sc.SortedList(key=lambda p: p[0])
        self.cone_i = cone_i
        self.theta = theta
        self.tree = self.build(self.node_list)


    #TODO: plan to deprecate build
    def build(self, arr):
        if not arr:
            return None
        mid = len(arr) // 2
        root = Node(arr[mid], sc.SortedList(arr, key=lambda p: p[1]))

        root.left = self.build(arr[:mid])
        root.right = self.build(arr[mid+1:])

        return root

    def add_node(self, normal_point, point_index):
        trans_point = transform(normal_point, self.theta, self.cone_i)
        self.node_list.add((trans_point[0], trans_point[1], normal_point[0], normal_point[1]))
        self.tree = self.build(self.node_list)

        # TODO: WE REALLY NEED TO CHANGE THIS TO (trans_point[0], trans_point[1], point_index)
        point = (trans_point[0], trans_point[1], point_index)
        root = self.tree
        y_node = InnerNode(point)
        while root is not None:
            add_inner_node(root.seconary, y_node)

            if point[0] >= root.point[0]:
                if root.right is not None:
                    root = root.right

                else:
                    #TODO: back propagate the updates to balance
                    root.right = Node(point, y_node, parent=root)
                    root = None
            else:
                if root.left is not None:
                    root = root.left
                else:
                    #TODO: back propagate the updates to balance
                    root.left = Node(point, y_node, parent=root)
                    root = None

    def query(self, original_point):
        smallest = None # This is used for the first quadrant cone best point
        biggest = None # This is used for the third quadrant cone best point
        u0, v0 = transform(original_point, self.theta, self.cone_i)
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
                    sl_left = node.right.secondary.bisect_key_left(v0)
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
                    sl_right = node.left.secondary.bisect_key_right(v0)
                    biggest = consider(max(islice(node.left.secondary, 0, sl_right),
                                           key=lambda p: p[0] + p[1],
                                          default=None), biggest, lambda a, b: a < b)
                # this part is to recurse for the main cone
                recurse(node.right)

            # happens only when node u == u0
            # we do not include u == u0 since that is on the counter-clockwise wall.
            else:
                if node.right is not None:
                    sl_left = node.right.secondary.bisect_key_left(v0)
                    smallest = consider(min(islice(node.right.secondary, sl_left, None),
                                            key=lambda p: p[0] + p[1],
                                            default=None), smallest, lambda a, b: a > b)
                if node.left is not None:
                    sl_right = node.left.secondary.bisect_key_right(v0)
                    biggest = consider(max(islice(node.left.secondary, 0, sl_right),
                                           key=lambda p: p[0] + p[1],
                                           default=None), biggest, lambda a, b: a < b)
        recurse(self.tree)
        return (
        (smallest[2], smallest[3]) if smallest is not None else None,
        (biggest[2], biggest[3]) if biggest is not None else None
        )