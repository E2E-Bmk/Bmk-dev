# JavaPoet Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`javapoet` is a Java library for generating `.java` source files. Callers assemble an immutable model of a compilation unit — type declarations, methods, fields, parameters, annotations, and code bodies — through builder objects, then emit that model as formatted Java source text or write it into a package-shaped directory tree.

The library has three cooperating layers over one model: a type-name model (`TypeName` and its subtypes) that names Java types independently of any generated file; a declaration model (`TypeSpec`, `MethodSpec`, `FieldSpec`, `ParameterSpec`, `AnnotationSpec`, `CodeBlock`) built through a placeholder-based format language; and a file assembler (`JavaFile`) that renders one top-level type together with a package statement and a computed import list. A helper, `NameAllocator`, produces collision-free legal Java identifiers.

## Non-Goals

- This specification does not require parsing existing Java source text.
- This specification does not require interoperability with `javax.lang.model` mirror APIs beyond accepting `javax.lang.model.element.Modifier` values on builders.
- This specification does not require compiling, type-checking, or validating that emitted source references resolvable types.
- This specification does not define emission of module declarations, records, or sealed types.
- This specification does not define thread-safety guarantees for builder objects.

## Representative Workflows

The first workflow builds the classic "hello world" program and renders it to a string. A `MethodSpec` describes `main`, a `TypeSpec` wraps it in a class, and a `JavaFile` supplies the package and computes imports.

```java
import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.TypeSpec;
import javax.lang.model.element.Modifier;

MethodSpec main = MethodSpec.methodBuilder("main")
    .addModifiers(Modifier.PUBLIC, Modifier.STATIC)
    .returns(void.class)
    .addParameter(String[].class, "args")
    .addStatement("$T.out.println($S)", System.class, "Hello, JavaPoet!")
    .build();

TypeSpec helloWorld = TypeSpec.classBuilder("HelloWorld")
    .addModifiers(Modifier.PUBLIC, Modifier.FINAL)
    .addMethod(main)
    .build();

JavaFile javaFile = JavaFile.builder("com.example.helloworld", helloWorld).build();
String source = javaFile.toString();
```

The second workflow generates an enum whose constants carry anonymous class bodies, then writes the file into a directory tree, producing `dir/com/example/Roshambo.java`.

```java
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.TypeSpec;
import javax.lang.model.element.Modifier;
import java.nio.file.Path;

TypeSpec roshambo = TypeSpec.enumBuilder("Roshambo")
    .addModifiers(Modifier.PUBLIC)
    .addEnumConstant("ROCK", TypeSpec.anonymousClassBuilder("$S", "fist")
        .addMethod(MethodSpec.methodBuilder("toString")
            .addAnnotation(Override.class)
            .addModifiers(Modifier.PUBLIC)
            .returns(String.class)
            .addStatement("return $S", "avalanche!")
            .build())
        .build())
    .addEnumConstant("PAPER")
    .build();

JavaFile file = JavaFile.builder("com.example", roshambo).build();
file.writeTo(Path.of("generated"));
```

## Code Blocks and the Format Language

`CodeBlock` is the unit of code text. Every builder method that accepts code accepts a format string plus arguments, and expands placeholders that each begin with `$`. This mini-language is the sole way arguments enter generated code.

**Placeholders.** The format language must support exactly the following expansions:

- `$L` emits the argument as a literal. When the argument is a `CodeBlock`, `TypeSpec`, `AnnotationSpec`, or another spec object, its rendered form is embedded; numbers, booleans, and character sequences are emitted through their string form. A null argument emits the text `null`.
- `$S` emits the argument as a double-quoted Java string literal. Backslashes, double quotes, and control characters in the argument must be escaped so the emitted literal round-trips the value; a tab character emits `\t`. When the argument is null, `$S` emits the unquoted text `null`.
- `$T` emits a type. The argument accepts a `TypeName`, a `Class`, or a `javax.lang.model` type mirror. When emission happens inside a `JavaFile`, the type is recorded for import collection and emitted by its short name where the import succeeds; when a `CodeBlock`, `MethodSpec`, or `TypeSpec` is rendered standalone through `toString`, there is no import context and every `$T` emits the fully qualified canonical name.
- `$N` emits the name of the argument, which accepts a `MethodSpec`, `FieldSpec`, `ParameterSpec`, `TypeSpec`, or a character sequence.
- `$$` emits one literal dollar sign.
- `$W` emits a single space, or a newline plus continuation indentation if the current line would otherwise grow beyond the wrapping limit.
- `$>` and `$<` increase and decrease the indentation level by one step; `$[` and `$]` open and close a statement region.

If a format string references an unknown placeholder letter, or the argument count does not match the placeholders consumed, then the call must raise `IllegalArgumentException`.

**Construction and composition.** `CodeBlock.of` builds a block from one format string. `CodeBlock.builder()` returns a builder whose `add` appends formatted text, whose `addStatement` appends the formatted text followed by a semicolon and newline within a statement region, and whose `beginControlFlow`, `nextControlFlow`, and `endControlFlow` open and close brace-delimited regions. `build` returns the immutable block. `CodeBlock.join(blocks, separator)` returns one block joining the given blocks with the separator text; `CodeBlock.joining(separator)` returns a `Collector` with the same result. `isEmpty` returns true exactly when the block contains no content. `toBuilder` returns a builder preloaded with the block's content. Two `CodeBlock` values with the same content must be `equals` with equal `hashCode`, and `toString` returns the rendered text.

**Control flow shape.** `beginControlFlow("if (a)")` emits `if (a) {` and indents by one step; `nextControlFlow("else")` closes the open brace and continues with `} else {` on one line; `endControlFlow()` emits the closing brace. One indentation step inside a rendered body is two spaces.

## Type Name Model

`TypeName` values name Java types independently of any file, and are the arguments `$T` consumes. The model must distinguish primitives, boxed primitives, class names, arrays, parameterized types, type variables, and wildcards.

**Primitives and boxing.** `TypeName` exposes the constants `VOID`, `BOOLEAN`, `BYTE`, `SHORT`, `INT`, `LONG`, `CHAR`, `FLOAT`, `DOUBLE`, and `OBJECT`. `TypeName.get(int.class)` must be equal to `TypeName.INT`, and the constants render as the Java keywords (`int`, `void`); `OBJECT` renders as `java.lang.Object`. `box()` on a primitive returns the boxed class name (`INT.box()` renders `java.lang.Integer`); `unbox()` on a boxed name returns the primitive; boxing then unboxing returns an equal value. `isPrimitive()` returns true only for the nine non-void primitives; `isBoxedPrimitive()` returns true only for their boxed class names. If `unbox()` is invoked on a type that is neither primitive nor boxed, then it must raise `UnsupportedOperationException`.

**Class names.** `ClassName.get(packageName, simpleName, nestedNames...)` names a top-level or nested class; `ClassName.get(Class)` and `ClassName.get(TypeElement)` convert existing types. `ClassName.bestGuess(text)` splits a dotted name by treating every leading segment that starts with a lowercase letter as package, and every segment that starts with an uppercase letter as a class nesting chain: `bestGuess("java.util.Map.Entry")` has `packageName()` `java.util`, `simpleName()` `Entry`, `canonicalName()` `java.util.Map.Entry`, and `reflectionName()` `java.util.Map$Entry`, and its `topLevelClassName()` is `java.util.Map`. If no class segment can be identified — for example a trailing dot or an all-lowercase name ending the string — then `bestGuess` must raise `IllegalArgumentException`. `nestedClass(name)` returns the name nested one level deeper; `peerClass(name)` returns a sibling in the same enclosing scope; `enclosingClassName()` returns the enclosing name or null for a top-level class. A `ClassName` in the default package uses the empty string as `packageName()` and renders without a package prefix. Equal package and nesting chains compare `equals`, and `ClassName` implements `Comparable`.

**Composite type names.** `ParameterizedTypeName.get(rawType, typeArguments...)` accepts a `ClassName` raw type with `TypeName` arguments, and a convenience overload accepts `Class` values; the rendered form is the raw canonical name followed by comma-separated type arguments in angle brackets. `ArrayTypeName.of(componentType)` renders the component followed by `[]`. `TypeVariableName.get(name)` renders the bare variable name and exposes its bounds through the public `bounds` list, which is empty for an unbounded variable and carries the given bounds otherwise. `WildcardTypeName.subtypeOf(bound)` renders `? extends {bound}`, except that a bound equal to `java.lang.Object` renders as the bare `?`; `WildcardTypeName.supertypeOf(bound)` renders `? super {bound}`. `annotated(annotations)` attaches type-use annotations and `withoutAnnotations()` removes them.

## Type Declarations

`TypeSpec` models one type declaration: class, interface, enum, annotation type, or anonymous class. The kind is fixed by the factory: `classBuilder`, `interfaceBuilder`, `enumBuilder`, `annotationBuilder`, and `anonymousClassBuilder`; `classBuilder` and the other named factories also accept a `ClassName` whose simple name is used.

**Members and structure.** The builder must accept modifiers (`addModifiers`), a superclass (`superclass`), superinterfaces (`addSuperinterface`), type variables (`addTypeVariable`), fields (`addField`, including a convenience overload taking type, name, and modifiers), methods (`addMethod`), nested types (`addType`), annotations (`addAnnotation`), Javadoc (`addJavadoc`), a static initializer block (`addStaticBlock`), and an instance initializer block (`addInitializerBlock`). `build` returns the immutable spec; `toBuilder` returns a builder preloaded with the spec's state; the public field `name` carries the declared simple name. Rendered members are separated by one blank line, and a rendered class places its static block, instance initializer block, fields, constructors, and methods in the order the emission rules define: fields and blocks in declaration order, then constructors, then methods.

**Enums.** Enum constants are added with `addEnumConstant(name)` or `addEnumConstant(name, TypeSpec)` where the `TypeSpec` comes from `anonymousClassBuilder` and supplies constructor arguments and an optional class body. A rendered enum separates its constants by commas with class-bodied constants on their own lines, and a constant with a body renders the body braces immediately after its argument list. If `build` is invoked on an enum with no constants, then it must raise `IllegalArgumentException`.

**Anonymous classes.** `anonymousClassBuilder(format, args...)` captures the constructor argument list. An anonymous `TypeSpec` embedded through `$L` renders as `new {supertype}({args}) { {members} }`.

**Interfaces.** Interface members are implicitly public; the emitter must omit the redundant `public` and `abstract` modifiers on interface methods and the redundant `public static final` on interface fields when rendering. An interface method carrying only `PUBLIC` and `ABSTRACT` renders as a bodiless declaration terminated by a semicolon.

**Validation.** If an interface method's modifiers include an access level other than public or private, then the enclosing `build` must raise `IllegalArgumentException` naming the offending modifiers. If an annotation-type member carries a default, it is set through `defaultValue` on the method. The builder must reject null member additions with `NullPointerException` or `IllegalArgumentException`.

## Methods, Fields, Parameters, and Annotations

`MethodSpec` models methods and constructors; `FieldSpec` models fields; `ParameterSpec` models parameters; `AnnotationSpec` models annotation uses.

**Methods.** `MethodSpec.methodBuilder(name)` starts a method; `MethodSpec.constructorBuilder()` starts a constructor. The builder accepts modifiers, type variables, a return type (`returns`; a method with no declared return type renders `void`), parameters (`addParameter` accepting a `ParameterSpec` or a type-name-and-name convenience), thrown exceptions (`addException`), Javadoc, annotations, a varargs flag (`varargs`), a default value for annotation-type members (`defaultValue`), and body code through `addCode`, `addComment`, `addStatement`, and the control-flow trio. The rendered form of a standalone method uses fully qualified type names, two-space body indentation, and a blank body renders as an empty brace pair on two lines. A varargs method renders its final array parameter with `...` in place of `[]`. If code is added to a method whose modifiers include `ABSTRACT`, then `build` must raise `IllegalArgumentException`. The public field `name` carries the method name; a constructor renders with the enclosing type's name inside a `TypeSpec`.

**Fields.** `FieldSpec.builder(type, name, modifiers...)` declares a field; `initializer(format, args...)` attaches an initializer expression; the rendered form is the modifiers, type, name, optional ` = {initializer}`, and a terminating semicolon.

**Parameters.** `ParameterSpec.builder(type, name, modifiers...)` declares a parameter with optional annotations and modifiers.

**Annotations.** `AnnotationSpec.builder(ClassName)` (or the `Class` convenience) starts an annotation; `addMember(name, format, args...)` adds one member value. A marker annotation renders as `@{type}`; an annotation with members renders `@{type}({name} = {value}, ...)` with members in insertion order; a members-only `value` shorthand is not implied — the member name is always emitted when any member other than a lone unnamed shorthand exists. `AnnotationSpec.get` converts an existing annotation object or mirror.

**Javadoc.** `addJavadoc(format, args...)` on types, methods, and fields renders a `/** ... */` block above the declaration with each line prefixed by ` * `.

## Source File Assembly and Import Resolution

`JavaFile` binds one top-level `TypeSpec` to a package and renders the complete compilation unit. This is where short names, imports, and file layout are decided; all other renderings are context-free.

**Layout.** `JavaFile.builder(packageName, typeSpec)` starts the file. The rendered unit is: the optional file comment (`addFileComment`, emitted as `//` lines), the `package` statement followed by one blank line (omitted entirely for the empty package name), the import list sorted lexicographically with one blank line after it when non-empty, then the type. `indent(text)` replaces the two-space indentation unit used throughout the file. `toString` returns the rendered text, and `writeTo` accepts a directory as `Path`, `File`, or an annotation-processing `Filer`, creating one subdirectory per package segment and a `{TypeName}.java` file whose content equals `toString()`.

**Import computation.** Every type referenced through `$T`, and every type used in signatures, superclasses, annotations, and initializers, is a candidate for import. Each candidate's top-level class is imported and referenced by its short name — a nested name such as `java.util.Map.Entry` imports `java.util.Map` and renders `Map.Entry`. When two candidate types share a simple name, the first one encountered wins the import and every later one renders fully qualified. Types in `java.lang` are imported explicitly by default; `skipJavaLangImports(true)` suppresses `java.lang` imports and renders those types by short name, except that a `java.lang` simple name that conflicts with another referenced type must still render fully qualified.

**Static imports.** `addStaticImport(ClassName, names...)` (or the enum-constant convenience) registers `import static` lines, rendered in their own sorted group before the type imports. A qualified call written as `$T.member(...)` where the type and member match a registered static import renders as the bare member reference.

## State Model

The core state is the immutable spec model: every `build()` yields a value object whose rendered text, equality, and hash are fixed at construction. Public projections of that one state are: the rendered text of each spec through `toString`; the assembled compilation unit through `JavaFile.toString`; the file-system tree through `writeTo`; equality and ordering (`equals`, `hashCode`, `compareTo` on `ClassName`); introspection surfaces (`name` fields, `bounds`, `packageName()`, `simpleName()`, nesting queries); and round-tripping through `toBuilder`.

- A spec rendered standalone must use fully qualified type names; the same spec rendered inside a `JavaFile` must use the file's import decisions. The underlying model is identical in both projections.
- `toBuilder().build()` must yield a value equal to the original spec.
- Two specs constructed with the same content through different call sequences must be `equals` and render identical text.
- `JavaFile.writeTo` must produce file content identical to `JavaFile.toString()`.

## Error Semantics

| Condition | Required result |
|---|---|
| Format string with unknown `$` placeholder or mismatched argument count | The formatting call must raise `IllegalArgumentException`. |
| `ClassName.bestGuess` on text with no identifiable class segment | Must raise `IllegalArgumentException`. |
| `unbox()` on a type that is neither primitive nor boxed | Must raise `UnsupportedOperationException`. |
| Code added to a method whose modifiers include `ABSTRACT` | `MethodSpec.Builder.build` must raise `IllegalArgumentException`. |
| Enum `build()` with zero constants | Must raise `IllegalArgumentException`. |
| Interface method with a disallowed access modifier | The enclosing type `build()` must raise `IllegalArgumentException`. |
| Null type, name, or spec argument to a builder method | Must raise `NullPointerException` or `IllegalArgumentException`. |

Exception messages are informative only; their exact wording is not part of this contract.

## Cross-View Invariants

1. For every spec object, the text embedded by `$L`/`$N` inside another spec must be consistent with the spec's own `toString` rendering under the surrounding context's import decisions.
2. A type referenced by `$T` must render with a short name in a `JavaFile` if and only if that file's import list contains the corresponding top-level import, and must render fully qualified otherwise; standalone renderings always match the fully-qualified projection.
3. `writeTo(directory)` must create exactly the package-segment directory chain of the file's package name, and the bytes written must equal `toString()`.
4. Equal specs (`equals` true) must render byte-identical text in the same context, and `hashCode` must agree with `equals`.
5. `toBuilder` followed by `build` with no interleaved mutation must reproduce a spec that is `equals` to the original and renders identically, for `TypeSpec`, `MethodSpec`, `FieldSpec`, `AnnotationSpec`, and `CodeBlock`.
6. `ClassName` navigation must be self-consistent: `nestedClass(n).enclosingClassName()` equals the receiver, `topLevelClassName()` of a nested name equals the head of its nesting chain, and `reflectionName()` uses `$` exactly where `canonicalName()` uses `.` between class segments.

## Public Interface

### Import Surface

```java
import com.squareup.javapoet.AnnotationSpec;
import com.squareup.javapoet.ArrayTypeName;
import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.CodeBlock;
import com.squareup.javapoet.FieldSpec;
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.NameAllocator;
import com.squareup.javapoet.ParameterSpec;
import com.squareup.javapoet.ParameterizedTypeName;
import com.squareup.javapoet.TypeName;
import com.squareup.javapoet.TypeSpec;
import com.squareup.javapoet.TypeVariableName;
import com.squareup.javapoet.WildcardTypeName;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `CodeBlock` | `of`, `builder`, `join`, `joining`, `isEmpty`, `toBuilder`, `toString`, `equals`, `hashCode`; builder: `add`, `addNamed`, `addStatement`, `beginControlFlow`, `nextControlFlow`, `endControlFlow`, `indent`, `unindent`, `isEmpty`, `build` |
| `TypeName` | constants `VOID`, `BOOLEAN`, `BYTE`, `SHORT`, `INT`, `LONG`, `CHAR`, `FLOAT`, `DOUBLE`, `OBJECT`; `get`, `box`, `unbox`, `isPrimitive`, `isBoxedPrimitive`, `annotated`, `withoutAnnotations`, `isAnnotated`, `toString`, `equals`, `hashCode` |
| `ClassName` | `get`, `bestGuess`, `packageName`, `simpleName`, `simpleNames`, `canonicalName`, `reflectionName`, `topLevelClassName`, `enclosingClassName`, `nestedClass`, `peerClass`, `compareTo` |
| `ParameterizedTypeName` | `get`, `nestedClass`, public field `rawType`, public field `typeArguments` |
| `ArrayTypeName` | `of`, `get`, public field `componentType` |
| `TypeVariableName` | `get`, `withBounds`, public field `name`, public field `bounds` |
| `WildcardTypeName` | `subtypeOf`, `supertypeOf`, `get` |
| `TypeSpec` | `classBuilder`, `interfaceBuilder`, `enumBuilder`, `annotationBuilder`, `anonymousClassBuilder`, `toBuilder`, `toString`, `equals`, public fields `name`, `kind`, `modifiers`, `methodSpecs`, `fieldSpecs`, `superinterfaces`, `enumConstants`; builder: `addModifiers`, `superclass`, `addSuperinterface`, `addTypeVariable`, `addField`, `addMethod`, `addType`, `addAnnotation`, `addJavadoc`, `addEnumConstant`, `addStaticBlock`, `addInitializerBlock`, `build` |
| `MethodSpec` | `methodBuilder`, `constructorBuilder`, `toBuilder`, `toString`, `equals`, `isConstructor`, public fields `name`, `modifiers`, `returnType`, `parameters`; builder: `addModifiers`, `addTypeVariable`, `returns`, `addParameter`, `addException`, `addAnnotation`, `addJavadoc`, `varargs`, `defaultValue`, `addCode`, `addComment`, `addStatement`, `beginControlFlow`, `nextControlFlow`, `endControlFlow`, `build` |
| `FieldSpec` | `builder`, `toBuilder`, `toString`, `equals`, public fields `name`, `type`, `modifiers`; builder: `addModifiers`, `addAnnotation`, `addJavadoc`, `initializer`, `build` |
| `ParameterSpec` | `builder`, `get`, `toBuilder`, `toString`, `equals`, public fields `name`, `type`; builder: `addModifiers`, `addAnnotation`, `addJavadoc`, `build` |
| `AnnotationSpec` | `builder`, `get`, `toBuilder`, `toString`, `equals`, public field `type`; builder: `addMember`, `build` |
| `JavaFile` | `builder`, `toBuilder`, `toString`, `writeTo`, `writeToPath`, `toJavaFileObject`, `equals`, public fields `packageName`, `typeSpec`; builder: `addFileComment`, `addStaticImport`, `skipJavaLangImports`, `indent`, `build` |
| `NameAllocator` | constructor, `newName` (with and without tag), `get`, `clone` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `CodeBlock` | class | Immutable fragment of code text built through the `$` format language. |
| `TypeName` | class | Root of the type-name model; carries primitive constants and boxing rules. |
| `ClassName` | class | Names a top-level or nested class with package and nesting chain. |
| `ParameterizedTypeName` | class | Names a generic type application. |
| `ArrayTypeName` | class | Names an array type by component. |
| `TypeVariableName` | class | Names a type variable with optional bounds. |
| `WildcardTypeName` | class | Names a bounded or unbounded wildcard. |
| `TypeSpec` | class | Immutable model of one type declaration. |
| `MethodSpec` | class | Immutable model of one method or constructor. |
| `FieldSpec` | class | Immutable model of one field. |
| `ParameterSpec` | class | Immutable model of one parameter. |
| `AnnotationSpec` | class | Immutable model of one annotation use. |
| `JavaFile` | class | One compilation unit: package, computed imports, and a top-level type. |
| `NameAllocator` | class | Allocates unique, legal Java identifiers. |

### Name Allocation

`NameAllocator` converts requested names into legal, unique Java identifiers within one scope. `newName(suggestion)` must replace every character that is not a Java identifier character with `_`, prefix `_` when the first character cannot start an identifier, and append `_` when the result collides with a Java keyword or a previously allocated name (`public` becomes `public_`, a second `foo` becomes `foo_`, `a-b` becomes `a_b`, `1st` becomes `_1st`). `newName(suggestion, tag)` additionally registers the result under the tag, and `get(tag)` returns the name registered for that tag. `clone()` produces an independent allocator preloaded with the same registrations.

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; no third-party runtime library beyond the target artifact is guaranteed to the implementation. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `com.squareup:javapoet`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises public construction and rendering across the format language, the type-name model, declaration builders, file assembly with import resolution, and name allocation. Tests compare rendered source text, returned values, exception classes, and cross-view consistency between standalone renderings, file renderings, and written files; they do not require private field layout, internal emitter classes, or exact exception message text. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that multiple projections remain consistent across complete generation workflows.
