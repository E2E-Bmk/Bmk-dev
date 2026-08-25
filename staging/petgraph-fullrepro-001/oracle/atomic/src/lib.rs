// Oracle atomic tests for the graph data structure library
#![cfg(test)]
#![allow(clippy::all)]

use std::collections::{BTreeSet, HashSet};
use std::panic::{catch_unwind, AssertUnwindSafe};

use petgraph::algo::{
    astar, bellman_ford, condensation, connected_components, dijkstra, has_path_connecting,
    is_cyclic_directed, is_cyclic_undirected, kosaraju_scc, min_spanning_tree, tarjan_scc,
    toposort,
};
use petgraph::data::{Element, FromElements};
use petgraph::graph::{DiGraph, EdgeIndex, NodeIndex, UnGraph};
use petgraph::graphmap::{DiGraphMap, UnGraphMap};
use petgraph::stable_graph::{StableDiGraph, StableUnGraph};
use petgraph::visit::{Bfs, Dfs, DfsPostOrder, EdgeFiltered, EdgeRef, NodeFiltered, Reversed, Topo};
use petgraph::{Directed, Direction, EdgeType, Graph, Incoming, Outgoing, Undirected};

fn panics<F: FnOnce() -> R, R>(f: F) -> bool {
    catch_unwind(AssertUnwindSafe(f)).is_err()
}

// ---------------------------------------------------------------------------
// Graph construction and mutation
// ---------------------------------------------------------------------------

#[test]
fn generated_new_graph_empty_and_directedness() {
    let d: DiGraph<u8, u8> = DiGraph::new();
    assert_eq!(d.node_count(), 0);
    assert_eq!(d.edge_count(), 0);
    assert!(d.is_directed());

    let u: UnGraph<u8, u8> = UnGraph::new_undirected();
    assert_eq!(u.node_count(), 0);
    assert!(!u.is_directed());
}

#[test]
fn generated_with_capacity_starts_empty() {
    let g: DiGraph<&str, u32> = Graph::with_capacity(12, 30);
    assert_eq!(g.node_count(), 0);
    assert_eq!(g.edge_count(), 0);
}

#[test]
fn generated_add_node_indices_ascend() {
    let mut g: DiGraph<&str, ()> = DiGraph::new();
    let a = g.add_node("kelp");
    let b = g.add_node("wrack");
    let c = g.add_node("dulse");
    assert_eq!(a.index(), 0);
    assert_eq!(b.index(), 1);
    assert_eq!(c.index(), 2);
    assert_eq!(g.node_count(), 3);
    assert_eq!(g[b], "wrack");
}

#[test]
fn generated_add_edge_indices_ascend_parallel_allowed() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let e0 = g.add_edge(a, b, 11);
    let e1 = g.add_edge(a, b, 22);
    assert_eq!(e0.index(), 0);
    assert_eq!(e1.index(), 1);
    assert_eq!(g.edge_count(), 2);
    assert_eq!(g[e0], 11);
    assert_eq!(g[e1], 22);
}

#[test]
fn generated_add_edge_missing_endpoint_panics() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    assert!(panics(|| {
        g.add_edge(a, NodeIndex::new(7), 5);
    }));
    assert_eq!(g.edge_count(), 0);
}

#[test]
fn generated_self_loop_allowed() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let a = g.add_node("eddy");
    let e = g.add_edge(a, a, 8);
    assert_eq!(g.edge_count(), 1);
    assert_eq!(g.edge_endpoints(e), Some((a, a)));
    let nbrs: Vec<_> = g.neighbors(a).collect();
    assert_eq!(nbrs, vec![a]);
}

#[test]
fn generated_update_edge_replaces_or_adds() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let first = g.add_edge(a, b, 3);
    let replaced = g.update_edge(a, b, 9);
    assert_eq!(replaced, first);
    assert_eq!(g.edge_count(), 1);
    assert_eq!(g[first], 9);

    let fresh = g.update_edge(b, c, 4);
    assert_ne!(fresh, first);
    assert_eq!(g.edge_count(), 2);
    assert_eq!(g[fresh], 4);
}

#[test]
fn generated_extend_with_edges_creates_missing_nodes() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    g.extend_with_edges([(0u32, 2u32, 7u32), (1, 2, 8), (2, 3, 9)]);
    assert_eq!(g.node_count(), 4);
    assert_eq!(g.edge_count(), 3);
    let e = g.find_edge(NodeIndex::new(1), NodeIndex::new(2)).unwrap();
    assert_eq!(g[e], 8);
}

#[test]
fn generated_from_edges_builds_graph() {
    let g = DiGraph::<(), i32>::from_edges([(0, 1, 40), (1, 2, 50)]);
    assert_eq!(g.node_count(), 3);
    assert_eq!(g.edge_count(), 2);
    let e = g.find_edge(NodeIndex::new(0), NodeIndex::new(1)).unwrap();
    assert_eq!(*g.edge_weight(e).unwrap(), 40);
}

#[test]
fn generated_remove_node_swap_relocates_last() {
    let mut g: DiGraph<&str, ()> = DiGraph::new();
    let _r = g.add_node("reef");
    let cove = g.add_node("cove");
    let _s = g.add_node("spit");
    let _l = g.add_node("lagoon");
    // Removing index 1 moves the last node (lagoon, index 3) into slot 1.
    assert_eq!(g.remove_node(cove), Some("cove"));
    assert_eq!(g.node_count(), 3);
    assert_eq!(g[NodeIndex::new(1)], "lagoon");
    assert_eq!(g[NodeIndex::new(0)], "reef");
    assert_eq!(g[NodeIndex::new(2)], "spit");
}

#[test]
fn generated_remove_node_drops_incident_edges() {
    let mut g: DiGraph<u8, u8> = DiGraph::new();
    let a = g.add_node(1);
    let b = g.add_node(2);
    let c = g.add_node(3);
    g.add_edge(a, b, 10);
    g.add_edge(b, c, 11);
    g.add_edge(c, a, 12);
    g.remove_node(b);
    assert_eq!(g.edge_count(), 1);
    // The surviving edge is c -> a; both endpoints kept their weights.
    let (s, t) = g.edge_endpoints(EdgeIndex::new(0)).unwrap();
    assert_eq!((g[s], g[t]), (3, 1));
}

#[test]
fn generated_remove_missing_returns_none() {
    let mut g: DiGraph<u8, u8> = DiGraph::new();
    let a = g.add_node(5);
    assert_eq!(g.remove_node(NodeIndex::new(4)), None);
    assert_eq!(g.remove_edge(EdgeIndex::new(0)), None);
    assert_eq!(g.node_count(), 1);
    assert_eq!(g[a], 5);
}

#[test]
fn generated_remove_edge_swap_relocates_last() {
    let mut g: DiGraph<(), &str> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let first = g.add_edge(a, b, "jib");
    let _mid = g.add_edge(b, c, "gaff");
    let _last = g.add_edge(c, a, "keel");
    assert_eq!(g.remove_edge(first), Some("jib"));
    assert_eq!(g.edge_count(), 2);
    // The previously-last edge (keel) adopted index 0.
    assert_eq!(g[EdgeIndex::new(0)], "keel");
    assert_eq!(g[EdgeIndex::new(1)], "gaff");
}

#[test]
fn generated_clear_and_clear_edges() {
    let mut g = DiGraph::<u8, u8>::from_edges([(0, 1, 1), (1, 2, 2)]);
    g.clear_edges();
    assert_eq!(g.node_count(), 3);
    assert_eq!(g.edge_count(), 0);
    g.add_edge(NodeIndex::new(0), NodeIndex::new(2), 9);
    g.clear();
    assert_eq!(g.node_count(), 0);
    assert_eq!(g.edge_count(), 0);
}

#[test]
fn generated_retain_nodes_keeps_predicate_survivors() {
    let mut g: DiGraph<u32, ()> = DiGraph::new();
    for w in [10u32, 11, 12, 13, 14] {
        g.add_node(w);
    }
    g.retain_nodes(|fr, ix| fr.node_weight(ix).map_or(false, |w| w % 2 == 1));
    assert_eq!(g.node_count(), 2);
    let kept: BTreeSet<u32> = g.node_weights().copied().collect();
    assert_eq!(kept, BTreeSet::from([11, 13]));
}

#[test]
fn generated_retain_edges_keeps_predicate_survivors() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, 3);
    g.add_edge(b, c, 30);
    g.add_edge(c, a, 5);
    g.retain_edges(|fr, e| fr.edge_weight(e).map_or(false, |w| *w < 10));
    assert_eq!(g.edge_count(), 2);
    let kept: BTreeSet<u32> = g.edge_weights().copied().collect();
    assert_eq!(kept, BTreeSet::from([3, 5]));
    assert_eq!(g.node_count(), 3);
}

#[test]
fn generated_map_preserves_structure() {
    let mut g: DiGraph<u32, u32> = DiGraph::new();
    let a = g.add_node(2);
    let b = g.add_node(5);
    g.add_edge(a, b, 7);
    let doubled = g.map(|_, w| w * 2, |_, w| w + 100);
    assert_eq!(doubled.node_count(), 2);
    assert_eq!(doubled.edge_count(), 1);
    assert_eq!(doubled[NodeIndex::new(0)], 4);
    assert_eq!(doubled[NodeIndex::new(1)], 10);
    assert_eq!(doubled[EdgeIndex::new(0)], 107);
    // The original graph is untouched.
    assert_eq!(g[a], 2);
}

#[test]
fn generated_filter_map_drops_node_and_reindexes() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let fen = g.add_node("fen");
    let bog = g.add_node("bog");
    let carr = g.add_node("carr");
    g.add_edge(fen, bog, 1);
    g.add_edge(bog, carr, 2);
    g.add_edge(fen, carr, 3);
    // Dropping "bog" removes its two incident edges; survivors re-index
    // compactly in original order: fen -> 0, carr -> 1.
    let kept = g.filter_map(
        |_, w| if *w == "bog" { None } else { Some(*w) },
        |_, w| Some(*w),
    );
    assert_eq!(kept.node_count(), 2);
    assert_eq!(kept.edge_count(), 1);
    assert_eq!(kept[NodeIndex::new(0)], "fen");
    assert_eq!(kept[NodeIndex::new(1)], "carr");
    let e = kept.find_edge(NodeIndex::new(0), NodeIndex::new(1)).unwrap();
    assert_eq!(kept[e], 3);
}

#[test]
fn generated_filter_map_drops_edges_only() {
    let mut g: DiGraph<u8, u32> = DiGraph::new();
    let a = g.add_node(1);
    let b = g.add_node(2);
    g.add_edge(a, b, 40);
    g.add_edge(b, a, 4);
    let light = g.filter_map(|_, w| Some(*w), |_, w| if *w > 10 { None } else { Some(*w) });
    assert_eq!(light.node_count(), 2);
    assert_eq!(light.edge_count(), 1);
    let e = light.find_edge(NodeIndex::new(1), NodeIndex::new(0)).unwrap();
    assert_eq!(light[e], 4);
}

#[test]
fn generated_reverse_flips_edges() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let e = g.add_edge(a, b, 6);
    g.reverse();
    assert_eq!(g.edge_endpoints(e), Some((b, a)));
    assert!(g.find_edge(b, a).is_some());
    assert!(g.find_edge(a, b).is_none());
}

#[test]
fn generated_weight_accessors_and_mut() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let a = g.add_node("skerry");
    let b = g.add_node("holm");
    let e = g.add_edge(a, b, 17);
    assert_eq!(g.node_weight(a), Some(&"skerry"));
    assert_eq!(g.edge_weight(e), Some(&17));
    assert_eq!(g.node_weight(NodeIndex::new(9)), None);
    assert_eq!(g.edge_weight(EdgeIndex::new(9)), None);
    *g.node_weight_mut(b).unwrap() = "voe";
    *g.edge_weight_mut(e).unwrap() = 18;
    assert_eq!(g[b], "voe");
    assert_eq!(g[e], 18);
}

#[test]
fn generated_index_operator_panics_on_invalid() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let a = g.add_node("tarn");
    assert_eq!(g[a], "tarn");
    assert!(panics(|| {
        let _ = g[NodeIndex::new(3)];
    }));
    assert!(panics(|| {
        let _ = g[EdgeIndex::new(0)];
    }));
}

#[test]
fn generated_weight_iterators_in_index_order() {
    let mut g: DiGraph<u32, u32> = DiGraph::new();
    let a = g.add_node(70);
    let b = g.add_node(71);
    let c = g.add_node(72);
    g.add_edge(a, b, 700);
    g.add_edge(b, c, 701);
    let nws: Vec<u32> = g.node_weights().copied().collect();
    assert_eq!(nws, vec![70, 71, 72]);
    let ews: Vec<u32> = g.edge_weights().copied().collect();
    assert_eq!(ews, vec![700, 701]);
    for w in g.node_weights_mut() {
        *w += 1;
    }
    assert_eq!(g[a], 71);
}

// ---------------------------------------------------------------------------
// Indices, direction, and adjacency queries
// ---------------------------------------------------------------------------

#[test]
fn generated_node_index_roundtrip_ord_hash() {
    let n = NodeIndex::<u32>::new(41);
    assert_eq!(n.index(), 41);
    let sorted: Vec<usize> = BTreeSet::from([NodeIndex::<u32>::new(2), NodeIndex::new(0), NodeIndex::new(1)])
        .into_iter()
        .map(|i| i.index())
        .collect();
    assert_eq!(sorted, vec![0, 1, 2]);
    let mut set = HashSet::new();
    set.insert(NodeIndex::<u32>::new(3));
    assert!(set.contains(&NodeIndex::new(3)));
}

#[test]
fn generated_edge_index_roundtrip() {
    let e = EdgeIndex::<u32>::new(13);
    assert_eq!(e.index(), 13);
    assert!(EdgeIndex::<u32>::new(1) < EdgeIndex::<u32>::new(2));
}

#[test]
fn generated_direction_opposite() {
    assert_eq!(Outgoing.opposite(), Incoming);
    assert_eq!(Incoming.opposite(), Outgoing);
    assert_eq!(Direction::Outgoing, Outgoing);
    assert_ne!(Outgoing, Incoming);
}

#[test]
fn generated_edge_type_reports_directedness() {
    assert!(<Directed as EdgeType>::is_directed());
    assert!(!<Undirected as EdgeType>::is_directed());
    let g: Graph<(), (), Undirected> = Graph::new_undirected();
    assert!(!g.is_directed());
}

#[test]
fn generated_neighbors_reverse_insertion_order() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let hub = g.add_node("hub");
    let east = g.add_node("east");
    let west = g.add_node("west");
    g.add_edge(hub, east, 1);
    g.add_edge(hub, west, 2);
    // Most recently added edge's neighbor first.
    let order: Vec<_> = g.neighbors(hub).collect();
    assert_eq!(order, vec![west, east]);
}

#[test]
fn generated_neighbors_directed_incoming() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, c, ());
    g.add_edge(b, c, ());
    let incoming: Vec<_> = g.neighbors_directed(c, Incoming).collect();
    assert_eq!(incoming, vec![b, a]);
    let outgoing: Vec<_> = g.neighbors_directed(c, Outgoing).collect();
    assert!(outgoing.is_empty());
}

#[test]
fn generated_neighbors_undirected_outgoing_then_incoming() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let hub = g.add_node("hub");
    let east = g.add_node("east");
    let pier = g.add_node("pier");
    g.add_edge(hub, east, 1);
    g.add_edge(east, pier, 3);
    // For east: outgoing neighbors first (pier), then incoming (hub).
    let all: Vec<_> = g.neighbors_undirected(east).collect();
    assert_eq!(all, vec![pier, hub]);
}

#[test]
fn generated_neighbors_missing_node_empty() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    g.add_node(());
    assert_eq!(g.neighbors(NodeIndex::new(9)).count(), 0);
    assert_eq!(g.edges(NodeIndex::new(9)).count(), 0);
}

#[test]
fn generated_undirected_neighbors_all_adjacent() {
    let mut g: UnGraph<&str, u32> = UnGraph::new_undirected();
    let mid = g.add_node("mid");
    let n1 = g.add_node("n1");
    let n2 = g.add_node("n2");
    g.add_edge(n1, mid, 1);
    g.add_edge(mid, n2, 2);
    let nbrs: HashSet<_> = g.neighbors(mid).collect();
    assert_eq!(nbrs, HashSet::from([n1, n2]));
    let directed_view: HashSet<_> = g.neighbors_directed(mid, Incoming).collect();
    assert_eq!(directed_view, nbrs);
}

#[test]
fn generated_edges_edgeref_accessors() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let e = g.add_edge(a, b, 55);
    let refs: Vec<_> = g.edges(a).collect();
    assert_eq!(refs.len(), 1);
    assert_eq!(refs[0].source(), a);
    assert_eq!(refs[0].target(), b);
    assert_eq!(refs[0].id(), e);
    assert_eq!(*refs[0].weight(), 55);
}

#[test]
fn generated_edges_directed_incoming_sources() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, c, 1);
    g.add_edge(b, c, 2);
    let sources: Vec<_> = g.edges_directed(c, Incoming).map(|e| e.source()).collect();
    assert_eq!(sources, vec![b, a]);
    let weights: Vec<u32> = g.edges_directed(c, Incoming).map(|e| *e.weight()).collect();
    assert_eq!(weights, vec![2, 1]);
}

#[test]
fn generated_find_edge_parallel_prefers_most_recent() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let _e0 = g.add_edge(a, b, 10);
    let e1 = g.add_edge(a, b, 20);
    assert_eq!(g.find_edge(a, b), Some(e1));
    assert_eq!(g.find_edge(b, a), None);
}

#[test]
fn generated_find_edge_undirected_reports_direction() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let e = g.add_edge(a, b, 5);
    assert_eq!(g.find_edge_undirected(a, b), Some((e, Outgoing)));
    assert_eq!(g.find_edge_undirected(b, a), Some((e, Incoming)));
    assert_eq!(g.find_edge_undirected(a, NodeIndex::new(9)), None);
}

#[test]
fn generated_find_edge_undirected_graph_ignores_order() {
    let mut g: UnGraph<(), u32> = UnGraph::new_undirected();
    let a = g.add_node(());
    let b = g.add_node(());
    let e = g.add_edge(a, b, 3);
    assert_eq!(g.find_edge(a, b), Some(e));
    assert_eq!(g.find_edge(b, a), Some(e));
}

#[test]
fn generated_edges_connecting_lists_parallel() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let e0 = g.add_edge(a, b, 1);
    let e1 = g.add_edge(a, b, 2);
    g.add_edge(a, c, 3);
    let ids: Vec<_> = g.edges_connecting(a, b).map(|e| e.id()).collect();
    assert_eq!(ids, vec![e1, e0]);
    assert!(g.contains_edge(a, b));
    assert!(!g.contains_edge(b, a));
}

#[test]
fn generated_edge_endpoints() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let e = g.add_edge(a, b, ());
    assert_eq!(g.edge_endpoints(e), Some((a, b)));
    assert_eq!(g.edge_endpoints(EdgeIndex::new(6)), None);
}

#[test]
fn generated_externals_by_direction() {
    let mut g: DiGraph<&str, ()> = DiGraph::new();
    let src = g.add_node("src");
    let mid = g.add_node("mid");
    let sink = g.add_node("sink");
    let lone = g.add_node("lone");
    g.add_edge(src, mid, ());
    g.add_edge(mid, sink, ());
    let roots: Vec<_> = g.externals(Incoming).collect();
    assert_eq!(roots, vec![src, lone]);
    let sinks: Vec<_> = g.externals(Outgoing).collect();
    assert_eq!(sinks, vec![sink, lone]);
}

#[test]
fn generated_index_iterators_ascend() {
    let mut g: DiGraph<u8, u8> = DiGraph::new();
    let a = g.add_node(1);
    let b = g.add_node(2);
    let c = g.add_node(3);
    g.add_edge(a, b, 10);
    g.add_edge(b, c, 11);
    let nidx: Vec<usize> = g.node_indices().map(|i| i.index()).collect();
    assert_eq!(nidx, vec![0, 1, 2]);
    let eidx: Vec<usize> = g.edge_indices().map(|i| i.index()).collect();
    assert_eq!(eidx, vec![0, 1]);
    let all: Vec<(usize, usize, u8)> = g
        .edge_references()
        .map(|e| (e.source().index(), e.target().index(), *e.weight()))
        .collect();
    assert_eq!(all, vec![(0, 1, 10), (1, 2, 11)]);
}

// ---------------------------------------------------------------------------
// StableGraph
// ---------------------------------------------------------------------------

#[test]
fn generated_stable_remove_keeps_other_indices() {
    let mut g: StableDiGraph<&str, u32> = StableDiGraph::new();
    let a = g.add_node("alder");
    let b = g.add_node("rowan");
    let c = g.add_node("yew");
    let d = g.add_node("elm");
    g.add_edge(a, d, 1);
    g.remove_node(b);
    assert_eq!(g.node_count(), 3);
    assert_eq!(g[c], "yew");
    assert_eq!(g[d], "elm");
    assert!(g.find_edge(a, d).is_some());
}

#[test]
fn generated_stable_vacancy_accessors() {
    let mut g: StableDiGraph<u8, u8> = StableDiGraph::new();
    let a = g.add_node(1);
    let b = g.add_node(2);
    g.remove_node(a);
    assert_eq!(g.node_weight(a), None);
    assert!(!g.contains_node(a));
    assert!(g.contains_node(b));
    assert!(panics(|| {
        let _ = g[a];
    }));
}

#[test]
fn generated_stable_node_index_reuse_lifo() {
    let mut g: StableDiGraph<u32, ()> = StableDiGraph::new();
    let _n0 = g.add_node(100);
    let n1 = g.add_node(101);
    let n2 = g.add_node(102);
    let _n3 = g.add_node(103);
    g.remove_node(n1);
    g.remove_node(n2);
    // Last freed (index 2) is reused first, then index 1, then fresh index 4.
    assert_eq!(g.add_node(201).index(), 2);
    assert_eq!(g.add_node(202).index(), 1);
    assert_eq!(g.add_node(203).index(), 4);
}

#[test]
fn generated_stable_edge_index_reuse_lifo() {
    let mut g: StableDiGraph<(), u32> = StableDiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let e0 = g.add_edge(a, b, 1);
    let e1 = g.add_edge(b, c, 2);
    let _e2 = g.add_edge(c, a, 3);
    g.remove_edge(e0);
    g.remove_edge(e1);
    assert_eq!(g.add_edge(a, c, 4).index(), 1);
    assert_eq!(g.add_edge(b, a, 5).index(), 0);
    assert_eq!(g.add_edge(c, b, 6).index(), 3);
}

#[test]
fn generated_stable_counts_and_indices_skip_vacancies() {
    let mut g: StableDiGraph<u8, u8> = StableDiGraph::new();
    let a = g.add_node(1);
    let b = g.add_node(2);
    let c = g.add_node(3);
    g.add_edge(a, b, 10);
    let eb = g.add_edge(b, c, 11);
    g.remove_node(b); // also removes both incident edges
    assert_eq!(g.node_count(), 2);
    assert_eq!(g.edge_count(), 0);
    let live: Vec<usize> = g.node_indices().map(|i| i.index()).collect();
    assert_eq!(live, vec![0, 2]);
    assert_eq!(g.edge_weight(eb), None);
}

#[test]
fn generated_stable_undirected_container() {
    let mut g: StableUnGraph<&str, u32> = StableUnGraph::with_capacity(0, 0);
    assert!(!g.is_directed());
    let a = g.add_node("port");
    let b = g.add_node("berth");
    let e = g.add_edge(a, b, 4);
    assert_eq!(g.find_edge(b, a), Some(e));
}

#[test]
fn generated_stable_remove_edge_keeps_other_edge_indices() {
    let mut g: StableDiGraph<(), &str> = StableDiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let e0 = g.add_edge(a, b, "warp");
    let e1 = g.add_edge(b, c, "weft");
    g.remove_edge(e0);
    // Unlike Graph, e1 keeps its index and weight.
    assert_eq!(g.edge_weight(e1), Some(&"weft"));
    assert_eq!(g.edge_count(), 1);
}

// ---------------------------------------------------------------------------
// GraphMap
// ---------------------------------------------------------------------------

#[test]
fn generated_graphmap_add_node_idempotent() {
    let mut m: DiGraphMap<&str, u32> = DiGraphMap::new();
    assert_eq!(m.add_node("quill"), "quill");
    assert_eq!(m.add_node("quill"), "quill");
    assert_eq!(m.node_count(), 1);
    assert!(m.contains_node("quill"));
    assert!(!m.contains_node("nib"));
}

#[test]
fn generated_graphmap_add_edge_none_then_replace() {
    let mut m: DiGraphMap<char, u32> = DiGraphMap::new();
    assert_eq!(m.add_edge('p', 'q', 7), None);
    assert_eq!(m.add_edge('p', 'q', 9), Some(7));
    assert_eq!(m.edge_count(), 1);
    assert_eq!(m.edge_weight('p', 'q'), Some(&9));
}

#[test]
fn generated_graphmap_add_edge_implicit_endpoints() {
    let mut m: DiGraphMap<u16, &str> = DiGraphMap::new();
    m.add_edge(31, 47, "sluice");
    assert_eq!(m.node_count(), 2);
    assert!(m.contains_node(31));
    assert!(m.contains_node(47));
    assert!(m.contains_edge(31, 47));
    assert!(!m.contains_edge(47, 31));
}

#[test]
fn generated_graphmap_remove_node_and_edges() {
    let mut m: DiGraphMap<&str, u32> = DiGraphMap::new();
    m.add_edge("mill", "race", 1);
    m.add_edge("race", "weir", 2);
    assert!(m.remove_node("race"));
    assert!(!m.remove_node("race"));
    assert_eq!(m.node_count(), 2);
    assert_eq!(m.edge_count(), 0);
    assert!(!m.contains_edge("mill", "race"));
}

#[test]
fn generated_graphmap_remove_edge_returns_weight() {
    let mut m: DiGraphMap<char, u32> = DiGraphMap::new();
    m.add_edge('x', 'y', 44);
    assert_eq!(m.remove_edge('x', 'y'), Some(44));
    assert_eq!(m.remove_edge('x', 'y'), None);
    // Endpoint keys remain after edge removal.
    assert!(m.contains_node('x'));
    assert!(m.contains_node('y'));
}

#[test]
fn generated_graphmap_edge_weight_mut() {
    let mut m: DiGraphMap<u8, u32> = DiGraphMap::new();
    m.add_edge(1, 2, 10);
    *m.edge_weight_mut(1, 2).unwrap() += 5;
    assert_eq!(m.edge_weight(1, 2), Some(&15));
    assert_eq!(m.edge_weight(2, 1), None);
}

#[test]
fn generated_graphmap_undirected_normalizes_endpoints() {
    let mut m: UnGraphMap<i32, &str> = UnGraphMap::new();
    m.add_edge(5, 2, "quay");
    m.add_edge(1, 7, "dock");
    let edges: Vec<(i32, i32, &str)> = m.all_edges().map(|(a, b, w)| (a, b, *w)).collect();
    // Stored endpoint pair is normalized smaller-first; insertion order kept.
    assert_eq!(edges, vec![(2, 5, "quay"), (1, 7, "dock")]);
}

#[test]
fn generated_graphmap_undirected_same_edge_both_orders() {
    let mut m: UnGraphMap<char, u32> = UnGraphMap::new();
    assert_eq!(m.add_edge('k', 'd', 3), None);
    // The reverse orientation names the same edge.
    assert_eq!(m.add_edge('d', 'k', 8), Some(3));
    assert_eq!(m.edge_count(), 1);
    assert_eq!(m.edge_weight('k', 'd'), Some(&8));
    assert_eq!(m.edge_weight('d', 'k'), Some(&8));
}

#[test]
fn generated_graphmap_nodes_in_insertion_order() {
    let mut m: DiGraphMap<&str, ()> = DiGraphMap::new();
    m.add_node("gorse");
    m.add_edge("heath", "furze", ());
    let nodes: Vec<&str> = m.nodes().collect();
    assert_eq!(nodes, vec!["gorse", "heath", "furze"]);
}

#[test]
fn generated_graphmap_all_edges_in_insertion_order() {
    let mut m: DiGraphMap<u8, u32> = DiGraphMap::new();
    m.add_edge(4, 2, 100);
    m.add_edge(1, 4, 101);
    m.add_edge(2, 1, 102);
    let edges: Vec<(u8, u8, u32)> = m.all_edges().map(|(a, b, w)| (a, b, *w)).collect();
    assert_eq!(edges, vec![(4, 2, 100), (1, 4, 101), (2, 1, 102)]);
}

#[test]
fn generated_graphmap_neighbors_directed() {
    let mut m: DiGraphMap<char, u32> = DiGraphMap::new();
    m.add_edge('m', 'a', 1);
    m.add_edge('m', 'z', 2);
    m.add_edge('q', 'm', 3);
    let out: HashSet<char> = m.neighbors('m').collect();
    assert_eq!(out, HashSet::from(['a', 'z']));
    let inc: Vec<char> = m.neighbors_directed('m', Incoming).collect();
    assert_eq!(inc, vec!['q']);
}

#[test]
fn generated_graphmap_from_edges() {
    let m = DiGraphMap::<i32, i32>::from_edges([(1, 2, 4), (2, 3, 5)]);
    assert_eq!(m.node_count(), 3);
    assert_eq!(m.edge_count(), 2);
    assert_eq!(m.edge_weight(2, 3), Some(&5));
}

#[test]
fn generated_graphmap_self_loop() {
    let mut m: DiGraphMap<&str, u32> = DiGraphMap::new();
    m.add_edge("coil", "coil", 9);
    assert_eq!(m.node_count(), 1);
    assert!(m.contains_edge("coil", "coil"));
    assert_eq!(m.edge_weight("coil", "coil"), Some(&9));
}

#[test]
fn generated_graphmap_into_graph_insertion_order() {
    let mut m: DiGraphMap<&str, u32> = DiGraphMap::new();
    m.add_edge("stern", "bow", 2);
    m.add_node("mast");
    let g: Graph<&str, u32, Directed> = m.into_graph();
    let weights: Vec<&str> = g.node_weights().copied().collect();
    assert_eq!(weights, vec!["stern", "bow", "mast"]);
    let e = g.find_edge(NodeIndex::new(0), NodeIndex::new(1)).unwrap();
    assert_eq!(g[e], 2);
}

// ---------------------------------------------------------------------------
// Traversal visitors and view adapters
// ---------------------------------------------------------------------------

// Shared traversal fixture: hub -> east (first), hub -> west (second),
// east -> pier. Neighbor order at hub is [west, east].
fn traversal_fixture() -> (DiGraph<&'static str, u32>, [NodeIndex; 4]) {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let hub = g.add_node("hub");
    let east = g.add_node("east");
    let west = g.add_node("west");
    let pier = g.add_node("pier");
    g.add_edge(hub, east, 1);
    g.add_edge(hub, west, 2);
    g.add_edge(east, pier, 3);
    (g, [hub, east, west, pier])
}

#[test]
fn generated_bfs_start_then_layers_in_neighbor_order() {
    let (g, [hub, east, west, pier]) = traversal_fixture();
    let mut bfs = Bfs::new(&g, hub);
    let mut order = Vec::new();
    while let Some(n) = bfs.next(&g) {
        order.push(n);
    }
    assert_eq!(order, vec![hub, west, east, pier]);
}

#[test]
fn generated_dfs_preorder_explores_earliest_edge_first() {
    let (g, [hub, east, west, pier]) = traversal_fixture();
    let mut dfs = Dfs::new(&g, hub);
    let mut order = Vec::new();
    while let Some(n) = dfs.next(&g) {
        order.push(n);
    }
    // Children are explored in reverse neighbor order: east's branch first.
    assert_eq!(order, vec![hub, east, pier, west]);
}

#[test]
fn generated_dfs_postorder_children_before_parent() {
    let (g, [hub, east, west, pier]) = traversal_fixture();
    let mut post = DfsPostOrder::new(&g, hub);
    let mut order = Vec::new();
    while let Some(n) = post.next(&g) {
        order.push(n);
    }
    assert_eq!(order, vec![pier, east, west, hub]);
}

#[test]
fn generated_topo_yields_valid_order() {
    let (g, [hub, east, _west, pier]) = traversal_fixture();
    let mut topo = Topo::new(&g);
    let mut order = Vec::new();
    while let Some(n) = topo.next(&g) {
        order.push(n);
    }
    assert_eq!(order.len(), 4);
    let pos = |n: NodeIndex| order.iter().position(|&x| x == n).unwrap();
    assert!(pos(hub) < pos(east));
    assert!(pos(east) < pos(pier));
}

#[test]
fn generated_topo_skips_cycle_members() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let lone = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, a, ());
    let mut topo = Topo::new(&g);
    let mut order = Vec::new();
    while let Some(n) = topo.next(&g) {
        order.push(n);
    }
    assert_eq!(order, vec![lone]);
}

#[test]
fn generated_visitor_yields_nodes_once_on_diamond() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let top = g.add_node(());
    let l = g.add_node(());
    let r = g.add_node(());
    let bottom = g.add_node(());
    g.add_edge(top, l, ());
    g.add_edge(top, r, ());
    g.add_edge(l, bottom, ());
    g.add_edge(r, bottom, ());
    let mut bfs = Bfs::new(&g, top);
    let mut seen = Vec::new();
    while let Some(n) = bfs.next(&g) {
        seen.push(n);
    }
    assert_eq!(seen.len(), 4);
    let unique: HashSet<_> = seen.iter().copied().collect();
    assert_eq!(unique.len(), 4);
}

#[test]
fn generated_dfs_move_to_keeps_visit_map() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let d = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(c, d, ());
    g.add_edge(c, b, ()); // b is reachable from both components
    let mut dfs = Dfs::new(&g, a);
    let mut seen = Vec::new();
    while let Some(n) = dfs.next(&g) {
        seen.push(n);
    }
    dfs.move_to(c);
    while let Some(n) = dfs.next(&g) {
        seen.push(n);
    }
    // b was already visited in the first walk and is not repeated.
    assert_eq!(seen, vec![a, b, c, d]);
}

#[test]
fn generated_reversed_neighbors_swapped() {
    let (g, [hub, east, _west, pier]) = traversal_fixture();
    let mut bfs = Bfs::new(Reversed(&g), pier);
    let mut order = Vec::new();
    while let Some(n) = bfs.next(Reversed(&g)) {
        order.push(n);
    }
    assert_eq!(order, vec![pier, east, hub]);
}

#[test]
fn generated_node_filtered_hides_node_and_edges() {
    let (g, [hub, east, west, pier]) = traversal_fixture();
    // Hide east: pier becomes unreachable from hub.
    let view = NodeFiltered(&g, |n: NodeIndex| n != east);
    let mut bfs = Bfs::new(&view, hub);
    let mut seen = Vec::new();
    while let Some(n) = bfs.next(&view) {
        seen.push(n);
    }
    assert_eq!(seen, vec![hub, west]);
    let _ = pier;
}

#[test]
fn generated_edge_filtered_from_fn_hides_edges() {
    let (g, [hub, east, west, pier]) = traversal_fixture();
    // Drop the east -> pier edge (weight 3).
    let view = EdgeFiltered::from_fn(&g, |e| *e.weight() < 3);
    let mut bfs = Bfs::new(&view, hub);
    let mut seen = Vec::new();
    while let Some(n) = bfs.next(&view) {
        seen.push(n);
    }
    assert_eq!(seen, vec![hub, west, east]);
    let _ = pier;
}

// ---------------------------------------------------------------------------
// Graph analysis
// ---------------------------------------------------------------------------

#[test]
fn generated_connected_components_weak_and_isolated() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let _lone = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(c, b, ()); // weakly connects c to {a, b}
    assert_eq!(connected_components(&g), 2);
}

#[test]
fn generated_connected_components_undirected() {
    let g = UnGraph::<(), ()>::from_edges([(0, 1), (2, 3), (3, 4)]);
    assert_eq!(connected_components(&g), 2);
}

#[test]
fn generated_is_cyclic_directed_detects() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, c, ());
    assert!(!is_cyclic_directed(&g));
    g.add_edge(c, a, ());
    assert!(is_cyclic_directed(&g));
}

#[test]
fn generated_is_cyclic_directed_self_loop() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    assert!(!is_cyclic_directed(&g));
    g.add_edge(a, a, ());
    assert!(is_cyclic_directed(&g));
}

#[test]
fn generated_is_cyclic_undirected() {
    let mut g: UnGraph<(), ()> = UnGraph::new_undirected();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, c, ());
    assert!(!is_cyclic_undirected(&g));
    g.add_edge(c, a, ());
    assert!(is_cyclic_undirected(&g));
}

#[test]
fn generated_has_path_connecting_follows_direction() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, c, ());
    assert!(has_path_connecting(&g, a, c, None));
    assert!(!has_path_connecting(&g, c, a, None));
    // Every node reaches itself.
    assert!(has_path_connecting(&g, b, b, None));
}

#[test]
fn generated_toposort_ok_successor_rule() {
    let mut g: DiGraph<&str, ()> = DiGraph::new();
    let seed = g.add_node("seed");
    let sprout = g.add_node("sprout");
    let stalk = g.add_node("stalk");
    let ear = g.add_node("ear");
    g.add_edge(seed, sprout, ());
    g.add_edge(sprout, stalk, ());
    g.add_edge(seed, stalk, ());
    g.add_edge(stalk, ear, ());
    let order = toposort(&g, None).unwrap();
    assert_eq!(order.len(), 4);
    let pos = |n: NodeIndex| order.iter().position(|&x| x == n).unwrap();
    for e in g.edge_references() {
        assert!(pos(e.source()) < pos(e.target()));
    }
}

#[test]
fn generated_toposort_cycle_error_names_participant() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let lone = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, a, ());
    let err = toposort(&g, None).unwrap_err();
    let culprit = err.node_id();
    assert!(culprit == a || culprit == b);
    assert_ne!(culprit, lone);
}

#[test]
fn generated_toposort_self_loop_is_cycle() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    g.add_edge(a, a, ());
    let err = toposort(&g, None).unwrap_err();
    assert_eq!(err.node_id(), a);
}

fn normalize_components(comps: &[Vec<NodeIndex>]) -> BTreeSet<Vec<usize>> {
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
fn generated_kosaraju_partitions_by_mutual_reachability() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, a, ());
    g.add_edge(b, c, ());
    let comps = kosaraju_scc(&g);
    assert_eq!(comps.len(), 2);
    assert_eq!(
        normalize_components(&comps),
        BTreeSet::from([vec![0, 1], vec![2]])
    );
}

#[test]
fn generated_tarjan_partitions_by_mutual_reachability() {
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let d = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, c, ());
    g.add_edge(c, a, ());
    g.add_edge(c, d, ());
    let comps = tarjan_scc(&g);
    assert_eq!(comps.len(), 2);
    assert_eq!(
        normalize_components(&comps),
        BTreeSet::from([vec![0, 1, 2], vec![3]])
    );
}

#[test]
fn generated_scc_postorder_sink_component_first() {
    // {a, b} is a cycle that links to sink node c: c's component must
    // appear before the {a, b} component.
    let mut g: DiGraph<(), ()> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, ());
    g.add_edge(b, a, ());
    g.add_edge(b, c, ());
    for comps in [kosaraju_scc(&g), tarjan_scc(&g)] {
        assert_eq!(comps[0].iter().map(|n| n.index()).collect::<Vec<_>>(), vec![2]);
        assert_eq!(comps[1].len(), 2);
    }
}

#[test]
fn generated_condensation_acyclic_drops_intra_edges() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let gale = g.add_node("gale");
    let sleet = g.add_node("sleet");
    let hail = g.add_node("hail");
    g.add_edge(gale, sleet, 1);
    g.add_edge(sleet, gale, 2);
    g.add_edge(sleet, hail, 3);
    let cond = condensation(g, true);
    assert_eq!(cond.node_count(), 2);
    assert_eq!(cond.edge_count(), 1);
    let groups: BTreeSet<Vec<&str>> = cond
        .node_weights()
        .map(|ws| {
            let mut v = ws.clone();
            v.sort();
            v
        })
        .collect();
    assert_eq!(
        groups,
        BTreeSet::from([vec!["gale", "sleet"], vec!["hail"]])
    );
    assert!(!is_cyclic_directed(&cond));
}

#[test]
fn generated_condensation_keeps_all_edges_when_not_acyclic() {
    let mut g: DiGraph<&str, u32> = DiGraph::new();
    let gale = g.add_node("gale");
    let sleet = g.add_node("sleet");
    let hail = g.add_node("hail");
    g.add_edge(gale, sleet, 1);
    g.add_edge(sleet, gale, 2);
    g.add_edge(sleet, hail, 3);
    let cond = condensation(g, false);
    assert_eq!(cond.node_count(), 2);
    // Every original edge preserved: the two intra-component edges become
    // self-loops on the merged node.
    assert_eq!(cond.edge_count(), 3);
    assert!(is_cyclic_directed(&cond));
}

// ---------------------------------------------------------------------------
// Path finding and spanning trees
// ---------------------------------------------------------------------------

#[test]
fn generated_dijkstra_costs_and_unreachable_absent() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let off = g.add_node(());
    g.add_edge(a, b, 4);
    g.add_edge(b, c, 3);
    g.add_edge(a, c, 10);
    g.add_edge(off, a, 1); // off reaches a, but a does not reach off
    let costs = dijkstra(&g, a, None, |e| *e.weight());
    assert_eq!(costs.get(&a), Some(&0));
    assert_eq!(costs.get(&b), Some(&4));
    assert_eq!(costs.get(&c), Some(&7));
    assert_eq!(costs.get(&off), None);
    assert_eq!(costs.len(), 3);
}

#[test]
fn generated_dijkstra_with_goal_contains_goal() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let d = g.add_node(());
    g.add_edge(a, b, 2);
    g.add_edge(b, c, 2);
    g.add_edge(c, d, 2);
    let costs = dijkstra(&g, a, Some(c), |e| *e.weight());
    assert_eq!(costs.get(&c), Some(&4));
    assert_eq!(costs.get(&a), Some(&0));
}

#[test]
fn generated_astar_returns_cost_and_path() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let d = g.add_node(());
    g.add_edge(a, b, 1);
    g.add_edge(b, d, 1);
    g.add_edge(a, c, 5);
    g.add_edge(c, d, 1);
    let (cost, path) = astar(&g, a, |n| n == d, |e| *e.weight(), |_| 0).unwrap();
    assert_eq!(cost, 2);
    assert_eq!(path, vec![a, b, d]);
}

#[test]
fn generated_astar_unreachable_none() {
    let mut g: DiGraph<(), u32> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let stranded = g.add_node(());
    g.add_edge(a, b, 1);
    assert_eq!(astar(&g, a, |n| n == stranded, |e| *e.weight(), |_| 0), None);
}

#[test]
fn generated_bellman_ford_distances_and_predecessors() {
    let mut g: DiGraph<(), f64> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    let far = g.add_node(());
    g.add_edge(a, b, 2.0);
    g.add_edge(b, c, 3.0);
    g.add_edge(a, c, 9.0);
    let paths = bellman_ford(&g, a).unwrap();
    assert_eq!(paths.distances[a.index()], 0.0);
    assert_eq!(paths.distances[b.index()], 2.0);
    assert_eq!(paths.distances[c.index()], 5.0);
    assert!(paths.distances[far.index()].is_infinite());
    assert_eq!(paths.predecessors[a.index()], None);
    assert_eq!(paths.predecessors[b.index()], Some(a));
    assert_eq!(paths.predecessors[c.index()], Some(b));
    assert_eq!(paths.predecessors[far.index()], None);
}

#[test]
fn generated_bellman_ford_negative_edge_ok() {
    let mut g: DiGraph<(), f64> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    let c = g.add_node(());
    g.add_edge(a, b, 4.0);
    g.add_edge(b, c, -2.0);
    g.add_edge(a, c, 3.5);
    let paths = bellman_ford(&g, a).unwrap();
    assert_eq!(paths.distances[c.index()], 2.0);
    assert_eq!(paths.predecessors[c.index()], Some(b));
}

#[test]
fn generated_bellman_ford_negative_cycle_error() {
    let mut g: DiGraph<(), f64> = DiGraph::new();
    let a = g.add_node(());
    let b = g.add_node(());
    g.add_edge(a, b, 1.0);
    g.add_edge(b, a, -3.0);
    assert!(bellman_ford(&g, a).is_err());
    // The same edge pair with a non-negative total is fine.
    let mut ok: DiGraph<(), f64> = DiGraph::new();
    let x = ok.add_node(());
    let y = ok.add_node(());
    ok.add_edge(x, y, 1.0);
    ok.add_edge(y, x, 3.0);
    let paths = bellman_ford(&ok, x).unwrap();
    assert_eq!(paths.distances[y.index()], 1.0);
}

#[test]
fn generated_min_spanning_tree_element_stream() {
    let mut g: UnGraph<&str, u32> = UnGraph::new_undirected();
    let ash = g.add_node("ash");
    let birch = g.add_node("birch");
    let cedar = g.add_node("cedar");
    g.add_edge(ash, birch, 4);
    g.add_edge(birch, cedar, 1);
    g.add_edge(ash, cedar, 2);
    let elems: Vec<Element<&str, u32>> = min_spanning_tree(&g).collect();
    let nodes: Vec<&str> = elems
        .iter()
        .filter_map(|e| match e {
            Element::Node { weight } => Some(*weight),
            _ => None,
        })
        .collect();
    assert_eq!(nodes, vec!["ash", "birch", "cedar"]);
    let mut edge_weights: Vec<u32> = elems
        .iter()
        .filter_map(|e| match e {
            Element::Edge { weight, .. } => Some(*weight),
            _ => None,
        })
        .collect();
    edge_weights.sort();
    assert_eq!(edge_weights, vec![1, 2]);
}

#[test]
fn generated_from_elements_materializes_tree() {
    let mut g: UnGraph<&str, u32> = UnGraph::new_undirected();
    let ash = g.add_node("ash");
    let birch = g.add_node("birch");
    let cedar = g.add_node("cedar");
    g.add_edge(ash, birch, 4);
    g.add_edge(birch, cedar, 1);
    g.add_edge(ash, cedar, 2);
    let tree: UnGraph<&str, u32> = UnGraph::from_elements(min_spanning_tree(&g));
    assert_eq!(tree.node_count(), 3);
    assert_eq!(tree.edge_count(), 2);
    assert_eq!(tree.edge_weights().sum::<u32>(), 3);
    assert_eq!(connected_components(&tree), 1);
}
