// Oracle integration tests for the version-solving engine
#![cfg(test)]
#![allow(clippy::all)]

use std::cell::RefCell;
use std::collections::BTreeMap;
use std::convert::Infallible;
use std::fmt;
use std::sync::Arc;

use pubgrub::{
    resolve, DefaultStringReporter, Dependencies, DependencyConstraints, DependencyProvider,
    DerivationTree, Derived, External, Map, OfflineDependencyProvider,
    PackageResolutionStatistics, PubGrubError, Ranges, ReportFormatter, Reporter, SemanticVersion,
    Term,
};

type NumVS = Ranges<u32>;
type SemVS = Ranges<SemanticVersion>;
type NumProvider = OfflineDependencyProvider<&'static str, NumVS>;
type SemProvider = OfflineDependencyProvider<&'static str, SemVS>;

fn sorted_num(sol: &Map<&'static str, u32>) -> BTreeMap<&'static str, u32> {
    sol.iter().map(|(p, v)| (*p, *v)).collect()
}

fn semver_range(lo: (u32, u32, u32), hi: (u32, u32, u32)) -> SemVS {
    SemVS::from_range_bounds(lo..hi)
}

fn expect_no_solution<DP: DependencyProvider>(
    result: Result<pubgrub::SelectedDependencies<DP>, PubGrubError<DP>>,
) -> pubgrub::NoSolutionError<DP> {
    match result {
        Err(PubGrubError::NoSolution(tree)) => tree,
        Err(_) => panic!("expected NoSolution, got another error"),
        Ok(_) => panic!("expected NoSolution, got a solution"),
    }
}

/// Collect every external fact in a tree, left to right.
fn collect_externals<'a>(
    tree: &'a DerivationTree<&'static str, NumVS, String>,
    out: &mut Vec<&'a External<&'static str, NumVS, String>>,
) {
    match tree {
        DerivationTree::External(external) => out.push(external),
        DerivationTree::Derived(derived) => {
            collect_externals(&derived.cause1, out);
            collect_externals(&derived.cause2, out);
        }
    }
}

/// In-memory provider that picks the LOWEST matching version and records
/// its callback traffic.
struct LowestProvider {
    registry: BTreeMap<&'static str, BTreeMap<u32, Vec<(&'static str, NumVS)>>>,
    dependency_calls: RefCell<Vec<(&'static str, u32)>>,
    observed_conflicts: RefCell<Vec<(&'static str, u32)>>,
}

impl LowestProvider {
    fn new() -> Self {
        Self {
            registry: BTreeMap::new(),
            dependency_calls: RefCell::new(Vec::new()),
            observed_conflicts: RefCell::new(Vec::new()),
        }
    }

    fn add(&mut self, package: &'static str, version: u32, deps: Vec<(&'static str, NumVS)>) {
        self.registry.entry(package).or_default().insert(version, deps);
    }
}

impl DependencyProvider for LowestProvider {
    type P = &'static str;
    type V = u32;
    type VS = NumVS;
    type M = String;
    type Err = Infallible;
    type Priority = std::cmp::Reverse<usize>;

    fn prioritize(
        &self,
        package: &Self::P,
        _range: &Self::VS,
        stats: &PackageResolutionStatistics,
    ) -> Self::Priority {
        self.observed_conflicts
            .borrow_mut()
            .push((*package, stats.conflict_count()));
        std::cmp::Reverse(self.registry.get(package).map(|m| m.len()).unwrap_or(0))
    }

    fn choose_version(&self, package: &Self::P, range: &Self::VS) -> Result<Option<u32>, Infallible> {
        Ok(self
            .registry
            .get(package)
            .and_then(|versions| versions.keys().find(|v| range.contains(v)).copied()))
    }

    fn get_dependencies(
        &self,
        package: &Self::P,
        version: &u32,
    ) -> Result<Dependencies<Self::P, Self::VS, String>, Infallible> {
        self.dependency_calls.borrow_mut().push((*package, *version));
        match self.registry.get(package).and_then(|m| m.get(version)) {
            Some(deps) => {
                let mut constraints: DependencyConstraints<Self::P, Self::VS> = Map::default();
                for (p, vs) in deps {
                    constraints.insert(*p, vs.clone());
                }
                Ok(Dependencies::Available(constraints))
            }
            None => Ok(Dependencies::Unavailable("unregistered".to_string())),
        }
    }
}

include!("all/solving.rs");
include!("all/proofs.rs");
include!("all/reports.rs");
include!("all/strategy.rs");
include!("all/compose.rs");
