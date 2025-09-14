#!/usr/bin/env python3
import json
import os
import sys
import random
import numpy as np
import statistics
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

# Add project root to path to import scripts
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)

# Import constants
from scripts.constants import (
    NUM_NODES,
    MAX_EDGES_PER_NODE,
    MAX_TOTAL_EDGES,
)


def load_graph(graph_file):
    """Load graph from a JSON file."""
    with open(graph_file, "r") as f:
        return json.load(f)


def load_results(results_file):
    """Load query results from a JSON file."""
    with open(results_file, "r") as f:
        return json.load(f)


def save_graph(graph, output_file):
    """Save graph to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(graph, f, indent=2)


def verify_constraints(graph, max_edges_per_node, max_total_edges):
    """Verify that the graph meets all constraints."""
    # Check total edges
    total_edges = sum(len(edges) for edges in graph.values())
    if total_edges > max_total_edges:
        print(
            f"WARNING: Graph has {total_edges} edges, exceeding limit of {max_total_edges}"
        )
        return False

    # Check max edges per node
    max_node_edges = max(len(edges) for edges in graph.values())
    if max_node_edges > max_edges_per_node:
        print(
            f"WARNING: A node has {max_node_edges} edges, exceeding limit of {max_edges_per_node}"
        )
        return False

    # Check all nodes are present
    if len(graph) != NUM_NODES:
        print(f"WARNING: Graph has {len(graph)} nodes, should have {NUM_NODES}")
        return False

    # Check edge weights are valid (between 0 and 10)
    for node, edges in graph.items():
        for target, weight in edges.items():
            if weight <= 0 or weight > 10:
                print(f"WARNING: Edge {node} -> {target} has invalid weight {weight}")
                return False

    return True


def optimize_graph(
    initial_graph,
    results,
    num_nodes=NUM_NODES,
    max_total_edges=int(MAX_TOTAL_EDGES),
    max_edges_per_node=MAX_EDGES_PER_NODE,
):
    """
    Optimize the graph to improve random walk query performance.

    Args:
        initial_graph: Initial graph adjacency list
        results: Results from queries on the initial graph
        num_nodes: Number of nodes in the graph
        max_total_edges: Maximum total edges allowed
        max_edges_per_node: Maximum edges per node

    Returns:
        Optimized graph
    """
    print("Starting graph optimization...")

    # Load queries
    with open(os.path.join(project_dir, "data", "queries.json"), "r") as f:
        queries = json.load(f)
    
    # Get queried nodes and sort remaining by value
    queried_nodes = sorted(set(queries))  # Unique queried nodes
    non_queried = [n for n in range(num_nodes) if n not in queried_nodes]
    
    # Split non-queried into low-valued (important) and rest
    low_valued_cutoff = 100  # Consider nodes 0-99 as low-valued/important
    low_valued_non_queried = [n for n in non_queried if n < low_valued_cutoff]
    remaining_nodes = [n for n in non_queried if n >= low_valued_cutoff]
    
    print(f"Queried nodes: {len(queried_nodes)}")
    print(f"Low-valued non-queried: {len(low_valued_non_queried)}")
    print(f"Remaining nodes: {len(remaining_nodes)}")
    
    # Create single optimized loop
    loop = [None] * num_nodes
    
    # 1. Place queried nodes evenly throughout the loop
    if queried_nodes:
        spacing = num_nodes / len(queried_nodes)
        for i, node in enumerate(queried_nodes):
            pos = int(i * spacing) % num_nodes
            loop[pos] = node
    
    # 2. Place low-valued non-queried nodes evenly with offset
    if low_valued_non_queried:
        spacing = num_nodes / len(low_valued_non_queried)
        for i, node in enumerate(low_valued_non_queried):
            pos = int((i * spacing + 20) % num_nodes)  # offset by 20 to avoid clustering
            # Find next empty position if collision
            while loop[pos] is not None:
                pos = (pos + 1) % num_nodes
            loop[pos] = node
    
    # 3. Fill remaining positions with random permutation
    shuffled_remaining = remaining_nodes.copy()
    random.shuffle(shuffled_remaining)
    remaining_iter = iter(shuffled_remaining)
    
    for i in range(num_nodes):
        if loop[i] is None:
            loop[i] = next(remaining_iter)
    
    # Build graph from single loop with top-100 shortcuts
    optimized_graph = {str(i): {} for i in range(num_nodes)}
    top100_nodes = set(range(100))  # Nodes 0-99 are important
    
    # Add edges: next node and/or next top-100 node
    for i in range(num_nodes):
        source = loop[i]
        next_node = loop[(i + 1) % num_nodes]
        
        # If next node is top-100, use higher weight
        if next_node in top100_nodes:
            optimized_graph[str(source)][str(next_node)] = 1.0
        else:
            # Next node is not top-100, add it with low weight
            optimized_graph[str(source)][str(next_node)] = 0.1
            
            # Also find and add next top-100 node
            for j in range(2, num_nodes):
                next_top100 = loop[(i + j) % num_nodes]
                if next_top100 in top100_nodes:
                    optimized_graph[str(source)][str(next_top100)] = 1.0
                    break
    
    total_edges = sum(len(edges) for edges in optimized_graph.values())
    print(f"Total edges: {total_edges}")
    
    # =============================================================
    # End of your implementation
    # =============================================================

    # Verify constraints
    if not verify_constraints(optimized_graph, max_edges_per_node, max_total_edges):
        print("WARNING: Your optimized graph does not meet the constraints!")
        print("The evaluation script will reject it. Please fix the issues.")

    return optimized_graph


if __name__ == "__main__":
    # Get file paths
    initial_graph_file = os.path.join(project_dir, "data", "initial_graph.json")
    results_file = os.path.join(project_dir, "data", "initial_results.json")
    output_file = os.path.join(
        project_dir, "candidate_submission", "optimized_graph.json"
    )

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Loading initial graph from {initial_graph_file}")
    initial_graph = load_graph(initial_graph_file)

    print(f"Loading query results from {results_file}")
    results = load_results(results_file)

    print("Optimizing graph...")
    optimized_graph = optimize_graph(initial_graph, results)

    print(f"Saving optimized graph to {output_file}")
    save_graph(optimized_graph, output_file)

    print("Done! Optimized graph has been saved.")
