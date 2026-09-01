# Markline Class-Value Annotation Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how the values of the members carried by their method annotations changed, focusing on members whose values are class literals or nested annotations. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, beneath it one record per method, beneath each method one record per annotation on that method, and beneath each annotation one record per annotation member (element). Each record carries a change status — new, removed, modified, or unchanged. An annotation record carries the annotation type name; an element record carries the member name and the old and new member value. A class-valued member names a type; a nested-annotation-valued member wraps an entire annotation. The comparison reads the compiled methods and their annotation attributes through the bytecode toolkit rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod` — and whose annotation member-value type `javassist.bytecode.annotation.MemberValue` appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of class-level, field-level, or constructor-level annotations; the tracked owners are the annotations carried by methods.
- This specification does not require compatibility with the change-classification of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting per-member change records are read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service"); // run() has @A(type=String.class)
CtClass newC = pool.makeClass("com.acme.Service"); // run() has @A(type=Integer.class)
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getMethods().get(0).getAnnotations().get(0).getElements().get(0).getChangeStatus() == MODIFIED
```

Each class record exposes its method records; each method record exposes its annotation records; each annotation record exposes its element records, classified independently.

## Classifying Class-Valued and Nested-Annotation-Valued Members

The comparator reads the runtime-visible annotations attached to each method on both sides, pairs them by fully-qualified type name, and pairs their members by member name.

- A member present on both sides whose value is equal is `UNCHANGED`; one whose value differs is `MODIFIED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`.
- Two class-valued members are equal exactly when they name the same fully-qualified type; naming a different type makes the member `MODIFIED`.
- Two nested-annotation-valued members are equal exactly when every member of the wrapped annotation is equal. The wrapped annotation's own type name is not part of this comparison: swapping the nested annotation type while keeping identical members leaves the outer member `UNCHANGED`, whereas any difference among the nested members makes the outer member `MODIFIED`.
- Each element record reports its name through `getName` and its two sides through `getOldValue` and `getNewValue`.

## Classifying Annotations, Methods and Classes

- An annotation present on both sides of a method is `UNCHANGED` when all of its members are unchanged, and `MODIFIED` when any member differs; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. A marker annotation carries no element records.
- Changing, adding, or removing a member value does not by itself change the method's own status; a method present on both sides with the same signature stays `UNCHANGED` regardless of its annotation or member changes.
- A method present only on the new side is `NEW`, one present only on the old side is `REMOVED`, and each carries its annotation and element records homogeneously as `NEW` or `REMOVED`.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides carries its method records classified independently.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, and an ordered list of method records. Each `JApiMethod` holds a name, a status, and an ordered list of annotation records. Each `JApiAnnotation` holds a fully-qualified type name, a status, and an ordered list of element records. Each `JApiAnnotationElement` holds a member name, a status, and an optional old and new `MemberValue`. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- An annotation or element record for an item present on both sides must never report `NEW` or `REMOVED`.
- Reading the member value of the side on which a one-sided member is absent must yield an empty `Optional`, never `null`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. An element record's status is `NEW` if and only if its member name is absent on the old side of that annotation and present on the new side, and `REMOVED` in the mirror case.
2. An element record is `MODIFIED` exactly when it is present on both sides and the two values are not equal, and `UNCHANGED` exactly when they are equal.
3. A class-valued member is `MODIFIED` exactly when the named type differs; a nested-annotation-valued member is `MODIFIED` exactly when one of the wrapped annotation's members differs, and is `UNCHANGED` when the wrapped members all agree even if the wrapped annotation type itself was swapped.
4. An annotation is `MODIFIED` exactly when it is present on both sides and at least one of its element records is not `UNCHANGED`.
5. A method's own status is independent of its member-value changes: a member changed, added, or removed on a method present on both sides leaves that method `UNCHANGED`.
6. A method present only on the new side reports status `NEW`, and each of its annotation and element records reports `NEW`.
7. The number of element records for an annotation equals the number of distinct member names across the two sides, and a marker annotation reports none.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the method/annotation/element records, and the status enum |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtMethod`) and the annotation member-value type (`javassist.bytecode.annotation.MemberValue`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

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

public class JApiMethod extends org.markline.model.JApiBehavior {
    public java.util.Optional<javassist.CtMethod> getOldMethod();
    public java.util.Optional<javassist.CtMethod> getNewMethod();
}

public class JApiClass implements org.markline.model.JApiHasChangeStatus {
    public String getFullyQualifiedName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public java.util.Optional<javassist.CtClass> getOldClass();
    public java.util.Optional<javassist.CtClass> getNewClass();
    public java.util.List<org.markline.model.JApiMethod> getMethods();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles whose methods carry runtime-visible annotations with class-literal and nested-annotation members. Single-owner checks confirm one decision at a time: the status of a class-valued member whose named type changed or stayed the same; the status of a nested-annotation-valued member whose wrapped member changed or stayed the same, including the case where the wrapped annotation type is swapped but its members agree; the status of a member added or removed; the roll-up onto the annotation; and the record counts. Cross-owner checks combine two views over one comparison — that a member change and a method addition are classified independently, that a one-sided method carries its records homogeneously, that per-class classification is independent. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, member names, list sizes; they never inspect private fields. Reading a method's annotations means reading the compiled method's annotation attribute from the bytecode handle rather than reflecting on a loaded type.
