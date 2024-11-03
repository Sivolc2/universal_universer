from hypergraph import Hypergraph

def test_visualization():
    # Create a sample hypergraph
    h = Hypergraph()
    
    # Add some edges
    h.add_edge({'A', 'B', 'C'})
    h.add_edge({'B', 'D'})
    h.add_edge({'C', 'D', 'E'})
    h.add_edge({'A', 'E'})
    
    # Visualize it
    h.visualize('hypergraph.png')
    print("Hypergraph visualization saved to hypergraph.png")

if __name__ == "__main__":
    test_visualization() 