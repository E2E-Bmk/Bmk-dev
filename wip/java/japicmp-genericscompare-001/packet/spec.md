# Markline Generics Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how each class's declared generic type parameters changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, and beneath each class one record per declared generic type parameter and one record per method. Each record carries a change status — new, removed, modified, or unchanged. A generic-parameter record also carries the parameter's name and the old and new form of its bound type. The comparison reads the compiled forms through the bytecode toolkit's class and member handles, resolving the generic type parameters from each handle's generic signature rather than through reflection on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod`, and `javassist.CtBehavior` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of wildcard type arguments at use sites; the tracked owners are the type parameters declared on the class and its methods.
- This specification does not require compatibility with the change-classification, signature-parsing, or option defaults of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting generics tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Box");
CtClass newC = pool.makeClass("com.acme.Box");
newC.setGenericSignature("<T:Ljava/lang/Object;>Ljava/lang/Object;"); // new side: Box<T>
JarArchiveComparator cmp = new JarArchiveComparator(new JarArchiveComparatorOptions());
List<JApiClass> tree = cmp.compareClassLists(cmp.getJarArchiveComparatorOptions(),
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getGenericTemplates().get(0).getName().equals("T")
// tree.get(0).getGenericTemplates().get(0).getChangeStatus() == NEW
```

The single class record exposes its list of generic-parameter records and its list of method records; each record is classified independently.

## Classifying Generic Type Parameters

The comparator resolves the declared generic type parameters of each side from the class handle's generic signature and pairs them by name.

- A type parameter present on both sides is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. Parameter records are keyed by declared name and their declaration order is preserved.
- The list of parameter records for a class covers the union of the parameter names across the two sides; every parameter present on either side yields exactly one record, so a record that is `REMOVED` still appears in the list.
- Renaming a parameter is reported as the removal of the old name and the addition of the new name, producing two records.
- Each parameter record reports its bound type through `getNewType` for the new side and `getOldType` for the old side; an unbounded parameter reports the bound `java.lang.Object`. A one-sided parameter has an empty `Optional` for the side on which it is absent.

## Classifying Methods and Class Status

- A method present on both sides with the same signature is `UNCHANGED`; one present only on the new side is `NEW`; one present only on the old side is `REMOVED`. Methods are keyed by name and parameter shape.
- A class present only on the new side is `NEW`; one present only on the old side is `REMOVED`; a class present on both sides carries its generic-parameter and method records classified independently of one another.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, an ordered list of generic-parameter records, and an ordered list of method records. Each `JApiGenericTemplate` holds a name, a status, and an optional old and new bound-type string. Each `JApiMethod` holds a name and a status. A one-sided class contributes its records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- A generic-parameter record for a name present on both sides must never report `NEW` or `REMOVED`.
- Reading the bound-type `Optional` of the side on which a one-sided parameter is absent must return an empty `Optional`, never `null`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. The number of generic-parameter records for a class equals the number of distinct parameter names across the two sides, and no name appears in two records.
2. A parameter record's status is `NEW` if and only if its name is absent on the old side and present on the new side, and `REMOVED` in the mirror case.
3. A class present only on the new side reports status `NEW`, its `getOldClass` is an empty `Optional`, and each of its parameter and method records reports `NEW`.
4. The generic-parameter records and the method records of one class are classified independently: adding a method does not alter any parameter record's status and adding a parameter does not alter any method record's status.
5. A `NEW` parameter has an empty old-type `Optional` and a present new-type `Optional`; a `REMOVED` parameter has the mirror; an `UNCHANGED` parameter has both present.
6. A one-sided class's records are homogeneous: every parameter and method record of a `NEW` class is `NEW`, and every record of a `REMOVED` class is `REMOVED`.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the generic-parameter and method records, and the status enum |

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

public class JApiGenericTemplate implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public String getOldType();
    public String getNewType();
    public java.util.Optional<String> getOldTypeOptional();
    public java.util.Optional<String> getNewTypeOptional();
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
    public java.util.List<org.markline.model.JApiGenericTemplate> getGenericTemplates();
    public java.util.List<org.markline.model.JApiMethod> getMethods();
}
```

### Command-Line Interface

Markline is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on the `javassist` bytecode toolkit (`org.javassist:javassist` at version 3.30.2-GA), provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles carrying generic signatures. Single-owner checks confirm one decision at a time: the status of a type parameter added, removed, or left unchanged, together with its name, its bound type, and the record count; and the status of a method added, removed, or left unchanged. Cross-owner checks combine two views over one comparison — that a parameter change and a method change are classified independently, that a one-sided class marks every record homogeneously, that the record count covers the union of both sides. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, parameter names, bound-type strings, list sizes; they never inspect private fields. Resolving type parameters means parsing the generic signature carried by the bytecode handle rather than reflecting on a loaded type. The pairing, status, and record-coverage rules stated above are the contract under test — a conforming implementation reproduces them exactly.
