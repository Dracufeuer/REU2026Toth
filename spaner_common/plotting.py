import networkx as nx
from matplotlib import patches, pyplot as plt


class GraphPlotter:
    def __init__(self, figsize=(10, 4)):
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=figsize)
        plt.show(block=False)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)

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

    def draw_graph(self, G, half_circle=True):
        self.ax.clear()

        pos = {n: n for n in G.nodes()}  # node IS its own position now: (x, 0)

        node_colors = [G.nodes[n]['color'] for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=self.ax, node_size=300)
        nx.draw_networkx_labels(G, pos, ax=self.ax)

        for u, v in G.edges():
            x1, x2 = u[0], v[0]
            if x1 == x2:
                continue

            if half_circle:
                center_x = (x1 + x2) / 2
                diameter = abs(x2 - x1)

                arc = patches.Arc(
                    (center_x, 0),
                    width=diameter,
                    height=diameter,
                    angle=0,
                    theta1=0,
                    theta2=180,
                    edgecolor='gray',
                    lw=1.5,
                )
                self.ax.add_patch(arc)
            else:
                self.ax.plot([x1, x2], [0, 0], color='gray', lw=1.5, zorder=1)

        self.ax.axhline(0, color='black', linewidth=0.5, zorder=0)

        nodes_x = [n[0] for n in G.nodes()]
        if nodes_x:
            self.ax.set_xlim(min(nodes_x) - 1, max(nodes_x) + 1)

        if half_circle and G.edges():
            max_span = max(abs(u[0] - v[0]) for u, v in G.edges())
            self.ax.set_ylim(-1, max_span / 2 + 1)
        else:
            self.ax.set_ylim(-1, 1)

        self.ax.set_aspect('equal', adjustable='box')
        self.ax.axis('off')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)