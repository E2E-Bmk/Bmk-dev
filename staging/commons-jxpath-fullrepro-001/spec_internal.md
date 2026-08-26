<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — commons-jxpath-fullrepro-001

- task_id: commons-jxpath-fullrepro-001
- language: java
- repo: apache/commons-jxpath (github)
- repo_commit: 146f2534e885fd7085fba4bf3fb658d434416504 (tag rel/commons-jxpath-1.4.0)
- maven_coordinates: commons-jxpath:commons-jxpath
- package root: org.apache.commons.jxpath
- source boundary: JXPathContext (newContext/getValue/setValue/createPath/
  createPathAndSetValue/removePath/removeAll/getPointer/getContextPointer/
  iterate/iteratePointers/selectNodes/selectSingleNode/getRelativeContext/
  variables/leniency/factory/functions/compile), Pointer, Variables,
  BasicVariables, AbstractFactory, CompiledExpression, Functions,
  ClassFunctions, PackageFunctions, FunctionLibrary, and the exception family
  (JXPathException + NotFound/InvalidSyntax/FunctionNotFound/InvalidAccess/
  AbstractFactory). Excludes JDOM and servlet models, XML namespaces,
  id()/key() managers, locale/decimal formats, DocumentContainer,
  ExceptionHandler, introspection SPI (JXPathIntrospector, JXPathBeanInfo,
  DynamicPropertyHandler), NodeSet/BasicNodeSet, and the util conversion
  registry (Non-Goals).
- spec basis: commons-jxpath users guide + apidocs public documentation and
  six empirical probe rounds against the pinned 1.4.0 artifact (probe
  programs under /tmp/probe during authoring): result typing (Double
  arithmetic, property types preserved), 1-based indexing and out-of-range
  strictness, map keys always-present (null reads in strict mode) vs bean
  strictness, alphabetical property and map-key enumeration, collection
  property expansion under wildcard, canonical asPath forms (bean /
  collection / map-entry /.[@name=] / DOM indexed / $variable) and
  predicate→positional canonicalization, round-trips, relative contexts
  reporting root-anchored paths, factory consultation for intermediate AND
  null leaf steps on createPath but intermediates only on
  createPathAndSetValue, map-key creation without factory on
  createPathAndSetValue/setValue, factory declareVariable hook, function-set
  replacement semantics (installing ClassFunctions removes default
  method-call functions; FunctionLibrary + PackageFunctions("", null)
  restores), argument conversion for extension functions, leniency matrix
  (getValue/getPointer/selectSingleNode only; iterate/selectNodes always
  empty-safe; writes unaffected; placeholder pointer setValue raises
  InvalidAccess), undeclared-variable reads raising in both modes with
  different types, exception wrap chains (createPath decline →
  JXPathException caused by JXPathAbstractFactoryException).
- contamination_note: commons-jxpath 1.4.0 released 2024-08 — before
  training cutoff; mitigated by Specification Authority disclaimer and
  behavior-observed assertions.
- spec_version: v1
- delta: initial version.
- note: commons-beanutils is an optional dependency of the reference;
  conversions that would fall back to it (arbitrary bean→scalar) are kept
  out of scope deliberately.
