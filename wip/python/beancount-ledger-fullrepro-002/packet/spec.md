# Beancount Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Beancount is a command-line double-entry accounting system built around plain text ledger files. A ledger records dated financial directives such as account openings, transactions, balance assertions, prices, notes, documents, and events. Beancount loads those files into Python objects, checks and transforms the resulting directive stream, and exposes the same facts through several public views: directive lists, inventories, realized account trees, price maps, formatted ledger text, and command-line diagnostics.

The library treats dates as day-level accounting dates. It does not model time of day. Decimal arithmetic is used for accounting quantities; callers should construct numbers with `D()` or `decimal.Decimal`, not floating-point arithmetic, when exact accounting behavior matters.

## Non-Goals

- Beancount does not provide a database server, hosted service, or network-backed accounting system in this surface.
- This specification does not cover web UI behavior, report-rendering projects split out of Beancount v3, ingestion frameworks outside the installed package surface, or deprecated v1/v2 command suites.
- The public contract does not require preserving comments or exact original layout through `load_file()` followed by `print_entries()`; use `bean-format` for whitespace-only source formatting.
- The public contract does not expose private parser extension modules, generated grammar internals, private display-context internals, or test-only comparison helpers.
- Price lookup is date-based, not time-of-day based, and does not synthesize intraday or day-trading semantics.
- Failed market conversion does not invent prices, raise by default, or silently drop the original units; it returns the unchanged amount or units.
- Inventory objects are not immutable. Directive objects are immutable tuple-like records, but inventories intentionally mutate when positions are added.
- Command-line tools are not required to fetch live prices or contact external services for the covered behavior.

## Representative Workflows

### Load, Inspect, Realize, and Value a Ledger

```python
import beancount as bn

entries, errors, options_map = bn.load_file("personal.beancount")
if errors:
    for error in errors:
        print(error.message)

accounts = bn.get_accounts(entries)
open_close = bn.get_account_open_close(entries)
root = bn.realize(entries, min_accounts=bn.get_account_types(options_map))

price_map = bn.build_price_map(entries)
for txn in bn.filter_txns(entries):
    rendered = bn.format_entry(txn, options_map["dcontext"])
    print(rendered)

checking = bn.account.join("Assets", "Bank", "Checking")
account_node = root.get("Assets", {}).get("Bank", {}).get("Checking")
if account_node is not None:
    units_balance = account_node.balance.reduce(bn.get_units)
    cost_balance = account_node.balance.reduce(bn.get_cost)
    value_balance = account_node.balance.reduce(bn.get_value, price_map)
```

This workflow uses the same loaded directive list to derive accounts, account lifecycle declarations, a realized tree, price map, formatted text, and inventory valuation views.

### Check and Format from the Command Line

```shell
bean-check --json personal.beancount
bean-format --currency-column 60 personal.beancount --output formatted.beancount
bean-doctor missing-open personal.beancount
bean-doctor display-context personal.beancount
```

The first command reports validation errors in JSON. The formatter aligns amounts without relying on a parse-and-print round trip. The doctor commands derive missing account openings and display precision from the loaded ledger.

### Write a Plugin

```python
__plugins__ = ("check_entries",)

def check_entries(entries, options_map):
    errors = []
    new_entries = entries
    return new_entries, errors
```

When enabled by a ledger `plugin` option, the function receives the current directive stream and options map, returns the stream to continue processing, and reports any plugin-specific errors as error objects.

## Ledger Loading and Validation

Loading parses ledger files into a date-sorted directive stream, resolves includes, applies plugins, and validates the result.

**File loading.** `load_file` must produce a single date-sorted directive stream from a top-level file and its includes. It must return `(entries, errors, options)`. The `options` map must include `title`, `operating_currency` (as a list), `filename`, and `include` (a list of parsed file paths). Include paths must be resolved relative to the file containing the include directive unless they are absolute. Duplicate included filenames must not be parsed again and must produce a load error. Include globs that match no files must produce a load error.

**Processing pipeline.** After parsing, the loader books incomplete transactions, applies plugins and standard transformations according to `plugin_processing_mode`, validates the resulting entries, and returns all accumulated errors instead of raising for normal ledger problems. When `plugin_processing_mode` is set to `"raw"`, standard balance validation must be skipped.

**Same-day ordering.** Balance assertions apply at the beginning of their date, so a balance directive on a date is ordered before transactions on the same date. Open directives sort before other same-day directives, document directives sort after transactions, and close directives sort last on the same date.

**Docstring loading.** `load_doc` must be a decorator that parses the decorated function's docstring as Beancount input and passes `(entries, errors, options)` to the function. The `options["filename"]` must be `"<string>"` for docstring-loaded input. When `expect_errors` is `True`, the decorator must accept ledgers that produce errors without failing.

## Ledger Syntax Objects

Each directive type represents a dated accounting event with specific public fields for programmatic access.

**Account lifecycle directives.** `Open` directives define account lifecycle and optional currency/booking restrictions. `Close` directives end an account lifecycle. `Commodity` directives are optional declarations used primarily for commodity metadata. `Pad` directives request automatic padding transactions so that a later balance assertion can succeed. `Balance` directives record expected units, tolerance, and a difference amount when checking fails.

**Transactions.** `Transaction` directives carry a `flag`, optional `payee`, `narration`, `tags` (as a frozenset without `#` markers), `links` (as a frozenset without `^` markers), and posting legs. Transaction postings may omit units during parsing so booking can infer them. A `Posting` may carry a concrete lot `Cost`, an incomplete `CostSpec` before booking, a `price`, an optional posting flag, and posting-level metadata.

**Information directives.** `Note` directives attach dated information to accounts and expose a `comment` attribute. `Event` directives record dated values for arbitrary named variables through `type` and `description` attributes. `Query` directives store named queries through `name` and `query_string` attributes. `Price` directives add dated exchange or commodity prices through an `amount` attribute. `Document` directives attach files through a `filename` attribute. `Custom` directives carry plugin-facing dated values through `type` and `values` attributes.

## Account Names and Account Types

Account names follow a colon-separated hierarchical structure, and account types classify accounts for financial reporting.

**Account name helpers.** The `account` module must provide `join`, `split`, `parent`, `leaf`, `sans_root`, `root`, `has_component`, `commonprefix`, `parents`, and `parent_matcher` for manipulating colon-separated account name strings. `is_valid`, `is_valid_root`, and `is_valid_leaf` must validate account name components—root components must start with an uppercase letter, and full account names must use properly capitalized colon-separated components.

**Account roots and types.** The default account roots are `Assets`, `Liabilities`, `Equity`, `Income`, and `Expenses`; these roots can be renamed by options such as `name_assets` and `name_income` near the beginning of the file. `get_account_types` must extract the configured root names from the options map. `get_account_type` must return the root component of an account name.

**Account classification and signs.** `is_balance_sheet_account` must identify Assets, Liabilities, and Equity accounts. `is_income_statement_account` must identify Income and Expenses accounts. `is_inverted_account` must identify Liabilities, Income, and Equity. `get_account_sign` must return `+1` for Assets and Expenses and `-1` for the other roots. `get_account_sort_key` must produce sort keys that order accounts by their configured root position.

## Inventories and Balances

Inventories collect positions keyed by currency and cost, providing the balance representation for accounts.

**Inventory construction.** `Inventory` is mutable and may be constructed empty or from a string representation via `Inventory.from_string`. `add_amount` must aggregate into existing lots and return `(prior_position, new_position)` where `prior_position` is `None` for new currencies. `add_position` must add a `Position` to the inventory. `add_inventory` must add all positions from another inventory and must return the modified inventory.

**Lot identity and zero removal.** Inventories preserve lot identity by unit currency and cost. Multiple positions with the same key aggregate into a single lot. Lots with a zero resulting unit quantity are removed rather than retained as zero positions, so `is_empty` returns `True` after opposing amounts cancel.

**Inventory queries.** `currencies` must return the set of unit currencies. `cost_currencies` must return the set of cost currencies. `currency_pairs` must return `(unit_currency, cost_currency)` pairs where cost-free positions use `None` as the cost currency. `get_currency_units` must return the `Amount` for a specific currency. `get_only_position` must return the only position when the inventory holds exactly one, return `None` when empty, and raise `AssertionError` when more than one position exists.

**Reduction and averaging.** `reduce` must apply a function like `get_units`, `get_cost`, or `get_value` to each position and return a new inventory with the results, leaving the original inventory unchanged. `split` must return the currency keys present. `average` must collapse same-currency lots into averaged positions.

**Boolean behavior.** `Inventory.__bool__` must raise `NotImplementedError`; callers must use `is_empty` instead.

**Realized accounts.** `realize` must convert a flat directive list into a tree of `RealAccount` nodes. Each node must expose `account`, `balance`, and `txn_postings`. When `min_accounts` is supplied, those accounts must be created even if no directives reference them. When `compute_balance` is `False`, balances must remain empty while postings are still tracked. Account-attached directives like `Open`, `Pad`, and `Note` must appear in the relevant account's `txn_postings`. A `Pad` must appear in both the source and target account's postings. A transaction with multiple postings must appear once per posting in realized views, wrapped as `TxnPosting` pairs that preserve both the parent `txn` and the individual `posting`.

## Prices and Market Value

Price directives build a date-indexed price database for currency conversion and market valuation.

**Price map construction.** `build_price_map` must construct a price database from `Price` directives. When multiple prices exist for the same pair and date, the later entry in the directive stream must win. The price map must automatically create inverse rates. `forward_pairs` must expose the list of directly declared `(base, quote)` currency pairs. An identity lookup such as `("USD", "USD")` must return `(None, Decimal("1"))`.

**Price lookup.** `get_price` must return the latest price whose date is not after the requested date as a `(date, rate)` pair. A missing price must return `(None, None)`. `get_latest_price` must accept a `"BASE/QUOTE"` string and return the most recent available price.

**Conversion.** `convert_amount` must convert an `Amount` to a target currency using the price map. When a direct rate is unavailable but a `via` chain of intermediate currencies is supplied, the conversion must proceed through the intermediaries. When no rate is available, the original amount must be returned unchanged.

**Weight and value.** `get_weight` must compute the balancing weight of a posting: when a cost is present, weight must be `units × cost` in the cost currency regardless of any posting price; when only a price is present, weight must be `units × price`; otherwise weight must equal the posting units. `get_value` must use the cost currency to look up a market price when a cost is present, and must use the price currency when only a posting price is present.

## Plugins and Transformations

Plugins extend the loading pipeline by transforming the directive stream and reporting custom errors.

**Plugin protocol.** A plugin module must expose a `__plugins__` tuple naming its entry-point functions. Each function must accept `(entries, options_map)` and return `(new_entries, errors)`. Plugin import failures and plugin callback exceptions must be returned as load errors with traceback text in the message. `SystemExit` from a plugin must be allowed to propagate.

**Processing modes.** Default loader mode runs standard document, padding, and balance processing around user plugins. When `plugin_processing_mode` is set to `"raw"`, callers gain explicit control over the plugin list and ordering, and standard balance validation is skipped.

**Auto plugins.** When a user enables the `--auto` flag for `bean-check`, Beancount temporarily enables the standard auto plugin set for that command invocation.

## Getters and Printing

Getters extract account and lifecycle information from directive streams, and printing renders directives as Beancount syntax.

**Account getters.** `get_accounts` must return the set of all accounts referenced by account-bearing directives and transaction postings, including accounts from `Pad`, `Balance`, `Note`, and `Document` directives. `get_account_open_close` must return a mapping from account names to `[open, close]` directive pairs, keeping the first open and first close when duplicates exist.

**Booking enum.** `Booking` must expose the members `STRICT`, `STRICT_WITH_SIZE`, `NONE`, `AVERAGE`, `FIFO`, `LIFO`, and `HIFO`.

**Formatting and printing.** `format_entry` must render a directive as Beancount syntax text using the directive fields. Source bookkeeping metadata such as `filename` and `lineno` must be omitted from normal metadata output. Tags must be rendered with `#` markers and links with `^` markers, both sorted alphabetically. When `write_source` is `True`, a comment indicating the source filename and line number must be included. `print_entry` must write one formatted directive to a file. `print_entries` must write a list of directives with blank-line separators and must raise `AssertionError` when passed a non-list iterable.

## Command-Line Tools

Beancount provides command-line tools for checking, formatting, diagnosing, and generating ledger files.

**bean-check.** `bean-check FILENAME` parses, books, transforms, and validates a ledger. It exits with status 0 when no errors are returned and status 1 when errors exist. `--json` writes a JSON object with an `errors` list containing message, filename, and line number. `--verbose` enables timing/logging output. `--no-cache` disables the load cache. `--cache-filename` overrides the cache filename pattern. `--auto` implicitly enables auto plugins while checking.

`bean-doctor` is a diagnostic command group. It provides commands to inspect lexing/parsing, round-trip printed output, validate document/account directory hierarchies, list available options, print parsed options, show context at a file location, find linked or tagged transactions, inspect a file region and balances, print missing open directives, and display inferred display precision. In the command group, subcommand lookup accepts hyphen and underscore variants and documented aliases.

`bean-example` writes a realistic generated ledger. It supports begin date, end date, fictional birth date, random seed, disabling reformatting, output file, and verbose logging. By default it writes to standard output and formats the generated ledger.

`bean-format` reformats Beancount input by aligning numbers and currencies. It uses text matching rather than a parse-and-print cycle, so the intended effect is whitespace-only alignment while preserving comments and file structure. It can write to standard output, a specified output file for a single input, or edit one or more files in place. Alignment may be controlled by prefix width, number width, or fixed currency column.

`treeify` is a standalone text tool for replacing a column of hierarchical names with an ASCII tree. It can read from a file or standard input, write to a file or standard output, choose account-like, loose-account, filename, or custom patterns, and customize delimiters, split regex, and filler text.

## State Model

A ledger has one ordered directive stream, an options map, a load-error stream, derived inventories and price maps, and a realized account tree. These are public projections of the same parsed financial state.

- Directives returned by `load_file()` must be the directives consumed by getters, realization, printing, plugins, and validation.
- Entries appended or transformed by a plugin must appear in the returned ordered stream and in every derived view built from that stream.
- Inventory balances, conversion results, and realized account balances must preserve the units, costs, and prices represented by the source directives.
- Printing and loading a supported directive must preserve its public date, account, currencies, tags, links, metadata, and posting semantics.

## Error Semantics

Normal ledger syntax, booking, transformation, validation, include, and plugin problems are reported as error objects in the loader's returned `errors` list. Public error objects have:

```python
error.source
error.message
error.entry
```

`source` is metadata, usually containing `filename` and `lineno`. `message` is human-readable. `entry` is the related directive or `None`.

Loader-level include errors include missing files, include globs that match no files, and duplicate filenames. These are returned as load errors rather than raised exceptions.

Plugin import failures and plugin callback exceptions are returned as load errors with traceback text in the message. `SystemExit` from a plugin is allowed to propagate.

Text constructors raise `ValueError` when they cannot parse their input: `Amount.from_string()`, `Position.from_string()`, invalid option converters, and invalid Decimal creation through `D()` all use this style.

Public APIs use `AssertionError` for programmer errors where the documented object type or invariant is violated, such as invalid directive metadata for type sanity checks, attempting to retrieve the only position from an inventory containing more than one position, constructing a `Position` with the wrong object types, or iterating realized postings in invalid date order.

`RealAccount.__setitem__()` raises `KeyError` for invalid child keys and `ValueError` for invalid child values or child names inconsistent with their keys.

`Inventory.__bool__()` raises `NotImplementedError`; callers must use `is_empty()`.

`bean-check` exits with status 1 when the checked ledger has errors and 0 when it has none. Click-based command-line argument errors use the normal command-line usage error behavior for that command.

## Cross-View Invariants

1. Loading and printing describe the same dated directives: `format_entry()` and `print_entries()` render public directive objects in Beancount syntax using the directive fields, while omitting source bookkeeping metadata from normal metadata output.

2. The account set reported by `get_accounts(entries)` matches the accounts that `realize(entries)` can create from account-bearing directives and transaction postings, subject to any extra accounts requested through `min_accounts`.

3. A transaction with multiple postings appears once in the directive stream but appears once per posting in realized account views, wrapped as `TxnPosting` pairs that preserve both the parent transaction and the individual posting.

4. Inventory balances and conversion views preserve lot identity until a caller explicitly reduces or averages them. Calling `reduce(get_units)`, `reduce(get_cost)`, or `reduce(get_value, price_map, date)` changes the valuation view but leaves the original inventory object unchanged.

5. Price maps and conversion helpers agree on missing-price behavior: absent rates are represented by `(None, None)` at lookup time and by returning the original units or amount at conversion time.

6. Same-day ordering is consistent across loader output, balance checking, realization, and printing: opens are first, balance assertions precede transactions, ordinary transaction-day directives follow, documents are after transactions, and closes are last.

7. Tags and links are stored without their leading `#` and `^` markers on directive objects and are rendered with those markers when printed.

8. Options influence all projections consistently: renamed account roots affect parsing, account classification, account signs, account sort keys, and account-type extraction from the returned options map.

9. A concrete cost on a posting determines both lot identity in inventories and cost/weight conversion behavior; a posting price without a cost affects balancing weight and value-currency inference but does not create a cost lot.

10. A successful load returns entries and an options map even when non-fatal errors exist. CLI checking turns those returned errors into user-visible output and process exit status.

## Public Interface

### Import Surface

The package is named `beancount`. The root package imports the public symbols from `beancount.api`, so these two styles are equivalent for the public API:

```python
import beancount as bn
from beancount import load_file, Amount, Transaction
from beancount.api import load_file, Amount, Transaction
```

The public root API includes these import namespaces:

```python
bn.account
bn.amount
bn.dtypes
```

The package installs these command-line entry points:

```text
bean-check
bean-doctor
bean-example
bean-format
treeify
```

Runtime dependencies are ordinary local Python dependencies. Beancount does not require a network service to parse, check, format, or realize a local ledger.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| D | function | Construct Decimal values for Beancount arithmetic |
| ZERO | constant | Decimal zero constant |
| Amount | class | Immutable number-currency pair |
| Cost | class | Per-unit cost attached to a booked lot |
| CostSpec | class | Incomplete cost specification before booking |
| Position | class | Holding with units and optional lot cost |
| new_metadata | function | Create metadata dictionary with filename and lineno |
| Open | class | Account opening directive |
| Close | class | Account closing directive |
| Commodity | class | Commodity declaration directive |
| Pad | class | Automatic padding directive |
| Balance | class | Balance assertion directive |
| Transaction | class | Financial transaction directive |
| Posting | class | Transaction posting leg |
| TxnPosting | class | Transaction-posting pair for realized accounts |
| Note | class | Dated note attached to an account |
| Event | class | Dated named event directive |
| Query | class | Named query directive |
| Price | class | Dated exchange price directive |
| Document | class | Document attachment directive |
| Custom | class | Plugin-facing custom directive |
| Account | class | String alias for account names |
| Currency | class | String alias for currencies |
| Flag | class | String alias for flags |
| Meta | class | Dictionary alias for metadata |
| Directive | class | Union type of all directive classes |
| Directives | class | List-of-directives type alias |
| Options | class | Options-map dictionary type alias |
| dtypes | module | Namespace containing all directive classes |
| Booking | class | Enum of account booking methods |
| FLAG_OKAY | constant | Transaction flag for normal entries |
| FLAG_WARNING | constant | Transaction flag for warnings |
| FLAG_PADDING | constant | Transaction flag for padding entries |
| FLAG_TRANSFER | constant | Transaction flag for transfers |
| FLAG_CONVERSIONS | constant | Transaction flag for conversions |
| FLAG_MERGING | constant | Transaction flag for merging entries |
| FLAG_SUMMARIZE | constant | Transaction flag for summarized entries |
| filter_txns | function | Yield only Transaction directives from an entry list |
| account | module | Account name manipulation utilities |
| get_account_type | function | Return root component of an account name |
| get_account_types | function | Extract configured root names from options map |
| get_account_sign | function | Return normal sign for an account type |
| get_account_sort_key | function | Sort key for accounts in configured root order |
| load_file | function | Load a Beancount ledger and return entries, errors, options |
| load_encrypted_file | function | Decrypt and load an encrypted Beancount file |
| load_doc | function | Decorator to parse a docstring as Beancount input |
| Inventory | class | Mutable collection of positions keyed by currency and cost |
| build_price_map | function | Build date-indexed price database from Price directives |
| get_latest_price | function | Return latest available price for a currency pair |
| get_price | function | Return latest price on or before a date |
| get_units | function | Extract units amount from a position |
| get_cost | function | Extract total cost from a position |
| get_weight | function | Extract balancing weight from a posting |
| get_value | function | Convert position to market value using price map |
| convert_position | function | Convert a position to a target currency |
| convert_amount | function | Convert an amount to a target currency |
| RealAccount | class | Dictionary-like account-tree node with balance |
| realize | function | Convert flat directive list into account tree |
| get_accounts | function | Return all accounts referenced by directives |
| get_account_open_close | function | Map accounts to open/close directive pairs |
| format_entry | function | Render a directive as Beancount syntax text |
| print_entry | function | Write one formatted directive to a file |
| print_entries | function | Write a list of directives with blank-line separators |

### CLI Entry Points

The covered console commands are `bean-check` and `bean-format`. `bean-check FILE` must parse and validate the ledger, return status 0 when no errors are produced, and return a nonzero status when load or validation errors are produced. `bean-format FILE` must emit formatted ledger text to standard output and return status 0 for valid input. Running `python -m beancount` is not supported by this specification.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers numeric and directive objects, loading and include behavior, plugins, inventories, prices, realization, getters, printing, and the covered command-line workflows. It compares public values, derived views, files, and exit statuses, including include resolution, same-day ordering, duplicate price dates, missing conversions, configured root names, and plugin failures. Private parser internals, caches, helper types, exact diagnostic wording, and source layout are not part of this contract.
