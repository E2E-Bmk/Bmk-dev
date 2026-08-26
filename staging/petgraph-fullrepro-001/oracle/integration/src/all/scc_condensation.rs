// Strongly connected structure across both SCC algorithms, condensation,
// reachability, and the reversal adapter.
mod scc_condensation {
    use std::collections::BTreeSet;

    use petgraph::algo::{
        condensation, has_path_connecting, is_cyclic_directed, kosaraju_scc, tarjan_scc, toposort,
    };
    use petgraph::graph::{DiGraph, NodeIndex};
    use petgraph::visit::{EdgeRef, Reversed};

    // Two interlocking cycles and a tail:
    // cycle A: 0 -> 1 -> 2 -> 0; cycle B: 3 -> 4 -> 3;
    // bridges: 2 -> 3, 4 -> 5 (tail), plus lone node 6.
    fn machine() -> DiGraph<u32, ()> {
        let mut g: DiGraph<u32, ()> = DiGraph::new();
        let n: Vec<NodeIndex> = (0..7).map(|i| g.add_node(i)).collect();
        for (a, b) in [
            (0usize, 1usize),
            (1, 2),
            (2, 0),
            (3, 4),
            (4, 3),
            (2, 3),
            (4, 5),
        ] {
            g.add_edge(n[a], n[b], ());
        }
        g
    }

    fn normalized(comps: &[Vec<NodeIndex>]) -> BTreeSet<Vec<usize>> {
        comps
            .iter()
            .map(|c| {
                let mut v: Vec<usize> = c.iter().map(|n| n.index()).collect();
                v.sort();
                v
            })
            .collect()
    }

    #[test]
    fn generated_scc_partitions_agree() {
        let g = machine();
        let k = normalized(&kosaraju_scc(&g));
        let t = normalized(&tarjan_scc(&g));
        assert_eq!(k, t);
        assert_eq!(
            k,
            BTreeSet::from([vec![0, 1, 2], vec![3, 4], vec![5], vec![6]])
        );
    }

    #[test]
    fn generated_scc_matches_mutual_reachability() {
        let g = machine();
        let comps = kosaraju_scc(&g);
        // Two nodes share a component exactly when each reaches the other.
        let component_of = |n: NodeIndex| comps.iter().position(|c| c.contains(&n)).unwrap();
        for a in g.node_indices() {
            for b in g.node_indices() {
                let mutual = has_path_connecting(&g, a, b, None)
                    && has_path_connecting(&g, b, a, None);
                assert_eq!(
                    component_of(a) == component_of(b),
                    mutual,
                    "{:?} vs {:?}",
                    a,
                    b
                );
            }
        }
    }

    #[test]
    fn generated_scc_postorder_respects_linkage() {
        let g = machine();
        for comps in [kosaraju_scc(&g), tarjan_scc(&g)] {
            let component_of =
                |n: NodeIndex| comps.iter().position(|c| c.contains(&n)).unwrap();
            // A component appears before any component that links to it:
            // for every edge crossing components, the target's component
            // comes earlier in the list.
            for e in g.edge_references() {
                let (cs, ct) = (component_of(e.source()), component_of(e.target()));
                if cs != ct {
                    assert!(ct < cs, "edge {:?}->{:?}", e.source(), e.target());
                }
            }
        }
    }

    #[test]
    fn generated_condensation_partitions_and_toposorts() {
        let g = machine();
        let cond = condensation(g.clone(), true);
        assert_eq!(cond.node_count(), 4);
        // Component weight vectors partition the original node weights.
        let groups: BTreeSet<Vec<u32>> = cond
            .node_weights()
            .map(|ws| {
                let mut v = ws.clone();
                v.sort();
                v
            })
            .collect();
        assert_eq!(
            groups,
            BTreeSet::from([vec![0, 1, 2], vec![3, 4], vec![5], vec![6]])
        );
        assert!(!is_cyclic_directed(&cond));
        let order = toposort(&cond, None).unwrap();
        assert_eq!(order.len(), 4);
    }

    #[test]
    fn generated_condensation_keep_edges_counts() {
        let g = machine();
        let strict = condensation(g.clone(), true);
        let full = condensation(g.clone(), false);
        // All 7 original edges survive in the non-acyclic condensation; the
        // acyclic one keeps only the 2 cross-component bridges.
        assert_eq!(full.edge_count(), 7);
        assert_eq!(strict.edge_count(), 2);
        assert!(is_cyclic_directed(&full));
        assert!(!is_cyclic_directed(&strict));
        assert_eq!(full.node_count(), strict.node_count());
    }

    #[test]
    fn generated_scc_invariant_under_reversal() {
        let g = machine();
        let forward = normalized(&kosaraju_scc(&g));
        let backward = normalized(&kosaraju_scc(Reversed(&g)));
        assert_eq!(forward, backward);
        let backward_tarjan = normalized(&tarjan_scc(Reversed(&g)));
        assert_eq!(forward, backward_tarjan);
    }

    #[test]
    fn generated_cycle_collapse_enables_toposort() {
        let mut g = machine();
        // The raw machine has cycles, so toposort fails and names a
        // participant of some cycle.
        assert!(is_cyclic_directed(&g));
        let err = toposort(&g, None).unwrap_err();
        let culprit = err.node_id();
        assert!(culprit.index() <= 4, "culprit {:?}", culprit);
        // Breaking both cycles makes toposort succeed over the same nodes.
        let back_a = g.find_edge(NodeIndex::new(2), NodeIndex::new(0)).unwrap();
        g.remove_edge(back_a);
        let back_b = g.find_edge(NodeIndex::new(4), NodeIndex::new(3)).unwrap();
        g.remove_edge(back_b);
        assert!(!is_cyclic_directed(&g));
        let order = toposort(&g, None).unwrap();
        assert_eq!(order.len(), 7);
    }
}
