import math
import numpy as np
import networkx as nx
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from scipy.spatial import cKDTree


class GraphPlotter:
    def __init__(self, figsize=(10, 4)):
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=figsize)
        plt.show(block=False)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.show_labels = True
        self.label_threshold = 700   # tune this; labels auto-hide above this many nodes

        self.edge_collection = LineCollection([], colors='green', linewidths=1.5, zorder=1)
        self.ax.add_collection(self.edge_collection)

        self.node_scatter = self.ax.scatter([], [], s=300, zorder=2)

        self.baseline_h = self.ax.axhline(0, color='black', linewidth=0.5, zorder=0)
        self.baseline_v = self.ax.axvline(0, color='black', linewidth=0.8, zorder=0)

        self.t_text = self.ax.text(
            0.02, 0.95, "", transform=self.ax.transAxes,
            fontsize=11, verticalalignment='top',
        )

        self._label_texts = []

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return  # ignore scrolls outside the plot area

        base_scale = 1.2
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata

        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
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

    def export_graph(self, G, filename, half_circle=False, t=None,
                      min_label_spacing_inches=0.35, font_size=6, dpi=300,
                      max_figsize=(80, 80)):
        nodes = list(G.nodes())
        n = len(nodes)
        if n == 0:
            return

        xs = np.fromiter((p[0] for p in nodes), dtype=float, count=n)
        ys = np.fromiter((p[1] for p in nodes), dtype=float, count=n)
        colors = [G.nodes[p]['color'] for p in nodes]

        if n > 1:
            coords = np.column_stack([xs, ys])
            tree = cKDTree(coords)
            dists, _ = tree.query(coords, k=2)
            nn_dists = dists[:, 1]
            nonzero = nn_dists[nn_dists > 0]
            typical_spacing = np.min(nonzero) if len(nonzero) else 1.0
        else:
            typical_spacing = 1.0

        inches_per_unit = min_label_spacing_inches / typical_spacing
        x_range = max(xs.max() - xs.min(), 1e-6)
        if half_circle:
            edges_for_sizing = list(G.edges())
            max_span = max((abs(u[0] - v[0]) for u, v in edges_for_sizing), default=0)
            y_range = max(max_span / 2, 1e-6)
        else:
            y_range = max(ys.max() - ys.min(), 1e-6)
        fig_w = min(max(x_range * inches_per_unit, 6), max_figsize[0])
        fig_h = min(max(y_range * inches_per_unit, 4), max_figsize[1])

        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.scatter(xs, ys, s=60, c=colors, zorder=2, edgecolors='black', linewidths=0.4, clip_on=False)

        edges = list(G.edges())
        segments = []
        if half_circle:
            arc_theta = np.linspace(0, math.pi, 20)
            for u, v in edges:
                x1, y1 = u
                x2, y2 = v
                if x1 == x2 and y1 == y2:
                    continue
                cx = (x1 + x2) / 2
                r = abs(x2 - x1) / 2
                segments.append(np.column_stack([cx + r * np.cos(arc_theta), r * np.sin(arc_theta)]))
        else:
            segments = [[u, v] for u, v in edges if u != v]
        ax.add_collection(LineCollection(segments, colors='green', linewidths=1.0, zorder=1))

        for i, p in enumerate(nodes, start=1):
            ax.annotate(str(i), p, fontsize=font_size, ha='center', va='center', zorder=3)

        ax.set_xlim(xs.min() - 1, xs.max() + 1)
        if half_circle:
            if edges:
                max_span = max(abs(u[0] - v[0]) for u, v in edges)
                ax.set_ylim(-1, max_span / 2 + 1)
            else:
                ax.set_ylim(-1, 1)
            ax.axis('off')
        else:
            ax.set_ylim(ys.min() - 1, ys.max() + 1)
        ax.set_aspect('equal', adjustable='box')
        if t is not None:
            ax.set_title(f"t = {t:.4f}")

        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    def draw_graph(self, G, half_circle=True, t=None):
        nodes = list(G.nodes())
        n = len(nodes)

        xs = np.fromiter((p[0] for p in nodes), dtype=float, count=n) if n else np.empty(0)
        ys = np.fromiter((p[1] for p in nodes), dtype=float, count=n) if n else np.empty(0)
        colors = [G.nodes[p]['color'] for p in nodes]

        self.node_scatter.set_offsets(np.column_stack([xs, ys]) if n else np.empty((0, 2)))
        self.node_scatter.set_color(colors)

        edges = list(G.edges())
        segments = []
        if half_circle:
            arc_theta = np.linspace(0, math.pi, 20)
            for u, v in edges:
                x1, y1 = u
                x2, y2 = v
                if x1 == x2 and y1 == y2:
                    continue
                center_x = (x1 + x2) / 2
                radius = abs(x2 - x1) / 2
                arc_x = center_x + radius * np.cos(arc_theta)
                arc_y = radius * np.sin(arc_theta)
                segments.append(np.column_stack([arc_x, arc_y]))
        else:
            for u, v in edges:
                if u == v:
                    continue
                segments.append([u, v])

        self.edge_collection.set_segments(segments)

        want_labels = self.show_labels and n <= self.label_threshold
        if want_labels:
            if len(self._label_texts) != n:
                for txt in self._label_texts:
                    txt.remove()
                self._label_texts = [
                    self.ax.text(p[0], p[1], str(i), fontsize=8,
                                 ha='center', va='center', zorder=3, clip_on=True)
                    for i, p in enumerate(nodes, start=1)
                ]
            else:
                for txt, p in zip(self._label_texts, nodes):
                    txt.set_position(p)
        elif self._label_texts:
            for txt in self._label_texts:
                txt.remove()
            self._label_texts = []

        if half_circle:
            self.baseline_v.set_visible(False)
            self.baseline_h.set_visible(True)
            self.ax.grid(False)
            self.ax.axis('off')
            if n:
                self.ax.set_xlim(xs.min() - 1, xs.max() + 1)
            if edges:
                max_span = max(abs(u[0] - v[0]) for u, v in edges)
                self.ax.set_ylim(-1, max_span / 2 + 1)
            else:
                self.ax.set_ylim(-1, 1)
        else:
            self.baseline_v.set_visible(True)
            self.baseline_h.set_visible(True)
            self.ax.axis('on')
            self.ax.grid(True, linestyle='--', alpha=0.3, zorder=-1)
            self.ax.set_axisbelow(True)
            if n:
                self.ax.set_xlim(xs.min() - 1, xs.max() + 1)
                self.ax.set_ylim(ys.min() - 1, ys.max() + 1)
            else:
                self.ax.set_xlim(-1, 1)
                self.ax.set_ylim(-1, 1)

        self.ax.set_aspect('equal', adjustable='box')

        if t is not None:
            self.t_text.set_text(f"t = {t:.4f}")

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.001)