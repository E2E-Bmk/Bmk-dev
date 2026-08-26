// Solver + provider + range-algebra interplay.
mod solving {
    use super::*;

    #[test]
    fn generated_diamond_intersection_solution() {
        let mut dp = NumProvider::new();
        dp.add_dependencies("apex", 1u32, [("left", NumVS::full()), ("right", NumVS::full())]);
        dp.add_dependencies("left", 2u32, [("base", NumVS::between(2u32, 4u32))]);
        dp.add_dependencies("left", 1u32, [("base", NumVS::between(1u32, 3u32))]);
        dp.add_dependencies("right", 2u32, [("base", NumVS::between(3u32, 5u32))]);
        dp.add_dependencies("right", 1u32, [("base", NumVS::between(1u32, 2u32))]);
        for v in 1..=4u32 {
            dp.add_dependencies("base", v, []);
        }
        let sol = resolve(&dp, "apex", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([("apex", 1u32), ("base", 3u32), ("left", 2u32), ("right", 2u32)])
        );
        // the selected base lies in the intersection of both requesting ranges
        let requested = NumVS::between(2u32, 4u32).intersection(&NumVS::between(3u32, 5u32));
        assert!(requested.contains(&sol["base"]));
        assert_eq!(requested, NumVS::between(3u32, 4u32));
    }

    #[test]
    fn generated_deep_backtrack_solution() {
        let mut dp = NumProvider::new();
        dp.add_dependencies("envoy", 1u32, [("carto", NumVS::full()), ("flint", NumVS::full())]);
        dp.add_dependencies("carto", 4u32, [("plinth", NumVS::higher_than(3u32))]);
        dp.add_dependencies("carto", 3u32, [("plinth", NumVS::higher_than(3u32))]);
        dp.add_dependencies("carto", 2u32, [("plinth", NumVS::lower_than(2u32))]);
        dp.add_dependencies("flint", 1u32, [("plinth", NumVS::lower_than(2u32))]);
        dp.add_dependencies("plinth", 1u32, []);
        dp.add_dependencies("plinth", 2u32, []);
        dp.add_dependencies("plinth", 4u32, []);
        // the two newest carto versions must be abandoned to satisfy flint
        let sol = resolve(&dp, "envoy", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([("envoy", 1u32), ("carto", 2u32), ("flint", 1u32), ("plinth", 2u32)])
        );
    }

    #[test]
    fn generated_solution_satisfies_all_constraints() {
        let mut dp = NumProvider::new();
        dp.add_dependencies(
            "port",
            1u32,
            [
                ("dock", NumVS::full()),
                ("crane", NumVS::between(2u32, 5u32)),
                ("radio", NumVS::between(1u32, 4u32)),
            ],
        );
        dp.add_dependencies("dock", 1u32, [("rope", NumVS::between(1u32, 3u32))]);
        dp.add_dependencies("dock", 2u32, [("rope", NumVS::between(2u32, 4u32))]);
        dp.add_dependencies("crane", 2u32, [("rope", NumVS::between(1u32, 4u32))]);
        dp.add_dependencies("crane", 4u32, [("rope", NumVS::between(3u32, 6u32))]);
        dp.add_dependencies("radio", 1u32, []);
        dp.add_dependencies("radio", 3u32, [("beacon", NumVS::full())]);
        dp.add_dependencies("beacon", 1u32, []);
        for v in [1u32, 2, 3, 5] {
            dp.add_dependencies("rope", v, []);
        }
        let sol = resolve(&dp, "port", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([
                ("port", 1u32),
                ("dock", 2u32),
                ("crane", 4u32),
                ("radio", 3u32),
                ("beacon", 1u32),
                ("rope", 3u32),
            ])
        );
        // cross-view check: walk the provider and verify every requesting
        // range contains the selected version of its target
        for (package, version) in sol.iter() {
            match dp.get_dependencies(package, version).unwrap() {
                Dependencies::Available(constraints) => {
                    for (needed, range) in constraints.iter() {
                        assert!(
                            range.contains(&sol[needed]),
                            "{needed} {} escapes {range}",
                            sol[needed]
                        );
                    }
                }
                Dependencies::Unavailable(_) => panic!("selected pair must be registered"),
            }
        }
    }

    #[test]
    fn generated_string_packages_semver_universe() {
        let mut dp = OfflineDependencyProvider::<String, SemVS>::new();
        dp.add_dependencies(
            "atlas".to_string(),
            (1, 0, 0),
            [("plate".to_string(), semver_range((0, 4, 0), (0, 9, 0)))],
        );
        dp.add_dependencies("plate".to_string(), (0, 4, 2), []);
        dp.add_dependencies("plate".to_string(), (0, 8, 5), []);
        dp.add_dependencies("plate".to_string(), (0, 9, 0), []);
        let sol = resolve(&dp, "atlas".to_string(), (1, 0, 0)).unwrap();
        assert_eq!(sol["plate"], SemanticVersion::new(0, 8, 5));
        assert_eq!(sol["atlas"], SemanticVersion::one());
        assert_eq!(sol.len(), 2);
    }

    #[test]
    fn generated_failing_determinism_across_runs() {
        let mut dp = SemProvider::new();
        dp.add_dependencies("helm", (1, 0, 0), [("mast", semver_range((1, 0, 0), (2, 0, 0)))]);
        dp.add_dependencies(
            "mast",
            (1, 0, 0),
            [
                ("flag", semver_range((1, 0, 0), (2, 0, 0))),
                ("rope", semver_range((1, 0, 0), (2, 0, 0))),
            ],
        );
        dp.add_dependencies("mast", (1, 1, 0), [("lantern", SemVS::full())]);
        dp.add_dependencies("flag", (1, 0, 0), [("rope", semver_range((2, 0, 0), (3, 0, 0)))]);
        dp.add_dependencies("rope", (1, 0, 0), []);
        dp.add_dependencies("rope", (2, 0, 0), []);
        let render = |collapse: bool| -> String {
            let mut tree = match resolve(&dp, "helm", (1, 0, 0)) {
                Err(PubGrubError::NoSolution(tree)) => tree,
                _ => panic!("expected NoSolution"),
            };
            if collapse {
                tree.collapse_no_versions();
            }
            DefaultStringReporter::report(&tree)
        };
        // identical proof text on every run, raw and collapsed
        assert_eq!(render(false), render(false));
        assert_eq!(render(true), render(true));
    }

    #[test]
    fn generated_custom_lowest_strategy_provider() {
        let mut custom = LowestProvider::new();
        custom.add("apex", 1, vec![("gear", NumVS::between(1u32, 9u32))]);
        custom.add("gear", 2, vec![]);
        custom.add("gear", 5, vec![]);
        let sol = resolve(&custom, "apex", 1u32).unwrap();
        // the solver honors the provider's choice: lowest matching version
        assert_eq!(sorted_num(&sol), BTreeMap::from([("apex", 1u32), ("gear", 2u32)]));
        // the same universe under the in-memory provider picks the newest
        let mut offline = NumProvider::new();
        offline.add_dependencies("apex", 1u32, [("gear", NumVS::between(1u32, 9u32))]);
        offline.add_dependencies("gear", 2u32, []);
        offline.add_dependencies("gear", 5u32, []);
        let newest = resolve(&offline, "apex", 1u32).unwrap();
        assert_eq!(newest["gear"], 5u32);
    }

    #[test]
    fn generated_cancel_budget_provider() {
        #[derive(Debug)]
        struct BudgetSpent;
        impl fmt::Display for BudgetSpent {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                write!(f, "poll budget spent")
            }
        }
        impl std::error::Error for BudgetSpent {}

        struct BudgetProvider {
            inner: NumProvider,
            polls: RefCell<u32>,
            limit: u32,
        }
        impl DependencyProvider for BudgetProvider {
            type P = &'static str;
            type V = u32;
            type VS = NumVS;
            type M = String;
            type Err = BudgetSpent;
            type Priority = (u32, std::cmp::Reverse<usize>);
            fn prioritize(
                &self,
                package: &Self::P,
                range: &Self::VS,
                stats: &PackageResolutionStatistics,
            ) -> Self::Priority {
                self.inner.prioritize(package, range, stats)
            }
            fn choose_version(&self, package: &Self::P, range: &Self::VS) -> Result<Option<u32>, BudgetSpent> {
                Ok(self.inner.choose_version(package, range).unwrap())
            }
            fn get_dependencies(
                &self,
                package: &Self::P,
                version: &u32,
            ) -> Result<Dependencies<Self::P, Self::VS, String>, BudgetSpent> {
                Ok(self.inner.get_dependencies(package, version).unwrap())
            }
            fn should_cancel(&self) -> Result<(), BudgetSpent> {
                let mut polls = self.polls.borrow_mut();
                *polls += 1;
                if *polls > self.limit {
                    Err(BudgetSpent)
                } else {
                    Ok(())
                }
            }
        }

        let mut inner = NumProvider::new();
        inner.add_dependencies("apex", 1u32, [("mast", NumVS::full())]);
        inner.add_dependencies("mast", 1u32, []);

        // a generous budget lets the solve finish
        let generous = BudgetProvider { inner: inner.clone(), polls: RefCell::new(0), limit: 100 };
        let sol = resolve(&generous, "apex", 1u32).unwrap();
        assert_eq!(sol["mast"], 1u32);
        assert!(*generous.polls.borrow() >= 1);

        // an exhausted budget surfaces as the cancellation variant
        let tight = BudgetProvider { inner, polls: RefCell::new(0), limit: 1 };
        match resolve(&tight, "apex", 1u32) {
            Err(PubGrubError::ErrorInShouldCancel(source)) => {
                assert_eq!(source.to_string(), "poll budget spent");
            }
            other => panic!("expected cancellation, got {:?}", other.map(|_| ())),
        }
        let err = resolve(
            &BudgetProvider {
                inner: {
                    let mut p = NumProvider::new();
                    p.add_dependencies("apex", 1u32, [("mast", NumVS::full())]);
                    p.add_dependencies("mast", 1u32, []);
                    p
                },
                polls: RefCell::new(0),
                limit: 1,
            },
            "apex",
            1u32,
        )
        .unwrap_err();
        assert_eq!(err.to_string(), "The solver was cancelled");
    }

    #[test]
    fn generated_dependencies_fetched_once() {
        let mut provider = LowestProvider::new();
        provider.add("apex", 1, vec![("left", NumVS::full()), ("right", NumVS::full())]);
        provider.add("left", 1, vec![("base", NumVS::full())]);
        provider.add("right", 1, vec![("base", NumVS::full())]);
        provider.add("base", 1, vec![]);
        let sol = resolve(&provider, "apex", 1u32).unwrap();
        assert_eq!(sol.len(), 4);
        let mut calls = provider.dependency_calls.borrow().clone();
        calls.sort();
        // each reachable pair is fetched exactly once, and nothing else is
        assert_eq!(
            calls,
            vec![("apex", 1u32), ("base", 1u32), ("left", 1u32), ("right", 1u32)]
        );
    }
}
