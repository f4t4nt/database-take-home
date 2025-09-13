## Solution 

### Approach & Analysis

The 200 queries mostly target low-numbered nodes (0-99). Only 37 unique nodes are queried. Initial median path length is 446. Key insights:

- Random walks are weighted, but this doesn't matter for loop solutions
- In a loop, each node has one outgoing edge, so weights don't matter
- Graph topology matters most - minimize distances between queried nodes
- With max 1000 edges and 500 nodes, single loop uses just 1 edge per node (500 total)
- Strong connectivity is essential (every node must be reachable from every other)

### Optimization Strategy

I used a single loop that positions nodes based on query frequency:

1. **Single cycle**: 500 edges connecting all nodes in a loop
2. **Even spacing**: Queried nodes spread evenly around the loop
3. **Offset placement**: Low-valued nodes positioned with offset to avoid clusters
4. **Single beats dual**: Single loop has shorter paths than dual loops

Tested adding skip connections (i→i+k) but the basic single loop performed best. Skip connections create longer alternative paths that hurt performance.

This spreads queried nodes around the loop, reducing path lengths.

### Implementation

The approach:

```python
# Single loop construction:
# 1. Space 37 queried nodes evenly around the 500-node loop
# 2. Place 63 low-valued non-queried nodes with offset to avoid clusters  
# 3. Fill remaining 400 positions with random permutation
# 4. Connect each node to the next, forming a Hamiltonian cycle
```

Key decisions:
- Simple cycle - each node connects to the next node
- Handle queried (37), low-valued (63), and remaining (400) nodes separately

### Results

**Performance improvement: 44.4%**
- Initial median path length: 446.0
- Optimized median path length: 248.0
- Initial success rate: 80.5%
- Optimized success rate: 100% (all queries found paths)
- Success rate improvement: 19.5 percentage points
- Graph constraints: 500 edges (50% of limit), max 1 edge/node, valid weights

Single loop reduces path lengths by spacing nodes well. Uses only half the allowed edges.

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

My approach evolved significantly over the ~4.5 hour development period:

1. **0-2 hours**: Built simulated annealing with edge swapping. Treated it as selecting edges from the initial graph. Slow and didn't improve much.

2. **2 hour mark**: Realized we can build any graph from scratch instead of using the initial graph. Changed from edge selection to graph design.

3. **2-3 hours**: Started building graphs from scratch. Tried different approaches, thought two loops would work well.

4. **4-4.5 hours**: Dropped simulated annealing. Used simple heuristic that spaces queried nodes evenly. Single loop beat dual loops by 44%.

The journey taught me that sometimes the best solution comes from questioning initial assumptions (working with the given graph) and that simple, well-motivated heuristics can outperform complex optimization algorithms.

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

---

* Be concise but thorough - aim for 500-1000 words total
* Include specific data and metrics where relevant
* Explain your reasoning, not just what you did