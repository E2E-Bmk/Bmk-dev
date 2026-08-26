// Cross-view workflows: algebra feeding universes, success/failure flips,
// version arithmetic, clone independence, census/report agreement.
mod compose {
    use super::*;

    #[test]
    fn generated_flip_success_to_failure() {
        let build = |with_matching: bool| {
            let mut dp = NumProvider::new();
            dp.add_dependencies("loom", 1u32, [("shuttle", NumVS::between(2u32, 4u32))]);
            dp.add_dependencies("shuttle", 1u32, []);
            if with_matching {
                dp.add_dependencies("shuttle", 3u32, []);
            }
            dp
        };

        let sol = resolve(&build(true), "loom", 1u32).unwrap();
        assert_eq!(sorted_num(&sol), BTreeMap::from([("loom", 1u32), ("shuttle", 3u32)]));

        // withdrawing the only matching version flips the outcome to a proof
        let tree = expect_no_solution::<NumProvider>(resolve(&build(false), "loom", 1u32));
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because there is no version of shuttle in >=2, <4 and loom 1 depends on \
             shuttle >=2, <4, loom 1 is forbidden."
        );
        let mut collapsed = tree.clone();
        collapsed.collapse_no_versions();
        assert_eq!(
            DefaultStringReporter::report(&collapsed),
            "loom 1 depends on shuttle >=2, <4"
        );
    }

    #[test]
    fn generated_algebra_computed_constraint_flows() {
        // the constraint is computed with set algebra, not written literally
        let banned = NumVS::between(2u32, 3u32).union(&NumVS::between(5u32, 6u32));
        let allowed = banned.complement().intersection(&NumVS::between(1u32, 8u32));
        assert_eq!(format!("{allowed}"), ">=1, <2 | >=3, <5 | >=6, <8");
        assert!(!allowed.contains(&2u32));
        assert!(!allowed.contains(&5u32));
        assert!(allowed.contains(&6u32));

        // only banned versions exist: the canonical display flows into the proof
        let mut dp = NumProvider::new();
        dp.add_dependencies("mill", 1u32, [("grain", allowed.clone())]);
        dp.add_dependencies("grain", 2u32, []);
        dp.add_dependencies("grain", 5u32, []);
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "mill", 1u32));
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because there is no version of grain in >=1, <2 | >=3, <5 | >=6, <8 and \
             mill 1 depends on grain >=1, <2 | >=3, <5 | >=6, <8, mill 1 is forbidden."
        );

        // adding one allowed version flips the same universe to a solution
        let mut dp = NumProvider::new();
        dp.add_dependencies("mill", 1u32, [("grain", allowed.clone())]);
        dp.add_dependencies("grain", 2u32, []);
        dp.add_dependencies("grain", 5u32, []);
        dp.add_dependencies("grain", 6u32, []);
        let sol = resolve(&dp, "mill", 1u32).unwrap();
        assert_eq!(sorted_num(&sol), BTreeMap::from([("mill", 1u32), ("grain", 6u32)]));
        assert!(allowed.contains(&sol["grain"]));
    }

    #[test]
    fn generated_bump_chain_universe() {
        // every version in the universe is derived by bump arithmetic
        let base = SemanticVersion::new(1, 2, 3);
        let window = SemVS::from_range_bounds(base.bump_minor()..base.bump_major());
        assert_eq!(format!("{window}"), ">=1.3.0, <2.0.0");

        let mut dp = SemProvider::new();
        dp.add_dependencies("forge", base, [("ingot", window.clone())]);
        dp.add_dependencies("ingot", base.bump_minor(), []);
        dp.add_dependencies("ingot", base.bump_minor().bump_patch(), []);
        dp.add_dependencies("ingot", base.bump_major(), []);
        let sol = resolve(&dp, "forge", base).unwrap();
        assert_eq!(sol["forge"], base);
        // highest inside the window: 1.3.1, not the excluded 2.0.0
        assert_eq!(sol["ingot"], SemanticVersion::new(1, 3, 1));
        assert!(window.contains(&sol["ingot"]));
        assert!(!window.contains(&base.bump_major()));

        // display/parse round-trip on the selected version
        let rendered = sol["ingot"].to_string();
        assert_eq!(rendered, "1.3.1");
        assert_eq!(rendered.parse::<SemanticVersion>().unwrap(), sol["ingot"]);
    }

    #[test]
    fn generated_clone_then_collapse_leaves_original() {
        let mut dp = SemProvider::new();
        dp.add_dependencies("ferry", (1, 0, 0), [("pier", semver_range((1, 0, 0), (2, 0, 0)))]);
        dp.add_dependencies("pier", (1, 2, 0), [("anchor", semver_range((2, 0, 0), (3, 0, 0)))]);
        dp.add_dependencies("anchor", (1, 5, 0), []);
        let original = expect_no_solution::<SemProvider>(resolve(&dp, "ferry", (1, 0, 0)));
        let raw_report = DefaultStringReporter::report(&original);

        let mut collapsed = original.clone();
        collapsed.collapse_no_versions();
        let collapsed_report = DefaultStringReporter::report(&collapsed);

        // the clone diverged; the original proof is untouched
        assert_ne!(raw_report, collapsed_report);
        assert_eq!(DefaultStringReporter::report(&original), raw_report);
        assert!(raw_report.contains("there is no version of anchor in >=2.0.0, <3.0.0"));
        assert!(!collapsed_report.contains("there is no version"));
        assert_eq!(
            collapsed_report,
            "Because pier >=1.0.0, <2.0.0 depends on anchor >=2.0.0, <3.0.0 and \
             ferry 1.0.0 depends on pier >=1.0.0, <2.0.0, ferry 1.0.0 is forbidden."
        );

        // both proofs still name the same packages
        let mut census_raw: Vec<_> = original.packages().into_iter().copied().collect();
        census_raw.sort();
        let mut census_collapsed: Vec<_> = collapsed.packages().into_iter().copied().collect();
        census_collapsed.sort();
        assert_eq!(census_raw, vec!["anchor", "ferry", "pier"]);
        assert_eq!(census_raw, census_collapsed);
    }

    #[test]
    fn generated_census_matches_report_mentions() {
        let mut dp = NumProvider::new();
        dp.add_dependencies("gantry", 1u32, [("hoist", NumVS::between(10u32, 20u32))]);
        dp.add_dependencies(
            "hoist",
            10u32,
            [("cable", NumVS::between(10u32, 20u32)), ("drum", NumVS::between(10u32, 20u32))],
        );
        dp.add_dependencies(
            "hoist",
            11u32,
            [("pulley", NumVS::between(10u32, 20u32)), ("sheave", NumVS::between(10u32, 20u32))],
        );
        dp.add_dependencies("cable", 10u32, [("drum", NumVS::between(20u32, 30u32))]);
        dp.add_dependencies("drum", 10u32, []);
        dp.add_dependencies("drum", 20u32, []);
        dp.add_dependencies("pulley", 10u32, [("sheave", NumVS::between(20u32, 30u32))]);
        dp.add_dependencies("sheave", 10u32, []);
        dp.add_dependencies("sheave", 20u32, []);

        let error = match resolve(&dp, "gantry", 1u32) {
            Err(error) => error,
            Ok(_) => panic!("expected failure"),
        };
        assert_eq!(error.to_string(), "There is no solution");
        let tree = match error {
            PubGrubError::NoSolution(tree) => tree,
            other => panic!("expected NoSolution, got {other:?}"),
        };

        let mut census: Vec<_> = tree.packages().into_iter().copied().collect();
        census.sort();
        assert_eq!(census, vec!["cable", "drum", "gantry", "hoist", "pulley", "sheave"]);

        // every package the proof names appears in the rendered report
        let report = DefaultStringReporter::report(&tree);
        for package in &census {
            assert!(report.contains(package), "{package} missing from the report");
        }
    }
}
