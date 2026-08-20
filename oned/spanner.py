import sortedcontainers as sc
import networkx as nx
import matplotlib


from spaner_common.plotting import GraphPlotter
from spaner_common.stretch_factor import stretch_factor

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import threading
import queue

class OneDGraph:
    """
    Incrementally builds a 1D online bichromatic geometric spanner.

    Each point added is colored opposite to its single nearest existing
    neighbor, then connected to its nearest left and right neighbor of that
    opposite color. the 1D analogue of one edge per cone in the 2D
    construction, since a point on a line has exactly two directions.
    """

    def __init__(self):
        """
        Initializes an empty spanner with separate sorted sets tracking red
        points, blue points, and all points together.
        """
        self.spanner = nx.Graph()
        self.red = sc.SortedSet()
        self.blue = sc.SortedSet()
        self.graphS = sc.SortedSet()
        self.plotter = GraphPlotter()
        self.t = 0

    def add_node(self, node):
        """
        Inserts ''node'' into the spanner.

        ''node'' is colored opposite to whichever of ''self.red'' or
        ''self.blue'' its single nearest existing neighbor (by absolute
        distance, ties going left) belongs to, then connected to that
        opposite color via ''connect_edge''. If ''node'' is the first point
        added, it is colored red with no edges.

        :param node: 1D coordinate to add to the spanner.
        """
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
        """
        Adds ''node'' to the spanner as ''color'', and connects it to its
        nearest left and right neighbor within ''color_set'' (the opposite
        color set), if either exists.

        :param node: 1D coordinate being added to the spanner.
        :param color_set: ''SortedSet'' (''self.red'' or ''self.blue'')
            to find ''node'''s nearest opposite-color neighbors in.
        :param color: The color ''node'' itself is being assigned, opposite
            to ''color_set'''s color.
        """
        idx = color_set.bisect_left(node)
        left_idx = color_set[idx - 1] if idx > 0 else None
        right_idx = color_set[idx] if idx < len(color_set) else None
        self.spanner.add_node((node, 0), color=color)
        if left_idx is not None:
            self.spanner.add_edge((node,0), (left_idx, 0), weight=abs(node - left_idx))
        if right_idx is not None:
            self.spanner.add_edge((node,0), (right_idx, 0), weight=abs(node - right_idx))

def oned_list(points):
    """
    Builds a 1D spanner from a fixed list of points, then draws and exports it.

    :param points: List of 1D coordinates to add to the spanner, in order.
    """
    my_graph = OneDGraph()
    for point in points:
        my_graph.add_node(point)
    my_graph.t = stretch_factor(my_graph.spanner)
    my_graph.plotter.draw_graph(my_graph.spanner, half_circle=True, t=my_graph.t)
    my_graph.plotter.export_graph(my_graph.spanner, "spanner_output.pdf", half_circle=True, t=my_graph.t)
    plt.show(block=True)

def oned_loop():
    """
    Runs an interactive session that reads 1D points from the console,
    adding each to the spanner and redrawing until the user exits.
    """
    my_graph = OneDGraph()
    redraw_queue = queue.Queue()

    def input_loop():
        """
        Reads coordinate input from the console on a background thread,
        adding each valid point to the spanner and signaling the main
        thread to redraw. Exits on the first non-numeric input.
        """
        while True:
            user_input = input("Enter a node to add to the graph (n to exit):")
            try:
                node = float(user_input)
                if node in my_graph.graphS:
                    print('node already exists')
                else:
                    my_graph.add_node(node)
                    my_graph.t = stretch_factor(my_graph.spanner)
                    redraw_queue.put(True)
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