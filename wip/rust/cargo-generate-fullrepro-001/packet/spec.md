# `cargo-generate` Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cargo-generate` is a Rust project generator that expands a local directory or git repository template into a new project directory. It renders Liquid placeholders in file contents and path names, applies template configuration from `cargo-generate.toml`, accepts user-supplied values from CLI arguments, environment variables, and config files, and exposes the resulting state through a `cargo generate` CLI command plus a small Rust library API.

The generator treats a template as a working tree plus optional configuration. The public result is the generated directory path, its rendered files, skipped or ignored files, generated Cargo metadata, optional git repository initialization, and optional Cargo workspace membership updates.

## Non-Goals

- This specification does not require live network access, GitHub availability, remote SSH authentication, ssh-agent behavior, or private key prompting.
- This specification does not require exact terminal wording, emojis, colors, progress bars, warning text, or error message text.
- This specification does not require private helper modules, private source-unit APIs, internal cache layout, or internal git command construction details.
- This specification does not define support for symbolic-link copying beyond reporting or skipping them without corrupting generated regular files.
- This specification does not require compatibility with undocumented template keys, undocumented Rhai extension modules, or Cargo features not listed in Appendix A.

## Representative Workflows

Generate a project from a local template directory:

```rust
use cargo_generate::{generate, GenerateArgs, TemplatePath, Vcs};

let args = GenerateArgs {
    name: Some("demo-app".to_string()),
    vcs: Some(Vcs::None),
    template_path: TemplatePath {
        path: Some("/templates/basic".to_string()),
        ..TemplatePath::default()
    },
    ..GenerateArgs::default()
};

let generated = generate(args)?;
```

When the template contains `Cargo.toml.liquid`, `README.md`, and `{{project-name}}.rs`, the call must create a `demo-app` output directory, render Liquid placeholders in included files and path names, remove the `.liquid` suffix in the copied output, and return the path to the generated directory. If the destination already contains a conflicting rendered `.liquid` target and overwrite is disabled, then generation must raise an error.

List and use favorite templates from a config file:

```rust
use cargo_generate::{generate, GenerateArgs, TemplatePath};

let args = GenerateArgs {
    config: Some("/tmp/cargo-generate.toml".into()),
    name: Some("chosen".to_string()),
    template_path: TemplatePath {
        auto_path: Some("demo".to_string()),
        ..TemplatePath::default()
    },
    ..GenerateArgs::default()
};

let generated = generate(args)?;
```

When the selected config contains a `[favorites.demo]` table with a local `path` or local git source, generation must resolve `demo` through that favorite, merge global and favorite values, and then apply CLI-supplied options over favorite options where the same public option exists. If `demo` is not defined as a favorite, then the input must be classified as a template source instead of silently succeeding with an empty favorite.

Run a template's hooks during expansion:

```sh
cargo generate --path ./template --name hook-demo --allow-commands
```

When `cargo-generate.toml` declares `init`, `pre`, or `post` hook script files, the command must run those Rhai scripts at the documented hook phase, expose template variables through the Rhai `variable` module, expose safe template-folder file operations through the Rhai `file` module, and allow `system::command` only when command execution has been authorized.

## Template Source Selection

Template source selection defines where the template tree comes from before rendering, including direct path inputs, git inputs, favorites, and subfolder selection.

**CLI And Library Entry.** The `Cli` enum must parse the `cargo generate` subcommand and its visible alias `cargo gen` into a `GenerateArgs` value. The `generate` function must accept a `GenerateArgs` value and return the final generated `PathBuf` when generation succeeds. If argument combinations violate the CLI contract, then the CLI parser must reject the invocation and return a usage failure before generation starts.

**Template Paths.** The `TemplatePath` value must carry the mutually exclusive source forms `git`, `path`, `favorite`, `auto_path`, and the optional source `subfolder`. When the `--path` option is present, the generator must copy a local directory template and must reject simultaneous `--git`. When the `--git` option is present, the generator must treat even a local path as a git source so branch, tag, revision, identity, gitconfig, and submodule options apply to the clone path. When no explicit source option is present, `auto_path` must classify input in this order: configured favorite, host-prefixed shorthand, full URL or scp-style URL, absolute path, existing local relative directory, unprefixed `owner/repo` shorthand, and finally a raw git URL string.

**Git Source Forms.** When a template input starts with `gh:`, `gl:`, `bb:`, or `sr:`, the generator must expand it respectively to the GitHub, GitLab, Bitbucket, or SourceHut HTTPS URL form documented for the prefix. When an unprefixed `owner/repo` input has exactly one slash and both parts contain only ASCII letters, digits, underscore, dash, or dot, the generator must expand it as a GitHub repository unless an existing local directory with that relative path exists. When the input is a full URL or scp-style `user@host:path`, the generator must use it as a git source without applying host shorthand expansion. If cloning a git source fails, then generation must raise an error and must not create a completed output project.

**Subfolders And Template Config Location.** When the selected repository or path contains several sub-templates, the generator must support selecting a specific relative template folder. Where a subfolder is selected, the generator must search for `cargo-generate.toml` in the selected folder and then upward toward the template root. If no required template folder exists or no selected sub-template is valid, then generation must raise an error before copying output files.

## Project Naming, Values, And Config

Project naming and template values determine the Liquid and Rhai variable object used by content rendering, path rendering, conditionals, and hooks.

**Project Name And Crate Type.** The generator must obtain `project-name` from the `name` field, from interactive input, from `CARGO_GENERATE_VALUE_PROJECT_NAME` in silent operation, or from an init hook that sets it before prompting. When force is disabled, `project-name` must be converted to kebab case for the output directory and `crate_name` must be the snake case form. When force is enabled, the output directory name must preserve the supplied `project-name` text while `crate_name` remains the Rust crate-safe variable. The `lib` and `bin` flags must populate `crate_type` with `"lib"` or `"bin"` and must reject simultaneous use. Where a library caller uses `GenerateArgs::default`, `crate_type` must default to `"lib"` unless `bin` is selected; where the CLI is invoked without either crate-type flag, `crate_type` must default to `"bin"`.

**Builtin Placeholders.** The template object must include `authors`, `project-name`, `crate_name`, `crate_type`, `os-arch`, `username`, `within_cargo_project`, and `is_init`. `within_cargo_project` must be true when the generation destination has a `Cargo.toml` in the current directory or a parent directory. `is_init` must reflect the effective init mode after CLI and template config have been merged. If a required builtin cannot be computed from the environment and no replacement value exists, then generation must raise an error.

**Template Defined Placeholders.** Where `cargo-generate.toml` contains a `[placeholders]` table, each placeholder definition must accept `prompt`, optional `choices`, optional `default`, optional string regex validation, and a `type` of `"string"`, `"text"`, `"editor"`, `"bool"`, or `"array"`. When a value is missing and silent mode is disabled, the generator must prompt for it using the placeholder definition. When a value is missing, silent mode is enabled, and the placeholder has a default value, the generator must use the default value instead of prompting. When a value is missing, silent mode is enabled, and the placeholder has no default value, the generator must raise an error instead of prompting. If a placeholder definition uses the reserved names `project-name`, `crate_name`, `crate_type`, `authors`, `os-arch`, `within_cargo_project`, or `is_init`, then generation must raise an error. If a supplied value violates its choices, regex, or declared type, then generation must raise an error.

**Value Precedence.** Template values must be merged in increasing priority from global config `[values]`, selected favorite `[favorites.<name>.values]`, environment file values from `CARGO_GENERATE_TEMPLATE_VALUES_FILE`, `CARGO_GENERATE_VALUE_<KEY>` environment variables, the `template_values_file` argument, and the `define` argument. The `define` argument must accept `key=value` strings whose keys start with an ASCII letter and then contain ASCII letters, digits, dash, or underscore. If a `define` entry has an invalid key or missing assignment syntax, then generation must raise an error.

**Application Config And Favorites.** `app_config_path` must return an explicit config path when one is supplied, otherwise it must use `$CARGO_HOME/cargo-generate.toml` when present, then `$CARGO_HOME/cargo-generate` when present, and otherwise the preferred `$CARGO_HOME/cargo-generate.toml` path. `AppConfig` must deserialize defaults, favorites, and values from TOML, and `get_favorite_cfg` must return the favorite table matching a name. `list_favorites` must load the selected config, filter favorite names by the optional `auto_path` prefix, sort matching names lexicographically, and return success for both empty and non-empty favorite lists.

## Rendering, File Selection, And Template Configuration

Rendering converts the prepared template tree into the filesystem contents that appear in the output project.

**Liquid Rendering.** The generator must process Liquid syntax in file contents selected for rendering and in file or directory names. It must support standard Liquid tags and filters plus the documented filters `rhai`, `kebab_case`, `lower_camel_case`, `pascal_case`, `shouty_kebab_case`, `shouty_snake_case`, `snake_case`, `title_case`, and `upper_camel_case`. When a rendered path contains characters invalid for file or directory names, the generator must sanitize those characters before creating the output path. If Liquid parsing or rendering fails for selected content and continue-on-error is disabled, then generation must raise an error; if continue-on-error is enabled, then generation must continue while preserving enough failure information for the command result.

**Include And Exclude.** Where `[template].include` is present, only paths matching the include list must be processed for Liquid content rendering. Where include is absent and `[template].exclude` is present, paths matching the exclude list must be copied without Liquid content rendering. Where both include and exclude are present, include must take precedence. Include and exclude patterns must match the pre-rename template path when placeholders occur in file names. Excluded files must still be copied unless they are ignored. If include or exclude contains an invalid glob pattern, then generation must raise an error.

**Ignored Files.** Where `[template].ignore` is present, matching files or directories must be removed from the generated template before final copy and must not appear in the output directory. Ignore entries must support literal files and folders and must not require wildcard matching. Ignore matching must be evaluated after `.liquid` suffix removal, so an ignore entry for `file.txt` must remove a template file named `file.txt.liquid` from the output. The `.genignore` file must be treated as deprecated input and must never be copied into the final project.

**Copy Semantics.** During final copy, `.git` directories from the template source must not be copied. A template file ending in `.liquid` must be copied without that suffix. When both `name` and `name.liquid` exist in the same source folder, the `.liquid` file must take precedence over the non-liquid file for the output path. If the final output path already exists and overwrite is disabled, then rendered `.liquid` output conflicts must raise an error and non-liquid file conflicts must be skipped without replacing the existing file. When overwrite is enabled, conflicting output files must be replaced.

**Version And Template Options.** Where `[template].cargo_generate_version` is present, the running implementation must satisfy that version requirement before expansion continues. Where `[template].init` is true, effective generation must behave as if init mode were requested. Where `[template].vcs` is present, it must set the effective VCS for generation even when the caller supplies a VCS option. If the version requirement is not satisfied or a template option has an invalid type, then generation must raise an error.

## Conditionals And Hooks

Conditionals and hooks let a template alter rendering decisions before the output is copied.

**Conditional Tables.** Where `cargo-generate.toml` contains `[conditional.'<expr>']` tables, the condition string must be evaluated as a Rhai expression against the values resolved before conditional processing. For each true condition, the table's `include`, `exclude`, `ignore`, and `placeholders` entries must contribute to the effective template configuration. Placeholder arrays must be exposed as Rhai arrays for conditional expressions. If a condition expression fails to evaluate to a valid boolean result, then generation must raise an error.

**Conditional Placeholder Timing.** The generator must resolve placeholders declared in the non-conditional `[placeholders]` table before evaluating conditional sections. Placeholders declared inside a true conditional section must become available for later template rendering and hooks, but they must not affect whether further conditional sections are enabled. If include and exclude become present through different true conditional sections, then include must still take precedence.

**Hook Phases.** Where `[hooks]` declares `init`, `pre`, or `post` script lists, the generator must execute init hooks before prompting for normal placeholder values, pre hooks after configured placeholders have been resolved and before template content rendering, and post hooks after template expansion but before final output is moved into the destination. If any hook returns an error or calls `abort`, then generation must raise an error and must not leave a completed output project in the user's destination.

**Rhai Variable Module.** Hook scripts must access template variables through `variable::is_set`, `variable::get`, and `variable::set`. `variable::set` must set a new value or overwrite an existing value without changing the existing value's type. It must accept complete arrays and must not support assigning an individual array element by indexed name. The `variable::prompt` overloads must collect boolean, string, regex-validated string, and choice values. If prompting is required during silent operation, then the hook operation must raise an error.

**Rhai File, System, And Environment Modules.** Hook scripts must access template-folder files through `file::exists`, `file::rename`, `file::delete`, `file::write`, and `file::listdir`. These file operations must be relative to the template folder and must reject paths outside the template folder. The `system::command` function must execute a command only after interactive approval or when `allow_commands` is true, and silent mode without command authorization must raise an error. `system::date` must return a UTC date object with `year`, `month`, and `day`. `env::working_directory` must expose the temporary template processing directory, and `env::destination_directory` must expose the final destination directory.

## Output Git, Test, And Workspace State

The output state covers where files are placed and what repository or workspace metadata is created around them.

**Destination And Init Mode.** When init mode is false, generation must create or reuse a subdirectory under `destination` named from the effective project name. When init mode is true, generation must write directly into `destination` and must not create a project-name subdirectory. If init mode would overwrite an existing file without overwrite enabled, then generation must raise or skip according to the copy conflict rules and must not silently replace user files.

**Git Initialization.** The `Vcs` enum must accept `Git` and `None`, and parsing must reject any other VCS value. When no caller, favorite, or template configuration selects a VCS, the effective VCS must be `Git`. When effective VCS is `Git`, init mode is false, and the project is not added as a workspace member, the generator must initialize a new git repository in the output project. When effective VCS is `None`, the generator must not initialize a repository. When force-git-init is true, the generator must initialize a fresh git repository even in cases where the normal path would avoid it. If git initialization fails, then generation must raise an error after file generation instead of reporting success.

**Cargo Workspace Membership.** Unless no-workspace is true, the generator must search parent directories for a Cargo workspace and add the generated project as a workspace member when a workspace is found. When the project is added to a workspace, normal fresh git initialization for the generated member must be suppressed unless force-git-init is true. If workspace manifest editing fails, then generation must raise an error.

**Template Test Mode.** When test mode is true, the generator must expand the selected template in a temporary processing directory and run the configured test command there instead of copying the result into the destination. Test mode must enable verbose output. When test mode is true and no template source input is supplied, the generator must use the current directory as the template source. When test mode is true and no project name is supplied, the generator must synthesize a project name before expansion. The default test command must be `cargo test`, and the `CARGO_GENERATE_TEST_CMD` environment variable must replace that command when it is set. CLI arguments following `--test` must be passed to the test command. If the test command exits unsuccessfully, then generation must raise an error.

**Logging Formatter.** The `log_formatter` function must write formatted log records to the supplied formatter and must prefix warning and error records with the public warning or error marker. If writing to the formatter fails, then the function must return the I/O error.

## State Model

The core state is the generation transaction built from a template source tree, application config, selected favorite, user arguments, environment values, resolved template configuration, template variable object, and output destination. The public projections are:

1. CLI parsing and process exit status from `cargo generate` and `cargo gen`.
2. Library return value from `generate`, which is the final output path or an error.
3. Generated filesystem tree, rendered file contents, rendered file and directory names, and omitted files.
4. Effective template variables visible to Liquid rendering, Rhai conditionals, and Rhai hooks.
5. Application config and favorites visible through `AppConfig`, `app_config_path`, and `list_favorites`.
6. Git repository state and Cargo workspace membership around the generated project.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid CLI argument combination or invalid VCS value | Return a usage failure before generation starts |
| Config path cannot be resolved from an explicit path or Cargo home | Raise an `anyhow::Error` |
| Config, template config, values file, placeholder, or conditional TOML is malformed | Raise an `anyhow::Error` |
| Source path is missing, selected subfolder is invalid, or git clone fails | Raise an `anyhow::Error` |
| Template version requirement is not satisfied | Raise an `anyhow::Error` |
| Required project name or placeholder value without a configured default is missing in silent mode | Raise an `anyhow::Error` |
| Placeholder value violates type, choices, or regex validation | Raise an `anyhow::Error` |
| `define` entry has an invalid key or invalid assignment syntax | Raise an `anyhow::Error` |
| Liquid parsing or rendering fails with continue-on-error disabled | Raise an `anyhow::Error` |
| Include or exclude glob is invalid | Raise an `anyhow::Error` |
| A rendered `.liquid` output conflicts with an existing file and overwrite is disabled | Raise an `anyhow::Error` |
| Hook script fails, calls `abort`, escapes the template directory, or requires disallowed command execution | Raise an `anyhow::Error` |
| Git initialization or workspace manifest editing fails | Raise an `anyhow::Error` |
| Test mode command exits unsuccessfully | Raise an `anyhow::Error` |
| Log formatter write fails | Return the underlying `std::io::Error` |

## Cross-View Invariants

1. A project name supplied through CLI arguments, values files, environment values, interactive input, or init hooks must produce consistent `project-name`, `crate_name`, destination path, rendered path names, and rendered file contents.
2. A value selected through config defaults, favorite values, environment values, values files, or `define` must be the same value visible to Liquid templates, Rhai conditionals, Rhai hook `variable::get`, and final generated files.
3. A file ignored through `[template].ignore`, deprecated `.genignore`, or a true conditional ignore entry must be absent from the final filesystem tree and must not be rendered, copied, or committed by git initialization.
4. A file excluded from Liquid processing must still be copied to the final output unless it is ignored, and that copied content must remain unrendered while rendered file and directory names elsewhere still use the template variables.
5. A hook-created, hook-renamed, or hook-deleted file in the template processing directory must affect the same final output tree returned by `generate` and observed after CLI completion.
6. A selected favorite must resolve to the same template source, subfolder, values, init behavior, overwrite behavior, and VCS behavior whether generation is invoked by `auto_path`, by the `favorite` field, or by the CLI favorite syntax.
7. When a generated project is added to a Cargo workspace, the workspace manifest and generated filesystem tree must agree on the relative member path, and normal fresh git initialization must be suppressed unless force-git-init is true.
8. The path returned by `generate` must be the same directory that contains rendered output files, git metadata when initialized, and workspace membership effects when a parent workspace is updated.

## Public Interface

### Import Surface

```rust
use cargo_generate::{
    app_config_path, generate, list_favorites, log_formatter, AppConfig, Cli, GenerateArgs,
    TemplatePath, Vcs,
};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `generate` | function | Expands a selected template using `GenerateArgs` and returns the final output path. |
| `list_favorites` | function | Loads config-defined favorite templates and writes the filtered favorite list through the logging system. |
| `app_config_path` | function | Resolves the application config file path from an explicit path or Cargo home defaults. |
| `log_formatter` | function | Formats log records for the CLI logger. |
| `Cli` | enum | Parses the `cargo generate` command and `cargo gen` alias into generation arguments. |
| `GenerateArgs` | struct | Holds CLI and library options controlling template source, output, config, values, hooks, git, and test behavior. |
| `TemplatePath` | struct | Holds the selected template source form and optional subfolder. |
| `Vcs` | enum | Selects whether generation initializes a git repository or no repository. |
| `AppConfig` | struct | Represents application defaults, favorites, and global template values loaded from TOML config. |

### CLI Entry Points

Console script: `cargo-generate`, installed as a Cargo subcommand invoked as `cargo generate`.

Command aliases:

| Command | Role |
|---|---|
| `cargo generate` | Generate a project from a template source. |
| `cargo gen` | Visible alias for `cargo generate` when the Cargo alias or binary invocation supports it. |

Exit behavior:

| Exit | Meaning |
|---:|---|
| 0 | The requested favorite listing, template generation, or template test operation completed successfully. |
| 1 | Generation started but failed because source acquisition, rendering, hook execution, file copy, git initialization, workspace update, or test execution failed. |
| 2 | CLI parsing or usage validation failed before generation started. |

Important public options:

| Option | Role |
|---|---|
| `--git`, `-g` | Select a git repository source. |
| `--path`, `-p` | Select a local directory source. |
| `--favorite` | Select a named favorite from config. |
| positional template input | Select a favorite, local path, shorthand, URL, or `owner/repo` source through automatic classification. |
| positional subfolder | Select a relative template folder inside the source. |
| `--branch`, `-b` | Select a git branch. |
| `--tag` | Select a git tag. |
| `--revision`, `--rev` | Select a git revision. |
| `--name`, `-n` | Set the project name. |
| `--force`, `-f` | Preserve the supplied project name instead of normalizing it for the output directory. |
| `--destination` | Set the destination directory. |
| `--init` | Generate directly into the destination directory. |
| `--overwrite`, `-o` | Allow template output to replace existing files. |
| `--vcs` | Select `git` or `none` for generated repository initialization. |
| `--force-git-init` | Force fresh git initialization. |
| `--no-workspace` | Skip automatic Cargo workspace member insertion. |
| `--define`, `-d` | Provide a template value as `key=value`. |
| `--values-file`, `--template-values-file` | Load template values from a TOML values file. |
| `--silent`, `-s` | Disable interactive prompting and require all values up front. |
| `--allow-commands`, `-a` | Allow hook scripts to run system commands without prompting. |
| `--config`, `-c` | Use a specific application config file. |
| `--list-favorites` | List configured favorites instead of generating. |
| `--identity`, `-i` | Select an SSH identity path for git sources. |
| `--gitconfig` | Select a gitconfig file for URL rewrite handling. |
| `--skip-submodules` | Skip git submodule download. |
| `--test` | Expand the template in test mode and run the template test command. |
| `--lib` | Set `crate_type` to `"lib"`. |
| `--bin` | Set `crate_type` to `"bin"`. |
| `--verbose`, `-v` | Enable verbose output. |
| `--quiet`, `-q` | Suppress warnings and errors and require continue-on-error. |
| `--continue-on-error` | Continue across recoverable template errors. |

## Appendix A: Environment

The working environment runs Rust 2021 on Linux without network access. The following third-party dependencies and tools are preinstalled or available from the manifest and lockfile: `anstyle`, `anyhow`, `assert_cmd`, `auth-git2`, `bstr`, `cargo-util-schemas`, `clap`, `console`, `dialoguer`, `env_logger`, `fs-err`, `git2`, `gix-config`, `gix-hash`, `heck`, `home`, `ignore`, `indexmap`, `indicatif`, `indoc`, `liquid`, `liquid-core`, `liquid-derive`, `liquid-lib`, `log`, `names`, `openssl`, `pastey`, `predicates`, `regex`, `remove_dir_all`, `rhai`, `sanitize-filename`, `semver`, `serde`, `tempfile`, `thiserror`, `time`, `toml`, `url`, and `walkdir`. Required command-line tools include `cargo`, `rustc`, `git`, and `cargo-nextest` for test execution.

The assessment environment provides the same runtime, toolchain, and dependency set. The project must declare its packaging metadata in a standard Cargo manifest at the project root so the crate and its binary target are buildable by Cargo. The assessment builds the package with the `vendored-openssl` feature enabled, so the manifest must declare that feature name, even if the feature has no behavior attached; the package version must be compatible with a `0.23` caret requirement.

## Appendix B: Assessment Notes

Assessment covers the documented public CLI and library behavior for local directories and local git repositories. It exercises template source classification, favorites and config merging, placeholder resolution, Liquid rendering, file and path rendering, include/exclude/ignore behavior, conditional template config, Rhai hook phases and extension modules, output copy conflict handling, git initialization, Cargo workspace insertion, template test mode, library return values, and CLI exit behavior.

Assessment does not depend on live external services. Tests use temporary local templates, local git repositories, local config files, and generated output inspection. Exact diagnostic prose, color, emoji, progress output, private helper APIs, and undocumented internals are not assessed.
