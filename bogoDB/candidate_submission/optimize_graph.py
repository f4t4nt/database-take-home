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

    # Store initial graph as our reference for valid edges
    initial_edges = {}
    for node, edges in initial_graph.items():
        initial_edges[node] = dict(edges)

    # Create a copy of the initial graph to modify
    optimized_graph = {}
    for node, edges in initial_graph.items():
        optimized_graph[node] = dict(edges)

    # =============================================================
    # TODO: Implement your optimization strategy here
    # =============================================================
    #
    # Your goal is to optimize the graph structure to:
    # 1. Increase the success rate of queries
    # 2. Minimize the path length for successful queries
    #
    # You have access to:
    # - initial_graph: The current graph structure
    # - results: The results of running queries on the initial graph
    #
    # Query results contain:
    # - Each query's target node
    # - Whether the query was successful
    # - The path taken during the random walk
    #
    # Remember the constraints:
    # - max_total_edges: Maximum number of edges in the graph
    # - max_edges_per_node: Maximum edges per node
    # - All nodes must remain in the graph
    # - Edge weights must be positive and ≤ 10

    # ---------------------------------------------------------------
    # EXAMPLE: Simple strategy to meet edge count constraint
    # This is just a basic example - you should implement a more
    # sophisticated strategy based on query analysis!
    # ---------------------------------------------------------------

    ########################################################
    # Base solution (remove edges to satisfy constraints): #
    ########################################################

    # Count total edges in the initial graph
    total_edges = sum(len(edges) for edges in optimized_graph.values())

    # If we exceed the limit, we need to prune edges
    if total_edges > max_total_edges:
        print(
            f"Initial graph has {total_edges} edges, need to remove {total_edges - max_total_edges}"
        )

        # Example pruning logic (replace with your optimized strategy)
        edges_to_remove = total_edges - max_total_edges
        removed = 0

        # Sort nodes by number of outgoing edges (descending)
        nodes_by_edge_count = sorted(
            optimized_graph.keys(), key=lambda n: len(optimized_graph[n]), reverse=True
        )

        # Remove edges from nodes with the most connections first
        for node in nodes_by_edge_count:
            if removed >= edges_to_remove:
                break

            # As a simplistic example, remove the edge with lowest weight
            if len(optimized_graph[node]) > 1:  # Ensure node keeps at least one edge
                # Find edge with minimum weight
                min_edge = min(optimized_graph[node].items(), key=lambda x: x[1])
                del optimized_graph[node][min_edge[0]]
                removed += 1
    
    #######################################
    # Basic simulated annealing solution: #
    #######################################
    
    # Simulated annealing parameters
    TEMPERATURE = 1.0
    COOLING_RATE = 0.7
    MIN_TEMPERATURE = 0.01
    MAX_ITERATIONS = 10
    
    # Node preference parameters
    NODE_PREFERENCE_FACTOR = 1.5  # Node 0 is 1.5x more likely than node 499
    
    # Pre-compute node weights
    node_weights = {}
    for n in range(num_nodes):
        # Exponentially scale weight from 1.0 (node 499) to (1 + factor) (node 0)
        weight = (1 + NODE_PREFERENCE_FACTOR) ** ((num_nodes - 1 - n) / (num_nodes - 1))
        node_weights[str(n)] = weight
    
    # Pre-compute all possible edge weights from initial graph
    edge_weight_dict = {}  # (source, target) -> weight
    for source, edges in initial_edges.items():
        for target in edges:
            weight = min(node_weights[source], node_weights[target])
            edge_weight_dict[(source, target)] = weight
    
    with open(os.path.join(project_dir, "data", "queries.json"), "r") as f:
        queries = json.load(f)
    
    # Count query frequencies to focus on important nodes
    query_counts = Counter(queries)
    important_nodes = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Import here so it's clear what we're using
    from scripts.random_walk import BogoDB, run_queries

    def get_metrics(graph, queries):
        """Run queries on a graph and return success rate and median path length"""
        # Create BogoDB instance and run queries
        db = BogoDB(graph)
        results = run_queries(db, queries)
        details = results.get("detailed_results", [])
        
        # Get success rate
        success = sum(1 for r in details if r.get("success", False) or r.get("is_success", False))
        rate = success / len(details) if details else 0
        
        # Get median path length
        lengths = [
            r.get("median_path_length", float("inf")) 
            for r in details 
            if (r.get("success", False) or r.get("is_success", False)) 
            and r.get("median_path_length", float("inf")) != float("inf")
        ]
        median = statistics.median(lengths) if lengths else float("inf")
        
        return rate, median
    
    # Get initial graph's baseline metrics
    initial_rate, initial_median = get_metrics(initial_graph, queries)
    print(f"Initial success rate: {initial_rate:.4f}, median path length: {initial_median:.2f}")
    
    def calculate_score(graph, results):
        # Get metrics for new graph
        optimized_rate, optimized_median = get_metrics(graph, queries)
        
        # Calculate combined score using exact same formula as evaluate_graph.py
        if optimized_rate == 0:
            # If nothing succeeds, score is 0
            combined_score = 0
        elif initial_median == float("inf") or optimized_median == float("inf"):
            # If we can't compute improvement, use only success rate
            combined_score = optimized_rate
        else:
            # Calculate a multiplier based on path length improvement
            path_multiplier = np.log1p(initial_median / optimized_median)
            combined_score = optimized_rate * (1 + path_multiplier)
            
        return combined_score

    def swap_single_edge(graph):
        """Make a single edge swap: remove one edge and add a different valid edge"""
        new_graph = {node: dict(edges) for node, edges in graph.items()}
        
        # 1. SELECT AND REMOVE AN EDGE FROM CURRENT GRAPH
        # Find all edges that can be safely removed (leaving at least one edge per node)
        removable_edges = []
        edge_weights_list = []  # Weights for selection probability
        for node, edges in new_graph.items():
            if len(edges) > 1:  # Only consider nodes with more than one edge
                for target, _ in edges.items():
                    removable_edges.append((node, target))
                    # Use pre-computed edge weight
                    edge_weights_list.append(edge_weight_dict[(node, target)])
        
        if not removable_edges:
            return new_graph
            
        # Remove a random edge using weighted selection
        chosen_idx = random.choices(range(len(removable_edges)), weights=edge_weights_list, k=1)[0]
        source, target = removable_edges[chosen_idx]
        del new_graph[source][target]
        
        # 2. ADD AN EDGE FROM INITIAL GRAPH THAT'S NOT IN CURRENT GRAPH
        # Find all possible edges from initial graph that we could add
        possible_edges = []
        add_weights = []  # Weights for selection probability
        for node, edges in initial_edges.items():
            # Skip if node already has max edges
            if len(new_graph[node]) >= max_edges_per_node:
                continue
            
            for target, weight in edges.items():
                # Check if this edge exists in current graph
                if target not in new_graph[node]:
                    possible_edges.append((node, target, weight))
                    # Use pre-computed edge weight
                    add_weights.append(edge_weight_dict[(node, target)])
        
        if possible_edges:
            # Add a random valid edge using weighted selection
            chosen_idx = random.choices(range(len(possible_edges)), weights=add_weights, k=1)[0]
            new_source, new_target, weight = possible_edges[chosen_idx]
            new_graph[new_source][new_target] = weight
            
        return new_graph
        
    def modify_graph(graph):
        """Make multiple random edge swaps for more chaotic transitions"""
        new_graph = {node: dict(edges) for node, edges in graph.items()}
        
        # Make multiple swaps
        num_swaps = random.randint(10, 50)  # Random number of swaps
        for _ in range(num_swaps):
            new_graph = swap_single_edge(new_graph)
            
            # Verify we haven't broken any constraints
            if not verify_constraints(new_graph, max_edges_per_node, max_total_edges):
                # If we broke constraints, revert to previous state
                return graph
                
        return new_graph
    
    # Run simulated annealing
    current_graph = optimized_graph.copy()
    best_graph = current_graph.copy()
    current_score = calculate_score(current_graph, results)
    best_score = current_score
    temperature = TEMPERATURE
    
    print(f"Starting simulated annealing with initial score: {current_score:.4f}")
    
    for iteration in range(MAX_ITERATIONS):
        # Make a random modification
        new_graph = modify_graph(current_graph)
        
        # Skip if constraints not met
        if not verify_constraints(new_graph, max_edges_per_node, max_total_edges):
            continue
        
        # Calculate new score
        new_score = calculate_score(new_graph, results)
        
        # Calculate acceptance probability
        delta = new_score - current_score
        acceptance_prob = 1.0 if delta > 0 else np.exp(delta / temperature)
        
        # Accept or reject new solution
        if random.random() < acceptance_prob:
            current_graph = new_graph
            current_score = new_score
            
            # Update best solution if this is better
            if current_score > best_score:
                best_score = current_score
                best_graph = current_graph.copy()
                print(f"New best score at iteration {iteration}: {best_score:.4f}")
        
        # Cool down
        temperature *= COOLING_RATE
        if temperature < MIN_TEMPERATURE:
            print("Reached minimum temperature, stopping...")
            break
    
    print(f"Final best score: {best_score:.4f}")
    optimized_graph = best_graph
    
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
