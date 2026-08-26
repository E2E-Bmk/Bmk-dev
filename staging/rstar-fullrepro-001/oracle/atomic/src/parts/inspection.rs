// Tree inspection: root node access, leaf/content agreement, envelope
// containment invariants, empty-tree structure.

fn collect_leaves(node: &rstar::ParentNode<[f64; 2]>, out: &mut Vec<[f64; 2]>) {
    for child in node.children() {
        match child {
            rstar::RTreeNode::Leaf(p) => out.push(*p),
            rstar::RTreeNode::Parent(inner) => collect_leaves(inner, out),
        }
    }
}

fn check_envelopes(node: &rstar::ParentNode<[f64; 2]>) {
    let env = node.envelope();
    for child in node.children() {
        match child {
            rstar::RTreeNode::Leaf(p) => {
                assert!(env.contains_envelope(&p.envelope()));
                assert!(child.is_leaf());
            }
            rstar::RTreeNode::Parent(inner) => {
                assert!(env.contains_envelope(&inner.envelope()));
                assert!(!child.is_leaf());
                check_envelopes(inner);
            }
        }
    }
}

#[test]
fn generated_empty_tree_root() {
    let tree: RTree<[f64; 2]> = RTree::new();
    let root = tree.root();
    assert!(root.children().is_empty());
    assert_eq!(root.envelope(), AABB::new_empty());
}

#[test]
fn generated_leaf_multiset_equals_content() {
    let elements: Vec<[f64; 2]> =
        (0..25).map(|i| [((i * 3) % 7) as f64, ((i * 2) % 5) as f64]).collect();
    let tree = RTree::bulk_load(elements.clone());
    let mut leaves = Vec::new();
    collect_leaves(tree.root(), &mut leaves);
    assert_eq!(sorted(leaves), sorted(elements));
}

#[test]
fn generated_envelope_containment_up_the_tree() {
    let elements: Vec<[f64; 2]> =
        (0..40).map(|i| [((i * 7) % 13) as f64, ((i * 11) % 17) as f64]).collect();
    let mut tree = RTree::new();
    for e in &elements {
        tree.insert(*e);
    }
    check_envelopes(tree.root());
    // the root envelope is the minimal merged envelope of the content:
    let merged = AABB::<[f64; 2]>::from_points(elements.iter());
    assert_eq!(tree.root().envelope(), merged);
}

#[test]
fn generated_root_envelope_tracks_removal() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 1.0], [10.0, 10.0]]);
    assert_eq!(tree.root().envelope(), AABB::from_corners([0.0, 0.0], [10.0, 10.0]));
    tree.remove(&[10.0, 10.0]);
    assert_eq!(tree.root().envelope(), AABB::from_corners([0.0, 0.0], [1.0, 1.0]));
}
