# Roaster Behavioral Clause Index

Stable IDs live only in this audit sidecar. Each quoted clause is verbatim from `spec_v2.md`; Stage 3 tests must cite the applicable IDs in method Javadocs.

## Representative Workflows

- `ROASTER-WF-001` — `Representative Workflows / Parse, modify, render, and reparse` — “The second model returns the same declared package, type name, method signature, and method body semantics exposed by the first model after mutation.”
- `ROASTER-WF-002` — `Representative Workflows / Inspect a complete compilation unit` — “The unit view retains all top-level declarations in source order, and its governing type returns the first top-level declaration.”

## Parsing, Creation, Formatting, and Validation

- `ROASTER-FAC-001` — “When `Roaster.create(type)` receives one of `JavaClassSource`, `JavaInterfaceSource`, `JavaEnumSource`, `JavaAnnotationSource`, or `JavaRecordSource`, the facade must return a new empty mutable instance of that requested public interface.”
- `ROASTER-FAC-002` — “If no parser provider supports the requested source interface, then the facade must raise `ParserException`; if no parser provider is available, then it must raise `IllegalStateException`.”
- `ROASTER-FAC-003` — “When `Roaster.parse(...)` receives Java source through a `String`, character array, `InputStream`, `File`, or `URL`, the facade must parse the governing declaration and return its matching public source-model view.”
- `ROASTER-FAC-004` — “When typed `parse(type, input)` receives a source whose governing declaration does not implement `type`, the facade must raise `ParserException`.”
- `ROASTER-FAC-005` — “If a `File` or `URL` cannot be read, then the corresponding parse operation must propagate an `IOException`.”
- `ROASTER-FAC-006` — “When an `InputStream` is parsed, the caller must retain responsibility for closing the stream.”
- `ROASTER-FAC-007` — “When `Roaster.parseUnit(...)` receives a `String` or `InputStream`, the facade must return a `JavaUnit` containing every top-level declaration in declared order.”
- `ROASTER-FAC-008` — “The `JavaUnit.getGoverningType()` member must return the first top-level declaration, and `getTopLevelTypes()` must return an immutable list.”
- `ROASTER-FAC-009` — “If no parser accepts the unit, then the facade must raise `ParserException`.”
- `ROASTER-FAC-010` — “When `Roaster.format(source)` receives Java source, the facade must return formatted Java source using the available formatter.”
- `ROASTER-FAC-011` — “Where caller-supplied formatter `Properties` are present, `Roaster.format(properties, source)` must apply those properties.”
- `ROASTER-FAC-012` — “If no formatter provider is available, then the format operation must raise `IllegalStateException`.”
- `ROASTER-FAC-013` — “Formatting must preserve the declarations and executable semantics represented by the input source.”
- `ROASTER-FAC-014` — “When `Roaster.validateSnippet(snippet)` receives syntactically valid Java code, the facade must return a non-null empty `List<Problem>`.”
- `ROASTER-FAC-015` — “When the snippet contains syntax problems, the facade must return a non-null list whose `Problem` elements expose `getMessage()`, `getSourceStart()`, `getSourceEnd()`, and `getSourceLineNumber()`.”
- `ROASTER-FAC-016` — “The `Problem` location members must use negative positions for unavailable offsets, and two `Problem` values with equal message and location data must compare equal.”
- `ROASTER-FAC-017` — “If no parser provider is available for validation, then the facade must raise `ParserException`.”
- `ROASTER-FAC-018` — “When a `ParserException` carries a problem list, `getProblems()` must return a non-null unmodifiable view of that list; when it carries no problems, `getProblems()` must return an empty list.”

## Compilation Units and Type Identity

- `ROASTER-TYPE-001` — “The `JavaType` view must expose `getName()`, `getPackage()`, `isDefaultPackage()`, `getQualifiedName()`, and `getCanonicalName()`.”
- `ROASTER-TYPE-002` — “When a top-level source model receives `setPackage(packageName)` and `setName(name)`, subsequent identity queries and rendered source must reflect both values.”
- `ROASTER-TYPE-003` — “When `setDefaultPackage()` is called, `getPackage()` must return `null` and `isDefaultPackage()` must return `true`.”
- `ROASTER-TYPE-018` — “The `Visibility` enum must expose `PUBLIC`, `PROTECTED`, `PRIVATE`, and `PACKAGE_PRIVATE`, with `scope()` returning the corresponding Java keyword or an empty string for package-private visibility.”
- `ROASTER-TYPE-019` — “When `Visibility.set(target, visibility)` is called, the target's visibility predicates and `Visibility.getFrom(target)` must reflect that value.”
- `ROASTER-TYPE-004` — “The predicates `isClass()`, `isInterface()`, `isEnum()`, `isAnnotation()`, and `isRecord()` must identify the represented declaration kind consistently.”
- `ROASTER-TYPE-005` — “When a type is top-level, `getEnclosingType()` must return that type itself.”
- `ROASTER-TYPE-006` — “When a nested type is added or parsed, the nested view's `getEnclosingType()` must return the governing parent, its `getOrigin()` must return the nested source view itself, and mutations through the nested view must update the parent's rendered source.”
- `ROASTER-TYPE-007` — “If `getNestedType(name)` does not find a declaration, then it must return `null`; removing an absent nested declaration must leave the parent unchanged.”
- `ROASTER-TYPE-008` — “When `addNestedType(type)`, `addNestedType(declaration)`, or `addNestedType(existingSource)` succeeds, the parent must expose the new declaration through `getNestedTypes()` and `getNestedType(name)`.”
- `ROASTER-TYPE-009` — “When `removeNestedType(type)` receives a nested model owned by the parent, the parent must stop exposing and rendering that declaration.”
- `ROASTER-TYPE-010` — “When a supported type or method adds a type variable by name, `hasTypeVariable(name)`, `getTypeVariable(name)`, and `getTypeVariables()` must agree on its presence.”
- `ROASTER-TYPE-011` — “When `TypeVariableSource.setBounds(...)` receives class, source-model, or string bounds, `getBounds()` must preserve the declared bound order as `Type` views and the owning source must import qualified bounds where required.”
- `ROASTER-TYPE-012` — “When bounds are removed, `getBounds()` must return an empty list; when a named type variable is absent, `getTypeVariable(name)` must return `null`.”
- `ROASTER-TYPE-013` — “A `Type` must expose erased `getName()`, import-aware `getSimpleName()`, expanded `getQualifiedName()`, generic-preserving `getQualifiedNameWithGenerics()`, type arguments, parent type, array dimensions, and primitive, qualified, parameterized, array, wildcard, and equality predicates.”
- `ROASTER-TYPE-014` — “These projections must describe one declaration consistently when a field, method, parameter, property, annotation element, or record component changes type.”
- `ROASTER-TYPE-015` — “When recoverable syntax problems exist, `JavaType.hasSyntaxErrors()` must return `true` and `getSyntaxErrors()` must expose `SyntaxError` values with description, line, column, error, and warning projections.”
- `ROASTER-TYPE-016` — “The `toUnformattedString()` member must return the current source without formatter application.”
- `ROASTER-TYPE-017` — “The ordinary source rendering must return reparsable Java source representing the current public model state, without requiring a particular whitespace layout.”

## Imports and Type Resolution

- `ROASTER-IMP-001` — “When `addImport(...)` receives a qualified class name, `Class`, public `JavaType`, `Type`, or existing `Import`, the source must add the import when the referenced type requires one and must return the corresponding `Import`.”
- `ROASTER-IMP-002` — “Repeating an equivalent addition must be idempotent.”
- `ROASTER-IMP-003` — “When an import is present, `hasImport(...)`, `getImport(...)`, and `getImports()` must agree on it, and `removeImport(...)` must remove it.”
- `ROASTER-IMP-004` — “When removal targets an absent import, the source must remain unchanged.”
- `ROASTER-IMP-005` — “If an import request names a primitive, a simple unqualified name, a type from `java.lang`, the source's own type, or a conflicting same-simple-name type, then `addImport(...)` must return `null` and must not add an import.”
- `ROASTER-IMP-006` — “The `requiresImport(...)` member must return `false` for primitives, `java.lang` types, same-package types, the source's own type, and references already covered by an import; it must return `true` for a distinct qualified type that lacks coverage.”
- `ROASTER-IMP-007` — “An `Import` must expose `getPackage()`, `getSimpleName()`, `getQualifiedName()`, `isWildcard()`, `isStatic()`, and `setStatic(boolean)`.”
- `ROASTER-IMP-008` — “A wildcard import's simple name must equal `Import.WILDCARD`, and its qualified name must include the wildcard suffix.”
- `ROASTER-IMP-009` — “Mutating static state on the returned import must update the owning source's import declaration.”
- `ROASTER-IMP-010` — “When `resolveType(type)` receives a primitive or already qualified type, it must return that resolved form directly.”
- `ROASTER-IMP-011` — “When a direct import matches the simple name, that import must win; when exactly one wildcard import supplies the unresolved name, that wildcard package must supply the qualification; otherwise the source package must qualify the name when defined, and an unresolved name must remain unqualified.”
- `ROASTER-IMP-013` — “When field, method-return, parameter, property, annotation-element, interface, supertype, or type-variable mutators receive a `Class`, public `JavaType`, or qualified string, the owning source must add required imports and the returned `Type` view must remain equivalent to the requested type.”
- `ROASTER-IMP-014` — “If an unqualified string lacks enough information to select an import, then the mutator must retain the supplied type reference without inventing a package.”

## Members, Initializers, and Properties

- `ROASTER-MEM-001` — “When `addField()` creates a stub or `addField(declaration)` parses a field declaration, the owner must expose the new `FieldSource` through `getFields()`, `getField(name)`, `hasField(name)`, and `getMembers()`.”
- `ROASTER-MEM-002` — “Field mutators must support name, type, visibility, static, final, transient, volatile, literal initializer, and string initializer state, and the corresponding getters must reflect each change.”
- `ROASTER-MEM-003` — “If `getField(name)` does not find a field, then it must return `null`; removing an absent field must leave the owner unchanged.”
- `ROASTER-MEM-004` — “When `addMethod()` creates a stub or `addMethod(declaration)` parses a method declaration, the owner must expose the new `MethodSource` through `getMethods()` and `getMembers()`.”
- `ROASTER-MEM-005` — “The `getMethod(name)` and `hasMethodSignature(name)` forms must address the zero-parameter overload, while the forms accepting parameter type names or classes must match by ordered equivalent parameter types and distinguish overloads.”
- `ROASTER-MEM-006` — “If no matching overload exists, then `getMethod(...)` must return `null`; removing an absent method must leave the owner unchanged.”
- `ROASTER-MEM-007` — “Method mutators must support name, visibility, body, return type or void, constructor state, ordered parameters, declared thrown exceptions, abstract, default, synchronized, native, static, final, and type-variable state, and the corresponding getters must reflect each change.”
- `ROASTER-MEM-008` — “When `setConstructor(true)` is called, the method name must match its owning class name.”
- `ROASTER-MEM-009` — “When `setNative(true)` is called, the method body must be removed.”
- `ROASTER-MEM-010` — “When parameters are added or removed, `getParameters()` and `toSignature()` must reflect the ordered parameter types.”
- `ROASTER-MEM-011` — “When a method adds a parameter from a class, public type, or type-name string, the returned `ParameterSource` must expose the requested name and equivalent `Type`, remain in insertion order, and support annotation, final, and varargs state.”
- `ROASTER-MEM-012` — “When an initializer is added from a stub or body declaration, `getInitializers()` must expose it, `setBody(body)` must update its body, and `setStatic(boolean)` must control whether it is static.”
- `ROASTER-MEM-013` — “Removing an owned parameter or initializer must remove it from both queries and rendered source.”
- `ROASTER-MEM-014` — “When `addProperty(type, name)` receives a class, public type, or type-name string, the owner must expose one `PropertySource` through `getProperty(name)`, `getProperties()`, type-filtered `getProperties(type)`, and `hasProperty(name)`.”
- `ROASTER-MEM-015` — “A property must coordinate a storing field, accessor, and mutator through `hasField()`, `getField()`, `isAccessible()`, `getAccessor()`, `isMutable()`, and `getMutator()`.”
- `ROASTER-MEM-016` — “When `setAccessible(false)` or `setMutable(false)` is applied, the respective method must disappear from both the property and method-holder views; restoring the flag must restore the corresponding method.”
- `ROASTER-MEM-017` — “If `createField()`, `createAccessor()`, or `createMutator()` is called before a property name is set or when that component already exists, then it must raise `IllegalStateException`.”
- `ROASTER-MEM-018` — “When a property or one of its field/accessor/mutator projections is removed through its public property operation, the property and owner collection views must immediately agree with the new state.”
- `ROASTER-MEM-019` — “If `getProperty(name)` does not find a bean property, then it must return `null`; removing an absent property must leave the owner unchanged.”

## Annotations, Documentation, and Specialized Declarations

- `ROASTER-ANN-001` — “When a supported type or member receives `addAnnotation(type)`, the returned `AnnotationSource` must become visible through `getAnnotations()`, `hasAnnotation(type)`, and `getAnnotation(type)`, and qualified annotation types must add required imports.”
- `ROASTER-ANN-002` — “When an annotation is absent, `getAnnotation(type)` must return `null`; removing an absent annotation must leave the target unchanged, and `removeAllAnnotations()` must empty the annotation view.”
- `ROASTER-ANN-003` — “An `AnnotationSource` must distinguish marker, single-value, and normal forms through `isMarker()`, `isSingleValue()`, and `isNormal()`.”
- `ROASTER-ANN-004` — “When callers set or add literal, string, enum, class, nested annotation, or array values with or without an element name, the matching typed getter and `isTypeElementDefined(name)` must reflect the value.”
- `ROASTER-ANN-005` — “When a second nested annotation is added to an existing single nested value, the value must become an annotation array while preserving the existing element.”
- `ROASTER-ANN-006` — “Removing a named value or all values must update both the form predicates and typed getters.”
- `ROASTER-ANN-007` — “When `JavaDocSource.setText(text)` is called, `getText()` must return comment text without tags.”
- `ROASTER-ANN-008` — “When `setFullText(text)` is called, `getFullText()` must expose text and tags represented by that input.”
- `ROASTER-ANN-009` — “When tags are added or removed, `getTagNames()`, `getTags(name)`, and `getTags()` must agree, preserve repeated tags as distinct `JavaDocTag` values, and return empty collections for absent tag names.”
- `ROASTER-ANN-010` — “When `removeJavaDoc()` is called on a documented element, `hasJavaDoc()` must return `false`.”
- `ROASTER-ANN-011` — “When `JavaEnumSource.addEnumConstant()` or `addEnumConstant(declaration)` succeeds, the enum must expose the constant through `getEnumConstant(name)` and declared-order `getEnumConstants()`.”
- `ROASTER-ANN-012` — “The constant must support name, annotations, documentation, literal constructor arguments, and an optional body containing fields, methods, and nested types.”
- `ROASTER-ANN-013` — “When `removeBody()` is called, the body projection and rendered anonymous subclass body must disappear; if a constant name is absent, then `getEnumConstant(name)` must return `null`.”
- `ROASTER-ANN-014` — “When `JavaAnnotationSource.addAnnotationElement()` or `addAnnotationElement(declaration)` succeeds, the annotation type must expose the element through `getAnnotationElement(name)` and declared-order `getAnnotationElements()`.”
- `ROASTER-ANN-015` — “The element must support name, type, annotations, documentation, and a default value represented as literal, string, enum, enum array, nested annotation, single class, or class array.”
- `ROASTER-ANN-016` — “If an element name is absent, then `getAnnotationElement(name)` must return `null`; removing an absent element must leave the annotation type unchanged.”
- `ROASTER-ANN-017` — “When `JavaRecordSource.addRecordComponent(type, name)` receives a class or type-name string, the record must expose the component through declared-order `getRecordComponents()`, and the component must expose name, type, annotations, and varargs state.”
- `ROASTER-ANN-018` — “When removal targets a component name or component model owned by the record, that component must disappear from the header and component list.”
- `ROASTER-ANN-019` — “When a newly added `JavaRecordComponentSource` is queried through `isFinal()`, the component must return `false`.”
- `ROASTER-ANN-020` — “When `setFinal(true)` is called, the operation must return the same component instance, and a subsequent `isFinal()` call must return `true`.”

## Error Semantics

- `ROASTER-ERR-001` — “If no parser provider is available for creation or parsing, then the facade must raise `IllegalStateException`.” `(non-testable)`
- `ROASTER-ERR-002` — “If no provider supports a requested source interface or typed parse result, then the facade must raise `ParserException`.”
- `ROASTER-ERR-003` — “If a typed parse receives a different governing declaration kind, then the facade must raise `ParserException`.”
- `ROASTER-ERR-004` — “If a `File` or `URL` input cannot be read, then the facade must propagate `IOException`.”
- `ROASTER-ERR-005` — “If no formatter provider is available, then the facade must raise `IllegalStateException`.” `(non-testable)`
- `ROASTER-ERR-006` — “If validation has no parser provider, then the facade must raise `ParserException`.” `(non-testable)`
- `ROASTER-ERR-007` — “If a named element is absent, then the corresponding singular lookup must return `null`.”
- `ROASTER-ERR-008` — “If a removal targets an absent model element, then the owner must remain unchanged.”
- `ROASTER-ERR-009` — “If a property component is created without a property name or duplicates an existing component, then the operation must raise `IllegalStateException`.”
- `ROASTER-ERR-011` — “If an import request names a non-importable or conflicting reference, then the operation must return `null` and leave imports unchanged.”

## Cross-View Invariants

- `ROASTER-CVI-001` — “A mutation through a child `FieldSource`, `MethodSource`, `ParameterSource`, `PropertySource`, annotation, documentation, initializer, type-variable, or nested-type view must update its owner queries and both source-rendering projections.”
- `ROASTER-CVI-002` — “Source rendered after public mutations must reparse into a model whose package, declaration kind, names, modifiers, types, member signatures, imports, annotations, and documentation semantics agree with the mutated model.”
- `ROASTER-CVI-003` — “A type supplied through a qualified string, `Class`, public `JavaType`, or `Type` must produce equivalent type projections, required imports, and reparsed type identity.”
- `ROASTER-CVI-004` — “Adding or removing an import must change `hasImport`, `getImport`, `getImports`, `requiresImport`, `resolveType`, and rendered source consistently.”
- `ROASTER-CVI-005` — “Adding, removing, or changing a field or method must update the specialized field/method collection and the aggregate `getMembers()` projection consistently.”
- `ROASTER-CVI-006` — “Property accessibility and mutability changes must agree across `PropertySource`, the owner's field and method collections, signature lookup, and rendered source.”
- `ROASTER-CVI-007` — “Adding or removing annotations or documentation through a type/member child view must agree with target lookups, tag/value projections, imports, and reparsed source.”
- `ROASTER-CVI-008` — “A `JavaUnit` governing type and top-level list must share package/import context and must render the same complete compilation unit in the same declaration order.”
- `ROASTER-CVI-009` — “A nested type's `getEnclosingType()` must identify its parent, its `getOrigin()` must return the nested source itself, and the parent's nested-type collection and rendered source must contain it.”
- `ROASTER-CVI-010` — “A record component's collection membership, name, type, annotations, and varargs state, and every enum constant or annotation element mutation, must agree with its specialized collection, governing type rendering, and reparsed specialized declaration.”

## Environment Contract

- `ROASTER-ENV-001` — `Appendix A: Environment` — “The project must declare a standard Maven `pom.xml` at the project root and must produce the artifact `org.jboss.forge.roaster:roaster-jdt`.”
- `ROASTER-ENV-002` — `Appendix A: Environment` — “Runtime implementation dependencies must be declared in that POM and must resolve from the pre-cached local Maven repository.”

## Summary

- Stable behavioral clauses: **113**.
- Behavior-domain clauses: **89**.
- Error clauses: **10**.
- Cross-view invariant clauses: **10**.
- Workflow clauses: **2**.
- Environment clauses: **2**.

## Revision audit

- v2 retired `ROASTER-ERR-010` because pinned-reference execution disproved the v1 exception contract.
- v2 replaced `ROASTER-ANN-019` with the directly observed initial getter result and added `ROASTER-ANN-020` for the directly observed `setFinal(true)` state transition.
- v3 retired `ROASTER-IMP-012` because an exact six-input pinned-reference execution disproved generic-argument and array-dimension preservation. No replacement clause was inferred; `ROASTER-IMP-011` retains the directly confirmed simple-name/direct-import contract.
- v4 preserves all 113 active contract sentences and marks only `ROASTER-ERR-001`, `ROASTER-ERR-005`, and `ROASTER-ERR-006` as `(non-testable)` under the fixed Maven coordinate, as required by `SPEC_STANDARD.md`.
