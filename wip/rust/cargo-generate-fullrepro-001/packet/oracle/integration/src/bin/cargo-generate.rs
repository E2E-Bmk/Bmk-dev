use cargo_generate::{generate, list_favorites, Cli};
use clap::Parser;

fn main() -> anyhow::Result<()> {
    env_logger::builder()
        .filter_level(log::LevelFilter::Info)
        .parse_default_env()
        .format_timestamp(None)
        .format_target(false)
        .format_module_path(false)
        .format_level(false)
        .target(env_logger::Target::Stdout)
        .init();

    let args = resolve_args();
    if args.list_favorites {
        list_favorites(&args)?;
    } else {
        generate(args)?;
    }
    Ok(())
}

fn resolve_args() -> cargo_generate::GenerateArgs {
    match Cli::parse_from(std::env::args()) {
        Cli::Generate(args) => args,
        _ => panic!("expected generate command"),
    }
}
