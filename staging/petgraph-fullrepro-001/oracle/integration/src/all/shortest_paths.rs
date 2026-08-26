// Shortest-path algorithms as agreeing projections of one edge set.
mod shortest_paths {
    use std::collections::{HashSet, VecDeque};

    use petgraph::algo::{astar, bellman_ford, dijkstra, has_path_connecting};
    use petgraph::graph::{DiGraph, NodeIndex};
    use petgraph::visit::EdgeFiltered;

    // Weighted road net: 0->1 (2), 0->2 (7), 1->2 (3), 1->3 (8), 2->3 (1),
    // 3->4 (2), 2->4 (12); node 5 is unreachable from 0 but reaches 4.
    fn roads() -> DiGraph<(), u32> {
        let mut g: DiGraph<(), u32> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..6).map(|_| g.add_node(())).collect();
        for (a, b, w) in [
            (0usize, 1usize, 2u32),
            (0, 2, 7),
            (1, 2, 3),
            (1, 3, 8),
            (2, 3, 1),
            (3, 4, 2),
            (2, 4, 12),
            (5, 4, 1),
        ] {
            g.add_edge(n[a], n[b], w);
        }
        g
    }

    #[test]
    fn generated_dijkstra_unit_costs_equal_bfs_depth() {
        let g = roads();
        let start = NodeIndex::new(0);
        let unit = dijkstra(&g, start, None, |_| 1usize);
        // Manual breadth-first layering over the same neighbor projection.
        let mut depth = vec![usize::MAX; g.node_count()];
        depth[start.index()] = 0;
        let mut queue = VecDeque::from([start]);
        while let Some(n) = queue.pop_front() {
            for m in g.neighbors(n) {
                if depth[m.index()] == usize::MAX {
                    depth[m.index()] = depth[n.index()] + 1;
                    queue.push_back(m);
                }
            }
        }
        for n in g.node_indices() {
            match unit.get(&n) {
                Some(cost) => assert_eq!(*cost, depth[n.index()], "node {:?}", n),
                None => assert_eq!(depth[n.index()], usize::MAX, "node {:?}", n),
            }
        }
    }

    #[test]
    fn generated_astar_zero_heuristic_matches_dijkstra() {
        let g = roads();
        let start = NodeIndex::new(0);
        let costs = dijkstra(&g, start, None, |e| *e.weight());
        for goal in g.node_indices() {
            let found = astar(&g, start, |n| n == goal, |e| *e.weight(), |_| 0);
            match costs.get(&goal) {
                Some(cost) => assert_eq!(found.map(|(c, _)| c), Some(*cost), "goal {:?}", goal),
                None => assert!(found.is_none(), "goal {:?}", goal),
            }
        }
    }

    #[test]
    fn generated_astar_path_is_valid_walk() {
        let g = roads();
        let start = NodeIndex::new(0);
        let goal = NodeIndex::new(4);
        let (total, path) = astar(&g, start, |n| n == goal, |e| *e.weight(), |_| 0).unwrap();
        assert_eq!(path.first(), Some(&start));
        assert_eq!(path.last(), Some(&goal));
        let mut walked = 0u32;
        for pair in path.windows(2) {
            let e = g.find_edge(pair[0], pair[1]).expect("path edge must exist");
            walked += *g.edge_weight(e).unwrap();
        }
        assert_eq!(walked, total);
        assert_eq!(total, 8); // 0 ->(2) 1 ->(3) 2 ->(1) 3 ->(2) 4
        assert_eq!(path.len(), 5);
    }

    #[test]
    fn generated_astar_admissible_heuristic_same_cost() {
        let g = roads();
        let start = NodeIndex::new(0);
        let goal = NodeIndex::new(4);
        // Remaining-cost lower bound: 0 at the goal, 1 elsewhere (all
        // weights are >= 1), never overestimates.
        let (with_h, _) = astar(
            &g,
            start,
            |n| n == goal,
            |e| *e.weight(),
            |n| if n == goal { 0 } else { 1 },
        )
        .unwrap();
        let (zero_h, _) = astar(&g, start, |n| n == goal, |e| *e.weight(), |_| 0).unwrap();
        assert_eq!(with_h, zero_h);
    }

    #[test]
    fn generated_bellman_ford_agrees_with_dijkstra() {
        // Same structure as roads() but with float weights.
        let mut g: DiGraph<(), f64> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..6).map(|_| g.add_node(())).collect();
        for (a, b, w) in [
            (0usize, 1usize, 2.0f64),
            (0, 2, 7.0),
            (1, 2, 3.0),
            (1, 3, 8.0),
            (2, 3, 1.0),
            (3, 4, 2.0),
            (2, 4, 12.0),
            (5, 4, 1.0),
        ] {
            g.add_edge(n[a], n[b], w);
        }
        let start = n[0];
        let paths = bellman_ford(&g, start).unwrap();
        let costs = dijkstra(&g, start, None, |e| *e.weight());
        for node in g.node_indices() {
            match costs.get(&node) {
                Some(c) => assert_eq!(paths.distances[node.index()], *c, "node {:?}", node),
                None => assert!(paths.distances[node.index()].is_infinite()),
            }
        }
        // Predecessor chain from node 4 walks back to the source with
        // distances decreasing by the connecting edge weight.
        let mut cur = n[4];
        let mut hops = 0;
        while let Some(prev) = paths.predecessors[cur.index()] {
            let e = g.find_edge(prev, cur).unwrap();
            let w = *g.edge_weight(e).unwrap();
            assert_eq!(
                paths.distances[prev.index()] + w,
                paths.distances[cur.index()]
            );
            cur = prev;
            hops += 1;
        }
        assert_eq!(cur, start);
        assert_eq!(hops, 4);
    }

    #[test]
    fn generated_edge_filtered_dijkstra_matches_subgraph() {
        let g = roads();
        let start = NodeIndex::new(0);
        // Keep only edges of weight < 5 in the view.
        let view = EdgeFiltered::from_fn(&g, |e| *e.weight() < 5);
        let view_costs = dijkstra(&view, start, None, |e| *e.weight());

        // Hand-build the light-edge subgraph over the same six nodes.
        let mut h: DiGraph<(), u32> = DiGraph::new();
        let m: Vec<NodeIndex> = (0..6).map(|_| h.add_node(())).collect();
        for (a, b, w) in [(0usize, 1usize, 2u32), (1, 2, 3), (2, 3, 1), (3, 4, 2), (5, 4, 1)] {
            h.add_edge(m[a], m[b], w);
        }
        let sub_costs = dijkstra(&h, m[0], None, |e| *e.weight());
        for i in 0..6 {
            assert_eq!(
                view_costs.get(&NodeIndex::new(i)),
                sub_costs.get(&NodeIndex::new(i)),
                "node {}",
                i
            );
        }
        assert_eq!(view_costs[&NodeIndex::new(4)], 8);
    }

    #[test]
    fn generated_reachability_views_agree() {
        let g = roads();
        let start = NodeIndex::new(0);
        let costs = dijkstra(&g, start, None, |e| *e.weight());
        let reachable: HashSet<NodeIndex> = costs.keys().copied().collect();
        for n in g.node_indices() {
            assert_eq!(
                reachable.contains(&n),
                has_path_connecting(&g, start, n, None),
                "node {:?}",
                n
            );
        }
        assert_eq!(reachable.len(), 5); // node 5 is not reachable
    }
}
