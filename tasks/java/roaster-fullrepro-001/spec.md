# Roaster Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`Roaster` is a Java source-model library that parses, creates, inspects, modifies, validates, formats, and renders Java compilation units through fluent public interfaces. Its central facade accepts source text and common input carriers, while its model objects expose Java types, members, imports, annotations, documentation, and diagnostics as connected views of one mutable source unit.

The installable Maven artifact is `org.jboss.forge.roaster:roaster-jdt`. It supplies the facade and public model packages required for programmatic use under Java 17.

## Non-Goals

- This specification does not require the distribution command-line formatter or its shell launchers.
- This specification does not define behavior that removes or hides parser or formatter providers from the fixed Maven coordinate, provider SPI implementations, service-discovery internals, shaded dependency types, or classes from implementation packages.
- This specification does not require convenience generators in `org.jboss.forge.roaster.model.util`, formatter-profile parsing, stream-copy helpers, or serial-version computation.
- This specification does not define exact whitespace, import ordering, exception-message wording, diagnostic-message wording, `toString()` decoration, or other representation text beyond semantic source content.
- This specification does not require package-info source creation, raw implementation handles, source-offset accessors on arbitrary elements, or direct construction of implementation classes.
- This specification does not define behavior for Java language constructs outside classes, interfaces, enums, annotation types, records, their selected members, and nested forms described below.

## Representative Workflows

### Create and enrich a class

```java
import java.io.Serializable;
import org.jboss.forge.roaster.Roaster;
import org.jboss.forge.roaster.model.source.JavaClassSource;

JavaClassSource person = Roaster.create(JavaClassSource.class)
      .setPackage("example.model")
      .setName("Person")
      .addInterface(Serializable.class);

person.addField()
      .setName("id")
      .setType(Long.class)
      .setPrivate()
      .setFinal(true);

person.addMethod()
      .setConstructor(true)
      .setPublic()
      .setBody("this.id = id;")
      .addParameter(Long.class, "id");
```

The returned child objects remain linked to the same `JavaClassSource`; member queries and the rendered source reflect the completed fluent mutations.

### Parse, modify, render, and reparse

```java
import org.jboss.forge.roaster.Roaster;
import org.jboss.forge.roaster.model.source.JavaClassSource;

JavaClassSource parsed = Roaster.parse(
      JavaClassSource.class,
      "package example; public class Greeting {}"
);
parsed.addMethod()
      .setPublic()
      .setName("message")
      .setReturnType(String.class)
      .setBody("return \"hello\";");

JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, parsed.toString());
boolean present = reparsed.hasMethodSignature("message");
```

The second model returns the same declared package, type name, method signature, and method body semantics exposed by the first model after mutation.

### Inspect a complete compilation unit

```java
import org.jboss.forge.roaster.Roaster;
import org.jboss.forge.roaster.model.JavaUnit;

JavaUnit unit = Roaster.parseUnit(
      "package example; public class First {} class Second {}"
);
String governingName = unit.getGoverningType().getName();
int topLevelCount = unit.getTopLevelTypes().size();
```

The unit view retains all top-level declarations in source order, and its governing type returns the first top-level declaration.

## Parsing, Creation, Formatting, and Validation

This section defines how callers enter the source-model lifecycle and obtain a type, compilation unit, formatted source, or validation report.

**Source creation.** When `Roaster.create(type)` receives one of `JavaClassSource`, `JavaInterfaceSource`, `JavaEnumSource`, `JavaAnnotationSource`, or `JavaRecordSource`, the facade must return a new empty mutable instance of that requested public interface. If no parser provider supports the requested source interface, then the facade must raise `ParserException`; if no parser provider is available, then it must raise `IllegalStateException`.

**Type parsing.** When `Roaster.parse(...)` receives Java source through a `String`, character array, `InputStream`, `File`, or `URL`, the facade must parse the governing declaration and return its matching public source-model view. When typed `parse(type, input)` receives a source whose governing declaration does not implement `type`, the facade must raise `ParserException`. If a `File` or `URL` cannot be read, then the corresponding parse operation must propagate an `IOException`. When an `InputStream` is parsed, the caller must retain responsibility for closing the stream.

**Compilation-unit parsing.** When `Roaster.parseUnit(...)` receives a `String` or `InputStream`, the facade must return a `JavaUnit` containing every top-level declaration in declared order. The `JavaUnit.getGoverningType()` member must return the first top-level declaration, and `getTopLevelTypes()` must return an immutable list. If no parser accepts the unit, then the facade must raise `ParserException`.

**Formatting.** When `Roaster.format(source)` receives Java source, the facade must return formatted Java source using the available formatter. Where caller-supplied formatter `Properties` are present, `Roaster.format(properties, source)` must apply those properties. If no formatter provider is available, then the format operation must raise `IllegalStateException`. Formatting must preserve the declarations and executable semantics represented by the input source.

**Validation.** When `Roaster.validateSnippet(snippet)` receives syntactically valid Java code, the facade must return a non-null empty `List<Problem>`. When the snippet contains syntax problems, the facade must return a non-null list whose `Problem` elements expose `getMessage()`, `getSourceStart()`, `getSourceEnd()`, and `getSourceLineNumber()`. The `Problem` location members must use negative positions for unavailable offsets, and two `Problem` values with equal message and location data must compare equal. If no parser provider is available for validation, then the facade must raise `ParserException`.

**Parser errors.** When a `ParserException` carries a problem list, `getProblems()` must return a non-null unmodifiable view of that list; when it carries no problems, `getProblems()` must return an empty list.

## Compilation Units and Type Identity

This section defines the stable identity, classification, nesting, generic, and source projections shared by public Java type models.

**Names and packages.** The `JavaType` view must expose `getName()`, `getPackage()`, `isDefaultPackage()`, `getQualifiedName()`, and `getCanonicalName()`. When a top-level source model receives `setPackage(packageName)` and `setName(name)`, subsequent identity queries and rendered source must reflect both values. When `setDefaultPackage()` is called, `getPackage()` must return `null` and `isDefaultPackage()` must return `true`.

**Visibility.** The `Visibility` enum must expose `PUBLIC`, `PROTECTED`, `PRIVATE`, and `PACKAGE_PRIVATE`, with `scope()` returning the corresponding Java keyword or an empty string for package-private visibility. When `Visibility.set(target, visibility)` is called, the target's visibility predicates and `Visibility.getFrom(target)` must reflect that value.

**Kind and enclosure.** The predicates `isClass()`, `isInterface()`, `isEnum()`, `isAnnotation()`, and `isRecord()` must identify the represented declaration kind consistently. When a type is top-level, `getEnclosingType()` must return that type itself. When a nested type is added or parsed, the nested view's `getEnclosingType()` must return the governing parent, its `getOrigin()` must return the nested source view itself, and mutations through the nested view must update the parent's rendered source. If `getNestedType(name)` does not find a declaration, then it must return `null`; removing an absent nested declaration must leave the parent unchanged.

**Nested declarations.** When `addNestedType(type)`, `addNestedType(declaration)`, or `addNestedType(existingSource)` succeeds, the parent must expose the new declaration through `getNestedTypes()` and `getNestedType(name)`. When `removeNestedType(type)` receives a nested model owned by the parent, the parent must stop exposing and rendering that declaration.

**Generic declarations.** When a supported type or method adds a type variable by name, `hasTypeVariable(name)`, `getTypeVariable(name)`, and `getTypeVariables()` must agree on its presence. When `TypeVariableSource.setBounds(...)` receives class, source-model, or string bounds, `getBounds()` must preserve the declared bound order as `Type` views and the owning source must import qualified bounds where required. When bounds are removed, `getBounds()` must return an empty list; when a named type variable is absent, `getTypeVariable(name)` must return `null`.

**Type projections.** A `Type` must expose erased `getName()`, import-aware `getSimpleName()`, expanded `getQualifiedName()`, generic-preserving `getQualifiedNameWithGenerics()`, type arguments, parent type, array dimensions, and primitive, qualified, parameterized, array, wildcard, and equality predicates. These projections must describe one declaration consistently when a field, method, parameter, property, annotation element, or record component changes type.

**Syntax and rendering.** When recoverable syntax problems exist, `JavaType.hasSyntaxErrors()` must return `true` and `getSyntaxErrors()` must expose `SyntaxError` values with description, line, column, error, and warning projections. The `toUnformattedString()` member must return the current source without formatter application. The ordinary source rendering must return reparsable Java source representing the current public model state, without requiring a particular whitespace layout.

## Imports and Type Resolution

This section defines how a mutable source tracks imports and resolves type names against its import and package context.

**Import lifecycle.** When `addImport(...)` receives a qualified class name, `Class`, public `JavaType`, `Type`, or existing `Import`, the source must add the import when the referenced type requires one and must return the corresponding `Import`. Repeating an equivalent addition must be idempotent. When an import is present, `hasImport(...)`, `getImport(...)`, and `getImports()` must agree on it, and `removeImport(...)` must remove it. When removal targets an absent import, the source must remain unchanged.

**Non-importable references.** If an import request names a primitive, a simple unqualified name, a type from `java.lang`, the source's own type, or a conflicting same-simple-name type, then `addImport(...)` must return `null` and must not add an import. The `requiresImport(...)` member must return `false` for primitives, `java.lang` types, same-package types, the source's own type, and references already covered by an import; it must return `true` for a distinct qualified type that lacks coverage.

**Import projection.** An `Import` must expose `getPackage()`, `getSimpleName()`, `getQualifiedName()`, `isWildcard()`, `isStatic()`, and `setStatic(boolean)`. A wildcard import's simple name must equal `Import.WILDCARD`, and its qualified name must include the wildcard suffix. Mutating static state on the returned import must update the owning source's import declaration.

**Resolution precedence.** When `resolveType(type)` receives a primitive or already qualified type, it must return that resolved form directly. When a direct import matches the simple name, that import must win; when exactly one wildcard import supplies the unresolved name, that wildcard package must supply the qualification; otherwise the source package must qualify the name when defined, and an unresolved name must remain unqualified.

**Type-setting integration.** When field, method-return, parameter, property, annotation-element, interface, supertype, or type-variable mutators receive a `Class`, public `JavaType`, or qualified string, the owning source must add required imports and the returned `Type` view must remain equivalent to the requested type. If an unqualified string lacks enough information to select an import, then the mutator must retain the supplied type reference without inventing a package.

## Members, Initializers, and Properties

This section defines collection, mutation, lookup, and coordinated bean-property behavior for fields, methods, parameters, initializers, and properties.

**Fields.** When `addField()` creates a stub or `addField(declaration)` parses a field declaration, the owner must expose the new `FieldSource` through `getFields()`, `getField(name)`, `hasField(name)`, and `getMembers()`. Field mutators must support name, type, visibility, static, final, transient, volatile, literal initializer, and string initializer state, and the corresponding getters must reflect each change. If `getField(name)` does not find a field, then it must return `null`; removing an absent field must leave the owner unchanged.

**Methods and overloads.** When `addMethod()` creates a stub or `addMethod(declaration)` parses a method declaration, the owner must expose the new `MethodSource` through `getMethods()` and `getMembers()`. The `getMethod(name)` and `hasMethodSignature(name)` forms must address the zero-parameter overload, while the forms accepting parameter type names or classes must match by ordered equivalent parameter types and distinguish overloads. If no matching overload exists, then `getMethod(...)` must return `null`; removing an absent method must leave the owner unchanged.

**Method state.** Method mutators must support name, visibility, body, return type or void, constructor state, ordered parameters, declared thrown exceptions, abstract, default, synchronized, native, static, final, and type-variable state, and the corresponding getters must reflect each change. When `setConstructor(true)` is called, the method name must match its owning class name. When `setNative(true)` is called, the method body must be removed. When parameters are added or removed, `getParameters()` and `toSignature()` must reflect the ordered parameter types.

**Parameters and initializers.** When a method adds a parameter from a class, public type, or type-name string, the returned `ParameterSource` must expose the requested name and equivalent `Type`, remain in insertion order, and support annotation, final, and varargs state. When an initializer is added from a stub or body declaration, `getInitializers()` must expose it, `setBody(body)` must update its body, and `setStatic(boolean)` must control whether it is static. Removing an owned parameter or initializer must remove it from both queries and rendered source.

**Properties.** When `addProperty(type, name)` receives a class, public type, or type-name string, the owner must expose one `PropertySource` through `getProperty(name)`, `getProperties()`, type-filtered `getProperties(type)`, and `hasProperty(name)`. A property must coordinate a storing field, accessor, and mutator through `hasField()`, `getField()`, `isAccessible()`, `getAccessor()`, `isMutable()`, and `getMutator()`. When `setAccessible(false)` or `setMutable(false)` is applied, the respective method must disappear from both the property and method-holder views; restoring the flag must restore the corresponding method. If `createField()`, `createAccessor()`, or `createMutator()` is called before a property name is set or when that component already exists, then it must raise `IllegalStateException`.

**Removal coherence.** When a property or one of its field/accessor/mutator projections is removed through its public property operation, the property and owner collection views must immediately agree with the new state. If `getProperty(name)` does not find a bean property, then it must return `null`; removing an absent property must leave the owner unchanged.

## Annotations, Documentation, and Specialized Declarations

This section defines annotation values, documentation comments, enum constants, annotation elements, records, and their observable model relationships.

**Annotation targets.** When a supported type or member receives `addAnnotation(type)`, the returned `AnnotationSource` must become visible through `getAnnotations()`, `hasAnnotation(type)`, and `getAnnotation(type)`, and qualified annotation types must add required imports. When an annotation is absent, `getAnnotation(type)` must return `null`; removing an absent annotation must leave the target unchanged, and `removeAllAnnotations()` must empty the annotation view.

**Annotation forms and values.** An `AnnotationSource` must distinguish marker, single-value, and normal forms through `isMarker()`, `isSingleValue()`, and `isNormal()`. When callers set or add literal, string, enum, class, nested annotation, or array values with or without an element name, the matching typed getter and `isTypeElementDefined(name)` must reflect the value. When a second nested annotation is added to an existing single nested value, the value must become an annotation array while preserving the existing element. Removing a named value or all values must update both the form predicates and typed getters.

**Documentation comments.** When `JavaDocSource.setText(text)` is called, `getText()` must return comment text without tags. When `setFullText(text)` is called, `getFullText()` must expose text and tags represented by that input. When tags are added or removed, `getTagNames()`, `getTags(name)`, and `getTags()` must agree, preserve repeated tags as distinct `JavaDocTag` values, and return empty collections for absent tag names. When `removeJavaDoc()` is called on a documented element, `hasJavaDoc()` must return `false`.

**Enum constants.** When `JavaEnumSource.addEnumConstant()` or `addEnumConstant(declaration)` succeeds, the enum must expose the constant through `getEnumConstant(name)` and declared-order `getEnumConstants()`. The constant must support name, annotations, documentation, literal constructor arguments, and an optional body containing fields, methods, and nested types. When `removeBody()` is called, the body projection and rendered anonymous subclass body must disappear; if a constant name is absent, then `getEnumConstant(name)` must return `null`.

**Annotation elements.** When `JavaAnnotationSource.addAnnotationElement()` or `addAnnotationElement(declaration)` succeeds, the annotation type must expose the element through `getAnnotationElement(name)` and declared-order `getAnnotationElements()`. The element must support name, type, annotations, documentation, and a default value represented as literal, string, enum, enum array, nested annotation, single class, or class array. If an element name is absent, then `getAnnotationElement(name)` must return `null`; removing an absent element must leave the annotation type unchanged.

**Records.** When `JavaRecordSource.addRecordComponent(type, name)` receives a class or type-name string, the record must expose the component through declared-order `getRecordComponents()`, and the component must expose name, type, annotations, and varargs state. When removal targets a component name or component model owned by the record, that component must disappear from the header and component list. When a newly added `JavaRecordComponentSource` is queried through `isFinal()`, the component must return `false`. When `setFinal(true)` is called, the operation must return the same component instance, and a subsequent `isFinal()` call must return `true`.

## State Model

The core state is one mutable Java compilation unit containing ordered top-level declarations, each declaration's nested types, imports, modifiers, annotations, documentation, members, generic variables, and syntax diagnostics.

The public projections of this state are:

- The facade projection returned by `Roaster.create`, `parse`, and `parseUnit`.
- The declaration projection exposed by `JavaType`, concrete source interfaces, and kind predicates.
- The collection projection exposed by imports, fields, methods, parameters, initializers, properties, annotations, type variables, nested types, enum constants, annotation elements, and record components.
- The ownership projection exposed by member-model `getOrigin()` and nested-source `getEnclosingType()`.
- The source projection exposed by ordinary rendering and `toUnformattedString()`.
- The diagnostic projection exposed by `Problem` and `SyntaxError` values.
- The formatter projection returned by `Roaster.format`.

## Error Semantics

| Condition | Required result |
|---|---|
| No parser provider is available for creation or parsing | If no parser provider is available for creation or parsing, then the facade must raise `IllegalStateException`. `(non-testable)` |
| No provider supports a requested source interface or typed parse result | If no provider supports a requested source interface or typed parse result, then the facade must raise `ParserException`. |
| A typed parse receives a different governing declaration kind | If a typed parse receives a different governing declaration kind, then the facade must raise `ParserException`. |
| A `File` or `URL` input cannot be read | If a `File` or `URL` input cannot be read, then the facade must propagate `IOException`. |
| No formatter provider is available | If no formatter provider is available, then the facade must raise `IllegalStateException`. `(non-testable)` |
| Validation has no parser provider | If validation has no parser provider, then the facade must raise `ParserException`. `(non-testable)` |
| A named field, method overload, property, annotation, nested type, enum constant, annotation element, import, or type variable is absent | If a named element is absent, then the corresponding singular lookup must return `null`. |
| A removal targets an absent model element | If a removal targets an absent model element, then the owner must remain unchanged. |
| A property component is created without a property name or duplicates an existing component | If a property component is created without a property name or duplicates an existing component, then the operation must raise `IllegalStateException`. |
| An import request names a non-importable or conflicting reference | If an import request names a non-importable or conflicting reference, then the operation must return `null` and leave imports unchanged. |

## Cross-View Invariants

1. A mutation through a child `FieldSource`, `MethodSource`, `ParameterSource`, `PropertySource`, annotation, documentation, initializer, type-variable, or nested-type view must update its owner queries and both source-rendering projections.
2. Source rendered after public mutations must reparse into a model whose package, declaration kind, names, modifiers, types, member signatures, imports, annotations, and documentation semantics agree with the mutated model.
3. A type supplied through a qualified string, `Class`, public `JavaType`, or `Type` must produce equivalent type projections, required imports, and reparsed type identity.
4. Adding or removing an import must change `hasImport`, `getImport`, `getImports`, `requiresImport`, `resolveType`, and rendered source consistently.
5. Adding, removing, or changing a field or method must update the specialized field/method collection and the aggregate `getMembers()` projection consistently.
6. Property accessibility and mutability changes must agree across `PropertySource`, the owner's field and method collections, signature lookup, and rendered source.
7. Adding or removing annotations or documentation through a type/member child view must agree with target lookups, tag/value projections, imports, and reparsed source.
8. A `JavaUnit` governing type and top-level list must share package/import context and must render the same complete compilation unit in the same declaration order.
9. A nested type's `getEnclosingType()` must identify its parent, its `getOrigin()` must return the nested source itself, and the parent's nested-type collection and rendered source must contain it.
10. A record component's collection membership, name, type, annotations, and varargs state, and every enum constant or annotation element mutation, must agree with its specialized collection, governing type rendering, and reparsed specialized declaration.

## Public Interface

### Import Surface

```java
import org.jboss.forge.roaster.ParserException;
import org.jboss.forge.roaster.Problem;
import org.jboss.forge.roaster.Roaster;

import org.jboss.forge.roaster.model.Annotation;
import org.jboss.forge.roaster.model.AnnotationElement;
import org.jboss.forge.roaster.model.EnumConstant;
import org.jboss.forge.roaster.model.Field;
import org.jboss.forge.roaster.model.Initializer;
import org.jboss.forge.roaster.model.JavaAnnotation;
import org.jboss.forge.roaster.model.JavaClass;
import org.jboss.forge.roaster.model.JavaDoc;
import org.jboss.forge.roaster.model.JavaDocTag;
import org.jboss.forge.roaster.model.JavaEnum;
import org.jboss.forge.roaster.model.JavaInterface;
import org.jboss.forge.roaster.model.JavaRecord;
import org.jboss.forge.roaster.model.JavaRecordComponent;
import org.jboss.forge.roaster.model.JavaType;
import org.jboss.forge.roaster.model.JavaUnit;
import org.jboss.forge.roaster.model.Method;
import org.jboss.forge.roaster.model.Parameter;
import org.jboss.forge.roaster.model.Property;
import org.jboss.forge.roaster.model.SyntaxError;
import org.jboss.forge.roaster.model.Type;
import org.jboss.forge.roaster.model.TypeVariable;
import org.jboss.forge.roaster.model.Visibility;

import org.jboss.forge.roaster.model.source.AnnotationElementSource;
import org.jboss.forge.roaster.model.source.AnnotationSource;
import org.jboss.forge.roaster.model.source.EnumConstantSource;
import org.jboss.forge.roaster.model.source.FieldSource;
import org.jboss.forge.roaster.model.source.Import;
import org.jboss.forge.roaster.model.source.InitializerSource;
import org.jboss.forge.roaster.model.source.JavaAnnotationSource;
import org.jboss.forge.roaster.model.source.JavaClassSource;
import org.jboss.forge.roaster.model.source.JavaDocSource;
import org.jboss.forge.roaster.model.source.JavaEnumSource;
import org.jboss.forge.roaster.model.source.JavaInterfaceSource;
import org.jboss.forge.roaster.model.source.JavaRecordComponentSource;
import org.jboss.forge.roaster.model.source.JavaRecordSource;
import org.jboss.forge.roaster.model.source.JavaSource;
import org.jboss.forge.roaster.model.source.MethodSource;
import org.jboss.forge.roaster.model.source.ParameterSource;
import org.jboss.forge.roaster.model.source.PropertySource;
import org.jboss.forge.roaster.model.source.TypeVariableSource;
```

### Public Members

| Public type | Public members in scope |
|---|---|
| `Roaster` | `create`, `parse`, `parseUnit`, `format`, `validateSnippet` |
| `ParserException` | constructors, `getProblems` |
| `Problem` | constructor, `getMessage`, `getSourceStart`, `getSourceEnd`, `getSourceLineNumber`, `equals`, `hashCode` |
| `JavaUnit` | `getGoverningType`, `getTopLevelTypes`, `toUnformattedString` |
| `JavaType`, `JavaSource` | `getName`, `setName`, `getPackage`, `setPackage`, `setDefaultPackage`, `isDefaultPackage`, `getCanonicalName`, `getQualifiedName`, `getSyntaxErrors`, `hasSyntaxErrors`, kind predicates, `getEnclosingType`, `getOrigin`, `toUnformattedString`, source rendering |
| `JavaClassSource` | supertype, interface, generic, modifier, field, method, initializer, property, annotation, documentation, import, and nested-type members described above |
| `JavaInterfaceSource` | extended-interface, generic, modifier, field, method, property, annotation, documentation, import, and nested-type members described above |
| `JavaEnumSource` | `addEnumConstant`, `getEnumConstant`, `getEnumConstants`, plus member/import/type operations described above |
| `JavaAnnotationSource` | `addAnnotationElement`, `getAnnotationElement`, `getAnnotationElements`, `removeAnnotationElement`, plus common source operations |
| `JavaRecordSource` | `addRecordComponent`, `getRecordComponents`, `removeRecordComponent`, plus method/initializer/interface/import/type operations described above |
| `FieldSource` | field add/get/list/remove; name, type, initializer, visibility, annotation, documentation, static, final, transient, volatile members |
| `MethodSource` | method add/get/list/remove; name, body, return type, constructor, parameter, throws, signature, generic, visibility, annotation, documentation, abstract, default, synchronized, native, static, final members |
| `ParameterSource` | parameter add/get/remove; name, type, annotation, final, varargs members |
| `InitializerSource` | initializer add/get/remove; `getBody`, `setBody`, `isStatic`, `setStatic` |
| `PropertySource` | property add/get/list/remove; name, type, field, accessor, mutator, accessible, mutable members |
| `Import` | import add/get/list/has/remove; `requiresImport`, `resolveType`, `WILDCARD`, package/simple/qualified name, wildcard/static members |
| `Type`, `TypeVariableSource` | type-name/generic/array predicates and views; type-variable add/get/list/has/remove/bounds members |
| `AnnotationSource` | annotation add/get/list/has/remove; name, form predicates, typed value getters/setters/adders/removers |
| `JavaDocSource`, `JavaDocTag` | JavaDoc get/set/remove; text/full-text/tag add/get/list/remove; tag name/value members |
| `EnumConstantSource` | name, constructor arguments, body, annotations, documentation, and body removal |
| `AnnotationElementSource` | name, type, default-value forms, annotations, documentation members |
| `JavaRecordComponentSource` | name, type, annotations, varargs, `isFinal`, and `setFinal` members |
| `SyntaxError` | `getDescription`, `getLine`, `getColumn`, `isError`, `isWarning` |
| `Visibility` | `PUBLIC`, `PROTECTED`, `PRIVATE`, `PACKAGE_PRIVATE`, `scope`, `getFrom`, `set` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Roaster` | class | Facade for source creation, parsing, formatting, and validation. |
| `ParserException` | exception | Reports unsupported or failed parse operations with optional problems. |
| `Problem` | class | Carries validation diagnostic text and source location. |
| `JavaUnit` | interface | Represents a complete ordered Java compilation unit. |
| `JavaType` | interface | Common read projection for a Java declaration. |
| `JavaSource` | interface | Common mutable source projection for a Java declaration. |
| `JavaClass` | interface | Read projection for a class declaration. |
| `JavaInterface` | interface | Read projection for an interface declaration. |
| `JavaEnum` | interface | Read projection for an enum declaration. |
| `JavaAnnotation` | interface | Read projection for an annotation-type declaration. |
| `JavaRecord` | interface | Read projection for a record declaration. |
| `JavaClassSource` | interface | Mutable class declaration. |
| `JavaInterfaceSource` | interface | Mutable interface declaration. |
| `JavaEnumSource` | interface | Mutable enum declaration. |
| `JavaAnnotationSource` | interface | Mutable annotation-type declaration. |
| `JavaRecordSource` | interface | Mutable record declaration. |
| `Field` | interface | Read projection for a field. |
| `FieldSource` | interface | Mutable field projection. |
| `Method` | interface | Read projection for a method or constructor. |
| `MethodSource` | interface | Mutable method or constructor projection. |
| `Parameter` | interface | Read projection for a method parameter. |
| `ParameterSource` | interface | Mutable method parameter projection. |
| `Initializer` | interface | Read projection for an initializer block. |
| `InitializerSource` | interface | Mutable initializer-block projection. |
| `Property` | interface | Coordinated bean-property projection. |
| `PropertySource` | interface | Mutable bean-property projection. |
| `Import` | interface | Mutable import declaration projection. |
| `Type` | interface | Import-aware Java type reference projection. |
| `TypeVariable` | interface | Read projection for a generic type variable. |
| `TypeVariableSource` | interface | Mutable generic type-variable projection. |
| `Annotation` | interface | Read projection for an annotation use. |
| `AnnotationSource` | interface | Mutable annotation-use projection. |
| `AnnotationElement` | interface | Read projection for an annotation declaration element. |
| `AnnotationElementSource` | interface | Mutable annotation declaration element. |
| `EnumConstant` | interface | Read projection for an enum constant. |
| `EnumConstantSource` | interface | Mutable enum-constant projection. |
| `JavaRecordComponent` | interface | Read projection for a record component. |
| `JavaRecordComponentSource` | interface | Mutable record-component projection. |
| `JavaDoc` | interface | Read projection for a documentation comment. |
| `JavaDocSource` | interface | Mutable documentation-comment projection. |
| `JavaDocTag` | interface | Name/value projection for one documentation tag. |
| `SyntaxError` | interface | Recoverable parse diagnostic projection. |
| `Visibility` | enum | Shared visibility values and conversion helpers. |

### CLI Entry Points

There is no console script, executable main class, or Maven plugin goal for this artifact. Programmatic use is through the Java packages listed above.

## Appendix A: Environment

The working environment runs Java 17 and Maven on Linux without network access. Maven dependencies required by the assessment are pre-cached, including JUnit Jupiter, AssertJ Core, and Maven Surefire for test execution; the target artifact is not preinstalled. The assessment environment provides the same JDK and dependency cache.

The project must declare a standard Maven `pom.xml` at the project root and must produce the artifact `org.jboss.forge.roaster:roaster-jdt`. Runtime implementation dependencies must be declared in that POM and must resolve from the pre-cached local Maven repository.

## Appendix B: Assessment Notes

Assessment exercises only the public Java interfaces and member families declared above. Checks cover creation and typed parsing, compilation-unit order, fluent mutation and lookup, imports and type resolution, member/property coherence, annotations and documentation, specialized declarations, diagnostics, formatting, source rendering, reparsing, error types, and cross-view invariants. The focus is observable semantic behavior; private classes, provider internals, exact messages, and exact whitespace are not assessed.
