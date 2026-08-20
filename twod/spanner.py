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



class TwoDGraph:
    """
    Incrementally builds a 2D online bichromatic geometric spanner.

    Each point added is colored red or blue, opposite to the color of its
    nearest already-placed neighbor, so that every edge crossing between a
    point and its nearest neighbor is bichromatic. One ''RangeTree'' per
    cone direction, per color, supports the nearest-neighbor-per-cone
    queries the construction relies on.
    """

    def __init__(self):
        """
        Initializes an empty spanner with ''NUM_CONES / 2'' red and blue
        range trees, one per two cone direction.
        """
        self.spanner = nx.Graph()
        self.points = []
        self.plotter = GraphPlotter()
        self.t = 0

        self.blue_trees = [
            RangeTree(cone_i = i, radian=CONE_WIDTH)
            for i in range(int(NUM_CONES/2))
        ]
        self.red_trees = [
            RangeTree(cone_i = i, radian=CONE_WIDTH)
            for i in range(int(NUM_CONES/2))
        ]

    def add_node_trees(self, point):
        """
        Inserts ''point'' into the spanner and connects it according to the
        online bichromatic construction rule.

        ''point'' is colored opposite to whichever existing color has the
        closer overall nearest neighbor to it (ensuring the edge to that
        neighbor is bichromatic); if only one color exists so far, ''point''
        is colored the other one. ''point'' is then inserted into every
        range tree matching its own color, so later points can find it.

        Two kinds of edges are added:
            - An edge from ''point'' to its nearest neighbor of the
              opposite color in every cone direction (''opposite_color'').
            - An edge from the single overall nearest opposite-color point
              (''nearest_point'') to each of ''point'''s nearest same-color
              neighbors per cone (''same_color''), if that edge does not
              already exist.

        :param point: Cartesian coordinate given ''(x, y)'' to add to the spanner.
        """
        self.points.append(point)
        point_index = len(self.points) - 1
        opposite_color = []
        same_color = []
        nearest_point = None
        if not self.spanner:
            color = 'red'
            for tree in self.red_trees:
                tree.add_node(point, point_index)
        else:
            red_nearest = [
                node
                for tree in self.red_trees
                for node in tree.query(point)
                if node is not None
            ]
            if red_nearest:
                red_nearest_point = min(red_nearest,
                                        key=lambda p : p[0]
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
                                        key=lambda p : p[0]
                                        )

            else:
                blue_nearest_point = None

            if red_nearest_point is not None and blue_nearest_point is not None:
                if red_nearest_point[0] < blue_nearest_point[0]:
                    color = 'blue'
                    opposite_color, same_color = red_nearest, blue_nearest
                    nearest_point = self.points[red_nearest_point[1]]
                    for tree in self.blue_trees:
                        tree.add_node(point, point_index)
                else:
                    color = 'red'
                    opposite_color, same_color = blue_nearest, red_nearest
                    nearest_point = self.points[blue_nearest_point[1]]
                    for tree in self.red_trees:
                        tree.add_node(point, point_index)
            elif red_nearest_point is None:
                color = 'red'
                opposite_color, same_color = blue_nearest, red_nearest
                nearest_point = self.points[blue_nearest_point[1]]
                for tree in self.red_trees:
                    tree.add_node(point, point_index)
            else:
                color = 'blue'
                opposite_color, same_color = red_nearest, blue_nearest
                nearest_point = self.points[red_nearest_point[1]]
                for tree in self.blue_trees:
                    tree.add_node(point, point_index)



        self.spanner.add_node(point, color=color)

        for q in opposite_color:
            self.spanner.add_edge(point, self.points[q[1]], weight=distance.euclidean(point, self.points[q[1]]))

        for q in same_color:
            if not self.spanner.has_edge(nearest_point, self.points[q[1]]):
                self.spanner.add_edge(nearest_point, self.points[q[1]], weight=distance.euclidean(nearest_point, self.points[q[1]]))
        #self.graphS.add(point)


def twod_list(points):
    """
    Builds a 2D spanner from a fixed list of points, then draws and exports it.

    :param points: List of ''(x, y)'' coordinates to add to the spanner, in order.
    """
    my_graph = TwoDGraph()
    for point in points:
        my_graph.add_node_trees(point)
    my_graph.t = stretch_factor(my_graph.spanner)
    my_graph.plotter.draw_graph(my_graph.spanner, half_circle=False, t=my_graph.t)
    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=False, t=my_graph.t)
    plt.show(block=True)

def twod_loop():
    """
    Runs an interactive session that reads 2D points from the console,
    adding each to the spanner and redrawing until the user exits.
    """
    my_graph = TwoDGraph()
    redraw_queue = queue.Queue()

    def input_loop():
        """
        Reads coordinate input from the console on a background thread,
        adding each valid point to the spanner and signaling the main
        thread to redraw.
        """
        while True:
            user_input = input("Enter 2D coordinates (x, y) separated by a space or comma (n to exit): ")
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

    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=False, t=my_graph.t)