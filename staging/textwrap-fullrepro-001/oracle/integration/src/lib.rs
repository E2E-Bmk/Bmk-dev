// Oracle integration tests for the text wrapping library
#![cfg(test)]
#![allow(clippy::all)]

include!("all/pipeline.rs");
include!("all/fill_refill.rs");
include!("all/indent_dedent.rs");
include!("all/columns_layout.rs");
include!("all/consistency.rs");
