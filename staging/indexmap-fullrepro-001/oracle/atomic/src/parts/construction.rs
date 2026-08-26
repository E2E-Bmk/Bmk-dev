// Construction, hashing, and capacity: constructors, duplicate laws,
// Equivalent lookups, custom hashers, allocation neutrality.

#[test]
fn generated_new_and_default_empty() {
    let m: IndexMap<&str, i32> = IndexMap::new();
    assert_eq!(m.len(), 0);
    assert!(m.is_empty());
    assert_eq!(m.first(), None);
    let d: IndexMap<&str, i32> = IndexMap::default();
    assert!(d.is_empty());
    let s: IndexSet<i32> = IndexSet::new();
    assert!(s.is_empty());
    let wc: IndexMap<&str, i32> = IndexMap::with_capacity(16);
    assert!(wc.is_empty());
}

#[test]
fn generated_from_iterator_duplicate_law() {
    // first occurrence fixes the position, last value wins
    let m: IndexMap<&str, i32> = [("a", 1), ("b", 2), ("a", 10)].into_iter().collect();
    assert_eq!(m.len(), 2);
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"a", &"b"]);
    assert_eq!(m.get("a"), Some(&10));
    let s: IndexSet<i32> = [3, 1, 3].into_iter().collect();
    assert_eq!(s.iter().collect::<Vec<_>>(), [&3, &1]);
}

#[test]
fn generated_from_array_preserves_order() {
    let m = IndexMap::from([("k", 1), ("j", 2)]);
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"k", &"j"]);
    let s = IndexSet::from([9, 8, 7]);
    assert_eq!(s.iter().collect::<Vec<_>>(), [&9, &8, &7]);
}

#[test]
fn generated_macros_duplicate_law() {
    let m = indexmap! {"x" => 1, "y" => 2, "x" => 10};
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"x", &"y"]);
    assert_eq!(m.get("x"), Some(&10));
    let s = indexset! {"p", "q", "p"};
    assert_eq!(s.iter().collect::<Vec<_>>(), [&"p", &"q"]);
}

#[test]
fn generated_equivalent_borrowed_lookups() {
    let mut m: IndexMap<String, i32> = IndexMap::new();
    m.insert("alpha".to_string(), 1);
    m.insert("beta".to_string(), 2);
    // &str queries a String-keyed map through the Equivalent relation:
    assert_eq!(m.get("alpha"), Some(&1));
    assert_eq!(m.get_index_of("beta"), Some(1));
    assert!(m.contains_key("alpha"));
    assert_eq!(m.swap_remove("alpha"), Some(1));
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Id(u32);

struct ById(u32);
impl Equivalent<Id> for ById {
    fn equivalent(&self, key: &Id) -> bool {
        self.0 == key.0
    }
}
impl Hash for ById {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.hash(state);
    }
}

#[test]
fn generated_custom_equivalent_impl() {
    let mut m: IndexMap<Id, &str> = IndexMap::new();
    m.insert(Id(7), "seven");
    assert_eq!(m.get(&ById(7)), Some(&"seven"));
    assert_eq!(m.get(&ById(8)), None);
    assert_eq!(m.get_full(&ById(7)), Some((0, &Id(7), &"seven")));
}

#[test]
fn generated_custom_hashers() {
    type DH = std::hash::BuildHasherDefault<std::collections::hash_map::DefaultHasher>;
    let mut m: IndexMap<&str, i32, DH> = IndexMap::with_hasher(DH::default());
    m.insert("k", 1);
    assert_eq!(m.get("k"), Some(&1));
    let mut s: IndexSet<&str, DH> = IndexSet::with_capacity_and_hasher(4, DH::default());
    s.insert("v");
    assert!(s.contains("v"));
    let d: IndexMap<&str, i32, DH> = IndexMap::default();
    assert!(d.is_empty());
    let _ = m.hasher(); // hash builder is exposed
}

#[test]
fn generated_capacity_neutrality_and_try_reserve() {
    let mut m = base();
    let before = key_list(&m);
    m.reserve(100);
    m.reserve_exact(50);
    m.shrink_to_fit();
    m.shrink_to(0);
    assert_eq!(key_list(&m), before);
    assert_eq!(m.len(), 5);
    assert!(m.capacity() >= m.len());
    assert!(m.try_reserve(10).is_ok());
    assert!(m.try_reserve(usize::MAX).is_err());
    let mut s: IndexSet<i32> = IndexSet::new();
    assert!(s.try_reserve_exact(usize::MAX).is_err());
}

#[test]
fn generated_clear_resets() {
    let mut m = base();
    m.clear();
    assert_eq!(m.len(), 0);
    assert!(m.is_empty());
    assert_eq!(m.get("a"), None);
    assert_eq!(m.as_slice().len(), 0);
}
