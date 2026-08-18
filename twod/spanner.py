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
        self.points = []
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
    my_graph = TwoDGraph()
    for point in points:
        my_graph.add_node_trees(point)
    my_graph.t = stretch_factor(my_graph.spanner)
    my_graph.plotter.draw_graph(my_graph.spanner, half_circle=False, t=my_graph.t)
    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=False, t=my_graph.t)
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

    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=False, t=my_graph.t)
