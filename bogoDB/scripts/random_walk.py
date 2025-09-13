#!/usr/bin/env python3
import json
import random
import numpy as np
import statistics
import multiprocessing as mp
from tqdm import tqdm
from functools import partial
from typing import List, Dict, Tuple, Optional, Union, Any
from scripts.constants import (
    MAX_DEPTH,
    NUM_WALKS_PER_QUERY,
    RANDOM_SEED,
    USE_MULTIPROCESSING,
    NUM_PROCESSES,
    INITIAL_GRAPH_FILE,
    QUERIES_FILE,
    INITIAL_RESULTS_FILE,
)


class BogoDB:
    """
    A database that implements random walk-based queries on a weighted graph.
    """

    def __init__(self, graph_source, max_depth: int = MAX_DEPTH):
        """
        Initialize the BogoDB with a graph.

        Args:
            graph_source: Either a path to a JSON file or a dictionary containing the graph
            max_depth: Maximum steps in a random walk before giving up
        """
        self.graph = self._load_graph(graph_source)
        self.max_depth = max_depth
        self.nodes = list(self.graph.keys())

        # Set random seeds for reproducibility
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

    def _load_graph(self, graph_source) -> Dict:
        """Load graph from file or dictionary."""
        # If graph_source is already a dictionary, return it directly
        if isinstance(graph_source, dict):
            return graph_source

        # Otherwise, assume it's a file path
        try:
            with open(graph_source, "r") as f:
                return json.load(f)
        except (TypeError, FileNotFoundError) as e:
            print(f"Error loading graph: {e}")
            raise ValueError(f"Failed to load graph from {graph_source}") from e

    def _single_query(
        self, target_node: int
    ) -> Tuple[bool, List[int], Union[int, float]]:
        """
        Perform a single random walk query to find a target node.

        Args:
            target_node: The node ID to find

        Returns:
            Tuple of (success, path, steps)
            - success: Whether the target was found
            - path: List of node IDs visited during the walk
            - steps: Number of steps taken in the walk (float('inf') if not found)
        """
        target_node_str = str(target_node)

        # Start at a random node
        current_node = random.choice(self.nodes)
        path = [int(current_node)]

        # Perform random walk
        for step in range(self.max_depth):
            # Check if we found the target
            if current_node == target_node_str:
                return True, path, step + 1

            # Get neighbors and their weights
            neighbors = self.graph.get(current_node, {})

            # If no neighbors, restart from a different random node
            if not neighbors:
                current_node = random.choice(self.nodes)
                path.append(int(current_node))
                continue

            # Select next node based on edge weights
            neighbor_ids = list(neighbors.keys())
            weights = list(neighbors.values())

            # Normalize weights to probabilities
            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]

            # Choose next node probabilistically
            current_node = np.random.choice(neighbor_ids, p=probabilities)
            path.append(int(current_node))

        # If we reach here, we didn't find the target within max_depth
        return False, path, float("inf")

    def query(self, target_node: int, num_walks: int = NUM_WALKS_PER_QUERY) -> Dict:
        """
        Perform multiple random walk queries and return results.

        Args:
            target_node: The node ID to find
            num_walks: Number of random walks to perform

        Returns:
            Dictionary with query results:
            - is_success: True if median path length is finite
            - median_path_length: Median length of successful paths or inf
            - paths: List of (success, path, steps) for all random walks
        """
        paths = []

        # Perform multiple random walks
        for _ in range(num_walks):
            success, path, steps = self._single_query(target_node)
            paths.append((success, path, steps))

        # Calculate median steps (using only successful walks if there are any)
        successful_steps = [steps for success, _, steps in paths if success]

        # Only report success if we have finite median path length
        if successful_steps:
            median_steps = statistics.median(successful_steps)
            is_success = True
        else:
            median_steps = float("inf")
            is_success = False

        return {
            "target": target_node,
            "is_success": is_success,
            "median_path_length": median_steps,
            "paths": paths,
        }


def _process_query(db: BogoDB, query: int) -> Dict:
    """
    Process a single query for multiprocessing.

    Args:
        db: BogoDB instance
        query: The node ID to query

    Returns:
        Dictionary with query results
    """
    return db.query(query)


def run_queries(db: BogoDB, queries: List[int]) -> Dict:
    """
    Run a set of queries and collect statistics.

    Args:
        db: BogoDB instance
        queries: List of node IDs to query

    Returns:
        Dictionary with query statistics
    """
    results = {
        "success_rate": 0,
        "median_path_length": 0,
        "path_length_distribution": {},
        "detailed_results": [],
    }

    # Run queries with progress bar and optional multiprocessing
    if USE_MULTIPROCESSING:
        num_processes = NUM_PROCESSES if NUM_PROCESSES > 0 else None
        with mp.Pool(processes=num_processes) as pool:
            process_query_fn = partial(_process_query, db)
            detailed_results = list(
                tqdm(
                    pool.imap(process_query_fn, queries),
                    total=len(queries),
                    desc="Processing queries",
                    unit="query",
                )
            )
    else:
        detailed_results = []
        for query in tqdm(queries, desc="Processing queries", unit="query"):
            detailed_results.append(_process_query(db, query))

    results["detailed_results"] = detailed_results

    # Calculate summary statistics
    successful_queries = sum(1 for r in detailed_results if r["is_success"])
    path_lengths = [
        r["median_path_length"]
        for r in detailed_results
        if r["is_success"] and r["median_path_length"] != float("inf")
    ]

    # Update path length distribution
    for result in detailed_results:
        if result["is_success"]:
            steps = result["median_path_length"]
            steps_bin = round(steps) if steps != float("inf") else "inf"
            if steps_bin in results["path_length_distribution"]:
                results["path_length_distribution"][steps_bin] += 1
            else:
                results["path_length_distribution"][steps_bin] = 1

    # Calculate summary statistics
    if successful_queries > 0:
        results["success_rate"] = successful_queries / len(queries)
        if path_lengths:
            results["median_path_length"] = statistics.median(path_lengths)

    return results


def print_results_summary(results: Dict) -> None:
    """
    Print a human-friendly summary of the query results.

    Args:
        results: Dictionary with query statistics
    """
    success_rate = results.get("success_rate", 0) * 100
    median_path = results.get("median_path_length", float("inf"))

    print("\n" + "=" * 50)
    print(f"{'QUERY RESULTS SUMMARY':^50}")
    print("=" * 50)

    print(f"\n✓ Success rate: {success_rate:.1f}%")
    if median_path != float("inf"):
        print(f"🛣️  Median path length: {median_path:.2f} steps")
    else:
        print(f"🛣️  Median path length: ∞ (could not reach targets)")

    # Distribution summary
    successful_queries = sum(1 for r in results["detailed_results"] if r["is_success"])
    total_queries = len(results["detailed_results"])

    print(f"\n📊 QUERIES: {successful_queries}/{total_queries} successful")

    # Print path length ranges if we have successful queries
    if successful_queries > 0 and median_path != float("inf"):
        path_lengths = [
            r["median_path_length"]
            for r in results["detailed_results"]
            if r["is_success"] and r["median_path_length"] != float("inf")
        ]

        if path_lengths:
            min_path = min(path_lengths)
            max_path = max(path_lengths)
            print(f"📏 Path length range: {min_path:.1f} - {max_path:.1f} steps")
            print(f"   (only considers queries with finite median path lengths)")

    print("=" * 50)


if __name__ == "__main__":
    # Load queries
    with open(QUERIES_FILE, "r") as f:
        queries = json.load(f)

    # Initialize database with the initial graph
    db = BogoDB(INITIAL_GRAPH_FILE)

    # Run queries and get results
    print("\nRunning queries with multiple random walks per query...")
    results = run_queries(db, queries)

    # Print summary statistics
    print_results_summary(results)

    # Save results
    with open(INITIAL_RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to {INITIAL_RESULTS_FILE}")
