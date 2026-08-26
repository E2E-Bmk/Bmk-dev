// Traversal visitors crossed with adapters, reachability, and mutation.
mod traversal {
    use std::collections::HashSet;

    use petgraph::algo::{dijkstra, has_path_connecting, toposort};
    use petgraph::graph::{DiGraph, NodeIndex};
    use petgraph::visit::{Bfs, Dfs, DfsPostOrder, EdgeRef, NodeFiltered, Reversed, Topo};

    // Shared DAG: 0->1, 0->2, 1->3, 2->3, 3->4, plus 5->4 side feed and
    // isolated node 6.
    fn dag() -> DiGraph<u32, u32> {
        let mut g: DiGraph<u32, u32> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..7).map(|i| g.add_node(i)).collect();
        for (a, b) in [(0usize, 1usize), (0, 2), (1, 3), (2, 3), (3, 4), (5, 4)] {
            g.add_edge(n[a], n[b], 1);
        }
        g
    }

    #[test]
    fn generated_reversed_walk_equals_reachability_set() {
        let g = dag();
        let target = NodeIndex::new(4);
        let mut walker = Bfs::new(Reversed(&g), target);
        let mut ancestors = HashSet::new();
        while let Some(n) = walker.next(Reversed(&g)) {
            ancestors.insert(n);
        }
        for n in g.node_indices() {
            assert_eq!(
                ancestors.contains(&n),
                has_path_connecting(&g, n, target, None),
                "node {:?}",
                n
            );
        }
        // Dfs over the same reversed view visits the same set.
        let mut dfs = Dfs::new(Reversed(&g), target);
        let mut via_dfs = HashSet::new();
        while let Some(n) = dfs.next(Reversed(&g)) {
            via_dfs.insert(n);
        }
        assert_eq!(via_dfs, ancestors);
    }

    #[test]
    fn generated_topo_walker_and_toposort_agree_on_rule() {
        let g = dag();
        let mut topo = Topo::new(&g);
        let mut walked = Vec::new();
        while let Some(n) = topo.next(&g) {
            walked.push(n);
        }
        let sorted = toposort(&g, None).unwrap();
        for order in [&walked, &sorted] {
            assert_eq!(order.len(), g.node_count());
            let pos =
                |n: NodeIndex| order.iter().position(|&x| x == n).unwrap();
            for e in g.edge_references() {
                assert!(
                    pos(e.source()) < pos(e.target()),
                    "edge {:?}->{:?} violated",
                    e.source(),
                    e.target()
                );
            }
        }
    }

    #[test]
    fn generated_visitor_interleaves_with_weight_mutation() {
        // The walker borrows the graph per step, so weights can change
        // between steps and later reads observe the new state.
        let mut g: DiGraph<u32, ()> = DiGraph::new();
        let a = g.add_node(1);
        let b = g.add_node(2);
        let c = g.add_node(3);
        g.add_edge(a, b, ());
        g.add_edge(b, c, ());
        let mut bfs = Bfs::new(&g, a);
        let first = bfs.next(&g).unwrap();
        assert_eq!(first, a);
        // Mutate an unvisited node's weight mid-walk.
        g[c] = 300;
        let mut rest = Vec::new();
        while let Some(n) = bfs.next(&g) {
            rest.push(g[n]);
        }
        assert_eq!(rest, vec![2, 300]);
    }

    #[test]
    fn generated_dfs_move_to_covers_forest_without_repeats() {
        let mut g: DiGraph<(), ()> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..6).map(|_| g.add_node(())).collect();
        g.add_edge(n[0], n[1], ());
        g.add_edge(n[1], n[2], ());
        g.add_edge(n[3], n[4], ());
        g.add_edge(n[4], n[2], ()); // cross edge into the first component
        g.add_edge(n[5], n[5], ()); // self-loop singleton
        let mut dfs = Dfs::new(&g, n[0]);
        let mut seen = Vec::new();
        while let Some(x) = dfs.next(&g) {
            seen.push(x);
        }
        dfs.move_to(n[3]);
        while let Some(x) = dfs.next(&g) {
            seen.push(x);
        }
        dfs.move_to(n[5]);
        while let Some(x) = dfs.next(&g) {
            seen.push(x);
        }
        // Every node exactly once even though n[2] is reachable twice.
        assert_eq!(seen.len(), 6);
        let unique: HashSet<_> = seen.iter().copied().collect();
        assert_eq!(unique.len(), 6);
        // First walk found the chain 0 -> 1 -> 2 before any second-component node.
        assert_eq!(&seen[..3], &[n[0], n[1], n[2]]);
    }

    #[test]
    fn generated_postorder_reversed_is_topological_for_reachable() {
        let g = dag();
        let root = NodeIndex::new(0);
        let mut post = DfsPostOrder::new(&g, root);
        let mut order = Vec::new();
        while let Some(n) = post.next(&g) {
            order.push(n);
        }
        order.reverse();
        // Reversed postorder of a DAG walk is a topological order of the
        // reachable subgraph.
        let reachable: HashSet<NodeIndex> = order.iter().copied().collect();
        let pos = |n: NodeIndex| order.iter().position(|&x| x == n).unwrap();
        for e in g.edge_references() {
            if reachable.contains(&e.source()) && reachable.contains(&e.target()) {
                assert!(pos(e.source()) < pos(e.target()));
            }
        }
        // Exactly the nodes reachable from the root are yielded.
        for n in g.node_indices() {
            assert_eq!(
                reachable.contains(&n),
                has_path_connecting(&g, root, n, None)
            );
        }
    }

    #[test]
    fn generated_walkers_and_dijkstra_agree_on_reachable_set() {
        let g = dag();
        let start = NodeIndex::new(0);
        let mut bfs = Bfs::new(&g, start);
        let mut via_bfs = HashSet::new();
        while let Some(n) = bfs.next(&g) {
            via_bfs.insert(n);
        }
        let costs = dijkstra(&g, start, None, |e| *e.weight());
        let via_dijkstra: HashSet<NodeIndex> = costs.keys().copied().collect();
        assert_eq!(via_bfs, via_dijkstra);
        assert_eq!(via_bfs.len(), 5); // nodes 5 and 6 unreachable
    }

    #[test]
    fn generated_node_filtered_walk_matches_hand_built_subgraph() {
        let g = dag();
        let cut = NodeIndex::new(3);
        let view = NodeFiltered(&g, |n: NodeIndex| n != cut);
        let mut bfs = Bfs::new(&view, NodeIndex::new(0));
        let mut filtered_reach = HashSet::new();
        while let Some(n) = bfs.next(&view) {
            filtered_reach.insert(n.index());
        }
        // Hand-build the same subgraph without node 3.
        let mut h: DiGraph<(), ()> = DiGraph::new();
        let m: Vec<NodeIndex> = (0..3).map(|_| h.add_node(())).collect();
        h.add_edge(m[0], m[1], ());
        h.add_edge(m[0], m[2], ());
        let mut hb = Bfs::new(&h, m[0]);
        let mut expect = HashSet::new();
        while let Some(n) = hb.next(&h) {
            expect.insert(n.index());
        }
        assert_eq!(filtered_reach, expect);
        assert_eq!(filtered_reach, HashSet::from([0, 1, 2]));
    }
}
