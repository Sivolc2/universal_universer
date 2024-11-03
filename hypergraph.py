import networkx as nx
import matplotlib.pyplot as plt
import random

class Hypergraph:
    def __init__(self):
        self.edges = set()
        self.nodes = set()
        
    def add_edge(self, edge):
        """Add a hyperedge (set of nodes)"""
        self.edges.add(frozenset(edge))
        self.nodes.update(edge)
    
    def remove_edge(self, edge):
        """Remove a hyperedge"""
        self.edges.remove(frozenset(edge))
        # Only remove nodes if they're not in any other edges
        for node in edge:
            if not any(node in e for e in self.edges):
                self.nodes.remove(node)
    
    def visualize(self, filename='hypergraph.png'):
        """Visualize hypergraph using networkx and matplotlib"""
        # Create a new graph
        G = nx.Graph()
        
        # Add all nodes
        G.add_nodes_from(self.nodes)
        
        # Create special nodes for hyperedges and connect them to their members
        edge_nodes = []
        for i, edge in enumerate(self.edges):
            edge_node = f'e{i}'  # Special node representing the hyperedge
            edge_nodes.append(edge_node)
            G.add_node(edge_node, node_type='hyperedge')
            # Connect the edge node to all nodes in the hyperedge
            for node in edge:
                G.add_edge(edge_node, node)
        
        # Set up the plot
        plt.figure(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(G)
        
        # Draw regular nodes
        nx.draw_networkx_nodes(G, pos, 
                             nodelist=[n for n in G.nodes() if n not in edge_nodes],
                             node_color='lightblue',
                             node_size=500)
        
        # Draw hyperedge nodes (smaller and different color)
        nx.draw_networkx_nodes(G, pos,
                             nodelist=edge_nodes,
                             node_color='red',
                             node_size=300,
                             node_shape='s')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos)
        
        # Add labels
        labels = {node: node for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels)
        
        plt.title("Hypergraph Visualization")
        plt.axis('off')
        
        # Save to file
        plt.savefig(filename)
        plt.close()
    
    def apply_rule(self, rule):
        """Apply a rewriting rule to this hypergraph"""
        left_side, right_side = rule
        matches = self.find_matches(left_side)
        if matches:
            self.rewrite(matches[0], right_side)
            return True
        return False
    
    def find_matches(self, pattern):
        """Find all subgraph matches for a pattern"""
        matches = []
        pattern_edges = [frozenset(edge) for edge in pattern]
        
        # For each possible starting edge
        for edge in self.edges:
            if len(edge) == len(pattern_edges[0]):
                # Try to match the rest of the pattern
                match = self._match_from_edge(edge, pattern_edges)
                if match:
                    matches.append(match)
        
        return matches
    
    def _match_from_edge(self, start_edge, pattern_edges):
        """Try to match pattern starting from a specific edge"""
        # This is a simplified version - would need more sophisticated
        # matching for variables and structural patterns
        matched_edges = {start_edge}
        node_mapping = {}
        
        # Map nodes from start edge to pattern
        pattern_nodes = list(pattern_edges[0])
        edge_nodes = list(start_edge)
        for i in range(len(edge_nodes)):
            node_mapping[pattern_nodes[i]] = edge_nodes[i]
        
        # Try to match remaining edges
        for pattern_edge in pattern_edges[1:]:
            found_match = False
            for edge in self.edges - matched_edges:
                if self._edge_matches(edge, pattern_edge, node_mapping):
                    matched_edges.add(edge)
                    found_match = True
                    break
            if not found_match:
                return None
        
        return matched_edges
    
    def _edge_matches(self, edge, pattern_edge, node_mapping):
        """Check if an edge matches a pattern edge given current node mapping"""
        if len(edge) != len(pattern_edge):
            return False
            
        # Check if edge nodes match pattern nodes according to mapping
        edge_nodes = list(edge)
        pattern_nodes = list(pattern_edge)
        
        for i in range(len(edge_nodes)):
            if pattern_nodes[i] in node_mapping:
                if node_mapping[pattern_nodes[i]] != edge_nodes[i]:
                    return False
            else:
                # New node in pattern - add to mapping
                node_mapping[pattern_nodes[i]] = edge_nodes[i]
        
        return True
    
    def rewrite(self, matched_edges, right_side):
        """Rewrite matched edges according to right side of rule"""
        # Remove matched edges
        for edge in matched_edges:
            self.remove_edge(edge)
        
        # Add new edges
        for new_edge in right_side:
            self.add_edge(new_edge)