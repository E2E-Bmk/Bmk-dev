// Provider call discipline: decision order, priority caching, conflict
// statistics, and unavailability metadata.
mod strategy {
    use super::*;

    /// Delegates to the in-memory provider while recording call traffic.
    struct SpyProvider {
        inner: NumProvider,
        chosen: RefCell<Vec<&'static str>>,
        prioritized: RefCell<Vec<(&'static str, String)>>,
    }

    impl SpyProvider {
        fn wrapping(inner: NumProvider) -> Self {
            Self { inner, chosen: RefCell::new(Vec::new()), prioritized: RefCell::new(Vec::new()) }
        }
    }

    impl DependencyProvider for SpyProvider {
        type P = &'static str;
        type V = u32;
        type VS = NumVS;
        type M = String;
        type Err = Infallible;
        type Priority = <NumProvider as DependencyProvider>::Priority;

        fn prioritize(
            &self,
            package: &Self::P,
            range: &Self::VS,
            stats: &PackageResolutionStatistics,
        ) -> Self::Priority {
            self.prioritized.borrow_mut().push((*package, format!("{range}")));
            self.inner.prioritize(package, range, stats)
        }

        fn choose_version(
            &self,
            package: &Self::P,
            range: &Self::VS,
        ) -> Result<Option<u32>, Infallible> {
            self.chosen.borrow_mut().push(*package);
            self.inner.choose_version(package, range)
        }

        fn get_dependencies(
            &self,
            package: &Self::P,
            version: &u32,
        ) -> Result<Dependencies<Self::P, Self::VS, String>, Infallible> {
            self.inner.get_dependencies(package, version)
        }
    }

    #[test]
    fn generated_fewest_candidates_decided_first() {
        let mut inner = NumProvider::new();
        inner.add_dependencies("apex", 1u32, [("rig", NumVS::full()), ("net", NumVS::full())]);
        for v in [1u32, 2, 3] {
            inner.add_dependencies("rig", v, []);
        }
        inner.add_dependencies("net", 1u32, []);
        let spy = SpyProvider::wrapping(inner);
        let sol = resolve(&spy, "apex", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([("apex", 1u32), ("net", 1u32), ("rig", 3u32)])
        );
        // the in-memory strategy decides the package with fewer matching
        // candidates (net: one) before the wider one (rig: three)
        assert_eq!(*spy.chosen.borrow(), vec!["apex", "net", "rig"]);
        // no constraint ever narrowed and no conflict arose, so each package
        // was prioritized exactly once
        let calls = spy.prioritized.borrow();
        let mut sorted: Vec<_> = calls.clone();
        sorted.sort();
        assert_eq!(
            sorted,
            vec![
                ("apex", "1".to_string()),
                ("net", "*".to_string()),
                ("rig", "*".to_string()),
            ]
        );
    }

    #[test]
    fn generated_prioritize_reasked_after_narrowing() {
        let mut inner = NumProvider::new();
        inner.add_dependencies("apex", 1u32, [("cog", NumVS::full()), ("pin", NumVS::full())]);
        inner.add_dependencies("cog", 1u32, [("pin", NumVS::between(1u32, 3u32))]);
        inner.add_dependencies("cog", 2u32, [("pin", NumVS::between(2u32, 4u32))]);
        for v in [1u32, 2, 3, 5] {
            inner.add_dependencies("pin", v, []);
        }
        let spy = SpyProvider::wrapping(inner);
        let sol = resolve(&spy, "apex", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([("apex", 1u32), ("cog", 2u32), ("pin", 3u32)])
        );
        // pin is prioritized under the full set first, then re-asked once its
        // constraint narrows to cog 2's requirement; cog is asked exactly once
        let calls = spy.prioritized.borrow();
        let pin_calls: Vec<&String> =
            calls.iter().filter(|(p, _)| *p == "pin").map(|(_, r)| r).collect();
        assert_eq!(pin_calls, vec!["*", ">=2, <4"]);
        let cog_calls: Vec<&String> =
            calls.iter().filter(|(p, _)| *p == "cog").map(|(_, r)| r).collect();
        assert_eq!(cog_calls, vec!["*"]);
        assert_eq!(
            calls.iter().filter(|(p, _)| *p == "apex").count(),
            1,
            "the root's priority is asked once"
        );
    }

    #[test]
    fn generated_conflict_statistics_observed() {
        struct StatProvider {
            inner: NumProvider,
            seen: RefCell<Vec<(&'static str, u32)>>,
        }
        impl DependencyProvider for StatProvider {
            type P = &'static str;
            type V = u32;
            type VS = NumVS;
            type M = String;
            type Err = Infallible;
            type Priority = <NumProvider as DependencyProvider>::Priority;
            fn prioritize(
                &self,
                package: &Self::P,
                range: &Self::VS,
                stats: &PackageResolutionStatistics,
            ) -> Self::Priority {
                self.seen.borrow_mut().push((*package, stats.conflict_count()));
                self.inner.prioritize(package, range, stats)
            }
            fn choose_version(
                &self,
                package: &Self::P,
                range: &Self::VS,
            ) -> Result<Option<u32>, Infallible> {
                self.inner.choose_version(package, range)
            }
            fn get_dependencies(
                &self,
                package: &Self::P,
                version: &u32,
            ) -> Result<Dependencies<Self::P, Self::VS, String>, Infallible> {
                self.inner.get_dependencies(package, version)
            }
        }

        let mut inner = NumProvider::new();
        inner.add_dependencies("envoy", 1u32, [("carto", NumVS::full()), ("flint", NumVS::full())]);
        inner.add_dependencies("carto", 4u32, [("plinth", NumVS::higher_than(3u32))]);
        inner.add_dependencies("carto", 3u32, [("plinth", NumVS::higher_than(3u32))]);
        inner.add_dependencies("carto", 2u32, [("plinth", NumVS::lower_than(2u32))]);
        inner.add_dependencies("flint", 1u32, [("plinth", NumVS::lower_than(2u32))]);
        inner.add_dependencies("plinth", 1u32, []);
        inner.add_dependencies("plinth", 2u32, []);
        inner.add_dependencies("plinth", 4u32, []);
        let provider = StatProvider { inner, seen: RefCell::new(Vec::new()) };
        let sol = resolve(&provider, "envoy", 1u32).unwrap();
        assert_eq!(
            sorted_num(&sol),
            BTreeMap::from([("envoy", 1u32), ("carto", 2u32), ("flint", 1u32), ("plinth", 2u32)])
        );

        // conflict counters rise for the packages that fought and stay zero for
        // the root, and the very first observation of every package is zero
        let seen = provider.seen.borrow();
        let max_of = |name: &str| {
            seen.iter().filter(|(p, _)| *p == name).map(|(_, c)| *c).max().unwrap_or(0)
        };
        assert!(max_of("carto") >= 1, "carto abandoned two versions");
        assert!(max_of("plinth") >= 1, "plinth sat inside the contested range");
        assert_eq!(max_of("envoy"), 0, "the root never conflicts here");
        let first_of = |name: &str| seen.iter().find(|(p, _)| *p == name).map(|(_, c)| *c);
        assert_eq!(first_of("carto"), Some(0));
        assert_eq!(first_of("plinth"), Some(0));
    }

    #[test]
    fn generated_unavailable_reason_reported() {
        struct GapProvider {
            inner: NumProvider,
        }
        impl DependencyProvider for GapProvider {
            type P = &'static str;
            type V = u32;
            type VS = NumVS;
            type M = String;
            type Err = Infallible;
            type Priority = <NumProvider as DependencyProvider>::Priority;
            fn prioritize(
                &self,
                package: &Self::P,
                range: &Self::VS,
                stats: &PackageResolutionStatistics,
            ) -> Self::Priority {
                self.inner.prioritize(package, range, stats)
            }
            fn choose_version(
                &self,
                package: &Self::P,
                range: &Self::VS,
            ) -> Result<Option<u32>, Infallible> {
                self.inner.choose_version(package, range)
            }
            fn get_dependencies(
                &self,
                package: &Self::P,
                version: &u32,
            ) -> Result<Dependencies<Self::P, Self::VS, String>, Infallible> {
                if *package == "vault" && *version == 2 {
                    return Ok(Dependencies::Unavailable("yanked by publisher".to_string()));
                }
                self.inner.get_dependencies(package, version)
            }
        }

        let mut inner = NumProvider::new();
        inner.add_dependencies("apex", 1u32, [("vault", NumVS::singleton(2u32))]);
        inner.add_dependencies("vault", 2u32, []);
        let provider = GapProvider { inner };
        let tree = expect_no_solution::<GapProvider>(resolve(&provider, "apex", 1u32));

        // the metadata surfaces as a Custom fact scoped to the one version
        let mut externals = Vec::new();
        collect_externals(&tree, &mut externals);
        let custom = externals
            .iter()
            .find_map(|e| match e {
                External::Custom(package, set, metadata) => Some((package, set, metadata)),
                _ => None,
            })
            .expect("a Custom fact carries the provider metadata");
        assert_eq!(*custom.0, "vault");
        assert_eq!(custom.1, &NumVS::singleton(2u32));
        assert_eq!(custom.2.as_str(), "yanked by publisher");
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because dependencies of vault at version 2 are unavailable yanked by \
             publisher and apex 1 depends on vault 2, apex 1 is forbidden."
        );
    }
}
