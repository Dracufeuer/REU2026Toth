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
        self.biggest = (point[0] + point[1], point[2]) # (u+v, point_index)
        self.smallest = (point[0] + point[1], point[2]) # (u+v, point_index)
        self.left = left
        self.right = right
        self.parent = parent
        self.balance = 0

    def new_smallest_biggest(self, node):
        node_bisect_distance = (node.point[0] + node.point[1], node.point[2])
        node.smallest, node.biggest = node_bisect_distance, node_bisect_distance

        # fixes node's inner structure
        if node.left is not None:
            if node.biggest < node.left.biggest:
                node.biggest = node.left.biggest
            if node.smallest > node.left.smallest:
                node.smallest = node.left.smallest

        if node.right is not None:
            if node.biggest < node.right.biggest:
                node.biggest = node.right.biggest
            if node.smallest > node.right.smallest:
                node.smallest = node.right.smallest

    def rotation(self, node, child):
        root = None
        if node.balance > 1:
            # (LL) rotation
            if node.left.balance >= 0:
                if node.parent is not None:
                    if node.parent.left is node:
                        node.parent.left = child
                    else:
                        node.parent.right = child
                else:
                    root = child

                middle = child.right
                child.parent, child.right, node.parent, node.left = \
                    node.parent, node, child, child.right

                if middle is not None:
                    middle.parent = node

                child.smallest = node.smallest
                child.biggest = node.biggest

                self.new_smallest_biggest(node)
                child.balance = 0
                node.balance = 0

            # (LR) rotation
            else:
                middle = child.right
                if node.parent is not None:
                    if node.parent.left is node:
                        node.parent.left = middle
                    else:
                        node.parent.right = middle
                else:
                    root = middle

                middle.parent = node.parent

                child.right = middle.left
                if middle.left is not None:
                    middle.left.parent = child

                node.left = middle.right
                if middle.right is not None:
                    middle.right.parent = node

                middle.left = child
                middle.right = node

                child.parent = middle
                node.parent = middle

                old_middle_balance = middle.balance

                middle.smallest = node.smallest
                middle.biggest = node.biggest

                self.new_smallest_biggest(node)
                self.new_smallest_biggest(child)

                if old_middle_balance == 0:
                    child.balance = 0
                    node.balance = 0
                elif old_middle_balance > 0:  # middle's left subtree was taller
                    child.balance = 0
                    node.balance = -1
                else:  # middle's right subtree was taller
                    child.balance = 1
                    node.balance = 0
                middle.balance = 0


        elif node.balance < -1:
            # (RR) rotation
            if node.right.balance <= 0:
                middle = child.left
                if node.parent is not None:
                    if node.parent.left is node:
                        node.parent.left = child
                    else:
                        node.parent.right = child
                else:
                    root = child


                child.parent, child.left, node.parent, node.right = \
                    node.parent, node, child, child.left

                if middle is not None:
                    middle.parent = node

                child.smallest = node.smallest
                child.biggest = node.biggest

                self.new_smallest_biggest(node)
                child.balance = 0
                node.balance = 0

            # (RL) rotation
            else:
                middle = child.left
                if node.parent is not None:
                    if node.parent.left is node:
                        node.parent.left = middle
                    else:
                        node.parent.right = middle
                else:
                    root = middle

                middle.parent = node.parent

                child.left = middle.right
                if middle.right is not None:
                    middle.right.parent = child

                node.right = middle.left
                if middle.left is not None:
                    middle.left.parent = node

                middle.right = child
                middle.left = node

                child.parent = middle
                node.parent = middle

                old_middle_balance = middle.balance

                middle.smallest = node.smallest
                middle.biggest = node.biggest

                self.new_smallest_biggest(node)
                self.new_smallest_biggest(child)

                if old_middle_balance == 0:
                    child.balance = 0
                    node.balance = 0
                elif old_middle_balance > 0:  # middle's left subtree was taller
                    child.balance = -1
                    node.balance = 0
                else:  # middle's right subtree was taller
                    child.balance = 0
                    node.balance = 1
                middle.balance = 0
        return root


def consider(candidate, best, condition):
    if candidate is not None and (best is None or condition(candidate[0] , best[0])):
        return candidate
    return best


def add_inner_node(node, new_node):
    while node is not None:
        #This is to update the parents and grandparents of the newly inserted node
        if node.biggest < new_node.biggest:
            node.biggest = new_node.biggest
        if node.smallest > new_node.smallest:
            node.smallest = new_node.smallest


        if new_node.point[1] >= node.point[1]:
            if node.right is not None:
                node = node.right
            else:
                #TODO: back propagate the updates to balance
                new_node.parent = node
                node.right = new_node
                return
        else:
            if node.left is not None:
                node = node.left
            else:
                #TODO: back propagate the updates to balance
                new_node.parent = node
                node.left = new_node
                return


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

    def backprop_insert(self, node, child, root):
        if node is None:
            return root

        if node.right == child:
            node.balance -= 1
        else:
            node.balance += 1

        if node.balance == 0:
            return root
        if node.balance > 1 or node.balance < -1:
            new_root = root.rotation(node, child)
            if new_root is not None:
                root = new_root
            return root
        return self.backprop_insert(node.parent, node, root)

    

    def add_node(self, normal_point, point_index):
        # IGNORE THESE 3 LINES WILL GET RID OF. IT IS DEPRECATED AND OLD
        trans_point = transform(normal_point, self.theta, self.cone_i)
        self.node_list.add((trans_point[0], trans_point[1], normal_point[0], normal_point[1]))
        self.tree = self.build(self.node_list)

        # TODO: WE REALLY NEED TO CHANGE THIS TO (trans_point[0], trans_point[1], point_index)
        trans_point = transform(normal_point, self.theta, self.cone_i)
        point = (trans_point[0], trans_point[1], point_index)

        if self.tree is None:
            self.tree = Node(point, InnerNode(point), parent=None)
            return

        node = self.tree
        while node is not None:

            add_inner_node(node.secondary, InnerNode(point))

            if point[0] >= node.point[0]:
                if node.right is not None:
                    node = node.right

                else:
                    node.right = Node(point, InnerNode(point), parent=node)
                    self.tree = self.backprop_insert(node, node.right, self.tree)
                    return

            else:
                if node.left is not None:
                    node = node.left
                else:
                    node.left = Node(point, InnerNode(point), parent=node)
                    self.tree = self.backprop_insert(node, node.left, self.tree)
                    return




    def new_query(self, query_point):
        u0, v0 = transform(query_point, self.theta, self.cone_i)
        smallest = None
        biggest = None

        greater = lambda a, b: a > b
        lesser = lambda a, b: a < b
        def recurse(node):
            nonlocal smallest
            nonlocal biggest

            if node is None:
                return

            if node.point[0] > u0:
                if node.point[1] >= v0:
                    smallest = consider((node.point[0] + node.point[1], node.point[3]), smallest, lesser)
                if node.right is not None:
                    temp, _ = inner_recurse(node.right.secondary, greater)
                    smallest = consider(temp, smallest, lesser)
                recurse(node.left)

            elif node.point[0] < u0:
                if node.point[1] <= v0:
                    biggest = consider((node.point[0] + node.point[1], node.point[3]), biggest, greater)
                if node.left is not None:
                    _, temp = inner_recurse(node.left.secondary, lesser)
                    biggest = consider(temp, biggest, greater)
                recurse(node.right)

            else:
                if node.right is not None:
                    recurse(node.right)
                if node.left is not None:
                    recurse(node.left)



        def inner_recurse(node, condition):

            if node is None:
                return None, None

            best_small = None
            best_big = None

            if condition == greater:
                child = node.right
                opp_child = node.left
            else:
                child = node.left
                opp_child = node.right

            bisect = (node.point[0] + node.point[1], node.point[3])
            if condition(node.point[1], v0):
                best_small = consider(bisect, best_small, lesser)
                best_big = consider(bisect, best_big, greater)
                if child is not None:
                    best_small = consider(child.smallest, best_small, lesser)
                    best_big = consider(child.biggest, best_big, greater)
                if opp_child is not None:
                    temp_small, temp_big = inner_recurse(opp_child, condition)
                    best_small = consider(temp_small, best_small, lesser)
                    best_big = consider(temp_big, best_big, greater)
            elif node.point[1] == v0:
                best_small = consider(bisect, best_small, lesser)
                best_big = consider(bisect, best_big, greater)

                if child is not None:
                    best_small = consider(child.smallest, best_small, lesser)
                    best_big = consider(child.biggest, best_big, greater)
                if opp_child is not None:
                    temp_small, temp_big = inner_recurse(opp_child, condition)
                    best_small = consider(temp_small, best_small, lesser)
                    best_big = consider(temp_big, best_big, greater)
            else:
                temp_small, temp_big = inner_recurse(child, condition)
                best_small = consider(temp_small, best_small, lesser)
                best_big = consider(temp_big, best_big, greater)

            return best_small, best_big

        recurse(self.tree)
        return (
            (abs(smallest[0] - (u0 + v0)), smallest[1]) if smallest is not None else None,
            (abs(biggest[0] - (u0 + v0)), biggest[1]) if biggest is not None else None
        )



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