import math


def transform(point, radian, cone_i):
    """
    performs an oblique coordinate transformation.

    The transformation maps a point from Cartesian coordinate system to coordinates
    defined by the boundaries of the cone sector.

    :param point: Original cartesian coordinate given ''(x, y)''.
    :param radian: Angular width of the cone sector, in radians.
    :param cone_i: Index of the cone sector.
    :return: Transformed point as ''(u, v)'' tuple.
    """
    a = cone_i * radian
    x = point[0]
    y = point[1]
    u = (math.sin(a + radian) * x - math.cos(a + radian)*y) / math.sin(radian)
    v = (math.cos(a)*y - math.sin(a)*x) / math.sin(radian)
    return u, v


def consider(candidate, best, condition):
    """
    Compares the current best ''(u+v, point_index)'' compared to the new candidate.
    Returning whichever gives the best ''u+v'', determined by the lambda function ''condition''.

    :param candidate: The new ''(u+v, point_index)'' to be compared to the current best.
    :param best: The current held best ''(u+v, point_index)'' tuple.
    :param condition: Lambda function that is either greater or less than.
    :return: The new best ''(u+v, point_index)'' tuple.
    """
    if candidate is not None and (best is None or condition(candidate[0], best[0])):
        return candidate
    return best


class RangeTree:
    """ Range tree for a cone sector. """

    def __init__(self, cone_i, radian):
        """
        Initialization of the range tree.
        :param cone_i: Index of the cone sector.
        :param radian: Angular width of the cone sector, in radians.
        """
        self.cone_i = cone_i
        self.radian = radian
        self.tree = None


    class Node:
        """ Node in the outer tree of the Range tree, ordered by the point's U-value."""
        __slots__ = ['point', 'secondary', 'left', 'right', 'parent', 'height']

        def __init__(self, point, secondary, left=None, right=None, parent=None):
            """
            Initialize the Node for the outer tree.
            :param point: Transformed point and its index as a
                ''(u, v, point_index)'' tuple.
            :param secondary: Root of the InnerNode secondary tree structure.
            :param left: Pointer to the left child Node.
            :param right: Pointer to the right child Node.
            :param parent: Pointer to the parent Node.
            """
            self.point = point
            self.secondary = secondary
            self.left = left
            self.right = right
            self.parent = parent
            self.height = 1

        def tree_merger(self):
            """
            Rebuilds this Node's secondary tree from its current children's
            secondary trees, plus its own point.

            Only called when a primary tree rotation changes this Node's
            children; ordinary insertions keep secondary trees correct
            incrementally through ''insert_into'', so this is not called on
            every insertion.
            """
            left_sec = self.left.secondary if self.left is not None else None
            right_sec = self.right.secondary if self.right is not None else None
            merged = RangeTree.union(left_sec, right_sec)
            self.secondary = RangeTree.insert_into(merged, RangeTree.InnerNode(self.point))


    class InnerNode:
        """Nodes in the inner tree of the Range tree, ordered by the point's v-value."""
        __slots__ = ['point', 'biggest', 'smallest', 'left', 'right', 'height']

        def __init__(self, point, left=None, right=None):
            """
            Initialize the InnerNode for the inner tree.
            :param point: Transformed point and its index as a
                ''(u, v, point_index)'' tuple.
            :param left: Pointer to the left child InnerNode.
            :param right: Pointer to the right child InnerNode.
            """
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
            # tracks the minimum (u + v, point_index) values in the subtree
            self.smallest = smallest

            # tracks the maximum (u + v, point_index) values in the subtree
            self.biggest = biggest

    @staticmethod
    def _cmp_key(node):
        """
        Builds the sort key used to order InnerNode's within the secondary tree.

        The point index is used as a tiebreaker so that duplicate v-values
        never cause ambiguity.

        :param node: InnerNode whose sort key is being built.
        :return: ''(v, point_index)'' sort key tuple.
        """
        # sort key for InnerNode: (v, point_index) -- index breaks ties
        # consistently so duplicate v-values never cause ambiguity
        return (node.point[1], node.point[2])

    @staticmethod
    def _h(n):
        """
        Reads the height of an InnerNode.

        :param n: InnerNode whose height is being read.
        :return: height of ''n'', or ''0'' if ''n'' is ''None''.
        """
        return n.height if n else 0

    @staticmethod
    def _mk(point_source, left, right):
        """Build a fresh InnerNode using point_source's .point, with the given
        (possibly shared, possibly freshly-built) children. Never mutates
        point_source itself.

        :param point_source: The InnerNode whose point is copied into the new node.
        :param left: Left child of the new node.
        :param right: Right child of the new node.
        :return: Newly built InnerNode.
        """
        return RangeTree.InnerNode(point_source.point, left, right)

    @staticmethod
    def _rot_right(node):
        """
        Performs a right rotation on ''node'', returning the new local root.

        ''node'' is never mutated; a fresh InnerNode is built for every
        position that changes.

        :param node: InnerNode to rotate.
        :return: New local root InnerNode after the rotation.
        """
        l = node.left
        new_node = RangeTree._mk(node, l.right, node.right)
        return RangeTree._mk(l, l.left, new_node)

    @staticmethod
    def _rot_left(node):
        """
        Performs a left rotation on ''node'', returning the new local root.

        ''node'' is never mutated; a fresh InnerNode is built for every
        position that changes.

        :param node: InnerNode to rotate.
        :return: New local root InnerNode after the rotation.
        """
        r = node.right
        new_node = RangeTree._mk(node, node.left, r.left)
        return RangeTree._mk(r, new_node, r.right)

    @staticmethod
    def _rebalance(node):
        """
        Restores the AVL balance property at ''node'', performing a single
        or double rotation if needed.

        :param node: InnerNode to check and rebalance.
        :return: New local root InnerNode, regardless whether a rotation occurred.
        """
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
        at node, returning the new root. node is never mutated.

        :param node: Root of the InnerNode tree to insert into.
        :param new_node: Fresh InnerNode being inserted.
        :return: New root InnerNode of the tree after insertion.
        """
        if node is None:
            if new_node.left is not None or new_node.right is not None:
                return RangeTree.InnerNode(new_node.point)
            return new_node
        if RangeTree._cmp_key(new_node) < RangeTree._cmp_key(node):
            node = RangeTree._mk(node, RangeTree.insert_into(node.left, new_node), node.right)
        else:
            node = RangeTree._mk(node, node.left, RangeTree.insert_into(node.right, new_node))
        return RangeTree._rebalance(node)

    @staticmethod
    def join_right(t1, k, t2):
        """
        Joins ''t1'', ''k'', and ''t2'' when ''t1'' is taller than ''t2'',
        descending ''t1'''s right spine until a matching-height subtree is
        found.

        Used internally by ''join''; neither ''t1'' nor ''t2'' is mutated.

        :param t1: Taller InnerNode tree, all keys less than ''k''.
        :param k: InnerNode pivot joining ''t1'' and ''t2''.
        :param t2: Shorter InnerNode tree, all keys greater than ''k''.
        :return: Root InnerNode of the joined tree.
        """
        h = RangeTree._h
        if h(t1.right) <= h(t2) + 1:
            return RangeTree._rebalance(RangeTree._mk(t1, t1.left, RangeTree._mk(k, t1.right, t2)))
        return RangeTree._rebalance(RangeTree._mk(t1, t1.left, RangeTree.join_right(t1.right, k, t2)))

    @staticmethod
    def join_left(t1, k, t2):
        """
        Joins ''t1'', ''k'', and ''t2'' when ''t2'' is taller than ''t1'',
        descending ''t2'''s left spine until a matching-height subtree is
        found.

        Used internally by ''join''; neither ''t1'' nor ''t2'' is mutated.

        :param t1: Shorter InnerNode tree, all keys less than ''k''.
        :param k: InnerNode pivot joining ''t1'' and ''t2''.
        :param t2: Taller InnerNode tree, all keys greater than ''k''.
        :return: Root InnerNode of the joined tree.
        """
        h = RangeTree._h
        if h(t2.left) <= h(t1) + 1:
            return RangeTree._rebalance(RangeTree._mk(t2, RangeTree._mk(k, t1, t2.left), t2.right))
        return RangeTree._rebalance(RangeTree._mk(t2, RangeTree.join_left(t1, k, t2.left), t2.right))

    @staticmethod
    def join(t1, k, t2):
        """Combine t1 (all keys < k) and t2 (all keys > k) with k as pivot.
        k's .point is used; k's own children (if any) are ignored/stripped
        via insert_into's base case. Neither t1 nor t2 is mutated.

        :param t1: InnerNode tree with keys less than ''k''.
        :param k: InnerNode pivot joining ''t1'' and ''t2''.
        :param t2: InnerNode tree with keys greater than ''k''.
        :return: Root InnerNode of the joined tree.
        """
        if t1 is None:
            return RangeTree.insert_into(t2, k)
        if t2 is None:
            return RangeTree.insert_into(t1, k)
        h1, h2 = RangeTree._h(t1), RangeTree._h(t2)
        if h1 > h2 + 1:
            return RangeTree.join_right(t1, k, t2)
        elif h2 > h1 + 1:
            return RangeTree.join_left(t1, k, t2)
        else:
            return RangeTree._mk(k, t1, t2)

    @staticmethod
    def split(T, key):
        """Split T into (< key, node with key or None, > key). T is not mutated.

        :param T: Root InnerNode of the tree to split.
        :param key: ''(v, point_index)'' key to split on.
        :return: ''(left, found, right)'' tuple, where ''left'' holds keys
            less than ''key'', ''right'' holds keys greater than ''key'', and
            ''found'' is the InnerNode matching ''key'', or ''None'' if absent.
        """
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
    def union(t1, t2):
        """Merge two InnerNode trees. Neither t1 nor t2 is mutated -- both
        remain fully valid, independent trees after this call, even though
        the result may share (not copy) most of their nodes.

        :param t1: First InnerNode tree to merge.
        :param t2: Second InnerNode tree to merge.
        :return: Root InnerNode of the merged tree.
        """
        if t1 is None:
            return t2
        if t2 is None:
            return t1
        L, found, R = RangeTree.split(t2, RangeTree._cmp_key(t1))
        return RangeTree.join(RangeTree.union(t1.left, L), t1, RangeTree.union(t1.right, R))

    @staticmethod
    def _p_attach(node, left, right, parent, hook=None):
        """
        Attaches ''left'' and ''right'' as the children of ''node'' and
        ''node'' as the child of ''parent'', updating ''node'''s height.

        :param node: Node whose children are being set.
        :param left: New left child of ''node''.
        :param right: New right child of ''node''.
        :param parent: New parent of ''node''.
        :param hook: Optional callback invoked with ''node'' after attaching.
        :return: ''node'', after being updated.
        """
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
        """
        Performs a right rotation on ''node'' in the primary tree, returning
        the new local root.

        :param node: Node to rotate.
        :param parent: Parent that the new local root should be attached to.
        :param hook: Optional callback invoked on each Node touched by the rotation.
        :return: New local root Node after the rotation.
        """
        l = node.left
        b = l.right
        RangeTree._p_attach(node, b, node.right, l, hook)
        RangeTree._p_attach(l, l.left, node, parent, hook)
        return l

    @staticmethod
    def _p_rotate_left(node, parent, hook=None):
        """
        Performs a left rotation on ''node'' in the primary tree, returning
        the new local root.

        :param node: Node to rotate.
        :param parent: Parent that the new local root should be attached to.
        :param hook: Optional callback invoked on each Node touched by the rotation.
        :return: New local root Node after the rotation.
        """
        r = node.right
        b = r.left
        RangeTree._p_attach(node, node.left, b, r, hook)
        RangeTree._p_attach(r, node, r.right, parent, hook)
        return r

    @staticmethod
    def _p_do_rotation(node, parent, hook=None):
        """
        Determines whether ''node'' needs a single or double rotation and
        performs it, returning the new local root.

        :param node: Unbalanced Node to rotate.
        :param parent: Parent that the new local root should be attached to.
        :param hook: Optional callback invoked on each Node touched by the rotation.
        :return: New local root Node after the rotation.
        """
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
        """
        Walks upward from ''node'' toward the root, updating heights and
        performing rotations as needed to restore the AVL balance property.

        :param node: Node to begin propagating upward from.
        :param child: Child Node that ''node'' was just reached through.
        :param root: Current root of the primary tree.
        :param always_hook: Optional callback invoked on every Node visited.
        :param rotate_hook: Optional callback invoked on each Node touched by
            a rotation.
        :return: The (possibly new) root Node of the primary tree.
        """
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


    def add_node(self, normal_point, point_index):
        """
        Inserts a new point into the range tree.

        :param normal_point: Original cartesian coordinate given ''(x, y)''.
        :param point_index: Index identifying this point.
        """
        trans_point = transform(normal_point, self.radian, self.cone_i)
        point = (trans_point[0], trans_point[1], point_index)

        if self.tree is None:
            self.tree = RangeTree.Node(point, RangeTree.InnerNode(point), parent=None)
            return

        node = self.tree
        while True:
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
        """
        Finds the nearest point ahead of ''query_point'' in the cone's main
        direction, and the nearest point behind it in the opposite direction.

        :param query_point: Original cartesian coordinate given ''(x, y)''.
        :return: A ''(smallest, biggest)'' tuple. ''smallest'' is the
            ''(distance, point_index)'' of the nearest point ahead, or
            ''None'' if none exists; ''biggest'' is the
            ''(distance, point_index)'' of the nearest point behind, or
            ''None'' if none exists.
        """
        u0, v0 = transform(query_point, self.radian, self.cone_i)
        smallest = None
        biggest = None

        greater = lambda a, b: a > b
        lesser = lambda a, b: a < b

        def recurse(node):
            """
            Walks a single path down the primary tree toward ''u0'',
            updating ''smallest'' and ''biggest'' with the nearest
            qualifying point found on each side of the cone.

            :param node: Node currently being visited.
            """
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
            """
            Finds the smallest and largest ''(u + v, point_index)'' values
            within ''node'''s secondary tree among points satisfying
            ''condition'' on ''v0'', using canonical decomposition to avoid
            visiting every point.

            :param node: InnerNode currently being visited.
            :param condition: Either ''greater'' or ''lesser'', determining
                which side of ''v0'' qualifies.
            :return: ''(best_small, best_big)'' tuple of the best
                qualifying ''(u + v, point_index)'' values found, or ''None''
                for either if none exist.
            """
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