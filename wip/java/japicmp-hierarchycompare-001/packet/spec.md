# Markline Hierarchy Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how each class's type hierarchy and constructor set changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, and beneath it one record for the superclass, one record per implemented interface, and one record per constructor. Each record carries a change status — new, removed, modified, or unchanged. The superclass record also carries the old and new superclass names; each interface record carries the interface's fully-qualified name; each constructor record carries its old and new bytecode handles. The comparison reads the compiled forms through the bytecode toolkit's class, interface, and constructor handles rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass` and `javassist.CtConstructor` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define method-level or field-level change tracking; the tracked owners are the superclass, the implemented interfaces, and the constructors.
- This specification does not require compatibility with the change-classification, hierarchy-resolution, or option defaults of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting hierarchy tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service");
oldC.setSuperclass(pool.get("java.util.ArrayList"));
CtClass newC = pool.makeClass("com.acme.Service");
newC.setSuperclass(pool.get("java.util.LinkedList"));
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getSuperclass().getChangeStatus() == MODIFIED
// tree.get(0).getSuperclass().getSuperclassOld().equals("java.util.ArrayList")
```

The single class record exposes its superclass record, its list of implemented-interface records, and its list of constructor records; each record is classified independently and the class's own status is the aggregate.

## Resolving the Type Hierarchy

The comparator resolves the superclass and the implemented interfaces of each side by reading the bytecode handle.

- The superclass record compares the fully-qualified name of the old side's superclass with that of the new side's superclass. A class whose declared superclass is `java.lang.Object` on a side is treated as having that name on that side. The record's status is `UNCHANGED` when the two names are equal, and `MODIFIED` when they differ (including when one side is `java.lang.Object` and the other is a named type).
- The set of implemented interfaces of a class is resolved **transitively**: it comprises the interfaces the class declares directly together with every interface reachable through its declared interfaces' super-interfaces and through its superclass hierarchy. Consequently an interface contributed by a resolvable superclass appears in the class's interface set on that side even when the class does not name it directly.
- Each interface present on both sides is `UNCHANGED`; an interface present only on the new side is `NEW`; an interface present only on the old side is `REMOVED`. Interface records are keyed by fully-qualified name and their order is not significant.

## Classifying Constructors and Class Status

- A constructor present on both sides with the same parameter shape is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. The old and new bytecode handle of a one-sided constructor is an empty `Optional`.
- The number of constructor records for a class equals the number of distinct constructors across the two sides.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides is `MODIFIED` when any of its superclass record, interface records, or constructor records is not `UNCHANGED`, and `UNCHANGED` otherwise.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, a class-type record, a single superclass record, an ordered list of implemented-interface records, and an ordered list of constructor records. Each `JApiSuperclass` holds the old and new superclass names and a status; each `JApiImplementedInterface` holds a fully-qualified name and a status; each `JApiConstructor` holds an optional old and new handle and a status. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- Reading the old or new handle of a one-sided constructor must return an empty `Optional`, never `null` and never a fabricated handle.
- A superclass or interface record for a member present on both sides must never report `NEW` or `REMOVED`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. A `JApiClass` reported `UNCHANGED` has its superclass record, every interface record, and every constructor record reported `UNCHANGED`.
2. A `JApiClass` present on both sides is `MODIFIED` if and only if at least one of its superclass record, interface records, or constructor records is not `UNCHANGED`.
3. The superclass record's `getSuperclassOld` and `getSuperclassNew` names are equal exactly when its status is `UNCHANGED`.
4. A class present only on the new side reports status `NEW`, its `getOldClass` is an empty `Optional`, and each of its interface and constructor records reports `NEW`.
5. An interface reachable only through a side's superclass hierarchy still appears in that side's interface set, so an interface common to both sides' superclasses is `UNCHANGED` even if neither class names it directly.
6. The number of `JApiClass` records equals the number of distinct fully-qualified class names across the two inputs, and no name appears in two records.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the hierarchy and constructor records, and the status enum |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtConstructor`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, parameter type, and return type does.

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

public enum AccessModifier { PRIVATE, PACKAGE_PROTECTED, PROTECTED, PUBLIC; }

public interface JApiHasChangeStatus {
    org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiClassType implements org.markline.model.JApiHasChangeStatus {
    public String getOldType();
    public String getNewType();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiSuperclass implements org.markline.model.JApiHasChangeStatus {
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public String getSuperclassOld();
    public String getSuperclassNew();
    public java.util.Optional<String> getOldSuperclassName();
    public java.util.Optional<String> getNewSuperclassName();
}

public class JApiImplementedInterface implements org.markline.model.JApiHasChangeStatus {
    public String getFullyQualifiedName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public abstract class JApiBehavior implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiConstructor extends org.markline.model.JApiBehavior {
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.CtConstructor> getOldConstructor();
    public java.util.Optional<javassist.CtConstructor> getNewConstructor();
}

public class JApiClass implements org.markline.model.JApiHasChangeStatus {
    public String getFullyQualifiedName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.CtClass> getOldClass();
    public java.util.Optional<javassist.CtClass> getNewClass();
    public org.markline.model.JApiClassType getClassType();
    public org.markline.model.JApiSuperclass getSuperclass();
    public java.util.List<org.markline.model.JApiImplementedInterface> getInterfaces();
    public java.util.List<org.markline.model.JApiConstructor> getConstructors();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles. Single-owner checks confirm one decision at a time: the four-way status of a class present on one or both sides; the status of a superclass changed, added, or left unchanged, together with its old and new names; the status of an interface added, removed, or left unchanged, together with its fully-qualified name; and the status of a constructor added, removed, or left unchanged. Cross-owner checks combine two views over one comparison — that an unchanged hierarchy leaves every owner unchanged, that a modified class follows from a non-unchanged superclass, interface, or constructor record, that a one-sided constructor's handle optional is empty. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, superclass names, interface names, list sizes; they never inspect private fields. Because interface resolution is transitive through the superclass hierarchy, hierarchy anchors chosen for interface checks matter: a resolvable superclass contributes its own interfaces to the set. The pairing, status, and resolution rules stated above are the contract under test — a conforming implementation reproduces them exactly.
