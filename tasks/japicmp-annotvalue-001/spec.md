# Markline Annotation Value Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how the values held by their annotation members changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, beneath it one record per runtime-visible annotation, and beneath each annotation one record per annotation member (element). Each element record carries a change status — new, removed, modified, or unchanged — together with the member's name and the old and new member value read from the compiled annotation. The comparison reads the compiled forms and their annotation member values through the bytecode toolkit rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod` — and whose annotation member-value type `javassist.bytecode.annotation.MemberValue` appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of source-retained annotations; only runtime-visible annotations and their members are tracked.
- This specification does not require compatibility with the change-classification or value-formatting of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting element tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service"); // carries @A(count=1)
CtClass newC = pool.makeClass("com.acme.Service"); // carries @A(count=2)
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getAnnotations().get(0).getElements().get(0).getChangeStatus() == MODIFIED
```

Each class record exposes its annotation records and its method records; each annotation record exposes its element records, classified independently.

## Classifying Annotation Members

The comparator reads the members of each runtime-visible annotation on both sides and pairs them by member name.

- A member present on both sides whose value is equal is `UNCHANGED`; a member present on both sides whose value differs is `MODIFIED`; a member present only on the new side is `NEW`; a member present only on the old side is `REMOVED`.
- The list of element records for an annotation covers the union of member names across the two sides; a `REMOVED` member still appears in the list.
- Each element record reports its member name through `getName` and its old and new member values through `getOldValue` and `getNewValue`, each an `Optional` holding a `javassist.bytecode.annotation.MemberValue`; the `Optional` is empty on the side where the member is absent.
- Member-value equality is decided by the value the compiled annotation carries (for example an int, a string, or a boolean), not by the textual form of the annotation.

## Classifying Annotations, Methods, and Class Status

- An annotation present on both sides is `MODIFIED` when any of its member records is not `UNCHANGED`, and `UNCHANGED` when every member record is `UNCHANGED`. A marker annotation with no members present on both sides is `UNCHANGED` and reports an empty element list.
- A method present on both sides with the same signature is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides carries its annotation and method records classified independently.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, an ordered list of annotation records, and an ordered list of method records. Each `JApiAnnotation` holds a fully-qualified type name, a status, and an ordered list of element records. Each `JApiAnnotationElement` holds a member name, a status, and an optional old and new `MemberValue`. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- An element record for a member present on both sides must never report `NEW` or `REMOVED`.
- Reading the member value of the side on which a one-sided member is absent must yield an empty `Optional`, never `null`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. An element record's status is `NEW` if and only if its member is absent on the old side and present on the new side, `REMOVED` in the mirror case, `MODIFIED` when present on both sides with differing values, and `UNCHANGED` when present on both sides with equal values.
2. The number of element records for an annotation equals the number of distinct member names across the two sides, and no member name appears in two records.
3. An annotation is `MODIFIED` exactly when at least one of its element records is not `UNCHANGED`.
4. A class present only on the new side reports status `NEW`, its `getOldClass` is an empty `Optional`, and each of its annotation, element, and method records reports `NEW`.
5. The element records of one annotation and the method records of the class are classified independently: adding a method does not alter any element record's status and changing a member value does not alter any method record's status.
6. A member present on both sides with equal values yields both a present old value and a present new value; a one-sided member yields exactly one present side.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the annotation and element records, and the status enum |

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
    public java.util.List<org.markline.model.JApiAnnotation> getAnnotations();
    public java.util.List<org.markline.model.JApiMethod> getMethods();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles whose annotations carry member values of several kinds. Single-owner checks confirm one decision at a time: the status of a member added, removed, changed, or left unchanged, together with its name and the record count, for int, string, and boolean members. Cross-owner checks combine two views over one comparison — that a member change and a method change are classified independently, that a one-sided class marks every record homogeneously, that the element count covers the union of both sides. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, member names, list sizes; they never inspect private fields. Reading a member value means reading the compiled annotation's member value from the bytecode handle rather than reflecting on a loaded type. The pairing, status, and value-equality rules stated above are the contract under test — a conforming implementation reproduces them exactly.
