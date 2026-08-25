# Markline Special Modifiers Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Markline is a Java library that compares two versions of a set of compiled classes and reports how the compiler-generated modifiers of each method changed. Given the old and new versions of each class as bytecode handles, it produces a tree of change records: one record per class, and beneath each class one record per method. Every method record exposes two special-modifier views — a bridge view and a synthetic view — each of which carries its own change status and its old and new modifier value. The comparison reads the compiled forms through the bytecode toolkit's class and method handles, inspecting each method's access flags rather than reflecting on loaded classes.

The published artifact has the Maven coordinates `org.markline:markline-core:1.0.0` and all of its own packages live under `org.markline`. It reads compiled classes through the `javassist` bytecode toolkit, whose handle types — `javassist.CtClass`, `javassist.CtMethod`, and `javassist.CtBehavior` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

## Non-Goals

- This specification does not require reading class files from a jar, a directory, or the network; the compared classes are supplied directly as bytecode handles.
- This specification does not define source-compatibility or binary-compatibility verdicts, nor the generation of any textual, XML, or semantic-version report.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define access-level, static, final, or abstract modifier tracking; the tracked modifiers are the bridge flag and the synthetic flag.
- This specification does not require compatibility with the change-classification, flag-detection, or option defaults of any similarly-named comparison library.

## Representative Workflows

Two versions of a class are handed to the comparator as bytecode handles and the resulting modifier tree is read:

```java
import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import javassist.ClassPool;
import javassist.CtClass;
import java.util.List;

ClassPool pool = new ClassPool(true);
CtClass oldC = pool.makeClass("com.acme.Service");
CtClass newC = pool.makeClass("com.acme.Service");
JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
options.setIncludeSynthetic(true);
JarArchiveComparator cmp = new JarArchiveComparator(options);
List<JApiClass> tree = cmp.compareClassLists(options,
        java.util.Arrays.asList(oldC), java.util.Arrays.asList(newC));
// tree.get(0).getMethods().get(0).getBridgeModifier().getNewModifier().get() == NON_BRIDGE
```

Because synthetic methods are omitted by default, the comparator is configured with `setIncludeSynthetic(true)` so that synthetic members appear in the method list. Each method record is classified independently.

## Detecting the Bridge Flag

The bridge view of a method reflects whether the method carries the bridge access flag on each side.

- A method carrying the bridge flag reports `org.markline.model.BridgeModifier.BRIDGE` as the value for that side; a method without it reports `org.markline.model.BridgeModifier.NON_BRIDGE`.
- When a method present on both sides carries the same bridge value, its bridge view reports status `UNCHANGED`.
- When a method present on both sides loses the bridge flag, its bridge view reports status `REMOVED`, its old modifier value is `BRIDGE`, and its new modifier value is absent.
- A method present only on one side contributes its bridge view with the value read from the side on which it exists.

## Detecting the Synthetic Flag and Class Status

- The synthetic view of a method reports `org.markline.model.SyntheticModifier.SYNTHETIC` for a side carrying the synthetic access flag and `org.markline.model.SyntheticModifier.NON_SYNTHETIC` otherwise.
- When a method present on both sides carries the same synthetic value, its synthetic view reports status `UNCHANGED`. When the synthetic value differs between the two sides, its synthetic view reports status `MODIFIED` and both the old and new modifier values are present.
- A method present only on the new side reports method status `NEW`; one present only on the old side reports `REMOVED`; a method present on both sides with equal signatures reports `UNCHANGED`.
- A class present on both sides reports status `MODIFIED` when a non-synthetic method is added or removed, and `UNCHANGED` when the only differences are the synthetic view of its methods or the addition of a synthetic method. A class present on only one side reports `NEW` or `REMOVED`.

## State Model

Each `JApiClass` holds an optional old and new `javassist.CtClass` handle, a fully-qualified name, and an ordered list of method records. Each `JApiMethod` holds a name, a status, a bridge-modifier view, and a synthetic-modifier view. Each modifier view holds an optional old value, an optional new value, and a status. A one-sided class contributes its method records entirely as `NEW` or entirely as `REMOVED`.

## Error Semantics

- `JarArchiveComparator.compareClassLists` must reject a `null` class list by raising `java.lang.IllegalArgumentException`.
- A modifier view for a method present on both sides carrying an equal value must report `UNCHANGED`, never `NEW`, `REMOVED`, or `MODIFIED`.
- Reading the modifier value of a side on which the flag is absent after a removal must yield an absent `Optional`, never `null`.
- Comparing two class lists that pair to nothing in common must return a list containing only `NEW` and `REMOVED` classes, never an `UNCHANGED` or `MODIFIED` one.

## Cross-View Invariants

1. A method's bridge view and its synthetic view are independent: changing one flag leaves the other view `UNCHANGED`.
2. The bridge view reports `REMOVED` if and only if the bridge flag is present on the old side and absent on the new side of a method present on both sides.
3. The synthetic view reports `MODIFIED` if and only if the synthetic flag differs between the two sides of a method present on both sides.
4. A method present only on the new side reports status `NEW`, and both its modifier views read their value from the new side.
5. Adding a synthetic method leaves the enclosing class `UNCHANGED`, whereas adding a non-synthetic method makes the enclosing class `MODIFIED`.
6. The number of method records equals the number of distinct method signatures across the two sides once synthetic members are included.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.markline.cmp` | the comparator and its options |
| `org.markline.model` | the change-record tree, the modifier views, and the modifier and status enums |

The bytecode-handle types (`javassist.CtClass`, `javassist.CtMethod`, `javassist.CtBehavior`) are supplied by the `org.javassist:javassist` dependency and are not part of this artifact.

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
public enum BridgeModifier { BRIDGE, NON_BRIDGE; }
public enum SyntheticModifier { SYNTHETIC, NON_SYNTHETIC; }

public interface JApiHasChangeStatus {
    org.markline.model.JApiChangeStatus getChangeStatus();
}

public class JApiModifier<T extends java.lang.Enum<T>> implements org.markline.model.JApiHasChangeStatus {
    public java.util.Optional<T> getOldModifier();
    public java.util.Optional<T> getNewModifier();
    public org.markline.model.JApiChangeStatus getChangeStatus();
}

public abstract class JApiBehavior implements org.markline.model.JApiHasChangeStatus {
    public String getName();
    public org.markline.model.JApiChangeStatus getChangeStatus();
    public org.markline.model.JApiModifier<org.markline.model.BridgeModifier> getBridgeModifier();
    public org.markline.model.JApiModifier<org.markline.model.SyntheticModifier> getSyntheticModifier();
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

Evaluation exercises the comparator on class versions synthesised in memory as bytecode handles whose methods carry the bridge or synthetic access flag. Single-owner checks confirm one decision at a time: the bridge value a method reports on each side, the status of a bridge flag left unchanged or removed, the synthetic value a method reports, the status of a synthetic flag left unchanged or changed, and the presence status of a flag-carrying method added or removed. Cross-owner checks combine two views over one comparison — that the bridge and synthetic views of a method move independently, that a synthetic-only change leaves the class unchanged while a method addition modifies it, that a class set classifies each method's flags independently. Whole-comparison checks compare small class sets and read the full record tree. Assertions pin concrete observable values — change statuses, modifier enum values, method statuses; they never inspect private fields. Detecting a special modifier means reading the method's access flags from the bytecode handle rather than reflecting on a loaded type. The detection, status, and class-impact rules stated above are the contract under test — a conforming implementation reproduces them exactly.
