# Markline Annotation Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how each class's declared annotations changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, and beneath each class one record per runtime-visible annotation and one record per method. Each record carries a change status — new, removed, modified, or unchanged. An annotation record also carries the annotation type's fully-qualified name and its element records. The comparison reads the compiled forms through the bytecode toolkit's class and member handles rather than through reflection on loaded classes, so annotation types need not be resolvable on the classpath.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod`, and `javassist.CtBehavior` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of source-retained annotations; only runtime-visible annotations are tracked.
- This specification does not require compatibility with the change-classification, annotation-resolution, or option defaults of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting annotation tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service");
CtClass newC = pool.makeClass("com.acme.Service"); // new side carries @Deprecated
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getAnnotations().get(0).getFullyQualifiedName().equals("java.lang.Deprecated")
// tree.get(0).getAnnotations().get(0).getChangeStatus() == NEW
```

The single class record exposes its list of annotation records and its list of method records; each record is classified independently.

## Classifying Annotations

The comparator reads the runtime-visible annotations attached to each class handle and pairs them by fully-qualified type name.

- An annotation type present on both sides is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. Annotation records are keyed by fully-qualified name and their order is not significant.
- The list of annotation records for a class covers the union of the annotation types across the two sides; every annotation present on either side yields exactly one record, so a record that is `REMOVED` still appears in the list.
- A class present on neither annotated side yields an empty annotation list. A class present only on one side contributes all of its annotations as `NEW` (new side) or `REMOVED` (old side).
- Each annotation record exposes the annotation type's fully-qualified name through `getFullyQualifiedName` and its element records through `getElements`.

## Classifying Methods and Class Status

- A method present on both sides with the same signature is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. Methods are keyed by name and parameter shape.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides carries its annotation and method records classified independently of one another.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, an ordered list of annotation records, and an ordered list of method records. Each `JApiAnnotation` holds a fully-qualified type name, a status, and a list of element records. Each `JApiMethod` holds a name and a status. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- An annotation record for a type present on both sides must never report `NEW` or `REMOVED`.
- A method present only on one side must report `NEW` or `REMOVED`, never `UNCHANGED`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. The number of annotation records for a class equals the number of distinct annotation type names across the two sides, and no annotation name appears in two records.
2. An annotation record's status is `NEW` if and only if its type is absent on the old side and present on the new side, and `REMOVED` in the mirror case.
3. A class present only on the new side reports status `NEW`, its `getOldClass` is an empty `Optional`, and each of its annotation and method records reports `NEW`.
4. The annotation records and the method records of one class are classified independently: adding a method does not alter any annotation record's status and adding an annotation does not alter any method record's status.
5. An annotation present on both sides is `UNCHANGED` and still appears in the annotation list, so the per-record view and the aggregate count agree.
6. A one-sided class's records are homogeneous: every annotation and method record of a `NEW` class is `NEW`, and every record of a `REMOVED` class is `REMOVED`.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the annotation and method records, and the status enum |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtMethod`, `javassist.CtBehavior`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

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

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles carrying runtime-visible annotations. Single-owner checks confirm one decision at a time: the status of an annotation added, removed, or left unchanged, together with its fully-qualified name and the record count; and the status of a method added, removed, or left unchanged. Cross-owner checks combine two views over one comparison — that an annotation change and a method change are classified independently, that a one-sided class marks every record homogeneously, that the record count covers the union of both sides. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, annotation names, list sizes; they never inspect private fields. Reading annotations from a compiled class means reading the runtime-visible annotation attribute of the bytecode handle rather than reflecting on a loaded type. The pairing, status, and record-coverage rules stated above are the contract under test — a conforming implementation reproduces them exactly.
