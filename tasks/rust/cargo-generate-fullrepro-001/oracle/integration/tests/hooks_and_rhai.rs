#![allow(dead_code, unused_imports)]
#[path = "../src/helpers/mod.rs"]
mod helpers;

use crate::helpers::prelude::*;

// Regression test for #1671: hook scripts must be removed from the generated
// output, and the removal must not touch a like-named file in the process CWD.
/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_removes_hook_files_from_output_without_touching_cwd() {
    let template = tempdir()
        .file(
            "post-script.rhai",
            indoc! {r#"
            file::rename("RENAME-ME", "renamed");
        "#},
        )
        .file("RENAME-ME", "content")
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [hooks]
            post = ["post-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    // The directory we run from contains a decoy with the same name as the hook.
    // Before the fix, the relative removal resolved against this CWD and deleted it.
    let dir = tempdir().file("post-script.rhai", "decoy").build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .current_dir(dir.path())
        .assert()
        .success();

    // The hook ran...
    assert!(dir.exists("script-project/renamed"));
    // ...the hook script is gone from the output...
    assert!(!dir.exists("script-project/post-script.rhai"));
    // ...and the like-named decoy in the CWD was left untouched.
    assert!(dir.exists("post-script.rhai"));
    assert!(dir.read("post-script.rhai").contains("decoy"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_runs_all_hook_types() {
    let template = tempdir()
        .file(
            "init-script.rhai",
            indoc! {r#"
            print("init-script has run");
        "#},
        )
        .file(
            "pre-script.rhai",
            indoc! {r#"
            file::rename("PRE-TEST", "PRE");
        "#},
        )
        .file(
            "post-script.rhai",
            indoc! {r#"
            file::rename("POST-TEST", "POST");
        "#},
        )
        .file(
            "system-script.rhai",
            indoc! {r#"
                let output = system::command("touch", ["touched_file"]);
            "#},
        )
        .file(
            "PRE-TEST",
            indoc! {r#"
            {{pre}};
        "#},
        )
        .file(
            "POST-TEST",
            indoc! {r#"
            {{post}};
        "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [template]
            exclude = ["PRE-TEST", "POST"]

            [hooks]
            init = ["init-script.rhai"]
            pre = ["pre-script.rhai"]
            post = ["post-script.rhai", "system-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .arg("-d")
        .arg("pre=hello")
        .arg("-d")
        .arg("post=world")
        .arg("--allow-commands")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("script-project/PRE"));
    assert!(dir.exists("script-project/POST"));

    assert!(dir.exists("script-project/touched_file"));

    assert!(dir.read("script-project/PRE").contains("hello"));
    assert!(dir.read("script-project/POST").contains("world"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_runs_system_commands() {
    let template = tempdir()
        .file(
            "system-script.rhai",
            indoc! {r#"
                let output = system::command("touch", ["touched_file"]);
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [hooks]
            post = ["system-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .arg("--allow-commands")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("script-project/touched_file"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_fails_to_prompt_for_system_commands_in_silent_mode() {
    let template = tempdir()
        .file(
            "system-script.rhai",
            indoc! {r#"
                let output = system::command("touch", ["touched_file"]);
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [hooks]
            post = ["system-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .arg("--silent")
        .current_dir(dir.path())
        .assert()
        .failure();
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_fails_when_a_system_command_returns_non_zero_exit_code() {
    let template = tempdir()
        .file(
            "system-script.rhai",
            r#"let output = system::command("mkdir", ["invalid_/.dir_name"]);"#,
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
                [hooks]
                post = ["system-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .arg("--allow-commands")
        .current_dir(dir.path())
        .assert()
        .failure();
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn it_fails_when_it_cant_execute_system_command() {
    let template = tempdir()
        .file(
            "system-script.rhai",
            indoc! {r#"
                let output = system::command("dummy_command_that_doesnt_exist", ["dummy_arg"]);
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
                [hooks]
                post = ["system-script.rhai"]
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .arg("--allow-commands")
        .current_dir(dir.path())
        .assert()
        .failure();
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn can_change_variables_from_pre_hook() {
    let template = tempdir()
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [placeholders]
            multi = {type = "array", prompt="??", choices=["a","b","c"], default=["a","b"]}
            [hooks]
            pre = ["pre-script.rhai"]
            "#},
        )
        .file(
            "pre-script.rhai",
            indoc! {r#"
                variable::set("foo", "bar");
                variable::set("multi", ["Q","b"]);
            "#},
        )
        .file(
            "PRE-TEST",
            indoc! {r#"
                {{foo}};
                {{multi}};
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("script-project")
        .current_dir(dir.path())
        .arg("-d")
        .arg("multi=a,b")
        .assert()
        .success();

    assert!(dir.exists("script-project/PRE-TEST"));
    let pre_test = dir.read("script-project/PRE-TEST");
    assert!(pre_test.contains("bar"));
    assert!(pre_test.contains("Q"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn init_hook_can_set_project_name() {
    let template = tempdir()
        .file(
            "init.rhai",
            indoc! {r#"
                variable::set("project-name", "ProjectBar");
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [hooks]
            init = ["init.rhai"]
            "#},
        )
        .file(
            "generated.txt",
            indoc! {r#"
            {{crate_name}}
        "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("project-bar/generated.txt"));
    assert!(dir
        .read("project-bar/generated.txt")
        .contains("project_bar"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn init_hook_can_change_project_name_but_keeps_cli_name_for_destination() {
    let template = tempdir()
        .file(
            "init.rhai",
            indoc! {r#"
                variable::set("project-name", "bar");
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
                [hooks]
                init = ["init.rhai"]
            "#},
        )
        .file(
            "generated.txt",
            indoc! {r#"
                {{crate_name}}
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foo")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("foo/generated.txt"));
    assert!(dir.read("foo/generated.txt").contains("bar"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn init_hook_can_change_project_name_but_keeps_init_destination() {
    let template = tempdir()
        .file(
            "init.rhai",
            indoc! {r#"
                variable::set("project-name", "bar");
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
            [hooks]
            init = ["init.rhai"]
            "#},
        )
        .file(
            "generated.txt",
            indoc! {r#"
            {{crate_name}}
        "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foo")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("generated.txt"));
    assert!(dir.read("generated.txt").contains("bar"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn rhai_filter_invokes_rhai_script() {
    let template = tempdir()
        .file(
            "filter-script.rhai",
            indoc! {r#"
                "content from RHAI"
            "#},
        )
        .file(
            "file_to_expand.txt",
            indoc! {r#"
                {{"filter-script.rhai"|rhai}}
            "#},
        )
        .init_git()
        .build();

    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("filter-project")
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir
        .read("filter-project/file_to_expand.txt")
        .contains("content from RHAI"));
}

/// Verifies: CG-HOOK-004, CG-HOOK-005, CG-HOOK-006, CG-INV-005
#[test]
fn date_works() {
    let template = tempdir()
        .file(
            "init.rhai",
            indoc! {r#"
                let dt = system::date();
                variable::set("year", `${dt.year}`);
                variable::set("month", `${dt.month}`);
                variable::set("day", `${dt.day}`);
            "#},
        )
        .file(
            "cargo-generate.toml",
            indoc! {r#"
                [hooks]
                init = ["init.rhai"]
            "#},
        )
        .file(
            "generated.txt",
            indoc! {r#"
                {{year}}-{{month}}-{{day}}
        "#},
        )
        .init_git()
        .build();
    let date = time::OffsetDateTime::now_utc();
    let dir = tempdir().build();

    binary()
        .arg_git(template.path())
        .arg_name("foo")
        .flag_init()
        .current_dir(dir.path())
        .assert()
        .success();

    assert!(dir.exists("generated.txt"), "generated.txt didn't exist");
    let content = dir.read("generated.txt");
    let expected = format!("{}-{}-{}", date.year(), u8::from(date.month()), date.day());
    assert!(
        content.contains(&expected),
        "generated.txt didn't include `{expected}`:\n`{content}`"
    );
}
