// Oracle atomic tests for the version-solving engine
#![cfg(test)]
#![allow(clippy::all)]

use std::collections::BTreeMap;
use std::fmt;
use std::ops::Bound::{Excluded, Included, Unbounded};

use pubgrub::{
    resolve, DefaultStringReportFormatter, DefaultStringReporter, Dependencies,
    DependencyConstraints, DependencyProvider, DerivationTree, Derived, External, Map,
    OfflineDependencyProvider, PackageResolutionStatistics, PubGrubError, Ranges, ReportFormatter,
    Reporter, SemanticVersion, Term, VersionParseError, VersionSet,
};

type NumVS = Ranges<u32>;
type SemVS = Ranges<SemanticVersion>;
type NumProvider = OfflineDependencyProvider<&'static str, NumVS>;

fn sorted_solution(sol: &Map<&'static str, u32>) -> BTreeMap<&'static str, u32> {
    sol.iter().map(|(p, v)| (*p, *v)).collect()
}

/// Provider whose callbacks fail on demand, for error-wrapping tests.
struct FaultyProvider {
    fail_choose: bool,
    fail_deps: bool,
    fail_cancel: bool,
}

#[derive(Debug)]
struct RegistryDown(&'static str);
impl fmt::Display for RegistryDown {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "registry down: {}", self.0)
    }
}
impl std::error::Error for RegistryDown {}

impl DependencyProvider for FaultyProvider {
    type P = &'static str;
    type V = u32;
    type VS = NumVS;
    type M = String;
    type Err = RegistryDown;
    type Priority = u32;

    fn prioritize(
        &self,
        _package: &Self::P,
        _range: &Self::VS,
        _stats: &PackageResolutionStatistics,
    ) -> u32 {
        0
    }

    fn choose_version(&self, _package: &Self::P, _range: &Self::VS) -> Result<Option<u32>, RegistryDown> {
        if self.fail_choose {
            Err(RegistryDown("mirror sync"))
        } else {
            Ok(Some(1))
        }
    }

    fn get_dependencies(
        &self,
        package: &Self::P,
        _version: &u32,
    ) -> Result<Dependencies<Self::P, Self::VS, String>, RegistryDown> {
        if self.fail_deps && *package == "quarry" {
            return Err(RegistryDown("manifest fetch"));
        }
        if *package == "apex" {
            let mut deps: DependencyConstraints<Self::P, Self::VS> = Map::default();
            deps.insert("quarry", NumVS::full());
            Ok(Dependencies::Available(deps))
        } else {
            Ok(Dependencies::Available(Map::default()))
        }
    }

    fn should_cancel(&self) -> Result<(), RegistryDown> {
        if self.fail_cancel {
            Err(RegistryDown("deadline"))
        } else {
            Ok(())
        }
    }
}

// ===================== Version Set Algebra: display =====================

#[test]
fn generated_display_atoms() {
    assert_eq!(NumVS::empty().to_string(), "∅");
    assert_eq!(NumVS::full().to_string(), "*");
    assert_eq!(NumVS::singleton(5u32).to_string(), "5");
    assert_eq!(NumVS::lower_than(3u32).to_string(), "<=3");
    assert_eq!(NumVS::strictly_lower_than(3u32).to_string(), "<3");
    assert_eq!(NumVS::higher_than(2u32).to_string(), ">=2");
    assert_eq!(NumVS::strictly_higher_than(2u32).to_string(), ">2");
}

#[test]
fn generated_display_bounded_pairs() {
    assert_eq!(NumVS::between(1u32, 4u32).to_string(), ">=1, <4");
    assert_eq!(NumVS::from_range_bounds(2u32..=6u32).to_string(), ">=2, <=6");
    let excl_incl = Ranges::from_iter([(Excluded(2u32), Included(6u32))]);
    assert_eq!(excl_incl.to_string(), ">2, <=6");
    let excl_excl = Ranges::from_iter([(Excluded(2u32), Excluded(6u32))]);
    assert_eq!(excl_excl.to_string(), ">2, <6");
}

#[test]
fn generated_display_union_join() {
    let u = NumVS::singleton(1u32).union(&NumVS::between(3u32, 5u32));
    assert_eq!(u.to_string(), "1 | >=3, <5");
    let three = u.union(&NumVS::higher_than(9u32));
    assert_eq!(three.to_string(), "1 | >=3, <5 | >=9");
}

// ===================== Version Set Algebra: constructors and queries =====================

#[test]
fn generated_constructor_boundaries() {
    assert!(NumVS::higher_than(2u32).contains(&2u32));
    assert!(!NumVS::strictly_higher_than(2u32).contains(&2u32));
    assert!(NumVS::strictly_higher_than(2u32).contains(&3u32));
    assert!(NumVS::lower_than(3u32).contains(&3u32));
    assert!(!NumVS::strictly_lower_than(3u32).contains(&3u32));
    assert!(NumVS::between(1u32, 4u32).contains(&1u32));
    assert!(NumVS::between(1u32, 4u32).contains(&3u32));
    assert!(!NumVS::between(1u32, 4u32).contains(&4u32));
    assert!(NumVS::singleton(7u32).contains(&7u32));
    assert!(!NumVS::singleton(7u32).contains(&8u32));
    assert!(NumVS::full().contains(&0u32));
    assert!(!NumVS::empty().contains(&0u32));
}

#[test]
fn generated_from_range_bounds_forms() {
    assert_eq!(NumVS::from_range_bounds(2u32..5u32), NumVS::between(2u32, 5u32));
    assert_eq!(NumVS::from_range_bounds(2u32..=2u32), NumVS::singleton(2u32));
    assert_eq!(NumVS::from_range_bounds::<_, u32>(..), NumVS::full());
    assert_eq!(NumVS::from_range_bounds(7u32..), NumVS::higher_than(7u32));
    // a segment admitting no version collapses to the empty set
    assert_eq!(NumVS::from_range_bounds(5u32..2u32), NumVS::empty());
    // tuple conversion reaches the version type
    let sem = SemVS::from_range_bounds((1, 0, 0)..(2, 0, 0));
    assert_eq!(sem.to_string(), ">=1.0.0, <2.0.0");
}

#[test]
fn generated_from_iter_normalizes() {
    let r = Ranges::from_iter([
        (Included(4u32), Excluded(8u32)),
        (Included(1u32), Included(2u32)),
        (Included(5u32), Included(9u32)),
        (Excluded(11u32), Excluded(11u32)), // admits no version: skipped
    ]);
    assert_eq!(r.to_string(), ">=1, <=2 | >=4, <=9");
    let expected = NumVS::from_range_bounds(1u32..=2u32)
        .union(&NumVS::from_range_bounds(4u32..=9u32));
    assert_eq!(r, expected);
}

#[test]
fn generated_contains_many_lockstep() {
    let set = NumVS::between(2u32, 5u32).union(&NumVS::singleton(9u32));
    let hits: Vec<bool> = set.contains_many([1u32, 2, 4, 5, 9, 10].iter()).collect();
    assert_eq!(hits, vec![false, true, true, false, true, false]);
    let singles: Vec<bool> = [1u32, 2, 4, 5, 9, 10].iter().map(|v| set.contains(v)).collect();
    assert_eq!(hits, singles);
}

#[test]
fn generated_as_singleton_rules() {
    assert_eq!(NumVS::singleton(7u32).as_singleton(), Some(&7u32));
    assert_eq!(NumVS::from_range_bounds(3u32..=3u32).as_singleton(), Some(&3u32));
    assert_eq!(NumVS::between(1u32, 4u32).as_singleton(), None);
    assert_eq!(NumVS::empty().as_singleton(), None);
    assert_eq!(NumVS::full().as_singleton(), None);
    let multi = NumVS::singleton(1u32).union(&NumVS::singleton(5u32));
    assert_eq!(multi.as_singleton(), None);
}

#[test]
fn generated_bounding_range_rules() {
    let set = NumVS::singleton(1u32).union(&NumVS::between(3u32, 5u32));
    assert_eq!(set.bounding_range(), Some((Included(&1u32), Excluded(&5u32))));
    assert_eq!(NumVS::empty().bounding_range(), None);
    assert_eq!(NumVS::full().bounding_range(), Some((Unbounded, Unbounded)));
    assert_eq!(
        NumVS::higher_than(4u32).bounding_range(),
        Some((Included(&4u32), Unbounded))
    );
}

#[test]
fn generated_segment_iteration() {
    let set = NumVS::from_range_bounds(1u32..=2u32).union(&NumVS::from_range_bounds(4u32..=9u32));
    let borrowed: Vec<_> = set.iter().collect();
    assert_eq!(
        borrowed,
        vec![
            (&Included(1u32), &Included(2u32)),
            (&Included(4u32), &Included(9u32)),
        ]
    );
    let owned: Vec<_> = set.clone().into_iter().collect();
    assert_eq!(
        owned,
        vec![
            (Included(1u32), Included(2u32)),
            (Included(4u32), Included(9u32)),
        ]
    );
    let iter = set.clone().into_iter();
    assert_eq!(iter.len(), 2);
    let backwards: Vec<_> = set.into_iter().rev().collect();
    assert_eq!(backwards[0], (Included(4u32), Included(9u32)));
}

#[test]
fn generated_is_empty_paths() {
    assert!(NumVS::empty().is_empty());
    assert!(!NumVS::full().is_empty());
    assert!(!NumVS::singleton(0u32).is_empty());
    let disjoint = NumVS::between(1u32, 3u32).intersection(&NumVS::between(5u32, 8u32));
    assert!(disjoint.is_empty());
}

// ===================== Version Set Algebra: operations =====================

#[test]
fn generated_union_merges_touching() {
    let merged = NumVS::between(1u32, 3u32).union(&NumVS::between(3u32, 5u32));
    assert_eq!(merged, NumVS::between(1u32, 5u32));
    assert_eq!(merged.to_string(), ">=1, <5");
    let open_end = NumVS::between(1u32, 3u32).union(&NumVS::higher_than(3u32));
    assert_eq!(open_end, NumVS::higher_than(1u32));
    let overlap = NumVS::between(1u32, 4u32).union(&NumVS::between(2u32, 6u32));
    assert_eq!(overlap, NumVS::between(1u32, 6u32));
}

#[test]
fn generated_union_keeps_discrete_gaps() {
    // the algebra never assumes a successor: 3..4 could hold a version
    let gapped = NumVS::between(1u32, 3u32).union(&NumVS::between(4u32, 6u32));
    assert_eq!(gapped.to_string(), ">=1, <3 | >=4, <6");
    assert_ne!(gapped, NumVS::between(1u32, 6u32));
    assert_eq!(gapped.iter().count(), 2);
}

#[test]
fn generated_equality_canonical_forms() {
    // same coverage, different construction: equal
    let a = NumVS::between(1u32, 4u32).union(&NumVS::between(2u32, 6u32));
    assert_eq!(a, NumVS::between(1u32, 6u32));
    // same members of a discrete type, different boundaries: unequal
    assert_ne!(NumVS::lower_than(3u32), NumVS::strictly_lower_than(4u32));
    // canonical ordering makes equality independent of union order
    let left = NumVS::singleton(1u32).union(&NumVS::singleton(5u32));
    let right = NumVS::singleton(5u32).union(&NumVS::singleton(1u32));
    assert_eq!(left, right);
}

#[test]
fn generated_complement_laws() {
    assert_eq!(NumVS::full().complement(), NumVS::empty());
    assert_eq!(NumVS::empty().complement(), NumVS::full());
    assert_eq!(NumVS::between(2u32, 5u32).complement().to_string(), "<2 | >=5");
    let set = NumVS::singleton(1u32).union(&NumVS::higher_than(4u32));
    assert_eq!(set.complement().complement(), set);
    assert!(!set.complement().contains(&1u32));
    assert!(set.complement().contains(&2u32));
}

#[test]
fn generated_intersection_and_empty() {
    let inter = NumVS::between(1u32, 5u32).intersection(&NumVS::between(3u32, 8u32));
    assert_eq!(inter, NumVS::between(3u32, 5u32));
    assert_eq!(inter.to_string(), ">=3, <5");
    let none = NumVS::between(1u32, 3u32).intersection(&NumVS::between(5u32, 8u32));
    assert_eq!(none, NumVS::empty());
    assert_eq!(NumVS::full().intersection(&NumVS::singleton(9u32)), NumVS::singleton(9u32));
}

#[test]
fn generated_disjoint_and_subset() {
    // an excluded end touching an included start leaves no shared version
    assert!(NumVS::between(1u32, 3u32).is_disjoint(&NumVS::between(3u32, 5u32)));
    assert!(!NumVS::between(1u32, 4u32).is_disjoint(&NumVS::between(3u32, 5u32)));
    assert!(NumVS::between(2u32, 4u32).subset_of(&NumVS::between(1u32, 5u32)));
    assert!(!NumVS::between(2u32, 6u32).subset_of(&NumVS::between(1u32, 5u32)));
    assert!(NumVS::empty().subset_of(&NumVS::singleton(1u32)));
    assert!(NumVS::singleton(3u32).subset_of(&NumVS::full()));
}

#[test]
fn generated_simplify_fixed_rules() {
    let complex = NumVS::between(1u32, 3u32).union(&NumVS::between(5u32, 8u32));
    // every supplied version contained: collapses to full
    assert_eq!(complex.simplify([2u32, 6u32].iter()), NumVS::full());
    // no supplied version contained: unchanged
    assert_eq!(complex.simplify([4u32].iter()), complex);
    // singletons are never simplified
    let single = NumVS::singleton(7u32);
    assert_eq!(single.simplify([7u32].iter()), single);
}

#[test]
fn generated_simplify_partial() {
    let complex = NumVS::between(1u32, 3u32).union(&NumVS::between(5u32, 8u32));
    // only the first segment matches a supplied version
    assert_eq!(complex.simplify([2u32, 4u32].iter()).to_string(), "<3");
    // only the second segment matches
    assert_eq!(complex.simplify([4u32, 6u32].iter()).to_string(), ">=5");
    // supplied versions straddling both segments and the outside keep both
    assert_eq!(
        complex.simplify([0u32, 2, 4, 6, 9].iter()).to_string(),
        ">=1, <3 | >=5, <8"
    );
    // agreement on supplied versions is preserved
    let simplified = complex.simplify([2u32, 4u32].iter());
    for v in [2u32, 4u32] {
        assert_eq!(simplified.contains(&v), complex.contains(&v));
    }
}

#[test]
fn generated_versionset_trait_laws() {
    // exercise Ranges through the VersionSet abstraction
    fn full_of<VS: VersionSet>() -> VS {
        VS::empty().complement()
    }
    let full: NumVS = full_of();
    assert_eq!(full, NumVS::full());
    let a = <NumVS as VersionSet>::singleton(4u32);
    assert!(<NumVS as VersionSet>::contains(&a, &4u32));
    let b = NumVS::between(1u32, 4u32);
    // union by De Morgan agrees with the optimized union
    let de_morgan = a.complement().intersection(&b.complement()).complement();
    assert_eq!(<NumVS as VersionSet>::union(&a, &b), de_morgan);
    assert!(<NumVS as VersionSet>::is_disjoint(
        &NumVS::singleton(9u32),
        &b
    ));
    assert!(<NumVS as VersionSet>::subset_of(&a, &NumVS::between(1u32, 5u32)));
}

// ===================== Semantic Versions =====================

#[test]
fn generated_semver_construct_display() {
    assert_eq!(SemanticVersion::new(1, 2, 3).to_string(), "1.2.3");
    assert_eq!(SemanticVersion::zero().to_string(), "0.0.0");
    assert_eq!(SemanticVersion::one().to_string(), "1.0.0");
    assert_eq!(SemanticVersion::two().to_string(), "2.0.0");
    assert_eq!(SemanticVersion::new(10, 0, 42).to_string(), "10.0.42");
}

#[test]
fn generated_semver_ordering_total() {
    let v = SemanticVersion::new;
    assert!(v(1, 9, 9) < v(2, 0, 0));
    assert!(v(1, 9, 0) < v(1, 10, 0));
    assert!(v(1, 2, 3) < v(1, 2, 4));
    assert_eq!(v(3, 4, 5), v(3, 4, 5));
    let mut versions = vec![v(2, 0, 0), v(0, 9, 1), v(1, 10, 0), v(1, 2, 0)];
    versions.sort();
    assert_eq!(versions, vec![v(0, 9, 1), v(1, 2, 0), v(1, 10, 0), v(2, 0, 0)]);
}

#[test]
fn generated_semver_bump_rules() {
    let v = SemanticVersion::new(1, 2, 3);
    assert_eq!(v.bump_patch(), SemanticVersion::new(1, 2, 4));
    assert_eq!(v.bump_minor(), SemanticVersion::new(1, 3, 0));
    assert_eq!(v.bump_major(), SemanticVersion::new(2, 0, 0));
    assert_eq!(SemanticVersion::zero().bump_patch(), SemanticVersion::new(0, 0, 1));
}

#[test]
fn generated_semver_tuple_conversions() {
    let from_tuple: SemanticVersion = (2, 4, 6).into();
    assert_eq!(from_tuple, SemanticVersion::new(2, 4, 6));
    let by_ref: SemanticVersion = (&(7, 8, 9)).into();
    assert_eq!(by_ref, SemanticVersion::new(7, 8, 9));
    let back: (u32, u32, u32) = SemanticVersion::new(9, 8, 7).into();
    assert_eq!(back, (9, 8, 7));
}

#[test]
fn generated_semver_parse_display_roundtrip() {
    let parsed: SemanticVersion = "4.27.1".parse().unwrap();
    assert_eq!(parsed, SemanticVersion::new(4, 27, 1));
    assert_eq!(parsed.to_string(), "4.27.1");
    for v in [SemanticVersion::zero(), SemanticVersion::new(3, 0, 11)] {
        let reparsed: SemanticVersion = v.to_string().parse().unwrap();
        assert_eq!(reparsed, v);
    }
}

#[test]
fn generated_semver_not_three_parts() {
    for bad in ["7", "1.2", "1.2.3.4", "1.2.3."] {
        assert_eq!(
            bad.parse::<SemanticVersion>(),
            Err(VersionParseError::NotThreeParts { full_version: bad.to_string() })
        );
    }
    let err = "1.2".parse::<SemanticVersion>().unwrap_err();
    assert_eq!(err.to_string(), "version 1.2 must contain 3 numbers separated by dot");
    // a valid sibling still parses
    assert!("1.2.0".parse::<SemanticVersion>().is_ok());
}

#[test]
fn generated_semver_parse_int_error_payloads() {
    let err = "1.x.3".parse::<SemanticVersion>().unwrap_err();
    assert_eq!(
        err,
        VersionParseError::ParseIntError {
            full_version: "1.x.3".to_string(),
            version_part: "x".to_string(),
            parse_error: "invalid digit found in string".to_string(),
        }
    );
    assert_eq!(
        err.to_string(),
        "cannot parse 'x' in '1.x.3' as u32: invalid digit found in string"
    );
    // a negative component is not an unsigned number
    let neg = "1.2.-3".parse::<SemanticVersion>().unwrap_err();
    assert_eq!(
        neg,
        VersionParseError::ParseIntError {
            full_version: "1.2.-3".to_string(),
            version_part: "-3".to_string(),
            parse_error: "invalid digit found in string".to_string(),
        }
    );
    // overflow of the 32-bit component
    let big = "1.2.9876543210".parse::<SemanticVersion>().unwrap_err();
    assert_eq!(
        big,
        VersionParseError::ParseIntError {
            full_version: "1.2.9876543210".to_string(),
            version_part: "9876543210".to_string(),
            parse_error: "number too large to fit in target type".to_string(),
        }
    );
}

// ===================== Dependency Universes and Providers =====================

#[test]
fn generated_offline_registry_views() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("kelp", 3u32, [("brine", NumVS::between(1u32, 9u32))]);
    dp.add_dependencies("kelp", 1u32, []);
    dp.add_dependencies("kelp", 7u32, []);
    dp.add_dependencies("brine", 4u32, []);
    let mut pkgs: Vec<&&str> = dp.packages().collect();
    pkgs.sort();
    assert_eq!(pkgs, vec![&"brine", &"kelp"]);
    let versions: Vec<&u32> = dp.versions(&"kelp").unwrap().collect();
    assert_eq!(versions, vec![&1u32, &3u32, &7u32]);
    assert!(dp.versions(&"tarpit").is_none());
}

#[test]
fn generated_offline_replacement() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("mill", 1u32, [("grain", NumVS::full())]);
    dp.add_dependencies("mill", 1u32, [("water", NumVS::full())]);
    match dp.get_dependencies(&"mill", &1u32).unwrap() {
        Dependencies::Available(constraints) => {
            let mut keys: Vec<&&str> = constraints.keys().collect();
            keys.sort();
            assert_eq!(keys, vec![&"water"]);
        }
        Dependencies::Unavailable(_) => panic!("registered pair must be available"),
    }
    // an empty list is the known fact "no dependencies"
    let mut dp2 = NumProvider::new();
    dp2.add_dependencies("solo", 2u32, []);
    match dp2.get_dependencies(&"solo", &2u32).unwrap() {
        Dependencies::Available(constraints) => assert!(constraints.is_empty()),
        Dependencies::Unavailable(_) => panic!("registered pair must be available"),
    }
}

#[test]
fn generated_offline_choose_version_strategy() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("kelp", 1u32, []);
    dp.add_dependencies("kelp", 3u32, []);
    dp.add_dependencies("kelp", 7u32, []);
    // highest registered version inside the range
    assert_eq!(dp.choose_version(&"kelp", &NumVS::full()), Ok(Some(7u32)));
    assert_eq!(dp.choose_version(&"kelp", &NumVS::between(1u32, 4u32)), Ok(Some(3u32)));
    assert_eq!(dp.choose_version(&"kelp", &NumVS::between(1u32, 2u32)), Ok(Some(1u32)));
    // nothing matches, or the package is unknown
    assert_eq!(dp.choose_version(&"kelp", &NumVS::singleton(9u32)), Ok(None));
    assert_eq!(dp.choose_version(&"tarpit", &NumVS::full()), Ok(None));
}

#[test]
fn generated_offline_unavailable_message() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("kelp", 3u32, []);
    match dp.get_dependencies(&"kelp", &9u32).unwrap() {
        Dependencies::Unavailable(reason) => {
            assert_eq!(reason, "its dependencies could not be determined");
        }
        Dependencies::Available(_) => panic!("unregistered pair must be unavailable"),
    }
    match dp.get_dependencies(&"tarpit", &1u32).unwrap() {
        Dependencies::Unavailable(reason) => {
            assert_eq!(reason, "its dependencies could not be determined");
        }
        Dependencies::Available(_) => panic!("unknown package must be unavailable"),
    }
}

#[test]
fn generated_offline_prioritize_ordering() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("kelp", 1u32, []);
    dp.add_dependencies("kelp", 3u32, []);
    dp.add_dependencies("kelp", 7u32, []);
    let stats = PackageResolutionStatistics::default();
    let wide = dp.prioritize(&"kelp", &NumVS::full(), &stats);
    let narrow = dp.prioritize(&"kelp", &NumVS::singleton(1u32), &stats);
    let none = dp.prioritize(&"kelp", &NumVS::singleton(9u32), &stats);
    // fewer matching candidates outrank more; no candidate outranks everything
    assert!(narrow > wide);
    assert!(none > narrow);
    assert!(none > wide);
}

#[test]
fn generated_statistics_default() {
    let stats = PackageResolutionStatistics::default();
    assert_eq!(stats.conflict_count(), 0);
    let cloned = stats.clone();
    assert_eq!(cloned.conflict_count(), 0);
}

// ===================== Resolution: successes =====================

#[test]
fn generated_resolve_chain_map() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("mast", NumVS::full()), ("hull", NumVS::full())]);
    dp.add_dependencies("mast", 1u32, [("sail", NumVS::full())]);
    dp.add_dependencies("sail", 1u32, [("hull", NumVS::full())]);
    dp.add_dependencies("hull", 1u32, []);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(
        sorted_solution(&sol),
        BTreeMap::from([("apex", 1u32), ("hull", 1u32), ("mast", 1u32), ("sail", 1u32)])
    );
}

#[test]
fn generated_resolve_prefers_newest() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("gear", NumVS::between(1u32, 9u32))]);
    dp.add_dependencies("gear", 2u32, []);
    dp.add_dependencies("gear", 5u32, []);
    dp.add_dependencies("gear", 9u32, []); // outside the half-open range
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(sol["gear"], 5u32);
    assert_eq!(sol.len(), 2);
}

#[test]
fn generated_resolve_backtracks_to_older() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("gear", NumVS::full()), ("axle", NumVS::singleton(1u32))]);
    dp.add_dependencies("gear", 2u32, [("axle", NumVS::singleton(2u32))]);
    dp.add_dependencies("gear", 1u32, [("axle", NumVS::singleton(1u32))]);
    dp.add_dependencies("axle", 1u32, []);
    dp.add_dependencies("axle", 2u32, []);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(
        sorted_solution(&sol),
        BTreeMap::from([("apex", 1u32), ("axle", 1u32), ("gear", 1u32)])
    );
}

#[test]
fn generated_resolve_intersects_shared_dep() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("left", NumVS::full()), ("right", NumVS::full())]);
    dp.add_dependencies("left", 1u32, [("core", NumVS::between(2u32, 6u32))]);
    dp.add_dependencies("right", 1u32, [("core", NumVS::between(1u32, 5u32))]);
    dp.add_dependencies("core", 1u32, []);
    dp.add_dependencies("core", 4u32, []);
    dp.add_dependencies("core", 7u32, []);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    // one version serves both dependents, inside the intersection [2, 5)
    assert_eq!(sol["core"], 4u32);
}

#[test]
fn generated_resolve_cycles_and_self() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("loop_a", NumVS::full())]);
    dp.add_dependencies("loop_a", 1u32, [("loop_b", NumVS::full())]);
    dp.add_dependencies("loop_b", 1u32, [("loop_a", NumVS::full())]);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(sol.len(), 3);
    assert_eq!(sol["loop_b"], 1u32);

    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("selfy", NumVS::full())]);
    dp.add_dependencies("selfy", 2u32, [("selfy", NumVS::higher_than(1u32))]);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(sol["selfy"], 2u32);

    // a dependency-free root resolves to itself alone
    let mut dp = NumProvider::new();
    dp.add_dependencies("solo", 1u32, []);
    let sol = resolve(&dp, "solo", 1u32).unwrap();
    assert_eq!(sorted_solution(&sol), BTreeMap::from([("solo", 1u32)]));
}

#[test]
fn generated_resolve_forced_older_choice() {
    // the newest beam requires a cog that does not exist
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("beam", NumVS::full()), ("cog", NumVS::full())]);
    dp.add_dependencies("beam", 1u32, [("cog", NumVS::singleton(1u32))]);
    dp.add_dependencies("beam", 2u32, [("cog", NumVS::singleton(2u32))]);
    dp.add_dependencies("cog", 1u32, []);
    let sol = resolve(&dp, "apex", 1u32).unwrap();
    assert_eq!(
        sorted_solution(&sol),
        BTreeMap::from([("apex", 1u32), ("beam", 1u32), ("cog", 1u32)])
    );
}

#[test]
fn generated_resolve_empty_range_rejects() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("void", NumVS::empty())]);
    dp.add_dependencies("void", 1u32, []);
    assert!(matches!(
        resolve(&dp, "apex", 1u32),
        Err(PubGrubError::NoSolution(_))
    ));
    // the same universe without the impossible edge solves
    let mut ok = NumProvider::new();
    ok.add_dependencies("apex", 1u32, [("void", NumVS::full())]);
    ok.add_dependencies("void", 1u32, []);
    let sol = resolve(&ok, "apex", 1u32).unwrap();
    assert_eq!(sol["void"], 1u32);
}

#[test]
fn generated_resolve_semver_universe() {
    let mut dp = OfflineDependencyProvider::<&str, SemVS>::new();
    dp.add_dependencies(
        "apex",
        (1, 0, 0),
        [("lib", SemVS::from_range_bounds((1, 0, 0)..(2, 0, 0)))],
    );
    dp.add_dependencies("lib", (1, 4, 2), []);
    dp.add_dependencies("lib", (2, 0, 0), []);
    let sol = resolve(&dp, "apex", (1, 0, 0)).unwrap();
    assert_eq!(sol["lib"], SemanticVersion::new(1, 4, 2));
    assert_eq!(sol["apex"], SemanticVersion::one());
}

#[test]
fn generated_resolve_repeated_runs_equal() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("left", NumVS::full()), ("right", NumVS::full())]);
    dp.add_dependencies("left", 2u32, [("base", NumVS::between(2u32, 4u32))]);
    dp.add_dependencies("left", 1u32, [("base", NumVS::between(1u32, 3u32))]);
    dp.add_dependencies("right", 2u32, [("base", NumVS::between(3u32, 5u32))]);
    dp.add_dependencies("right", 1u32, [("base", NumVS::between(1u32, 2u32))]);
    for v in 1..=4u32 {
        dp.add_dependencies("base", v, []);
    }
    let first = resolve(&dp, "apex", 1u32).unwrap();
    for _ in 0..5 {
        let again = resolve(&dp, "apex", 1u32).unwrap();
        assert_eq!(again, first);
    }
    assert_eq!(
        sorted_solution(&first),
        BTreeMap::from([("apex", 1u32), ("base", 3u32), ("left", 2u32), ("right", 2u32)])
    );
}

// ===================== Resolution: provider error wrapping =====================

#[test]
fn generated_error_choosing_version_wrap() {
    let provider = FaultyProvider { fail_choose: true, fail_deps: false, fail_cancel: false };
    match resolve(&provider, "apex", 1u32) {
        Err(PubGrubError::ErrorChoosingVersion { package, source }) => {
            assert_eq!(package, "apex");
            assert_eq!(source.to_string(), "registry down: mirror sync");
        }
        other => panic!("expected ErrorChoosingVersion, got {:?}", other.map(|_| ())),
    }
    let err = resolve(&provider, "apex", 1u32).unwrap_err();
    assert_eq!(err.to_string(), "Choosing a version for apex failed");
}

#[test]
fn generated_error_retrieving_dependencies_wrap() {
    let provider = FaultyProvider { fail_choose: false, fail_deps: true, fail_cancel: false };
    match resolve(&provider, "apex", 1u32) {
        Err(PubGrubError::ErrorRetrievingDependencies { package, version, source }) => {
            assert_eq!(package, "quarry");
            assert_eq!(version, 1u32);
            assert_eq!(source.to_string(), "registry down: manifest fetch");
        }
        other => panic!("expected ErrorRetrievingDependencies, got {:?}", other.map(|_| ())),
    }
    let err = resolve(&provider, "apex", 1u32).unwrap_err();
    assert_eq!(err.to_string(), "Retrieving dependencies of quarry 1 failed");
}

#[test]
fn generated_error_cancel_wrap() {
    let provider = FaultyProvider { fail_choose: false, fail_deps: false, fail_cancel: true };
    match resolve(&provider, "apex", 1u32) {
        Err(PubGrubError::ErrorInShouldCancel(source)) => {
            assert_eq!(source.to_string(), "registry down: deadline");
        }
        other => panic!("expected ErrorInShouldCancel, got {:?}", other.map(|_| ())),
    }
    let err = resolve(&provider, "apex", 1u32).unwrap_err();
    assert_eq!(err.to_string(), "The solver was cancelled");
}

#[test]
fn generated_nosolution_error_display_from() {
    let dp = NumProvider::new();
    let err = resolve(&dp, "apex", 1u32).unwrap_err();
    assert!(matches!(err, PubGrubError::NoSolution(_)));
    assert_eq!(err.to_string(), "There is no solution");
    // a derivation tree converts into the error type
    let tree: DerivationTree<&str, NumVS, String> =
        DerivationTree::External(External::NoVersions("apex", NumVS::singleton(1u32)));
    let converted: PubGrubError<NumProvider> = tree.into();
    assert!(matches!(converted, PubGrubError::NoSolution(_)));
}

// ===================== Terms =====================

#[test]
fn generated_term_display_and_eq() {
    let positive: Term<NumVS> = Term::Positive(NumVS::between(1u32, 4u32));
    let negative: Term<NumVS> = Term::Negative(NumVS::singleton(2u32));
    assert_eq!(positive.to_string(), ">=1, <4");
    assert_eq!(negative.to_string(), "Not ( 2 )");
    assert_eq!(positive, Term::Positive(NumVS::between(1u32, 4u32)));
    assert_ne!(positive, Term::Negative(NumVS::between(1u32, 4u32)));
    let cloned = negative.clone();
    assert_eq!(cloned, negative);
}

// ===================== Failure proofs: external facts =====================

#[test]
fn generated_external_notroot_noversions_display() {
    let not_root: External<&str, NumVS, String> = External::NotRoot("apex", 1);
    assert_eq!(not_root.to_string(), "we are solving dependencies of apex 1");
    let none_at_all: External<&str, NumVS, String> = External::NoVersions("gear", NumVS::full());
    assert_eq!(none_at_all.to_string(), "there is no available version for gear");
    let none_in_range: External<&str, NumVS, String> =
        External::NoVersions("gear", NumVS::between(2u32, 5u32));
    assert_eq!(none_in_range.to_string(), "there is no version of gear in >=2, <5");
}

#[test]
fn generated_external_custom_fromdep_display() {
    let m = "requires manual purchase".to_string();
    let custom_full: External<&str, NumVS, String> =
        External::Custom("vault", NumVS::full(), m.clone());
    assert_eq!(
        custom_full.to_string(),
        "dependencies of vault are unavailable requires manual purchase"
    );
    let custom_at: External<&str, NumVS, String> =
        External::Custom("vault", NumVS::singleton(2u32), m);
    assert_eq!(
        custom_at.to_string(),
        "dependencies of vault at version 2 are unavailable requires manual purchase"
    );
    let dep = |s: NumVS, t: NumVS| -> External<&'static str, NumVS, String> {
        External::FromDependencyOf("apex", s, "gear", t)
    };
    assert_eq!(dep(NumVS::full(), NumVS::full()).to_string(), "apex depends on gear");
    assert_eq!(
        dep(NumVS::full(), NumVS::between(1u32, 3u32)).to_string(),
        "apex depends on gear >=1, <3"
    );
    assert_eq!(
        dep(NumVS::singleton(1u32), NumVS::full()).to_string(),
        "apex 1 depends on gear"
    );
    assert_eq!(
        dep(NumVS::singleton(1u32), NumVS::between(1u32, 3u32)).to_string(),
        "apex 1 depends on gear >=1, <3"
    );
}

#[test]
fn generated_derived_node_fields() {
    let mut terms: Map<&str, Term<NumVS>> = Map::default();
    terms.insert("apex", Term::Positive(NumVS::singleton(1u32)));
    let node: Derived<&str, NumVS, String> = Derived {
        terms,
        shared_id: Some(3),
        cause1: std::sync::Arc::new(DerivationTree::External(External::NoVersions(
            "gear",
            NumVS::between(1u32, 3u32),
        ))),
        cause2: std::sync::Arc::new(DerivationTree::External(External::FromDependencyOf(
            "apex",
            NumVS::singleton(1u32),
            "gear",
            NumVS::between(1u32, 3u32),
        ))),
    };
    assert_eq!(node.shared_id, Some(3));
    assert_eq!(node.terms.len(), 1);
    assert_eq!(node.terms["apex"], Term::Positive(NumVS::singleton(1u32)));
    assert!(matches!(
        node.cause1.as_ref(),
        DerivationTree::External(External::NoVersions(_, _))
    ));
    assert!(matches!(
        node.cause2.as_ref(),
        DerivationTree::External(External::FromDependencyOf(_, _, _, _))
    ));
    let tree = DerivationTree::Derived(node.clone());
    let again = tree.clone();
    assert!(matches!(again, DerivationTree::Derived(_)));
}

#[test]
fn generated_tree_packages_by_variant() {
    let dep_tree: DerivationTree<&str, NumVS, String> = DerivationTree::External(
        External::FromDependencyOf("apex", NumVS::full(), "gear", NumVS::full()),
    );
    let mut named: Vec<&&str> = dep_tree.packages().into_iter().collect();
    named.sort();
    assert_eq!(named, vec![&"apex", &"gear"]);

    let solo_tree: DerivationTree<&str, NumVS, String> =
        DerivationTree::External(External::NoVersions("gear", NumVS::full()));
    let named: Vec<&&str> = solo_tree.packages().into_iter().collect();
    assert_eq!(named, vec![&"gear"]);

    let custom_tree: DerivationTree<&str, NumVS, String> =
        DerivationTree::External(External::Custom("vault", NumVS::full(), "gated".to_string()));
    let named: Vec<&&str> = custom_tree.packages().into_iter().collect();
    assert_eq!(named, vec![&"vault"]);
}

// ===================== Failure reports: formatter and reporter =====================

#[test]
fn generated_format_terms_shapes() {
    let formatter = DefaultStringReportFormatter;
    let empty: Map<&str, Term<NumVS>> = Map::default();
    assert_eq!(
        ReportFormatter::<&str, NumVS, String>::format_terms(&formatter, &empty),
        "version solving failed"
    );
    let mut one_pos: Map<&str, Term<NumVS>> = Map::default();
    one_pos.insert("gear", Term::Positive(NumVS::between(1u32, 3u32)));
    assert_eq!(
        ReportFormatter::<&str, NumVS, String>::format_terms(&formatter, &one_pos),
        "gear >=1, <3 is forbidden"
    );
    let mut one_neg: Map<&str, Term<NumVS>> = Map::default();
    one_neg.insert("gear", Term::Negative(NumVS::between(1u32, 3u32)));
    assert_eq!(
        ReportFormatter::<&str, NumVS, String>::format_terms(&formatter, &one_neg),
        "gear >=1, <3 is mandatory"
    );
    // a positive/negative pair renders as a dependency sentence, positive first,
    // regardless of insertion order
    let mut pair: Map<&str, Term<NumVS>> = Map::default();
    pair.insert("alpha", Term::Positive(NumVS::singleton(1u32)));
    pair.insert("beta", Term::Negative(NumVS::between(2u32, 4u32)));
    let mut swapped: Map<&str, Term<NumVS>> = Map::default();
    swapped.insert("beta", Term::Negative(NumVS::between(2u32, 4u32)));
    swapped.insert("alpha", Term::Positive(NumVS::singleton(1u32)));
    let rendered = ReportFormatter::<&str, NumVS, String>::format_terms(&formatter, &pair);
    assert_eq!(rendered, "alpha 1 depends on beta >=2, <4");
    assert_eq!(
        rendered,
        ReportFormatter::<&str, NumVS, String>::format_terms(&formatter, &swapped)
    );
}

#[test]
fn generated_format_external_passthrough() {
    let formatter = DefaultStringReportFormatter;
    let fact: External<&str, NumVS, String> =
        External::FromDependencyOf("apex", NumVS::singleton(1u32), "gear", NumVS::between(1u32, 3u32));
    assert_eq!(
        ReportFormatter::<&str, NumVS, String>::format_external(&formatter, &fact),
        fact.to_string()
    );
}

#[test]
fn generated_report_single_external() {
    let tree: DerivationTree<&str, NumVS, String> = DerivationTree::External(
        External::FromDependencyOf("apex", NumVS::singleton(1u32), "gear", NumVS::between(1u32, 3u32)),
    );
    assert_eq!(
        DefaultStringReporter::report(&tree),
        "apex 1 depends on gear >=1, <3"
    );
}

#[test]
fn generated_report_two_external_derived() {
    let mut terms: Map<&str, Term<NumVS>> = Map::default();
    terms.insert("apex", Term::Positive(NumVS::singleton(1u32)));
    let tree: DerivationTree<&str, NumVS, String> = DerivationTree::Derived(Derived {
        terms,
        shared_id: None,
        cause1: std::sync::Arc::new(DerivationTree::External(External::NoVersions(
            "gear",
            NumVS::between(1u32, 3u32),
        ))),
        cause2: std::sync::Arc::new(DerivationTree::External(External::FromDependencyOf(
            "apex",
            NumVS::singleton(1u32),
            "gear",
            NumVS::between(1u32, 3u32),
        ))),
    });
    assert_eq!(
        DefaultStringReporter::report(&tree),
        "Because there is no version of gear in >=1, <3 and apex 1 depends on gear >=1, <3, apex 1 is forbidden."
    );
}

#[test]
fn generated_report_with_formatter_default_equiv() {
    let mut dp = NumProvider::new();
    dp.add_dependencies("apex", 1u32, [("ghost", NumVS::full())]);
    let Err(PubGrubError::NoSolution(tree)) = resolve(&dp, "apex", 1u32) else {
        panic!("expected NoSolution");
    };
    assert_eq!(
        DefaultStringReporter::report_with_formatter(&tree, &DefaultStringReportFormatter),
        DefaultStringReporter::report(&tree)
    );
}
