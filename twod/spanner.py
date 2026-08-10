import networkx as nx
import matplotlib
import math
from scipy.spatial import distance

from spaner_common.plotting import GraphPlotter
from spaner_common.stretch_factor import stretch_factor
from twod.range_tree import RangeTree

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import threading
import queue

NUM_CONES = 12 # NEEDS to be an even number
CONE_WIDTH = 2 * math.pi / NUM_CONES


def cone_index(px, py, qx, qy):
    angle = math.atan2(qy - py, qx - px)
    if angle < 0:
        angle += 2 * math.pi
    return int(angle // CONE_WIDTH)


class TwoDGraph:
    def __init__(self):
        self.spanner = nx.Graph()
        self.red = set() # deprecated with range trees
        self.blue = set() # deprecated with range trees
        self.graphS = set() # deprecated with range trees
        self.plotter = GraphPlotter()
        self.t = 0

        self.blue_trees = [
            RangeTree(cone_i = i, theta=CONE_WIDTH)
            for i in range(int(NUM_CONES/2))
        ]
        self.red_trees = [
            RangeTree(cone_i = i, theta=CONE_WIDTH)
            for i in range(int(NUM_CONES/2))
        ]

    def add_node_trees(self, point):
        opposite_color = []
        same_color = []
        nearest_point = None
        if not self.spanner:
            color = 'red'
            for tree in self.red_trees:
                tree.add_node(point)
        else:
            red_nearest = [
                node
                for tree in self.red_trees
                for node in tree.query(point)
                if node is not None
            ]
            if red_nearest:
                red_nearest_point = min(red_nearest,
                                        key=lambda p : distance.euclidean(point, p)
                                        )
            else:
                red_nearest_point = None


            blue_nearest = [
                node
                for tree in self.blue_trees
                for node in tree.query(point)
                if node is not None
            ]
            if blue_nearest:
                blue_nearest_point = min(blue_nearest,
                                        key=lambda p : distance.euclidean(point, p)
                                        )
            else:
                blue_nearest_point = None

            # this is to find which is the nearest point of the colors to
            # decide the color of our point
            if red_nearest_point is not None:
                red_dis = distance.euclidean(point, red_nearest_point)
            else:
                red_dis = math.inf

            if blue_nearest_point is not None:
                blue_dis = distance.euclidean(point, blue_nearest_point)
            else:
                blue_dis = math.inf

            if red_dis < blue_dis:
                color = 'blue'
                opposite_color, same_color = red_nearest, blue_nearest
                nearest_point = red_nearest_point
                for tree in self.blue_trees:
                    tree.add_node(point)
            else:
                color = 'red'
                opposite_color, same_color = blue_nearest, red_nearest
                nearest_point = blue_nearest_point
                for tree in self.red_trees:
                    tree.add_node(point)

        self.spanner.add_node(point, color=color)

        for q in opposite_color:
            self.spanner.add_edge(point, q, weight=distance.euclidean(point, q))

        for q in same_color:
            if not self.spanner.has_edge(nearest_point, q):
                self.spanner.add_edge(nearest_point, q, weight=distance.euclidean(nearest_point, q))
        #self.graphS.add(point)

    def add_node(self, node):
        current = []
        opposite = []
        if not self.graphS:
            color = 'red'
        else:
            nearest = min(self.graphS, key=lambda q: distance.euclidean(q, node))
            nearest_color = self.spanner.nodes[nearest]['color']
            color = 'blue' if nearest_color == 'red' else 'red'

        self.spanner.add_node(node, color=color)

        #opposite, current = self.blue, self.red if color == 'red' else self.red, self.blue
        if color =='red':
            current, opposite = self.red, self.blue
        else:
            current, opposite = self.blue, self.red
        opp_buckets = [None] * NUM_CONES
        curr_buckets = [None] * NUM_CONES
        edges_added = 0
        curr_edges = 0
        not_entered = 0

        for q in opposite:
            i = cone_index(node[0], node[1], q[0], q[1])
            dist = distance.euclidean(node, q)
            if opp_buckets[i] is None or dist < opp_buckets[i][0]:
                opp_buckets[i] = (dist, q)

        for entry in opp_buckets:
            if entry is not None:
                _, q = entry
                self.spanner.add_edge(node, q, weight=distance.euclidean(node, q))
                edges_added += 1

        for q in current:
            i = cone_index(node[0], node[1], q[0], q[1])
            dist = distance.euclidean(node, q)
            if curr_buckets[i] is None or dist < curr_buckets[i][0]:
                curr_buckets[i] = (dist, q)

        for entry in curr_buckets:
            if entry is not None:
                _, q = entry
                not_entered += 1
                if not self.spanner.has_edge(nearest, q):
                    curr_edges += 1
                    self.spanner.add_edge(nearest, q, weight=distance.euclidean(nearest, q))
                    edges_added += 1
        print(f"edges added: {edges_added} curr_edges added: {curr_edges} entered: {not_entered}")

        (self.red if color == 'red' else self.blue).add(node)
        self.graphS.add(node)

def twod_list(points):
    my_graph = TwoDGraph()
    for point in points:
        my_graph.add_node_trees(point)
    my_graph.t = stretch_factor(my_graph.spanner)
    my_graph.plotter.draw_graph(my_graph.spanner, half_circle=False, t=my_graph.t)
    plt.show(block=True)

def twod_loop():
    my_graph = TwoDGraph()
    redraw_queue = queue.Queue()

    def input_loop():
        while True:
            user_input = input("Enter 2D coordinates (x, y) separated by a space or comma: ")
            if user_input.strip().lower() == "n":
                break
            try:
                x_str, y_str = user_input.replace(',', ' ').split()
                x, y = float(x_str), float(y_str)
            except ValueError:
                print("Invalid input. Please enter exactly two numbers.")
                continue

            node = (x, y)
            if my_graph.spanner.has_node(node):
                print('node already exists')
            else:
                my_graph.add_node_trees(node)
                my_graph.t = stretch_factor(my_graph.spanner)
                redraw_queue.put(True)


    thread = threading.Thread(target=input_loop, daemon=True)
    thread.start()

    while thread.is_alive():
        try:
            redraw_queue.get(timeout=0.1)
            my_graph.plotter.draw_graph(my_graph.spanner, half_circle=False, t=my_graph.t)
        except queue.Empty:
            pass
        plt.pause(0.05)