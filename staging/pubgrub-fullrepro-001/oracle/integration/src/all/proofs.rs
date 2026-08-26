// Derivation-tree structure, queries, and collapse transformations.
mod proofs {
    use super::*;

    #[test]
    fn generated_unknown_root_tree_is_single_noversions() {
        let dp = NumProvider::new();
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "keel", 7u32));
        match &tree {
            DerivationTree::External(External::NoVersions(package, set)) => {
                assert_eq!(*package, "keel");
                assert_eq!(set, &NumVS::singleton(7u32));
                assert!(set.contains(&7u32));
            }
            other => panic!("expected a single NoVersions leaf, got {other:?}"),
        }
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "there is no version of keel in 7"
        );
        let census: Vec<_> = tree.packages().into_iter().copied().collect();
        assert_eq!(census, vec!["keel"]);
    }

    #[test]
    fn generated_conflict_tree_structure_and_externals() {
        let mut dp = NumProvider::new();
        dp.add_dependencies(
            "apex",
            1u32,
            [("hull", NumVS::between(1u32, 2u32)), ("sail", NumVS::between(1u32, 2u32))],
        );
        dp.add_dependencies("hull", 1u32, [("gear", NumVS::between(2u32, 3u32))]);
        dp.add_dependencies("sail", 1u32, [("gear", NumVS::between(1u32, 2u32))]);
        dp.add_dependencies("gear", 1u32, []);
        dp.add_dependencies("gear", 2u32, []);
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "apex", 1u32));

        // the root of a solver-produced proof concludes the root's impossibility
        let derived = match &tree {
            DerivationTree::Derived(derived) => derived,
            DerivationTree::External(e) => panic!("expected a derived root, got {e}"),
        };
        assert_eq!(derived.terms.len(), 1);
        assert_eq!(
            derived.terms.get("apex"),
            Some(&Term::Positive(NumVS::singleton(1u32)))
        );

        // every leaf fact, left to right
        let mut externals = Vec::new();
        collect_externals(&tree, &mut externals);
        let mut displays: Vec<String> = externals.iter().map(|e| e.to_string()).collect();
        displays.sort();
        assert_eq!(
            displays,
            vec![
                "apex 1 depends on hull >=1, <2".to_string(),
                "apex 1 depends on sail >=1, <2".to_string(),
                "hull 1 depends on gear >=2, <3".to_string(),
                "sail 1 depends on gear >=1, <2".to_string(),
                "there is no version of hull in >1, <2".to_string(),
                "there is no version of sail in >1, <2".to_string(),
            ]
        );

        // census covers every named package, including the contended one
        let mut census: Vec<_> = tree.packages().into_iter().copied().collect();
        census.sort();
        assert_eq!(census, vec!["apex", "gear", "hull", "sail"]);
    }

    #[test]
    fn generated_collapse_folds_noversions_into_fact() {
        let mut dp = NumProvider::new();
        dp.add_dependencies("apex", 1u32, [("mast", NumVS::higher_than(2u32))]);
        dp.add_dependencies("mast", 1u32, []);
        let mut tree = expect_no_solution::<NumProvider>(resolve(&dp, "apex", 1u32));

        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because there is no version of mast in >=2 and apex 1 depends on mast >=2, \
             apex 1 is forbidden."
        );
        match &tree {
            DerivationTree::Derived(derived) => {
                assert!(matches!(
                    derived.cause1.as_ref(),
                    DerivationTree::External(External::NoVersions(_, _))
                ));
            }
            other => panic!("expected derived root, got {other:?}"),
        }

        tree.collapse_no_versions();
        // the NoVersions leaf was folded into the surviving dependency fact
        match &tree {
            DerivationTree::External(external @ External::FromDependencyOf(p, _, q, _)) => {
                assert_eq!(*p, "apex");
                assert_eq!(*q, "mast");
                assert_eq!(external.to_string(), "apex 1 depends on mast >=2");
            }
            other => panic!("expected a folded dependency fact, got {other:?}"),
        }
        assert_eq!(DefaultStringReporter::report(&tree), "apex 1 depends on mast >=2");
        let mut census: Vec<_> = tree.packages().into_iter().copied().collect();
        census.sort();
        assert_eq!(census, vec!["apex", "mast"]);
    }

    #[test]
    fn generated_collapse_merges_partial_conflict() {
        let mut dp = NumProvider::new();
        dp.add_dependencies(
            "apex",
            1u32,
            [("hull", NumVS::between(1u32, 2u32)), ("sail", NumVS::between(1u32, 2u32))],
        );
        dp.add_dependencies("hull", 1u32, [("gear", NumVS::between(2u32, 3u32))]);
        dp.add_dependencies("sail", 1u32, [("gear", NumVS::between(1u32, 2u32))]);
        dp.add_dependencies("gear", 1u32, []);
        dp.add_dependencies("gear", 2u32, []);
        let mut tree = expect_no_solution::<NumProvider>(resolve(&dp, "apex", 1u32));
        tree.collapse_no_versions();

        // only dependency facts survive: each NoVersions sentence was folded away
        let mut externals = Vec::new();
        collect_externals(&tree, &mut externals);
        assert_eq!(externals.len(), 4);
        assert!(externals
            .iter()
            .all(|e| matches!(e, External::FromDependencyOf(_, _, _, _))));
        let mut displays: Vec<String> = externals.iter().map(|e| e.to_string()).collect();
        displays.sort();
        assert_eq!(
            displays,
            vec![
                "apex 1 depends on hull >=1, <2".to_string(),
                "apex 1 depends on sail >=1, <2".to_string(),
                "hull >=1, <2 depends on gear >=2, <3".to_string(),
                "sail 1 depends on gear >=1, <2".to_string(),
            ]
        );

        // the collapsed proof still concludes the same root impossibility
        let report = DefaultStringReporter::report(&tree);
        assert!(report.ends_with("apex 1 is forbidden."));
        assert!(!report.contains("there is no version"));
        let mut census: Vec<_> = tree.packages().into_iter().copied().collect();
        census.sort();
        assert_eq!(census, vec!["apex", "gear", "hull", "sail"]);
    }

    #[test]
    fn generated_hand_built_shared_node_cited_once() {
        type Tree = DerivationTree<&'static str, NumVS, String>;
        let shared: Tree = DerivationTree::Derived(Derived {
            terms: {
                let mut m: Map<&'static str, Term<NumVS>> = Map::default();
                m.insert("mast", Term::Positive(NumVS::singleton(1u32)));
                m
            },
            shared_id: Some(42),
            cause1: Arc::new(DerivationTree::External(External::FromDependencyOf(
                "mast",
                NumVS::singleton(1u32),
                "boom",
                NumVS::between(2u32, 3u32),
            ))),
            cause2: Arc::new(DerivationTree::External(External::NoVersions(
                "boom",
                NumVS::between(2u32, 3u32),
            ))),
        });
        let second: Tree = DerivationTree::Derived(Derived {
            terms: {
                let mut m: Map<&'static str, Term<NumVS>> = Map::default();
                m.insert("deck", Term::Positive(NumVS::singleton(1u32)));
                m
            },
            shared_id: None,
            cause1: Arc::new(shared.clone()),
            cause2: Arc::new(DerivationTree::External(External::FromDependencyOf(
                "deck",
                NumVS::singleton(1u32),
                "mast",
                NumVS::singleton(1u32),
            ))),
        });
        let root: Tree = DerivationTree::Derived(Derived {
            terms: Map::default(),
            shared_id: None,
            cause1: Arc::new(shared),
            cause2: Arc::new(second),
        });

        // the shared node is explained once, then cited by its line reference;
        // the empty root terms render as the version-solving-failed sentence
        assert_eq!(
            DefaultStringReporter::report(&root),
            "Because mast 1 depends on boom >=2, <3 and there is no version of boom in \
             >=2, <3, mast 1 is forbidden. (1)\n\nBecause mast 1 is forbidden (1) and \
             deck 1 depends on mast 1, deck 1 is forbidden.\nAnd because mast 1 is \
             forbidden (1), version solving failed."
        );
        let mut census: Vec<_> = root.packages().into_iter().copied().collect();
        census.sort();
        assert_eq!(census, vec!["boom", "deck", "mast"]);
    }
}
