# Markline Constructor Annotation Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how the runtime-visible annotations carried by their constructors changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, beneath it one record per constructor, beneath each constructor one record per annotation on that constructor, and beneath each annotation one record per annotation member (element). Each record carries a change status — new, removed, modified, or unchanged. An annotation record carries the annotation type name; an element record carries the member name and the old and new member value. The comparison reads the compiled constructors and their annotation attributes through the bytecode toolkit rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtConstructor` — and whose annotation member-value type `javassist.bytecode.annotation.MemberValue` appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of class-level, method-level, or field-level annotations; the tracked owners are the annotations carried by constructors.
- This specification does not require compatibility with the change-classification of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting per-constructor annotation tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import org.markline.model.JApiConstructor;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service"); // has a no-arg constructor
CtClass newC = pool.makeClass("com.acme.Service"); // constructor carrying @Deprecated
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getConstructors().get(0).getAnnotations().get(0).getChangeStatus() == NEW
```

Each class record exposes its constructor records; each constructor record exposes its annotation records; each annotation record exposes its element records, classified independently. Constructors are paired across the two sides by their parameter signature.

## Classifying Constructor Annotations

The comparator reads the runtime-visible annotations attached to each constructor on both sides and pairs them by fully-qualified type name.

- An annotation present on both sides of a constructor is `UNCHANGED` when all of its members are unchanged, and `MODIFIED` when any member differs; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`.
- Adding, removing, or changing an annotation on a constructor does not by itself change the constructor's own status; a constructor present on both sides with the same parameter signature stays `UNCHANGED` regardless of its annotation changes.
- The annotation records for a constructor cover the union of annotation types across the two sides, keyed by fully-qualified name.

## Classifying Annotation Members and Class Status

- A member of a constructor annotation present on both sides whose value is equal is `UNCHANGED`; one whose value differs is `MODIFIED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. Each element record reports its name through `getName`.
- A constructor present only on the new side is `NEW`, one present only on the old side is `REMOVED`, and each carries its annotation and element records homogeneously as `NEW` or `REMOVED`.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides carries its constructor records classified independently.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, and an ordered list of constructor records. Each `JApiConstructor` holds a name, a status, and an ordered list of annotation records. Each `JApiAnnotation` holds a fully-qualified type name, a status, and an ordered list of element records. Each `JApiAnnotationElement` holds a member name, a status, and an optional old and new `MemberValue`. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- An annotation or element record for an item present on both sides must never report `NEW` or `REMOVED`.
- Reading the member value of the side on which a one-sided member is absent must yield an empty `Optional`, never `null`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. A constructor annotation's status is `NEW` if and only if its type is absent on the old side of that constructor and present on the new side, and `REMOVED` in the mirror case.
2. A constructor annotation is `MODIFIED` exactly when it is present on both sides and at least one of its element records is not `UNCHANGED`.
3. An element record's status is `MODIFIED` when present on both sides with differing values and `UNCHANGED` when the values are equal.
4. A constructor's own status is independent of its annotation changes: an annotation added to, removed from, or changed on a constructor present on both sides leaves that constructor `UNCHANGED`.
5. A constructor present only on the new side reports status `NEW`, and each of its annotation and element records reports `NEW`.
6. The number of annotation records for a constructor equals the number of distinct annotation type names across the two sides, and the number of element records for an annotation equals the number of distinct member names across the two sides.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the constructor/annotation/element records, and the status enum |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtConstructor`) and the annotation member-value type (`javassist.bytecode.annotation.MemberValue`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, parameter type, and return type does.

#### `org.markline.cmp`

```java
public class JarArchiveComparatorOptions {
    public JarArchiveComparatorOptions();
    public void setAccessModifier(org.markline.model.AccessModifier accessModifier);
    public org.markline.model.AccessModifier getAccessModifier();
    public void setNoAnnotations(boolean noAnnotations);
    public boolean isNoAnnotations();
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

public class JApiAnnotationElement implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.bytecode.annotation.MemberValue> getOldValue();
    public java.util.Optional<javassist.bytecode.annotation.MemberValue> getNewValue();
}

public class JApiAnnotation implements org.markline.model.JApiHasChangeStatus {
    public String getFullyQualifiedName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.List<org.markline.model.JApiAnnotationElement> getElements();
}

public abstract class JApiBehavior implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.List<org.markline.model.JApiAnnotation> getAnnotations();
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
    public java.util.List<org.markline.model.JApiConstructor> getConstructors();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles whose constructors carry runtime-visible annotations. Constructors are distinguished by their parameter signature. Single-owner checks confirm one decision at a time: the status of an annotation added to, removed from, or left unchanged on a constructor; the status and value of a member added, removed, changed, or left unchanged; and the record counts. Cross-owner checks combine two views over one comparison — that an annotation change and a constructor addition are classified independently, that a one-sided constructor carries its records homogeneously, that per-class classification is independent. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, type and member names, list sizes; they never inspect private fields. Reading a constructor's annotations means reading the compiled constructor's annotation attribute from the bytecode handle rather than reflecting on a loaded type.
