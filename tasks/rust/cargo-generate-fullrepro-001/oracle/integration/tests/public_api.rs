#![allow(dead_code, unused_imports)]
#[path = "../src/helpers/mod.rs"]
mod helpers;

use crate::helpers::prelude::*;

use cargo_generate::{generate, GenerateArgs, TemplatePath};

/// Verifies: CG-SRC-002, CG-VAL-002, CG-INV-008
#[test]
fn it_allows_generate_call_with_public_args_and_returns_the_generated_path() {
    let cwd_before = std::env::current_dir().unwrap();

    let template = tempdir().init_default_template().init_git().build();

    let dir = tempdir().build().root.keep();

    let mut args_exposed = GenerateArgs::default();
    args_exposed.template_path = TemplatePath {
        git: Some(format!("{}", template.path().display())),
        ..TemplatePath::default()
    };
    args_exposed.name = Some(String::from("foobar_project"));
    args_exposed.force = true;
    args_exposed.verbose = true;
    args_exposed.destination = Some(dir.clone());
    args_exposed.bin = true;
    args_exposed.lib = false;

    assert_eq!(
        generate(args_exposed).expect("cannot generate project"),
        dir.join("foobar_project")
    );

    assert!(
        std::fs::read_to_string(dir.join("foobar_project").join("Cargo.toml"))
            .expect("cannot read file")
            .contains("foobar_project")
    );

    let cwd_after = std::env::current_dir().unwrap();
    assert!(cwd_after == cwd_before);
}
