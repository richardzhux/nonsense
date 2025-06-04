import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph
G = nx.DiGraph()

# Define nodes with descriptions
nodes = {
    "Sample": "Radioactive Sample\n(Gamma-ray source)",
    "Phototube": "Phototube Sensors\n(Detects gamma emissions)",
    "Oscilloscope": "Oscilloscope\n(Calibration, waveform analysis)",
    "Amplifier": "Signal Amplifier\n(Enhances weak signals)",
    "Fine-Tuner": "Signal Fine-Tuner\n(Filters noise, isolates peaks)",
    "Delay": "Delay Generator\n(Aligns signal peaks)",
    "Analyzer": "Multichannel Analyzer\n(Counts valid detection events)",
    "Counter": "Coincidence Counter\n(Detects simultaneous gamma events)"
}

# Add nodes to the graph
G.add_nodes_from(nodes.keys())

# Define edges (signal flow sequence)
edges = [
    ("Sample", "Phototube"),
    ("Phototube", "Oscilloscope"),
    ("Oscilloscope", "Amplifier"),
    ("Amplifier", "Fine-Tuner"),
    ("Fine-Tuner", "Delay"),
    ("Delay", "Analyzer"),
    ("Analyzer", "Counter")
]

# Add edges to the graph
G.add_edges_from(edges)

# Define a hierarchical layout
pos = nx.spring_layout(G, seed=42, k=0.8)  # Adjust spacing

# Create the figure
plt.figure(figsize=(10, 6))
nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=3500, edge_color="gray", font_size=8, font_weight="bold")

# Add descriptions as labels
labels = {node: desc for node, desc in nodes.items()}
nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)

# Save the figure as a high-resolution PNG
flowchart_path = "/Users/rx/Downloads"
plt.savefig(flowchart_path, dpi=300, bbox_inches="tight")
plt.show()

# Provide the file path for download
flowchart_path
