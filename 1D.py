import sortedcontainers as sc
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import threading
import queue

class OneDGraph:
    def __init__(self):
        self.spanner = nx.Graph()
        self.red = sc.SortedSet()
        self.blue = sc.SortedSet()
        self.graphS = sc.SortedSet()

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        plt.show(block=False)

        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)

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
            self.spanner.add_node(node, color='red')
        self.graphS.add(node)


    def connect_edge(self, node, color_set, color):
        idx = color_set.bisect_left(node)
        left_idx = color_set[idx - 1] if idx > 0 else None
        right_idx = color_set[idx] if idx < len(color_set) else None
        self.spanner.add_node(node, color=color)
        if left_idx is not None:
            self.spanner.add_edge(node, left_idx, weight=abs(node - left_idx))
        if right_idx is not None:
            self.spanner.add_edge(node, right_idx, weight=abs(node - right_idx))

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return  # ignore scrolls outside the plot area

        base_scale = 1.2
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata  # cursor's x position in data coordinates
        ydata = event.ydata

        if event.button == 'up':  # scroll up = zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':  # scroll down = zoom out
            scale_factor = base_scale
        else:
            return

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        self.fig.canvas.draw_idle()

    def draw_1d_graph(self):
        self.ax.clear()  # wipe previous drawing, but keep the same window

        G = self.spanner
        pos = {n: (n, 0) for n in G.nodes()}

        node_colors = [G.nodes[n]['color'] for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=self.ax, node_size=300)
        nx.draw_networkx_labels(G, pos, ax=self.ax)

        for u, v in G.edges():
            x1, x2 = pos[u][0], pos[v][0]
            mid_x = (x1 + x2) / 2
            height = abs(x2 - x1) * 0.3

            verts = [(x1, 0), (mid_x, height), (x2, 0)]
            codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
            path = Path(verts, codes)

            arc = patches.PathPatch(path, facecolor='none', edgecolor='gray', lw=1.5)
            self.ax.add_patch(arc)

        self.ax.axhline(0, color='black', linewidth=0.5, zorder=0)
        if G.edges():
            self.ax.set_ylim(-1, max(abs(u - v) for u, v in G.edges()) * 0.3 + 1)
        self.ax.axis('off')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

def main():
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
                    my_graph.add_node(node)       # safe: no GUI calls here
                    redraw_queue.put(True)         # just signal main thread to redraw
            except ValueError:
                print("not a number")
                break

    thread = threading.Thread(target=input_loop, daemon=True)
    thread.start()

    while thread.is_alive():
        try:
            redraw_queue.get(timeout=0.1)   # wait briefly for a signal
            my_graph.draw_1d_graph()         # actual drawing happens on MAIN thread
        except queue.Empty:
            pass
        plt.pause(0.05)

if __name__ == "__main__":
    main()