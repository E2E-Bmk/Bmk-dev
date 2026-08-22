#![allow(dead_code, unused_imports)]
#[path = "../src/helpers/mod.rs"]
mod helpers;

use crate::helpers::prelude::*;

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_use_a_plain_folder() {
    let template = tempdir().with_default_manifest().build();

    let dir = tempdir().build();

    binary()
        .arg_name("foobar-project")
        .arg(template.path())
        .current_dir(dir.path())
        .assert()
        .success();

    let repo = git2::Repository::open(dir.path().join("foobar-project")).unwrap();
    let references = repo.references().unwrap().count();
    assert_eq!(0, references);
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_use_a_specified_path() {
    let template = tempdir().with_default_manifest().build();

    let dir = tempdir().build();

    binary()
        .arg_name("foobar-project")
        .arg_path(template.path())
        .current_dir(dir.path())
        .assert()
        .success();

    let repo = git2::Repository::open(dir.path().join("foobar-project")).unwrap();
    let references = repo.references().unwrap().count();
    assert_eq!(0, references);
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_uses_the_default_subtemplate_in_silent_mode() {
    let template = tempdir()
        .file(
            "cargo-generate.toml",
            indoc! {r#"
                [template]
                sub_templates = ["sub1", "sub2"]
            "#},
        )
        .file(
            "sub1/Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "first subtemplate"
                version = "0.1.0"
            "#},
        )
        .file("sub1/source.txt", "sub1")
        .file(
            "sub2/Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "second subtemplate"
                version = "0.1.0"
            "#},
        )
        .file("sub2/source.txt", "sub2")
        .build();

    let dir = tempdir().build();

    binary()
        .arg("--silent")
        .arg_name("foobar-project")
        .arg_path(template.path())
        .current_dir(dir.path())
        .assert()
        .success();

    assert_eq!("sub1", dir.read("foobar-project/source.txt"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_substitutes_projectname_in_cargo_toml() {
    let template = tempdir().init_default_template().build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains("foobar-project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_substitutes_authors_and_username() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            r#"[package]
name = "{{project-name}}"
authors = "{{authors}}"
description = "A wonderful project by {{username}}"
version = "0.1.0"
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .env("CARGO_EMAIL", "Email")
        .env("CARGO_NAME", "Author")
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains(r#"authors = "Author <Email>""#));
    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains(r#"description = "A wonderful project by Author""#));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_substitutes_os_arch() {
    let template = tempdir()
        .file("some-file", r#"{{os-arch}}"#)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.read("foobar-project/some-file").contains(&format!(
        "{}-{}",
        env::consts::OS,
        env::consts::ARCH
    )));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_keeps_snake_case_projectname() {
    let template = tempdir().init_default_template().build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar_project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar_project/Cargo.toml")
        .contains("foobar_project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_substitutes_cratename_in_a_rust_file() {
    let template = tempdir()
        .file(
            "main.rs",
            r#"
extern crate {{crate_name}};
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    let file = dir.read("foobar-project/main.rs");
    assert!(file.contains("foobar_project"));
    assert!(!file.contains("foobar-project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn short_commands_work() {
    let template = tempdir().init_default_template().build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains("foobar-project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_generate_inside_existing_repository() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().build();
    binary()
        .arg_git(template.path())
        .arg_name("outer")
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir.read("outer/Cargo.toml").contains("outer"));
    let outer_project_dir = dir.path().join("outer");
    let outer_repo = git2::Repository::discover(&outer_project_dir)?;

    binary()
        .arg_git(template.path())
        .arg_name("inner")
        .current_dir(&outer_project_dir)
        .assert()
        .success();
    assert!(dir.read("outer/inner/Cargo.toml").contains("inner"));
    let inner_project_dir = outer_project_dir.join("inner");
    let inner_repo = git2::Repository::discover(inner_project_dir)?;
    assert_eq!(outer_repo.path(), inner_repo.path());
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_generate_into_cwd() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().build();
    assert!(
        !dir.path().join(".git").exists(),
        "Pre-condition: there should not be a .git dir in CWD"
    );

    binary()
        .arg_git(template.path())
        .arg_name("my-proj")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir.read("Cargo.toml").contains("my-proj"));

    assert!(
        !dir.path().join(".git").exists(),
        "Post-condition: there should not be a .git dir in CWD"
    );
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_generate_into_existing_git_dir() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().file(".git/config", "foobar").build();
    assert!(
        dir.path().join(".git").exists(),
        "Pre-condition: there is a .git dir in CWD"
    );

    binary()
        .arg_git(template.path())
        .arg_name("my-proj")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir.read("Cargo.toml").contains("my-proj"));
    assert!(
        dir.read(".git/config").contains("foobar"),
        "Post-condition: .git/config is preserved"
    );
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_generate_at_given_path() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().build();
    let dest = dir.path().join("destination");
    fs::create_dir(&dest).expect("can create directory");
    binary()
        .arg_git(template.path())
        .arg_name("my-proj")
        .arg("--destination")
        .arg(&dest)
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir
        .read("destination/my-proj/Cargo.toml")
        .contains("my-proj"));
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_does_not_overwrite_existing_files() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().build();
    let _ = binary()
        .arg_git(template.path())
        .arg_name("my-proj")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();
    binary()
        .arg_git(template.path())
        .arg_name("overwritten-proj")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir.read("Cargo.toml").contains("my-proj"));
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_can_overwrite_files() -> anyhow::Result<()> {
    let template = tempdir().init_default_template().build();
    let dir = tempdir().build();
    let _ = binary()
        .arg_git(template.path())
        .arg_name("my-proj")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();
    binary()
        .arg_git(template.path())
        .arg_name("overwritten-proj")
        .flag_init()
        .arg("--overwrite")
        .current_dir(dir.path())
        .assert()
        .success();
    assert!(dir.read("Cargo.toml").contains("overwritten-proj"));
    Ok(())
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_allows_user_defined_projectname_when_passing_force_flag() {
    let template = tempdir().init_default_template().build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar_project")
        .arg_branch("main")
        .arg("--force")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar_project/Cargo.toml")
        .contains("foobar_project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_removes_files_listed_in_genignore() {
    let template = tempdir()
        .with_default_manifest()
        .file(
            ".genignore",
            r#"deleteme.sh
*.trash
"#,
        )
        .file("deleteme.sh", r#"Nothing to see here"#)
        .file("deleteme.trash", r#"This is trash"#)
        .file("notme.sh", r#"I'm here!"#)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("foobar-project/notme.sh"));
    assert!(dir.exists("foobar-project/deleteme.sh").not());
    assert!(dir.exists("foobar-project/deleteme.trash").not());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[allow(dead_code)]
fn it_always_removes_genignore_file() {
    let template = tempdir()
        .with_default_manifest()
        .file(".genignore", r#"farts"#)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("foobar-project/.genignore").not());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[allow(dead_code)]
fn it_always_removes_cargo_ok_file() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .file(".genignore", r#"farts"#)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("foobar-project/.cargo-ok").not());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[allow(dead_code)]
fn it_removes_genignore_files_before_substitution() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .file(".cicd_workflow", "i contain a ${{ github }} var")
        .file(".genignore", r#".cicd_workflow"#)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("foobar-project/.cicd_workflow").not());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[allow(dead_code)]
fn it_does_not_remove_files_from_outside_project_dir() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .file(
            ".genignore",
            r#"../dangerous.todelete.cargogeneratetests
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    let dangerous_file = template
        .path()
        .join("..")
        .join("dangerous.todelete.cargogeneratetests");

    fs::write(&dangerous_file, "YOU BETTER NOT").unwrap_or_else(|_| {
        panic!(
            "Could not write {}",
            dangerous_file.to_str().expect("Could not read path.")
        )
    });

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(fs::metadata(&dangerous_file)
        .expect("should exist")
        .is_file());
    fs::remove_file(&dangerous_file).expect("failed to clean up test file");
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[allow(dead_code)]
fn errant_ignore_entry_doesnt_affect_template_files() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! {r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .file(
            ".genignore",
            r#"../dangerous.todelete.cargogeneratetests
"#,
        )
        .file("./dangerous.todelete.cargogeneratetests", "IM FINE OK")
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(fs::metadata(
        template
            .path()
            .join("dangerous.todelete.cargogeneratetests")
    )
    .unwrap()
    .is_file());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_loads_a_submodule() {
    let submodule = tempdir()
        .file("README.md", "*JUST A SUBMODULE*")
        .init_git()
        .build();

    let submodule_url = url::Url::from_file_path(submodule.path()).unwrap();
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! { r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .init_git()
        .add_submodule("./submodule/", submodule_url.as_str())
        .build();

    let dir = tempdir().build();
    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains("foobar-project"));
    assert!(dir
        .read("foobar-project/submodule/README.md")
        .contains("*JUST A SUBMODULE*"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_allows_relative_paths() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            indoc! { r#"
                [package]
                name = "{{project-name}}"
                description = "A wonderful project"
                version = "0.1.0"
            "#},
        )
        .init_git()
        .build();

    let relative_path = {
        let mut relative_path = std::path::PathBuf::new();
        relative_path.push("../");
        relative_path.push(template.path().file_name().unwrap().to_str().unwrap());
        relative_path
    };

    let dir = tempdir().build();
    binary()
        .arg_git(relative_path)
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains("foobar-project"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_respects_template_branch_name() {
    let template = tempdir().file("index.html", "My Page").init_git().build();

    Command::new("git")
        .arg("branch")
        .arg("-m")
        .arg("main")
        .arg("gh-pages")
        .current_dir(template.path())
        .assert()
        .success();

    let dir = tempdir().build();
    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("gh-pages")
        .current_dir(dir.path())
        .assert()
        .success();

    Command::new("git")
        .args(["symbolic-ref", "--short", "HEAD"])
        .current_dir(dir.path().join("foobar-project"))
        .assert()
        .success()
        .stdout(predicates::str::diff("gh-pages\n"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_processes_dot_github_directory_files() {
    let template = tempdir()
        .file(".github/foo.txt", "{{project-name}}")
        .init_git()
        .build();
    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert_eq!(dir.read("foobar-project/.github/foo.txt"), "foobar-project");
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_ignore_tags_inside_raw_block() {
    let raw_body = r#"{{badges}}
# {{crate}} {{project-name}}
{{readme}}
{{license}}
## Contribution
Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
dual licensed as above, without any additional terms or conditions.
This project try follow rules:
* [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
* [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
_This README was generated with [cargo-readme](https://github.com/livioribeiro/cargo-readme) from [template](https://github.com/xoac/crates-io-lib-template)
"#;
    let raw_template = format!("{{% raw %}}{raw_body}{{% endraw %}}");
    let template = tempdir()
        .file("README.tpl", raw_template)
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    let template = dir.read("foobar-project/README.tpl");
    assert!(template.contains("{{badges}}"));
    assert!(template.contains("{{crate}}"));
    assert!(template.contains("{{project-name}}"));
    assert!(template.contains("{{readme}}"));
    assert!(template.contains("{{license}}"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_uses_vsc_none_to_avoid_initializing_repository() {
    // Build and commit on branch named 'main'
    let template = tempdir().init_default_template().build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg("--vcs")
        .arg("nONE")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("foobar-project/Cargo.toml")
        .contains("foobar-project"));
    assert!(Repository::open(dir.path().join("foobar-project")).is_err());
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_provides_crate_type_lib() {
    // Build and commit on branch named 'main'
    let template = tempdir()
        .file(
            "Cargo.toml",
            r#"[package]
name = "{{project-name}}"
description = "this is a {{crate_type}}"
version = "0.1.0"
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg("--lib")
        .current_dir(dir.path())
        .assert()
        .success();

    let cargo_toml = dir.read("foobar-project/Cargo.toml");
    assert!(cargo_toml.contains("this is a lib"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_provides_crate_type_bin() {
    // Build and commit on branch named 'main'
    let template = tempdir()
        .file(
            "Cargo.toml",
            r#"[package]
name = "{{project-name}}"
description = "this is a {{crate_type}}"
version = "0.1.0"
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .current_dir(dir.path())
        .assert()
        .success();

    let cargo_toml = dir.read("foobar-project/Cargo.toml");
    assert!(cargo_toml.contains("this is a bin"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_skips_substitution_for_random_garbage_in_cargo_toml() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            r#"[package]
name = "{{function fart() { return "pfffttt"; } fart();}}"
description = "A wonderful project"
version = "0.1.0"
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .arg("--continue-on-error")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.read("foobar-project/Cargo.toml").contains("fart"));
}

/// Verifies: CG-SRC-003, CG-SRC-004, CG-VAL-001, CG-VAL-002, CG-REN-001, CG-OUT-001, CG-OUT-008
#[test]
fn it_skips_substitution_for_unknown_variables_in_cargo_toml() {
    let template = tempdir()
        .file(
            "Cargo.toml",
            r#"[package]
name = "{{ project-name }}"
description = "{{ project-description }}"
description2 = "{{ project-some-other-thing }}"
version = "0.1.0"
"#,
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foobar-project")
        .arg_branch("main")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(
        dir.read("foobar-project/Cargo.toml")
            .contains("foobar-project"),
        "project-name was not substituted"
    );
    assert!(!dir
        .read("foobar-project/Cargo.toml")
        .contains("{{ project-description }}"));
    assert!(!dir
        .read("foobar-project/Cargo.toml")
        .contains("{{ project-some-other-thing }}"));
}
