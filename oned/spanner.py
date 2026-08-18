import sortedcontainers as sc
import networkx as nx
import matplotlib
from networkx import Graph

from spaner_common.plotting import GraphPlotter
from spaner_common.stretch_factor import stretch_factor

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import threading
import queue

class OneDGraph:
    def __init__(self):
        self.spanner = nx.Graph()
        self.red = sc.SortedSet()
        self.blue = sc.SortedSet()
        self.graphS = sc.SortedSet()
        self.plotter = GraphPlotter()
        self.t = 0

    def add_node(self, node):
        idx = self.graphS.bisect_left(node)
        left_idx = self.graphS[idx - 1] if idx > 0 else float('inf')
        right_idx = self.graphS[idx] if idx < len(self.graphS) else float('inf')


        if abs(left_idx - node) <= abs(node - right_idx):
            nearest = left_idx
        else:
            nearest = right_idx

        if nearest in self.red:
            self.connect_edge(node, self.red, 'blue')
            self.blue.add(node)
        elif nearest in self.blue:
            self.connect_edge(node, self.blue, 'red')
            self.red.add(node)
        else:
            self.red.add(node)
            self.spanner.add_node((node, 0), color='red')
        self.graphS.add(node)



    def connect_edge(self, node, color_set, color):
        idx = color_set.bisect_left(node)
        left_idx = color_set[idx - 1] if idx > 0 else None
        right_idx = color_set[idx] if idx < len(color_set) else None
        self.spanner.add_node((node, 0), color=color)
        if left_idx is not None:
            self.spanner.add_edge((node,0), (left_idx, 0), weight=abs(node - left_idx))
        if right_idx is not None:
            self.spanner.add_edge((node,0), (right_idx, 0), weight=abs(node - right_idx))
def oned_list(points):
    my_graph = OneDGraph()
    for point in points:
        my_graph.add_node(point)
    my_graph.t = stretch_factor(my_graph.spanner)
    my_graph.plotter.draw_graph(my_graph.spanner, half_circle=True, t=my_graph.t)
    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=True, t=my_graph.t)
    plt.show(block=True)

def oned_loop():
    my_graph = OneDGraph()
    redraw_queue = queue.Queue()

    def input_loop():
        while True:
            user_input = input("Enter a node to add to the graph:")
            try:
                node = float(user_input)
                if node in my_graph.graphS:
                    print('node already exists')
                else:
                    my_graph.add_node(node)  # safe: no GUI calls here
                    my_graph.t = stretch_factor(my_graph.spanner)
                    redraw_queue.put(True)  # just signal main thread to redraw
            except ValueError:
                print("not a number")
                break

    thread = threading.Thread(target=input_loop, daemon=True)
    thread.start()

    while thread.is_alive():
        try:
            redraw_queue.get(timeout=0.1)  # wait briefly for a signal
            my_graph.plotter.draw_graph(my_graph.spanner, t=my_graph.t)
        except queue.Empty:
            pass
        plt.pause(0.05)
    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=True, t=my_graph.t)


