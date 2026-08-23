# TypeDoc Reflection Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`typedoc` is a TypeScript documentation generator that converts exported TypeScript declarations and their comments into a reflection graph, then projects that graph as rendered documentation or a JSON model. The same project state is available through a Node API, a command-line entry point, model classes, JSON serialization, and a browser-safe revival entry point.

The core contract is the reflection graph. A project contains declarations, signatures, parameters, type objects, comments, source references, grouping metadata, category metadata, and external documents. Conversion is deterministic for local source files and configuration, and JSON revival preserves the public model behavior needed for callers to inspect the graph without running the TypeScript compiler again.

## Non-Goals

- This specification does not require network access, remote repositories, package publishing, browser automation, or hosted documentation services.
- This specification does not require exact rendered HTML, CSS assets, syntax highlighting token spans, search-index byte layout, ANSI colors, warning text, or stack traces.
- This specification does not define private modules, private fields, internal helper functions, compiler host internals, plugin loading internals, or dependency versions.
- This specification does not require compatibility with every TypeScript release outside the supported peer range declared by package metadata.
- This specification does not define source maps, incremental watch-mode rebuild timing, filesystem cleanup policy, or renderer snapshot formatting.
- This specification does not require non-public comment lexer entry points; comment behavior is specified through converted comments and public model objects.
- This specification does not define third-party plugin behavior beyond public hooks and extension points that interact with the reflection graph.

## Representative Workflows

### Convert A Project And Write JSON

```ts
import { Application } from "typedoc";

const app = await Application.bootstrap({
  entryPoints: ["src/index.ts"],
  json: "docs/api.json",
  pretty: true,
});

const project = await app.convert();
if (project) {
  await app.generateJson(project, "docs/api.json");
}
```

The application reads options, resolves entry points, converts exported declarations into a `ProjectReflection`, validates the project according to configured validation settings, and writes a JSON object whose schema version and reflection identifiers are suitable for later revival.

### Inspect A Revived Browser Model

```ts
import {
  ConsoleLogger,
  Deserializer,
  FileRegistry,
  ReflectionKind,
  setTranslations,
} from "typedoc/browser";
import translations from "typedoc/browser/en";

setTranslations(translations);

const deserializer = new Deserializer(new ConsoleLogger());
const project = deserializer.reviveProject("API Docs", projectJson, {
  projectRoot: "/",
  registry: new FileRegistry(),
});

const classes = project.getReflectionsByKind(ReflectionKind.Class);
const member = project.getChildByName(["Widget", "render"]);
```

The browser entry point exposes the model and serializer utilities needed to revive JSON without Node-only conversion. Revived reflections support the same traversal, lookup, kind, comment, type-string, and source-file registry behavior as converted reflections.

### Resolve Comment Links And Groups

```ts
/**
 * Primary widget API.
 *
 * {@link Widget.render | render a widget}
 * @group Components
 * @category UI
 */
export class Widget {
  /** Render the current instance. */
  render(): string;
}
```

During conversion, comment tags are parsed into display parts and block tags. Link tags resolve to target reflections or external URLs, and grouping/category tags project into reflection metadata used by model inspection, JSON output, and routed documentation pages.

## Application Conversion And Outputs

Application conversion creates the root project model and emits the same model through API and CLI outputs.

**Bootstrapping and options.** `Application.bootstrap` must create an application without loading plugins, and `Application.bootstrapWithPlugins` must create an application after loading configured plugins. Both methods must accept an options object and an optional ordered list of option readers. When option readers are supplied, the application must read them before freezing effective options. When an option value is invalid, `setOptions` must return `false` and log an error; valid values must update the option store and return `true`.

**Entry point discovery.** When `entryPoints` is set, `getEntryPoints` must resolve the configured entry points using the selected `entryPointStrategy`. When `entryPoints` is absent, `getEntryPoints` must infer package entry points from package metadata and compiler options. `getDefinedEntryPoints` must return `undefined` if configured entry points cannot be expanded. Non-flag CLI arguments must be treated as entry points.

**Conversion.** `convert` must return a `ProjectReflection` on successful conversion and `undefined` when fatal option, entry-point, or TypeScript diagnostic errors prevent a project. When `entryPointStrategy` is `merge`, conversion must revive and merge JSON project inputs. When `entryPointStrategy` is `packages`, conversion must convert each configured package directory independently and merge the resulting projects. When `skipErrorChecking` is false, TypeScript pre-emit diagnostics must prevent conversion.

**Output generation.** `generateJson` must write a JSON reflection file for the provided project. `generateDocs` must render HTML documentation for the provided project. `generateOutputs` must write every output selected through options. Each output generation method must emit begin and end generation events around the write operation.

**CLI projection.** The `typedoc` command must read command-line options and configuration files, treat positional arguments as entry points, and apply command-line options with higher precedence than configuration files. `--json` must write a JSON model, `--out` or `--html` must write HTML documentation, and `--emit none` must convert and validate without documentation output. `--help` must display available options, and `--version` must display the package version.

## Reflection Graph And Model Lookup

The model layer represents converted source declarations as a typed tree with stable public traversal methods.

**Reflection identity and kinds.** Every `Reflection` must expose `id`, `name`, `kind`, `variant`, `flags`, optional `parent`, a `project` reference, and optional `comment`. `kindOf` must return whether a reflection belongs to the supplied `ReflectionKind` bit mask. `getFullName` must join parent names until the project root, and `getFriendlyFullName` must omit signature names where that omission avoids duplicate signature labels.

**Tree traversal.** `ContainerReflection` must expose `children`, `documents`, `childrenIncludingDocuments`, `groups`, and `categories`. `addChild` must place declaration children, document children, and signatures into their corresponding public arrays. `removeChild` must remove the child from every public child projection that contains it. `traverse` must visit child declarations and documents in stored order and must stop when the callback returns `false`.

**Declaration members.** `DeclarationReflection` must represent modules, namespaces, classes, interfaces, functions, variables, properties, accessors, and type aliases through `kind`. It must expose `type`, `typeParameters`, `signatures`, `indexSignatures`, `getSignature`, `setSignature`, `defaultValue`, `overwrites`, `inheritedFrom`, `implementationOf`, `extendedTypes`, `extendedBy`, `implementedTypes`, `implementedBy`, `typeHierarchy`, `readme`, and `packageVersion` where those facts exist. `getAllSignatures` must return call, index, get, and set signatures. `getNonIndexSignatures` must return call, set, and get signatures without index signatures. `getProperties` must return direct children when present and reflected type-literal children otherwise.

**Project indexes.** `ProjectReflection` must expose the project `reflections` registry, optional `packageName`, optional `packageVersion`, optional `readme`, and a `files` registry. `getReflectionById` must return the registered reflection for an identifier or `undefined`. `getReflectionsByKind` must return every registered reflection whose kind matches the supplied `ReflectionKind`. `registerReflection` must add a reflection to the registry, parent-child index, optional symbol index, and optional file registry. `removeReflection` must remove the reflection, nested children, and reference reflections that point to it.

**Reference reflections.** `ReferenceReflection` must represent a declaration that forwards to another reflection. `tryGetTargetReflection` must return the immediate target or `undefined`. `tryGetTargetReflectionDeep` must follow nested reference reflections until a non-reference target or unresolved reference is reached. `getTargetReflection` and `getTargetReflectionDeep` must raise `Error` when the target is unresolved. `getChildByName` on a reference reflection must delegate lookup to the target reflection.

**Flags and names.** `ReflectionFlags` must expose boolean getters for `isPrivate`, `isProtected`, `isPublic`, `isStatic`, `isExternal`, `isOptional`, `isRest`, `isAbstract`, `isConst`, `isReadonly`, and `isInherited`. Setting `Private`, `Protected`, or `Public` must clear the other visibility flags. `getFlagStrings` must return translated labels for visible flags in the stable order private, protected, static, optional, abstract, const, and readonly.

## Comment Tags And Declaration Links

Comment conversion turns source comments into model parts that preserve visible text, tags, and resolved links.

**Display parts and block tags.** `CommentDisplayPart` must distinguish text, fenced code, inline tags, and relative links. `Comment.combineDisplayParts` must concatenate text and code directly, render inline tags in tag form, and include the original relative-link text. `Comment.cloneDisplayParts` must return a new array of shallow-copied display parts. `CommentTag` must expose `tag`, optional `name`, optional `typeAnnotation`, `content`, and `skipRendering`; `similarTo` must compare tag name, identifier, and combined content while ignoring `skipRendering`.

**Comment summaries.** A `Comment` must expose `summary`, `blockTags`, `modifierTags`, optional `label`, and optional `sourcePath`. `getShortSummary` must return `@summary` content when that tag exists; otherwise it must return an empty list when first-paragraph extraction is disabled and the first paragraph of `summary` when enabled. `splitPartsToHeaderAndBody` must return a trimmed first-line header plus the remaining body and must not split inside a code display part.

**Comment tags.** `hasModifier`, `removeModifier`, `getTag`, `getTags`, `getIdentifiedTag`, and `removeTags` must operate on public modifier and block-tag collections. `@default`, `@defaultValue`, `@example`, `@see`, `@group`, `@category`, `@label`, `@overload`, `@readonly`, `@hideconstructor`, `@document`, `@sortStrategy`, `@reexport`, `@inline`, `@inlineType`, `@preventInline`, and `@useDeclaredType` must affect the converted model according to the tag's documented purpose. Comments containing `@license` or `@import` must be ignored for documentation content.

**Inline links.** `{@link}`, `{@linkplain}`, and `{@linkcode}` must parse their target text and optional link text. When TypeScript link resolution is enabled and succeeds, the inline tag target must refer to the resolved reflection. When TypeScript link resolution is disabled or fails, declaration-reference resolution must be used. Unresolved links must remain as inline tag display parts and must produce validation warnings when invalid-link validation is enabled.

**Declaration references.** Declaration references must parse an optional module source before `!`, a component path separated by `.`, `#`, or `~`, and an optional meaning suffix. `.` must prefer exports and static members before instance members, `#` must target instance members, and `~` must target module or namespace exports. A leading `!` with no module source must start resolution at the project root. Meaning suffixes must support documented keywords, overload indexes, and `@label` identifiers.

**Inheritance and visibility.** `@inheritDoc` must copy summary and relevant block-tag content from the resolved target and must detect recursive inheritance without unbounded recursion. Visibility controls from TypeScript modifiers, `excludePrivate`, `excludeProtected`, `excludeInternal`, `@hidden`, and `@hideconstructor` must remove or mark affected reflections consistently across children, signatures, JSON, and rendered output.

## Type Models And Serialization

Type objects expose a public string form, visitor contract, JSON schema projection, and revival behavior.

**Type stringification.** Every `Type` subclass must expose a `type` discriminator, `toString`, `stringify`, `visit`, `toObject`, `fromObject`, `needsParenthesis`, and `estimatePrintWidth`. `toString` must delegate to `stringify` with no context. Parentheses must be inserted when the current `TypeContext` requires them for correct TypeScript expression grouping.

**Type variants.** The model must include `ArrayType`, `ConditionalType`, `IndexedAccessType`, `InferredType`, `IntersectionType`, `IntrinsicType`, `LiteralType`, `MappedType`, `OptionalType`, `PredicateType`, `QueryType`, `ReferenceType`, `ReflectionType`, `RestType`, `TemplateLiteralType`, `TupleType`, `NamedTupleMember`, `TypeOperatorType`, `UnionType`, and `UnknownType`. Each variant must preserve its documented public fields in `toObject` and restore them in `fromObject`.

**Reference types.** `ReferenceType.createResolvedReference` must create a reference to a reflection or reflection identifier. `ReferenceType.createUnresolvedReference` must create a symbol-id based reference associated with a project. `ReferenceType.createBrokenReference` must create an intentionally unresolved reference for type parameters or removed symbols. The `reflection` getter must resolve symbol identifiers through the project, preferring value or type targets according to `preferValues`. `isIntentionallyBroken` must return true for `-1`, type-parameter references, or references to symbols removed from the project.

**Visitors.** `makeRecursiveVisitor` must create a complete `TypeVisitor` that invokes supplied visitor callbacks and recursively visits nested types for arrays, conditionals, indexed access, inferred constraints, intersections, mapped types, optionals, predicates, queries, references, rest types, template literals, tuples, type operators, and unions.

**Serialization.** `Serializer` must convert models to JSON objects, run registered serializer components in priority order, omit empty optional arrays, and expose begin/end events for `projectToObject`. `projectToObject` must set `projectRoot` and `project` during serialization and clear them afterward. `ProjectReflection.toObject` must include `schemaVersion`, project identity, package metadata, readme display parts, symbol-id map, and file registry data.

**Deserialization.** `Deserializer` must revive project JSON whose `schemaVersion` is supported, assign new reflection identifiers, preserve the old-to-new id map during revival, restore file ids, rebuild reference targets through deferred work, and clear temporary state afterward. `reviveProjects` must return a single revived project when one input is supplied and entry-point module creation is not forced; otherwise it must create module reflections for each input project. Unsupported schema versions must raise `Error`.

**Browser entry point.** `typedoc/browser` must export model classes, `Serializer`, `Deserializer`, `JSONOutput`, `ConsoleLogger`, `Logger`, `LogLevel`, `FileRegistry`, translation helpers, and declaration-reference utility types without requiring Node-only conversion APIs. `setTranslations` must replace active translations, and `addTranslations` must merge additional translations into the active table.

## Organization, Documents, And File References

Converted projects carry organization metadata and document/file references that must survive across API, JSON, and browser views.

**Groups and categories.** `@group` and `@category` tags must place reflections into named `ReflectionGroup` and `ReflectionCategory` collections. Group and category ordering must follow configured sort rules and explicit `@sortStrategy` values. Excluded categories must be omitted from the converted project. When a comment is inherited without redefining group or category tags, inherited group and category metadata must apply to the derived reflection.

**Documents.** Markdown documents supplied by `projectDocuments` or `@document` tags must become `DocumentReflection` entries associated with the project or parent reflection. Document reflections must appear in `documents` and `childrenIncludingDocuments`, and their ordering must be preserved for routing and serialization. Document comments must support inline links, relative links, include directives, and regular comment display parts.

**Source and file registry.** `SourceReference` must record source `fileName`, optional `line`, optional `character`, and optional `url`. `FileRegistry.registerAbsolute` must return a stable file id and optional anchor for an absolute path, reusing the same id for repeated paths. `registerReflection` must associate a path with a reflection, `registerReflectionPath` must add an alternate path for that reflection, and `resolve` must return either the registered reflection or path for a file id.

**Relative assets.** Relative links in comments and documents must register through `FileRegistry`, preserve original text, and resolve to either a copied media path, a target reflection, or `undefined` when the target does not exist. `getName` must choose a unique output filename for registered media paths by appending a numeric suffix when basenames collide.

**Filtering exported declarations.** `exclude`, `excludeExternals`, `excludeNotDocumented`, `excludeNotDocumentedKinds`, `excludeInternal`, `excludePrivate`, `excludePrivateClassFields`, `excludeProtected`, `excludeReferences`, and `excludeCategories` must control which reflections appear in the converted project. Filtering must update parent-child arrays, project indexes, symbol indexes, groups, categories, JSON output, and reference graph consistently.

## State Model

The core state is a converted TypeScript project represented by one `ProjectReflection`. The project owns a registry of reflection ids, symbol-to-reflection mappings, a file registry, package metadata, readme content, and the root children/documents that define the public tree.

The public projections are:

1. The Node API projection through `Application`, `Converter`, model classes, serializer/deserializer classes, and option-driven output methods.
2. The CLI projection through the `typedoc` command, entry-point arguments, configuration files, output flags, validation flags, and exit status.
3. The reflection-tree projection through `ProjectReflection`, `DeclarationReflection`, `SignatureReflection`, `ParameterReflection`, `TypeParameterReflection`, `ReferenceReflection`, `DocumentReflection`, and traversal methods.
4. The comment projection through `Comment`, `CommentTag`, display parts, declaration-reference targets, relative links, group tags, category tags, and modifier tags.
5. The type projection through `Type` subclasses, type stringification, visitors, and reference resolution.
6. The JSON projection through `JSONOutput`, `Serializer.projectToObject`, `Application.generateJson`, and `Deserializer.reviveProject`.
7. The browser projection through `typedoc/browser`, revived model objects, translation helpers, and file registry lookups.

## Error Semantics

| Condition | Required result |
|---|---|
| Application construction is attempted directly | The constructor must raise `Error`; callers must use `Application.bootstrap` or `Application.bootstrapWithPlugins`. |
| An option supplied to `setOptions` is invalid | `setOptions` must return `false` and log an error when reporting is enabled. |
| Entry points cannot be resolved | `getDefinedEntryPoints` or `getEntryPoints` must return `undefined`, and `convert` must return `undefined`. |
| TypeScript diagnostics exist while `skipErrorChecking` is false | `convert` must log diagnostics and return `undefined`. |
| `entryPointStrategy` is `packages` with no configured entry points | `convert` must log an error and return `undefined`. |
| Watch conversion is requested with unsupported entry-point strategy | `convertAndWatch` must log an error and return `false`. |
| A reference reflection target is unresolved | `getTargetReflection` and `getTargetReflectionDeep` must raise `Error`. |
| A JSON project has an unsupported schema version | `Deserializer.reviveProject` and `Deserializer.reviveProjects` must raise `Error`. |
| Deserializer deferred work is requested outside an active revival | The deserializer must raise an assertion error. |
| A declaration-reference string is malformed | Parsing must fail without producing a partial successful reference. |
| Invalid links are present and invalid-link validation is enabled | Validation must report warnings without removing the original comment text. |
| A file registry id is unknown | `resolve`, `resolvePath`, and `getName` must return `undefined`. |

## Cross-View Invariants

1. A project returned by `Application.convert` and then written by `generateJson` must revive through `Deserializer.reviveProject` into a `ProjectReflection` with the same names, kinds, comments, type discriminators, and child relationships.
2. Every reflection reachable through `ProjectReflection.reflections` must be reachable by `getReflectionById`, and every child reflection must retain a parent chain ending at the same project.
3. Removing a reflection from a project must remove its nested children and reference reflections from project lookup, parent child arrays, symbol lookup, and file registry projections.
4. A `ReferenceReflection` that resolves through a chain must expose the same child lookup result as its final target reflection.
5. A comment inline link resolved during conversion must serialize to JSON and revive to the corresponding new reflection id or external URL.
6. A `ReferenceType` that resolves to a reflection before serialization must revive as a reference type whose `reflection` getter returns the corresponding revived reflection.
7. A file path registered for a reflection must serialize relative to the project root and revive to a path that resolves to the revived reflection.
8. Group and category metadata derived from comments must be visible through model collections, JSON output, and revived browser models for the same reflections.
9. Filtering options that exclude a declaration must remove that declaration from API traversal, JSON output, browser revival, and rendered routing inputs.
10. CLI `--json` output and `Application.generateJson` output for the same converted project must expose the same schema version, project metadata, reflection variants, comment parts, and type objects.
11. Type stringification before serialization and after revival must return the same text for supported type variants when their referenced targets still exist.
12. `typedoc/browser` revived models must support the same public lookup and traversal methods used by Node-side model inspection.

## Public Interface

### Import Surface

The package is installed as `typedoc` and exposes these public module entry points:

```ts
import {
  Application,
  Converter,
  Context,
  Deserializer,
  Serializer,
  JSONOutput,
  SerializeEvent,
  Models,
  ReflectionKind,
  ReflectionFlag,
  ReflectionFlags,
  TraverseProperty,
  ProjectReflection,
  Reflection,
  ContainerReflection,
  DeclarationReflection,
  SignatureReflection,
  ParameterReflection,
  TypeParameterReflection,
  ReferenceReflection,
  DocumentReflection,
  Comment,
  CommentTag,
  FileRegistry,
  ReflectionCategory,
  ReflectionGroup,
  ReflectionSymbolId,
  SourceReference,
  Type,
  ArrayType,
  ConditionalType,
  IndexedAccessType,
  InferredType,
  IntersectionType,
  IntrinsicType,
  LiteralType,
  MappedType,
  OptionalType,
  PredicateType,
  QueryType,
  ReferenceType,
  ReflectionType,
  RestType,
  TemplateLiteralType,
  TupleType,
  NamedTupleMember,
  TypeOperatorType,
  UnionType,
  UnknownType,
  TypeContext,
  makeRecursiveVisitor,
  EntryPointStrategy,
  Option,
  OptionDefaults,
  Options,
  ParameterType,
  ParameterHint,
  ArgumentsReader,
  TypeDocReader,
  TSConfigReader,
  PackageJsonReader,
  ConsoleLogger,
  Logger,
  LogLevel,
  EventDispatcher,
  EventHooks,
  MinimalSourceFile,
  i18n,
  translateTagName,
  normalizePath,
  ValidatingFileRegistry,
  TypeScript,
} from "typedoc";

import {
  Deserializer as BrowserDeserializer,
  Serializer as BrowserSerializer,
  JSONOutput as BrowserJSONOutput,
  ConsoleLogger as BrowserConsoleLogger,
  FileRegistry as BrowserFileRegistry,
  ReflectionKind as BrowserReflectionKind,
  setTranslations,
  addTranslations,
  translateTagName as browserTranslateTagName,
} from "typedoc/browser";

import translations from "typedoc/browser/en";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Application | class | Root Node API for option reading, conversion, validation, serialization, and output generation. |
| Converter | class | Component that converts TypeScript entry points into a project reflection. |
| Context | class | Conversion context exposed to converter extensions and event handlers. |
| ProjectReflection | class | Root reflection containing project metadata, reflection registry, symbol lookup, and file registry. |
| Reflection | class | Base model for named documented items with kind, flags, comments, traversal, and JSON behavior. |
| ContainerReflection | class | Reflection that owns child declarations, documents, groups, and categories. |
| DeclarationReflection | class | Reflection for modules, classes, interfaces, functions, variables, properties, accessors, and type aliases. |
| SignatureReflection | class | Reflection for call, constructor, index, get, and set signatures. |
| ParameterReflection | class | Reflection for function, method, constructor, and signature parameters. |
| TypeParameterReflection | class | Reflection for generic type parameters and variance metadata. |
| ReferenceReflection | class | Forwarding reflection used for re-exports and imported references. |
| DocumentReflection | class | Reflection for Markdown documents associated with a project or declaration. |
| ReflectionKind | enum | Bit-mask vocabulary for reflection kinds and kind-group tests. |
| ReflectionFlag | enum | Bit-mask vocabulary for visibility and modifier flags. |
| ReflectionFlags | class | Mutable public flag wrapper with boolean getters and serialized flag projection. |
| TraverseProperty | enum | Vocabulary describing which child collection traversal is visiting. |
| ReflectionGroup | class | Group metadata for organized child reflection lists. |
| ReflectionCategory | class | Category metadata for organized child reflection lists. |
| ReflectionSymbolId | class | Stable symbol identifier used to reconnect references across conversion and JSON. |
| SourceReference | class | Source-file, line, character, and URL metadata for a reflection. |
| FileRegistry | class | Registry for source files, media files, reflection paths, relative links, and revived file ids. |
| Comment | class | Parsed comment model with summary, block tags, modifier tags, display parts, and JSON behavior. |
| CommentTag | class | Parsed block tag model with tag name, identifier, type annotation, and display parts. |
| Type | class | Base class for public type model variants. |
| ArrayType | class | Type model for array syntax. |
| ConditionalType | class | Type model for conditional types. |
| IndexedAccessType | class | Type model for indexed access syntax. |
| InferredType | class | Type model for inferred type variables. |
| IntersectionType | class | Type model for intersection types. |
| IntrinsicType | class | Type model for intrinsic names such as string or number. |
| LiteralType | class | Type model for literal values. |
| MappedType | class | Type model for mapped type syntax. |
| OptionalType | class | Type model for optional tuple or element syntax. |
| PredicateType | class | Type model for predicate return types. |
| QueryType | class | Type model for `typeof` query syntax. |
| ReferenceType | class | Type model for references to reflected or external symbols. |
| ReflectionType | class | Type model for object and function type literals represented by nested reflections. |
| RestType | class | Type model for rest tuple elements. |
| TemplateLiteralType | class | Type model for template literal types. |
| TupleType | class | Type model for tuple types. |
| NamedTupleMember | class | Type model for named tuple members. |
| TypeOperatorType | class | Type model for operators such as `keyof`, `readonly`, and `unique`. |
| UnionType | class | Type model for union types. |
| UnknownType | class | Type model for unrecognized type text. |
| TypeContext | constant | String-valued contexts used by type stringification. |
| makeRecursiveVisitor | function | Creates a visitor that walks nested type objects. |
| Serializer | class | Converts model objects and projects into JSON output. |
| Deserializer | class | Revives JSON output into model objects. |
| JSONOutput | namespace | Public JSON schema type namespace and schema version. |
| SerializeEvent | class | Event payload for serializer begin and end events. |
| EntryPointStrategy | enum | Supported strategies for resolving entry points. |
| Option | function | Decorator helper for option-backed component properties. |
| Options | class | Runtime option container. |
| OptionDefaults | constant | Default option values. |
| ParameterType | enum | Option declaration value-type vocabulary. |
| ParameterHint | enum | Option help hint vocabulary. |
| ArgumentsReader | class | Option reader for command-line arguments. |
| TypeDocReader | class | Option reader for package configuration files. |
| TSConfigReader | class | Option reader for TypeScript configuration. |
| PackageJsonReader | class | Option reader for package metadata. |
| ConsoleLogger | class | Logger implementation that writes to console channels. |
| Logger | class | Base logger with levels and diagnostics methods. |
| LogLevel | enum | Logging threshold vocabulary. |
| EventDispatcher | class | Typed event emitter used by application, serializer, and components. |
| EventHooks | class | Priority-ordered hook collection. |
| MinimalSourceFile | class | Minimal source-file shape used by utilities and browser-safe models. |
| i18n | constant | Translation proxy for active locale strings. |
| setTranslations | function | Browser entry helper that replaces active translations. |
| addTranslations | function | Browser entry helper that merges active translations. |
| translateTagName | function | Returns the display label for a documentation tag. |
| normalizePath | function | Returns normalized path strings for the public path vocabulary. |
| ValidatingFileRegistry | class | File registry variant that validates registered paths against a base path. |
| TypeScript | namespace | Re-export of the TypeScript module used by the package. |
| Models | namespace | Namespace containing the public reflection, comment, type, and file model classes. |

### CLI Entry Points

Console script: `typedoc`

| Exit | Meaning |
|---:|---|
| 0 | Requested conversion, validation, and output generation completed successfully, or informational output such as help/version completed. |
| 1 | Conversion, validation, option reading, or output generation failed. |

The command accepts positional entry points and documented options. Important public options in this specification are `entryPoints`, `entryPointStrategy`, `alwaysCreateEntryPointModule`, `projectDocuments`, `exclude`, `externalPattern`, `excludeExternals`, `excludeNotDocumented`, `excludeNotDocumentedKinds`, `excludeInternal`, `excludePrivate`, `excludePrivateClassFields`, `excludeProtected`, `excludeReferences`, `excludeCategories`, `maxTypeConversionDepth`, `outputs`, `out`, `html`, `json`, `pretty`, `emit`, `theme`, `router`, `highlightLanguages`, `ignoredHighlightLanguages`, `typePrintWidth`, `validation`, `useTsLinkResolution`, and `skipErrorChecking`.

## Appendix A: Environment

The working environment runs Node.js 20 on Linux without network access during assessment. TypeScript, Mocha, tsx, markdown-it, minimatch, yaml, lunr, and @gerrit0/mini-shiki are preinstalled and importable. The assessment environment provides the same runtime and package set.

The project must declare its packaging metadata in a standard `package.json` at the project root so the package is installable with the package manager available in the environment. The package must expose ESM entry points compatible with `import` from `typedoc` and `typedoc/browser`.

## Appendix B: Assessment Notes

Assessment covers public behavior through TypeScript projects created in temporary local directories, Node API conversion, CLI JSON output, direct model-object operations, declaration-reference parsing and resolution, comment tag behavior, serializer/deserializer round trips, browser-entry revival, and cross-view consistency. Exact HTML snapshots, private helper modules, renderer styling, and non-public lexer internals are not assessed.
