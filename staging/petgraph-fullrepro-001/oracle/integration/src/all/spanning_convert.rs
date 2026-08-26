// Spanning forests, element streams, keyed-to-indexed conversion, and
// algorithms over the alternative containers.
mod spanning_convert {
    use std::collections::{BTreeSet, HashSet};

    use petgraph::algo::{connected_components, dijkstra, min_spanning_tree, toposort};
    use petgraph::data::FromElements;
    use petgraph::graph::{DiGraph, NodeIndex, UnGraph};
    use petgraph::graphmap::DiGraphMap;
    use petgraph::stable_graph::StableDiGraph;
    use petgraph::visit::EdgeRef;
    use petgraph::{Directed, Graph};

    // Two-component weighted terrain:
    // component A over {0,1,2,3}: 0-1 (3), 1-2 (1), 2-3 (4), 0-2 (2), 1-3 (7)
    // component B over {4,5}: 4-5 (6)
    fn terrain() -> UnGraph<&'static str, u32> {
        let mut g: UnGraph<&str, u32> = UnGraph::new_undirected();
        let names = ["scree", "talus", "cirque", "arete", "col", "saddle"];
        let n: Vec<NodeIndex> = names.iter().map(|w| g.add_node(*w)).collect();
        for (a, b, w) in [
            (0usize, 1usize, 3u32),
            (1, 2, 1),
            (2, 3, 4),
            (0, 2, 2),
            (1, 3, 7),
            (4, 5, 6),
        ] {
            g.add_edge(n[a], n[b], w);
        }
        g
    }

    #[test]
    fn generated_mst_roundtrip_preserves_components() {
        let g = terrain();
        let forest: UnGraph<&str, u32> = UnGraph::from_elements(min_spanning_tree(&g));
        assert_eq!(forest.node_count(), g.node_count());
        assert_eq!(connected_components(&forest), connected_components(&g));
        // nodes - components edges in a spanning forest.
        assert_eq!(forest.edge_count(), 6 - 2);
        // Minimum total: component A needs {1, 2, 4} = 7, component B {6}.
        assert_eq!(forest.edge_weights().sum::<u32>(), 13);
    }

    #[test]
    fn generated_mst_beats_alternative_spanning_edges() {
        let g = terrain();
        let forest: UnGraph<&str, u32> = UnGraph::from_elements(min_spanning_tree(&g));
        let mst_total: u32 = forest.edge_weights().sum();
        // A hand-picked alternative spanning forest: 0-1 (3), 2-3 (4),
        // 1-3 (7), 4-5 (6) = 20; the MST must beat it.
        assert!(mst_total < 20);
        assert_eq!(mst_total, 13);
        // Every chosen edge exists in the source graph with the same weight
        // between the same endpoint names.
        let source_edges: BTreeSet<(String, String, u32)> = g
            .edge_references()
            .map(|e| {
                let mut pair = [g[e.source()], g[e.target()]];
                pair.sort();
                (pair[0].to_string(), pair[1].to_string(), *e.weight())
            })
            .collect();
        for e in forest.edge_references() {
            let mut pair = [forest[e.source()], forest[e.target()]];
            pair.sort();
            let key = (pair[0].to_string(), pair[1].to_string(), *e.weight());
            assert!(source_edges.contains(&key), "unknown edge {:?}", key);
        }
    }

    #[test]
    fn generated_mst_of_tree_is_identity() {
        let mut g: UnGraph<u8, u32> = UnGraph::new_undirected();
        let a = g.add_node(1);
        let b = g.add_node(2);
        let c = g.add_node(3);
        g.add_edge(a, b, 10);
        g.add_edge(b, c, 20);
        let again: UnGraph<u8, u32> = UnGraph::from_elements(min_spanning_tree(&g));
        assert_eq!(again.node_count(), 3);
        assert_eq!(again.edge_count(), 2);
        let weights: BTreeSet<u32> = again.edge_weights().copied().collect();
        assert_eq!(weights, BTreeSet::from([10, 20]));
    }

    #[test]
    fn generated_graphmap_into_graph_consistency() {
        let mut m: DiGraphMap<&str, u32> = DiGraphMap::new();
        m.add_edge("intake", "filter", 4);
        m.add_edge("filter", "outflow", 5);
        m.add_edge("intake", "outflow", 20);
        m.add_node("gauge");
        let key_edges: Vec<(&str, &str, u32)> =
            m.all_edges().map(|(a, b, w)| (a, b, *w)).collect();

        let g: Graph<&str, u32, Directed> = m.into_graph();
        // Node weights are the keys in insertion order.
        let weights: Vec<&str> = g.node_weights().copied().collect();
        assert_eq!(weights, vec!["intake", "filter", "outflow", "gauge"]);
        // The edge sets correspond one-to-one.
        assert_eq!(g.edge_count(), key_edges.len());
        let index_of = |name: &str| {
            g.node_indices().find(|&i| g[i] == name).unwrap()
        };
        for (a, b, w) in key_edges {
            let e = g.find_edge(index_of(a), index_of(b)).unwrap();
            assert_eq!(g[e], w);
        }
    }

    #[test]
    fn generated_graphmap_and_graph_dijkstra_agree() {
        let mut m: DiGraphMap<char, u32> = DiGraphMap::new();
        m.add_edge('s', 'a', 2);
        m.add_edge('a', 'b', 3);
        m.add_edge('s', 'b', 9);
        m.add_edge('b', 't', 1);
        let keyed = dijkstra(&m, 's', None, |e| *e.weight());

        let g: Graph<char, u32, Directed> = m.into_graph();
        let index_of = |c: char| g.node_indices().find(|&i| g[i] == c).unwrap();
        let indexed = dijkstra(&g, index_of('s'), None, |e| *e.weight());
        for c in ['s', 'a', 'b', 't'] {
            assert_eq!(keyed.get(&c), indexed.get(&index_of(c)), "key {}", c);
        }
        assert_eq!(keyed[&'t'], 6);
    }

    #[test]
    fn generated_stable_graph_algorithms_after_removals() {
        let mut g: StableDiGraph<&str, u32> = StableDiGraph::new();
        let a = g.add_node("sow");
        let doomed = g.add_node("chaff");
        let b = g.add_node("grow");
        let c = g.add_node("reap");
        g.add_edge(a, doomed, 50);
        g.add_edge(doomed, c, 50);
        g.add_edge(a, b, 2);
        g.add_edge(b, c, 3);
        g.remove_node(doomed);
        // Algorithms operate over the container with vacancies.
        let order = toposort(&g, None).unwrap();
        assert_eq!(order.len(), 3);
        let pos = |n| order.iter().position(|&x| x == n).unwrap();
        assert!(pos(a) < pos(b));
        assert!(pos(b) < pos(c));
        let costs = dijkstra(&g, a, None, |e| *e.weight());
        assert_eq!(costs.get(&c), Some(&5));
        assert_eq!(costs.len(), 3);
    }

    #[test]
    fn generated_from_elements_stream_reindexes_positions() {
        // Element edges refer to node positions in emission order; a
        // freshly built directed graph from a filtered stable graph's MST...
        // Keep it simple: materialize the terrain forest into a DiGraph and
        // check the endpoint names survive position mapping.
        let g = terrain();
        let forest: DiGraph<&str, u32> = DiGraph::from_elements(min_spanning_tree(&g));
        assert_eq!(forest.node_count(), 6);
        assert_eq!(forest.edge_count(), 4);
        let names: HashSet<&str> = forest.node_weights().copied().collect();
        assert_eq!(
            names,
            HashSet::from(["scree", "talus", "cirque", "arete", "col", "saddle"])
        );
        // The cheap 1-weight edge connects talus and cirque in the source;
        // the same endpoints must be joined in the materialized forest.
        let light = forest
            .edge_references()
            .find(|e| *e.weight() == 1)
            .expect("weight-1 edge kept");
        let mut pair = [forest[light.source()], forest[light.target()]];
        pair.sort();
        assert_eq!(pair, ["cirque", "talus"]);
    }
}
