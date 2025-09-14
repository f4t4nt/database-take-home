## Solution 

### Approach & Analysis

The 200 queries mostly target low-numbered nodes (0-99). Only 37 unique nodes are queried. Initial median path length is 446. Key insights:

- Random walks are weighted, but this doesn't matter for loop solutions
- In a loop, each node has one outgoing edge, so weights don't matter
- Graph topology matters most - minimize distances between queried nodes
- With max 1000 edges and 500 nodes, single loop uses just 1 edge per node (500 total)
- Strong connectivity is essential (every node must be reachable from every other)

### Optimization Strategy

After testing multiple approaches, I found that a simple sequential ordering works best:

1. **Sequential loop**: Nodes ordered 0-1-2-3-4... (not randomized)
2. **Top-100 shortcuts**: Each node connects to the next top-100 node in the loop
3. **Weighted edges**: Low weight (0.1) for next node, weight 1.0 for top-100 jumps
4. **Generalizable**: Uses top-100 instead of specific query nodes to avoid overfitting

Sequential ordering keeps frequently queried nodes (0-99) close together, minimizing path lengths.

### Implementation

The approach:

```python
# Sequential loop construction:
# 1. Create simple sequential ordering: [0, 1, 2, ..., 499]
# 2. Connect each node to the next node in sequence
# 3. Add shortcuts from each node to the next top-100 node
```

Key decisions:
- Each node has 1-2 edges: next node (0.1 weight) and/or next top-100 (1.0 weight)
- If next node is already top-100, only one edge with weight 1.0
- 900 total edges used, max 2 per node

### Results

**Performance improvement: 98.2%**
- Initial median path length: 446.0
- Optimized median path length: 8.0
- Initial success rate: 80.5%
- Optimized success rate: 100% (all queries found paths)
- Success rate improvement: 19.5 percentage points
- Graph constraints: 900 edges (90% of limit), max 2 edges/node, valid weights

Sequential ordering with top-100 shortcuts dramatically reduces path lengths while maintaining full connectivity.

### Trade-offs & Limitations

**Trade-offs:**
- Focuses on queried nodes, may hurt connectivity for others
- Fixed structure won't adapt to different query patterns
- Simple approach, not guaranteed optimal

**Limitations:**
- More complex algorithms might do better
- Only considers queried vs non-queried, not frequency
- Single loop may not work for all query patterns

### Iteration Journey

My approach evolved significantly over the development period:

1. **0-2 hours**: Built simulated annealing with edge swapping. Treated it as selecting edges from the initial graph. Slow and didn't improve much.

2. **2 hour mark**: Realized we can build any graph from scratch instead of using the initial graph. Changed from edge selection to graph design.

3. **2-3 hours**: Started building graphs from scratch. Tried different approaches, thought two loops would work well.

4. **4-4.5 hours**: Dropped simulated annealing. Used heuristic that spaces queried nodes evenly. Got 87% improvement with single loop.

5. **Final iteration**: Tested different orderings (interleaved vs sequential). Sequential ordering (0-1-2-3...) performed best with 98.2% improvement.

The journey taught me that sometimes the best solution comes from questioning initial assumptions and that simple, well-motivated approaches can outperform complex algorithms. I've done an NP-hard graph partitioning problem (https://github.com/f4t4nt/cs170-project) before where simulated annealing + genetic algorithm worked ridiculously well, but here a simple heuristic was best.

### Timeline

10:20AM: started setting up local copy of repo

10:33AM: everything set up on Windows, ran base solution

10:41AM: switched to WSL successfully

10:50AM: finished basic analysis of question, beginning naive simulated annealing approach

11:33AM: completed naive simulated annealing approach, testing locally
- prunes edges with given solution
- swaps included/excluded edges randomly with decaying temperature
- really slow, plenty of room to improve but things seem to be working

12:05PM: added timestamped results tracking to easily check for future improvement

12:25PM: exponentially weighted nodes (edges connected to smaller nodes are more likely to be deleted / added)

12:25PM: realized edge weights AND edges are probably modifiable (we don't need to be choosing subset of edges from initial graph)

**2 HOUR MARK**

12:25-12:55PM: lunch

12:55PM: began creating own seed graph instead of relying on initial graph
- edge weights weighted by target node ID (lower ID = higher weight)

1:18PM: realized two loops is probably really good
- used this for seed graph for simulated annealing

2:05PM: realizing simulated annealing isn't able to improve the seed graph much, thinking if I should just try a better heuristic

2:45PM: tried a heuristic that makes sense, could obviously randomize better but this seems much more motivated and better than a simulated annealing approach or another random search

3:00PM: single loop works even better than double loop lol

7:19PM: came up with an idea of skipping connections while out running, came back and implemented it - 87% improvement!

---

* Be concise but thorough - aim for 500-1000 words total
* Include specific data and metrics where relevant
* Explain your reasoning, not just what you did