# Markline Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports the differences in their public shape. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, and beneath it one record per method, constructor, and field. Each record carries a change status — new, removed, modified, or unchanged — together with the old and new form of every modifier it tracks (access level, static, final, abstract, bridge, synthetic, transient, volatile) and, for behaviors, the return type and parameters. The comparison reads the compiled forms through the bytecode toolkit's class, method, constructor, and field handles rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod`, `javassist.CtConstructor`, `javassist.CtField`, and `javassist.CtBehavior` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define annotation-value comparison beyond recording an annotation's presence, nor generic-signature resolution beyond the recorded type strings.
- This specification does not require compatibility with the change-classification, modifier-tracking, or option defaults of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool oldPool = new ClassPool(true);
ClassPool newPool = new ClassPool(true);
CtClass oldC = oldPool.makeClass("com.acme.Service");
CtClass newC = newPool.makeClass("com.acme.Service");
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
List<JApiClass> classes = cmp.compareClassLists(options, List.of(oldC), List.of(newC));
```

## Building the Comparison Model

`JarArchiveComparator.compareClassLists` pairs the old and new classes by fully-qualified name and returns one `JApiClass` per distinct name. A class present only on the new side has status `NEW`; only on the old side, `REMOVED`; on both sides with no tracked change, `UNCHANGED`; on both sides with any tracked change, `MODIFIED`. Under each `JApiClass`, the comparator pairs methods by name and parameter signature, constructors by parameter signature, and fields by name, and produces a `JApiMethod`, `JApiConstructor`, or `JApiField` for each with the same four-way status rule. The comparator reads names, modifiers, return types, and parameters from the supplied `javassist` handles; a handle may be absent (the member exists only on one side), which the model records as an empty `java.util.Optional`.

`JarArchiveComparatorOptions` carries the access-modifier floor (members below it are excluded), whether synthetic members are included, and the class-path configuration; a default-constructed options object includes public and protected members and excludes synthetic ones.

## Classifying Members and Modifiers

Every class, behavior, and field exposes each modifier it tracks as a `JApiModifier<T>` whose type parameter is the modifier enum: `AccessModifier` (`PUBLIC`, `PROTECTED`, `PACKAGE_PROTECTED`, `PRIVATE`), `StaticModifier`, `FinalModifier`, `AbstractModifier`, `BridgeModifier`, `SyntheticModifier`, `TransientModifier`, and `VolatileModifier` (each a two-valued enum with a present and an absent constant). A `JApiModifier` holds the old and new value as `java.util.Optional<T>` and a `JApiChangeStatus`; its status is `MODIFIED` when the old and new values differ, `NEW`/`REMOVED` when the member is one-sided, and `UNCHANGED` otherwise. A `JApiMethod` additionally exposes a `JApiReturnType` recording the old and new return-type strings and their change status. A `JApiClass` exposes its `JApiClassType` (whether it is a class, interface, annotation, or enum) and the same access/static/final/abstract modifiers.

## State Model

The comparison result is an immutable tree: a `List<JApiClass>`, each holding immutable lists of `JApiMethod`, `JApiConstructor`, and `JApiField`, each of those holding its `JApiModifier`s and (for behaviors) parameters and return type. Every node carries a `JApiChangeStatus`. The `javassist` handles behind a node are retained as `Optional`s but the tree does not mutate them. A `JarArchiveComparator` is constructed once from an options object and produces one tree per `compare` call.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- A `JApiModifier` whose member is present on both sides must never report status `NEW` or `REMOVED`; a one-sided member's modifiers must never report `MODIFIED`.
- Reading the old or new handle of a one-sided member must return an empty `Optional`, never `null` and never a fabricated handle.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. A `JApiClass` reported `UNCHANGED` has every method, constructor, and field reported `UNCHANGED`, and every modifier of each reported `UNCHANGED`.
2. A member's `JApiChangeStatus` is `MODIFIED` if and only if at least one of its tracked modifiers, its return type, or its parameter list changed while the member is present on both sides.
3. The access modifier a `JApiField` or `JApiBehavior` reports for a side is present in its `getModifiers` list for that side, so the per-modifier view and the aggregate view agree.
4. A method present only on the new side reports status `NEW`, its `getOldMethod` is an empty `Optional`, and each of its modifiers reports `NEW`.
5. A `JApiReturnType` reports `MODIFIED` exactly when the old and new return-type strings differ, and `UNCHANGED` when they are equal, consistent with the enclosing method's status contribution.
6. The number of `JApiClass` records equals the number of distinct fully-qualified class names across the two inputs, and no name appears in two records.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the modifier records, and the modifier and status enums |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtMethod`, `javassist.CtConstructor`, `javassist.CtField`, `javassist.CtBehavior`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, parameter type, and return type does.

#### `org.markline.cmp`

```java
public class JarArchiveComparatorOptions {
    public JarArchiveComparatorOptions();
    public void setAccessModifier(org.markline.model.AccessModifier accessModifier);
    public org.markline.model.AccessModifier getAccessModifier();
    public void setIncludeSynthetic(boolean includeSynthetic);
    public boolean isIncludeSynthetic();
}

public class JarArchiveComparator {
    public JarArchiveComparator(org.markline.cmp.JarArchiveComparatorOptions options);
    public java.util.List<org.markline.model.JApiClass> compareClassLists(org.markline.cmp.JarArchiveComparatorOptions options, java.util.List<javassist.CtClass> oldClasses, java.util.List<javassist.CtClass> newClasses);
    public org.markline.cmp.JarArchiveComparatorOptions getJarArchiveComparatorOptions();
}
```

#### `org.markline.model`

```java
public enum JApiChangeStatus { NEW, REMOVED, UNCHANGED, MODIFIED; }

public interface JApiHasChangeStatus {
    org.markline.model.JApiChangeStatus getChangeStatus();
}

public enum AccessModifier { PRIVATE, PACKAGE_PROTECTED, PROTECTED, PUBLIC; }
public enum StaticModifier { STATIC, NON_STATIC; }
public enum FinalModifier { FINAL, NON_FINAL; }
public enum AbstractModifier { ABSTRACT, NON_ABSTRACT; }
public enum BridgeModifier { BRIDGE, NON_BRIDGE; }
public enum SyntheticModifier { SYNTHETIC, NON_SYNTHETIC; }
public enum TransientModifier { TRANSIENT, NON_TRANSIENT; }
public enum VolatileModifier { VOLATILE, NON_VOLATILE; }

public class JApiModifier<T extends java.lang.Enum<T>> implements org.markline.model.JApiHasChangeStatus {
    public java.util.Optional<T> getOldModifier();
    public java.util.Optional<T> getNewModifier();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiClassType implements org.markline.model.JApiHasChangeStatus {
    public String getOldType();
    public String getNewType();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiReturnType implements org.markline.model.JApiHasChangeStatus {
    public String getOldReturnType();
    public String getNewReturnType();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiField implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.CtField> getOldFieldOptional();
    public java.util.Optional<javassist.CtField> getNewFieldOptional();
    public org.markline.model.JApiModifier<org.markline.model.AccessModifier> getAccessModifier();
    public org.markline.model.JApiModifier<org.markline.model.StaticModifier> getStaticModifier();
    public org.markline.model.JApiModifier<org.markline.model.FinalModifier> getFinalModifier();
}

public abstract class JApiBehavior implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.List<org.markline.model.JApiParameter> getParameters();
    public org.markline.model.JApiModifier<org.markline.model.AccessModifier> getAccessModifier();
    public org.markline.model.JApiModifier<org.markline.model.StaticModifier> getStaticModifier();
    public org.markline.model.JApiModifier<org.markline.model.FinalModifier> getFinalModifier();
    public org.markline.model.JApiModifier<org.markline.model.AbstractModifier> getAbstractModifier();
    public org.markline.model.JApiModifier<org.markline.model.BridgeModifier> getBridgeModifier();
    public org.markline.model.JApiModifier<org.markline.model.SyntheticModifier> getSyntheticModifier();
}

public class JApiMethod extends org.markline.model.JApiBehavior {
    public java.util.Optional<javassist.CtMethod> getOldMethod();
    public java.util.Optional<javassist.CtMethod> getNewMethod();
    public org.markline.model.JApiReturnType getReturnType();
}

public class JApiConstructor extends org.markline.model.JApiBehavior {
    public java.util.Optional<javassist.CtConstructor> getOldConstructor();
    public java.util.Optional<javassist.CtConstructor> getNewConstructor();
}

public class JApiClass implements org.markline.model.JApiHasChangeStatus {
    public String getFullyQualifiedName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.CtClass> getOldClass();
    public java.util.Optional<javassist.CtClass> getNewClass();
    public org.markline.model.JApiClassType getClassType();
    public java.util.List<org.markline.model.JApiMethod> getMethods();
    public java.util.List<org.markline.model.JApiConstructor> getConstructors();
    public java.util.List<org.markline.model.JApiField> getFields();
    public org.markline.model.JApiModifier<org.markline.model.AccessModifier> getAccessModifier();
    public org.markline.model.JApiModifier<org.markline.model.AbstractModifier> getAbstractModifier();
}

public class JApiParameter {
    public String getType();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles. Single-owner checks confirm one decision at a time: the four-way status of a class present on one or both sides; the status of a method or field added, removed, or left unchanged; the old and new value of one modifier record; the return-type record of a method whose return type changed; and the class-type record of a type. Cross-owner checks combine two views over one comparison — that an unchanged class has only unchanged members, that a modified member's status follows from its modifier and return-type records, that a one-sided member's handle optional is empty. Whole-comparison checks compare small class sets with several members and read the full record tree. Assertions pin concrete observable values — change statuses, modifier old/new values, names, return-type strings, list sizes; they never inspect private fields. The pairing, status, and modifier rules stated above are the contract under test — a conforming implementation reproduces them exactly.
