// Container mutation contracts crossed with adjacency and algorithm views.
mod containers {
    use std::collections::BTreeSet;

    use petgraph::algo::{connected_components, dijkstra, has_path_connecting, toposort};
    use petgraph::graph::{DiGraph, NodeIndex};
    use petgraph::stable_graph::StableDiGraph;
    use petgraph::visit::{EdgeRef, Reversed};
    use petgraph::Incoming;

    #[test]
    fn generated_graph_vs_stable_removal_contract() {
        // Same five nodes and edges in both containers.
        let names = ["quern", "adze", "loom", "kiln", "awl"];
        let mut g: DiGraph<&str, u32> = DiGraph::new();
        let mut s: StableDiGraph<&str, u32> = StableDiGraph::new();
        let gn: Vec<NodeIndex> = names.iter().map(|w| g.add_node(*w)).collect();
        let sn: Vec<NodeIndex> = names.iter().map(|w| s.add_node(*w)).collect();
        for (a, b, w) in [(0usize, 1usize, 5u32), (1, 2, 6), (3, 4, 7), (0, 4, 8)] {
            g.add_edge(gn[a], gn[b], w);
            s.add_edge(sn[a], sn[b], w);
        }

        // Remove index 1 ("adze") from both.
        g.remove_node(gn[1]);
        s.remove_node(sn[1]);

        // StableGraph: every other index keeps its weight and adjacency.
        assert_eq!(s[sn[0]], "quern");
        assert_eq!(s[sn[2]], "loom");
        assert_eq!(s[sn[3]], "kiln");
        assert_eq!(s[sn[4]], "awl");
        assert!(s.find_edge(sn[3], sn[4]).is_some());
        assert!(s.find_edge(sn[0], sn[4]).is_some());
        assert_eq!(s.node_weight(sn[1]), None);

        // Graph: the previously-last node ("awl") relocated to index 1 with
        // its adjacency intact.
        assert_eq!(g[NodeIndex::new(1)], "awl");
        assert_eq!(g.node_count(), 4);
        let relocated = NodeIndex::new(1);
        let inbound: BTreeSet<&str> = g
            .neighbors_directed(relocated, Incoming)
            .map(|n| g[n])
            .collect();
        assert_eq!(inbound, BTreeSet::from(["kiln", "quern"]));

        // Both containers agree on surviving structure as a fact source.
        assert_eq!(g.edge_count(), s.edge_count());
        let g_kiln = g.node_indices().find(|&i| g[i] == "kiln").unwrap();
        let g_awl = g.node_indices().find(|&i| g[i] == "awl").unwrap();
        assert!(has_path_connecting(&g, g_kiln, g_awl, None));
        assert!(has_path_connecting(&s, sn[3], sn[4], None));
        assert!(!has_path_connecting(&g, g_awl, g_kiln, None));
        assert!(!has_path_connecting(&s, sn[4], sn[3], None));
    }

    #[test]
    fn generated_filter_map_matches_hand_built_subgraph() {
        let mut g: DiGraph<u32, u32> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..5).map(|i| g.add_node(i * 10)).collect();
        for (a, b, w) in [(0usize, 1usize, 1u32), (1, 2, 2), (2, 3, 3), (3, 4, 4), (0, 4, 20)] {
            g.add_edge(n[a], n[b], w);
        }
        // Drop node weight 20 (index 2) via filter_map.
        let filtered = g.filter_map(
            |_, w| if *w == 20 { None } else { Some(*w) },
            |_, w| Some(*w),
        );

        // Hand-build the expected survivor graph.
        let mut expected: DiGraph<u32, u32> = DiGraph::new();
        let e: Vec<NodeIndex> = [0u32, 10, 30, 40].iter().map(|w| expected.add_node(*w)).collect();
        expected.add_edge(e[0], e[1], 1);
        expected.add_edge(e[2], e[3], 4);
        expected.add_edge(e[0], e[3], 20);

        assert_eq!(filtered.node_count(), expected.node_count());
        assert_eq!(filtered.edge_count(), expected.edge_count());
        let fw: Vec<u32> = filtered.node_weights().copied().collect();
        let ew: Vec<u32> = expected.node_weights().copied().collect();
        assert_eq!(fw, ew);
        assert_eq!(
            connected_components(&filtered),
            connected_components(&expected)
        );
        let costs_f = dijkstra(&filtered, NodeIndex::new(0), None, |e| *e.weight());
        let costs_e = dijkstra(&expected, NodeIndex::new(0), None, |e| *e.weight());
        for i in 0..filtered.node_count() {
            assert_eq!(
                costs_f.get(&NodeIndex::new(i)),
                costs_e.get(&NodeIndex::new(i)),
                "node {}",
                i
            );
        }
    }

    #[test]
    fn generated_retain_edges_changes_reachability() {
        let mut g: DiGraph<(), u32> = DiGraph::new();
        let a = g.add_node(());
        let b = g.add_node(());
        let c = g.add_node(());
        g.add_edge(a, b, 2);
        g.add_edge(b, c, 50); // heavy edge is the only b -> c link
        g.add_edge(a, c, 3);
        assert!(has_path_connecting(&g, b, c, None));
        g.retain_edges(|fr, e| fr.edge_weight(e).map_or(false, |w| *w < 10));
        assert_eq!(g.edge_count(), 2);
        assert!(!has_path_connecting(&g, b, c, None));
        let costs = dijkstra(&g, a, None, |e| *e.weight());
        assert_eq!(costs.get(&c), Some(&3));
        assert_eq!(costs.get(&b), Some(&2));
    }

    #[test]
    fn generated_map_scales_dijkstra_costs() {
        let mut g: DiGraph<&str, u32> = DiGraph::new();
        let a = g.add_node("byre");
        let b = g.add_node("garth");
        let c = g.add_node("close");
        g.add_edge(a, b, 3);
        g.add_edge(b, c, 4);
        g.add_edge(a, c, 9);
        let tripled = g.map(|_, w| *w, |_, w| w * 3);
        let base = dijkstra(&g, a, None, |e| *e.weight());
        let scaled = dijkstra(&tripled, a, None, |e| *e.weight());
        for node in [a, b, c] {
            assert_eq!(scaled[&node], base[&node] * 3);
        }
        // Structure is unchanged by map.
        assert_eq!(tripled.node_count(), 3);
        assert_eq!(tripled.edge_count(), 3);
        assert_eq!(tripled[a], "byre");
    }

    #[test]
    fn generated_extend_with_edges_then_analysis() {
        let mut g: DiGraph<(), ()> = DiGraph::new();
        g.extend_with_edges([(0u32, 1u32), (1, 2), (0, 2), (3, 4)]);
        assert_eq!(g.node_count(), 5);
        assert_eq!(connected_components(&g), 2);
        let order = toposort(&g, None).unwrap();
        let pos = |i: usize| {
            order
                .iter()
                .position(|&x| x == NodeIndex::new(i))
                .unwrap()
        };
        assert!(pos(0) < pos(1));
        assert!(pos(1) < pos(2));
        assert!(pos(3) < pos(4));
        let roots: Vec<usize> = g.externals(Incoming).map(|n| n.index()).collect();
        assert_eq!(roots, vec![0, 3]);
    }

    #[test]
    fn generated_reverse_matches_reversed_view() {
        let mut g: DiGraph<(), u32> = DiGraph::new();
        let a = g.add_node(());
        let b = g.add_node(());
        let c = g.add_node(());
        g.add_edge(a, b, 2);
        g.add_edge(b, c, 5);
        g.add_edge(a, c, 9);

        // Costs from c over the reversed *view* of the original...
        let view_costs = dijkstra(Reversed(&g), c, None, |e| *e.weight());

        // ...must equal costs from c after reversing in place.
        let mut flipped = g.clone();
        flipped.reverse();
        let flip_costs = dijkstra(&flipped, c, None, |e| *e.weight());

        for node in [a, b, c] {
            assert_eq!(view_costs.get(&node), flip_costs.get(&node));
        }
        assert_eq!(view_costs[&a], 7);
    }
}
