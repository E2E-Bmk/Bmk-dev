// Report rendering: linear chains, branching references, custom formatters.
mod reports {
    use super::*;

    fn linear_universe() -> NumProvider {
        let mut dp = NumProvider::new();
        dp.add_dependencies("quay", 1u32, [("berth", NumVS::between(3u32, 5u32))]);
        dp.add_dependencies("berth", 3u32, [("bollard", NumVS::between(2u32, 3u32))]);
        dp.add_dependencies("berth", 4u32, [("bollard", NumVS::between(2u32, 3u32))]);
        dp.add_dependencies("bollard", 1u32, []);
        dp.add_dependencies("bollard", 3u32, []);
        dp
    }

    fn branching_universe() -> NumProvider {
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
        dp
    }

    #[test]
    fn generated_linear_chain_report_exact() {
        let dp = linear_universe();
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "quay", 1u32));
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because there is no version of bollard in >=2, <3 and berth 3 | 4 depends \
             on bollard >=2, <3, berth 3 | 4 is forbidden.\nAnd because there is no \
             version of berth in >3, <4 | >4, <5 and quay 1 depends on berth >=3, <5, \
             quay 1 is forbidden."
        );
        let mut collapsed = tree.clone();
        collapsed.collapse_no_versions();
        assert_eq!(
            DefaultStringReporter::report(&collapsed),
            "Because berth >=3, <5 depends on bollard >=2, <3 and quay 1 depends on \
             berth >=3, <5, quay 1 is forbidden."
        );
    }

    #[test]
    fn generated_branching_report_refs_and_blank_line() {
        let dp = branching_universe();
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "gantry", 1u32));
        let report = DefaultStringReporter::report(&tree);
        assert_eq!(
            report,
            "Because cable 10 depends on drum >=20, <30 and there is no version of \
             cable in >10, <20, cable >=10, <20 depends on drum >=20, <30.\nAnd \
             because hoist 10 depends on drum >=10, <20, cable >=10, <20, hoist 10 \
             are incompatible.\nAnd because hoist 10 depends on cable >=10, <20 and \
             there is no version of hoist in >10, <11 | >11, <20, hoist >=10, <11 | \
             >11, <20 is forbidden. (1)\n\nBecause there is no version of pulley in \
             >10, <20 and pulley 10 depends on sheave >=20, <30, pulley >=10, <20 \
             depends on sheave >=20, <30.\nAnd because hoist 11 depends on pulley \
             >=10, <20 and hoist 11 depends on sheave >=10, <20, hoist 11 is \
             forbidden.\nAnd because hoist >=10, <11 | >11, <20 is forbidden (1), \
             hoist >=10, <20 is forbidden.\nAnd because gantry 1 depends on hoist \
             >=10, <20, gantry 1 is forbidden."
        );
        // structure: the first sub-proof ends with its reference marker, the two
        // sub-proofs are separated by exactly one empty line, and the citation
        // reuses the assigned number
        let lines: Vec<&str> = report.lines().collect();
        assert_eq!(lines.len(), 8);
        assert!(lines[2].ends_with("is forbidden. (1)"));
        assert_eq!(lines[3], "");
        assert!(lines[6].contains("is forbidden (1)"));
    }

    #[test]
    fn generated_branching_collapsed_report_exact() {
        let dp = branching_universe();
        let mut tree = expect_no_solution::<NumProvider>(resolve(&dp, "gantry", 1u32));
        tree.collapse_no_versions();
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because cable >=10, <20 depends on drum >=20, <30 and hoist 10 depends \
             on drum >=10, <20, cable >=10, <20, hoist 10 are incompatible.\nAnd \
             because hoist 10 depends on cable >=10, <20, hoist 10 is forbidden. \
             (1)\n\nBecause pulley >=10, <20 depends on sheave >=20, <30 and hoist \
             11 depends on pulley >=10, <20, hoist 11 depends on sheave >=20, \
             <30.\nAnd because hoist 11 depends on sheave >=10, <20, hoist 11 is \
             forbidden.\nAnd because hoist 10 is forbidden (1), hoist >=10, <20 is \
             forbidden.\nAnd because gantry 1 depends on hoist >=10, <20, gantry 1 \
             is forbidden."
        );
    }

    #[test]
    fn generated_custom_formatter_drives_reporter() {
        struct TersFormatter;
        impl ReportFormatter<&'static str, NumVS, String> for TersFormatter {
            type Output = String;
            fn format_external(&self, external: &External<&'static str, NumVS, String>) -> String {
                format!("<{}>", external)
            }
            fn format_terms(&self, terms: &Map<&'static str, Term<NumVS>>) -> String {
                let mut entries: Vec<_> =
                    terms.iter().map(|(p, t)| format!("{p}~{t}")).collect();
                entries.sort();
                format!("[{}]", entries.join(" & "))
            }
            fn explain_both_external(
                &self,
                e1: &External<&'static str, NumVS, String>,
                e2: &External<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!(
                    "STEP {} + {} => {}",
                    self.format_external(e1),
                    self.format_external(e2),
                    self.format_terms(terms)
                )
            }
            fn explain_both_ref(
                &self,
                r1: usize,
                _d1: &Derived<&'static str, NumVS, String>,
                r2: usize,
                _d2: &Derived<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!("STEP #{} + #{} => {}", r1, r2, self.format_terms(terms))
            }
            fn explain_ref_and_external(
                &self,
                r: usize,
                _d: &Derived<&'static str, NumVS, String>,
                e: &External<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!(
                    "STEP #{} + {} => {}",
                    r,
                    self.format_external(e),
                    self.format_terms(terms)
                )
            }
            fn and_explain_external(
                &self,
                e: &External<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!("THEN {} => {}", self.format_external(e), self.format_terms(terms))
            }
            fn and_explain_ref(
                &self,
                r: usize,
                _d: &Derived<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!("THEN #{} => {}", r, self.format_terms(terms))
            }
            fn and_explain_prior_and_external(
                &self,
                p: &External<&'static str, NumVS, String>,
                e: &External<&'static str, NumVS, String>,
                terms: &Map<&'static str, Term<NumVS>>,
            ) -> String {
                format!(
                    "THEN {} + {} => {}",
                    self.format_external(p),
                    self.format_external(e),
                    self.format_terms(terms)
                )
            }
        }

        let dp = branching_universe();
        let tree = expect_no_solution::<NumProvider>(resolve(&dp, "gantry", 1u32));
        // the reporter drives the caller's formatter through every callback and
        // still owns line joining, blank-line separation, and reference markers
        assert_eq!(
            DefaultStringReporter::report_with_formatter(&tree, &TersFormatter),
            "STEP <cable 10 depends on drum >=20, <30> + <there is no version of \
             cable in >10, <20> => [cable~>=10, <20 & drum~Not ( >=20, <30 )]\nTHEN \
             <hoist 10 depends on drum >=10, <20> => [cable~>=10, <20 & \
             hoist~10]\nTHEN <hoist 10 depends on cable >=10, <20> + <there is no \
             version of hoist in >10, <11 | >11, <20> => [hoist~>=10, <11 | >11, \
             <20] (1)\n\nSTEP <there is no version of pulley in >10, <20> + <pulley \
             10 depends on sheave >=20, <30> => [pulley~>=10, <20 & sheave~Not ( \
             >=20, <30 )]\nTHEN <hoist 11 depends on pulley >=10, <20> + <hoist 11 \
             depends on sheave >=10, <20> => [hoist~11]\nTHEN #1 => [hoist~>=10, \
             <20]\nTHEN <gantry 1 depends on hoist >=10, <20> => [gantry~1]"
        );
    }

    #[test]
    fn generated_semver_universe_report_exact() {
        let mut dp = SemProvider::new();
        dp.add_dependencies("ferry", (1, 0, 0), [("pier", semver_range((1, 0, 0), (2, 0, 0)))]);
        dp.add_dependencies("pier", (1, 2, 0), [("anchor", semver_range((2, 0, 0), (3, 0, 0)))]);
        dp.add_dependencies("anchor", (1, 5, 0), []);
        let tree = expect_no_solution::<SemProvider>(resolve(&dp, "ferry", (1, 0, 0)));
        assert_eq!(
            DefaultStringReporter::report(&tree),
            "Because there is no version of anchor in >=2.0.0, <3.0.0 and pier 1.2.0 \
             depends on anchor >=2.0.0, <3.0.0, pier 1.2.0 is forbidden.\nAnd \
             because there is no version of pier in >=1.0.0, <1.2.0 | >1.2.0, \
             <2.0.0 and ferry 1.0.0 depends on pier >=1.0.0, <2.0.0, ferry 1.0.0 is \
             forbidden."
        );
        let mut collapsed = tree.clone();
        collapsed.collapse_no_versions();
        assert_eq!(
            DefaultStringReporter::report(&collapsed),
            "Because pier >=1.0.0, <2.0.0 depends on anchor >=2.0.0, <3.0.0 and \
             ferry 1.0.0 depends on pier >=1.0.0, <2.0.0, ferry 1.0.0 is forbidden."
        );
    }
}
