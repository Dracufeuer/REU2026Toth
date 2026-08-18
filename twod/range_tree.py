import math
import sortedcontainers as sc



def transform(point, theta, cone_i):
    a = cone_i * theta
    x = point[0]
    y = point[1]
    u = (math.sin(a + theta) * x - math.cos(a + theta)*y) / math.sin(theta)
    v = (math.cos(a)*y - math.sin(a)*x) / math.sin(theta)
    return u, v


def consider(candidate, best, condition):
    if candidate is not None and (best is None or condition(candidate[0], best[0])):
        return candidate
    return best


class RangeTree:
    def __init__(self, cone_i, theta):
        self.cone_i = cone_i
        self.theta = theta
        self.tree = None

    # ======================================================================
    # PRIMARY TREE NODE -- height-based AVL, mutating (no persistence needed
    # here: there is only ever one live primary tree, nothing holds onto an
    # "old" version of it, so in-place rotation is safe and cheap).
    # ======================================================================
    class Node:
        __slots__ = ['point', 'secondary', 'left', 'right', 'parent', 'height']

        def __init__(self, point, secondary, left=None, right=None, parent=None):
            self.point = point          # (u, v, point_index)
            self.secondary = secondary  # root of this node's InnerNode secondary tree
            self.left = left
            self.right = right
            self.parent = parent
            self.height = 1

        def tree_merger(self):
            """Rebuild this node's secondary tree from its (current) children's
            secondaries, plus its own point. Called only when a PRIMARY rotation
            changes this node's children -- ordinary insertions keep secondaries
            correct incrementally via add_inner_node, so this is not called on
            every insert, only on rotation."""
            left_sec = self.left.secondary if self.left is not None else None
            right_sec = self.right.secondary if self.right is not None else None
            merged = RangeTree.union(left_sec, right_sec)
            self.secondary = RangeTree.insert_into(merged, RangeTree.InnerNode(self.point))

    # ======================================================================
    # SECONDARY TREE NODE -- height-based AVL, FULLY FUNCTIONAL/PERSISTENT.
    # No .parent field: nodes are shared across multiple trees (this node's
    # own secondary, its ancestors' merged secondaries, etc.), and a single
    # mutable parent pointer cannot be correct for more than one of those
    # trees at once. Nothing in this design reads .parent, so it is safely
    # omitted rather than left silently wrong.
    #
    # Every operation below (insert_into, join, split, union, rotations)
    # NEVER mutates an existing node's fields. It only ever creates new
    # nodes for the specific path that changes, and shares (points at,
    # never touches) everything else. This is what makes it safe for one
    # tree to be built from pieces of another without corrupting the
    # original -- verified extensively before being written here.
    # ======================================================================
    class InnerNode:
        __slots__ = ['point', 'biggest', 'smallest', 'left', 'right', 'height']

        def __init__(self, point, left=None, right=None):
            self.point = point  # (u, v, point_index)
            self.left = left
            self.right = right
            lh = left.height if left else 0
            rh = right.height if right else 0
            self.height = 1 + max(lh, rh)
            own = (point[0] + point[1], point[2])
            smallest = own
            biggest = own
            if left:
                if left.smallest < smallest:
                    smallest = left.smallest
                if left.biggest > biggest:
                    biggest = left.biggest
            if right:
                if right.smallest < smallest:
                    smallest = right.smallest
                if right.biggest > biggest:
                    biggest = right.biggest
            self.smallest = smallest
            self.biggest = biggest

    @staticmethod
    def _cmp_key(node):
        # sort key for InnerNode: (v, point_index) -- index breaks ties
        # consistently so duplicate v-values never cause ambiguity
        return (node.point[1], node.point[2])

    @staticmethod
    def _h(n):
        return n.height if n else 0

    @staticmethod
    def _mk(point_source, left, right):
        """Build a fresh InnerNode using point_source's .point, with the given
        (possibly shared, possibly freshly-built) children. Never mutates
        point_source itself."""
        return RangeTree.InnerNode(point_source.point, left, right)

    @staticmethod
    def _rot_right(node):
        l = node.left
        new_node = RangeTree._mk(node, l.right, node.right)
        return RangeTree._mk(l, l.left, new_node)

    @staticmethod
    def _rot_left(node):
        r = node.right
        new_node = RangeTree._mk(node, node.left, r.left)
        return RangeTree._mk(r, new_node, r.right)

    @staticmethod
    def _rebalance(node):
        h = RangeTree._h
        bf = h(node.left) - h(node.right)
        if bf > 1:
            if h(node.left.left) < h(node.left.right):
                node = RangeTree._mk(node, RangeTree._rot_left(node.left), node.right)
            return RangeTree._rot_right(node)
        if bf < -1:
            if h(node.right.right) < h(node.right.left):
                node = RangeTree._mk(node, node.left, RangeTree._rot_right(node.right))
            return RangeTree._rot_left(node)
        return node

    @staticmethod
    def insert_into(node, new_node):
        """Insert new_node (a fresh, childless InnerNode) into the tree rooted
        at node, returning the new root. node is never mutated."""
        if node is None:
            if new_node.left is not None or new_node.right is not None:
                return RangeTree.InnerNode(new_node.point)  # strip any stale children
            return new_node
        if RangeTree._cmp_key(new_node) < RangeTree._cmp_key(node):
            node = RangeTree._mk(node, RangeTree.insert_into(node.left, new_node), node.right)
        else:
            node = RangeTree._mk(node, node.left, RangeTree.insert_into(node.right, new_node))
        return RangeTree._rebalance(node)

    @staticmethod
    def join_right(T1, k, T2):
        h = RangeTree._h
        if h(T1.right) <= h(T2) + 1:
            return RangeTree._rebalance(RangeTree._mk(T1, T1.left, RangeTree._mk(k, T1.right, T2)))
        return RangeTree._rebalance(RangeTree._mk(T1, T1.left, RangeTree.join_right(T1.right, k, T2)))

    @staticmethod
    def join_left(T1, k, T2):
        h = RangeTree._h
        if h(T2.left) <= h(T1) + 1:
            return RangeTree._rebalance(RangeTree._mk(T2, RangeTree._mk(k, T1, T2.left), T2.right))
        return RangeTree._rebalance(RangeTree._mk(T2, RangeTree.join_left(T1, k, T2.left), T2.right))

    @staticmethod
    def join(T1, k, T2):
        """Combine T1 (all keys < k) and T2 (all keys > k) with k as pivot.
        k's .point is used; k's own children (if any) are ignored/stripped
        via insert_into's base case. Neither T1 nor T2 is mutated."""
        if T1 is None:
            return RangeTree.insert_into(T2, k)
        if T2 is None:
            return RangeTree.insert_into(T1, k)
        h1, h2 = RangeTree._h(T1), RangeTree._h(T2)
        if h1 > h2 + 1:
            return RangeTree.join_right(T1, k, T2)
        elif h2 > h1 + 1:
            return RangeTree.join_left(T1, k, T2)
        else:
            return RangeTree._mk(k, T1, T2)

    @staticmethod
    def split(T, key):
        """Split T into (< key, node with key or None, > key). T is not mutated."""
        if T is None:
            return None, None, None
        if key < RangeTree._cmp_key(T):
            L, found, R = RangeTree.split(T.left, key)
            return L, found, RangeTree.join(R, T, T.right)
        elif key > RangeTree._cmp_key(T):
            L, found, R = RangeTree.split(T.right, key)
            return RangeTree.join(T.left, T, L), found, R
        else:
            return T.left, T, T.right

    @staticmethod
    def union(T1, T2):
        """Merge two InnerNode trees. Neither T1 nor T2 is mutated -- both
        remain fully valid, independent trees after this call, even though
        the result may share (not copy) most of their nodes."""
        if T1 is None:
            return T2
        if T2 is None:
            return T1
        L, found, R = RangeTree.split(T2, RangeTree._cmp_key(T1))
        return RangeTree.join(RangeTree.union(T1.left, L), T1, RangeTree.union(T1.right, R))

    # ======================================================================
    # PRIMARY TREE ROTATION CORE -- shared by Node's own insertion backprop.
    # This part IS mutating (fine: only one live primary tree exists).
    # rotate_hook fires only on the 1-3 nodes actually touched by a rotation
    # (used for Node.tree_merger). always_hook fires on every ancestor
    # visited during backprop (not used for Node; kept for generality).
    # ======================================================================
    @staticmethod
    def _p_attach(node, left, right, parent, hook=None):
        node.left = left
        node.right = right
        node.parent = parent
        if left is not None:
            left.parent = node
        if right is not None:
            right.parent = node
        node.height = 1 + max(RangeTree._h(left), RangeTree._h(right))
        if hook is not None:
            hook(node)
        return node

    @staticmethod
    def _p_rotate_right(node, parent, hook=None):
        l = node.left
        b = l.right
        RangeTree._p_attach(node, b, node.right, l, hook)
        RangeTree._p_attach(l, l.left, node, parent, hook)
        return l

    @staticmethod
    def _p_rotate_left(node, parent, hook=None):
        r = node.right
        b = r.left
        RangeTree._p_attach(node, node.left, b, r, hook)
        RangeTree._p_attach(r, node, r.right, parent, hook)
        return r

    @staticmethod
    def _p_do_rotation(node, parent, hook=None):
        bf = RangeTree._h(node.left) - RangeTree._h(node.right)
        if bf > 1:
            if RangeTree._h(node.left.left) >= RangeTree._h(node.left.right):
                return RangeTree._p_rotate_right(node, parent, hook)
            node.left = RangeTree._p_rotate_left(node.left, node, hook)
            return RangeTree._p_rotate_right(node, parent, hook)
        else:
            if RangeTree._h(node.right.right) >= RangeTree._h(node.right.left):
                return RangeTree._p_rotate_left(node, parent, hook)
            node.right = RangeTree._p_rotate_right(node.right, node, hook)
            return RangeTree._p_rotate_left(node, parent, hook)

    @staticmethod
    def backprop_insert(node, child, root, always_hook=None, rotate_hook=None):
        if node is None:
            return root
        old_height = node.height
        node.height = 1 + max(RangeTree._h(node.left), RangeTree._h(node.right))
        if always_hook is not None:
            always_hook(node)
        bf = RangeTree._h(node.left) - RangeTree._h(node.right)
        if bf > 1 or bf < -1:
            parent = node.parent
            new_local_root = RangeTree._p_do_rotation(node, parent, rotate_hook)
            if parent is not None:
                if parent.left is node:
                    parent.left = new_local_root
                else:
                    parent.right = new_local_root
            else:
                root = new_local_root
            return RangeTree.backprop_insert(parent, new_local_root, root, always_hook, rotate_hook)
        if node.height == old_height and always_hook is None:
            return root
        return RangeTree.backprop_insert(node.parent, node, root, always_hook, rotate_hook)

    # ======================================================================
    # PUBLIC API
    # ======================================================================
    def add_node(self, normal_point, point_index):
        trans_point = transform(normal_point, self.theta, self.cone_i)
        point = (trans_point[0], trans_point[1], point_index)

        if self.tree is None:
            self.tree = RangeTree.Node(point, RangeTree.InnerNode(point), parent=None)
            return

        node = self.tree
        while True:
            # FUNCTIONAL insert -- never mutates node.secondary's existing nodes,
            # so this is always safe even if node.secondary shares structure
            # with some ancestor's already-computed merged secondary.
            node.secondary = RangeTree.insert_into(node.secondary, RangeTree.InnerNode(point))

            if point[0] >= node.point[0]:
                if node.right is not None:
                    node = node.right
                else:
                    node.right = RangeTree.Node(point, RangeTree.InnerNode(point), parent=node)
                    self.tree = RangeTree.backprop_insert(
                        node, node.right, self.tree,
                        always_hook=None, rotate_hook=lambda n: n.tree_merger()
                    )
                    return
            else:
                if node.left is not None:
                    node = node.left
                else:
                    node.left = RangeTree.Node(point, RangeTree.InnerNode(point), parent=node)
                    self.tree = RangeTree.backprop_insert(
                        node, node.left, self.tree,
                        always_hook=None, rotate_hook=lambda n: n.tree_merger()
                    )
                    return

    def query(self, query_point):
        u0, v0 = transform(query_point, self.theta, self.cone_i)
        smallest = None
        biggest = None

        greater = lambda a, b: a > b
        lesser = lambda a, b: a < b

        def recurse(node):
            nonlocal smallest, biggest
            if node is None:
                return
            if node.point[0] > u0:
                if node.point[1] >= v0:
                    smallest = consider((node.point[0] + node.point[1], node.point[2]), smallest, lesser)
                if node.right is not None:
                    temp, _ = inner_recurse(node.right.secondary, greater)
                    smallest = consider(temp, smallest, lesser)
                recurse(node.left)
            elif node.point[0] < u0:
                if node.point[1] <= v0:
                    biggest = consider((node.point[0] + node.point[1], node.point[2]), biggest, greater)
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
            bisect = (node.point[0] + node.point[1], node.point[2])
            if condition(node.point[1], v0) or node.point[1] == v0:
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