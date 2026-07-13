# Beancount Specification

## Product Overview

Beancount is a command-line double-entry accounting system built around plain text ledger files. A ledger records dated financial directives such as account openings, transactions, balance assertions, prices, notes, documents, and events. Beancount loads those files into Python objects, checks and transforms the resulting directive stream, and exposes the same facts through several public views: directive lists, inventories, realized account trees, price maps, formatted ledger text, and command-line diagnostics.

The library treats dates as day-level accounting dates. It does not model time of day. Decimal arithmetic is used for accounting quantities; callers should construct numbers with `D()` or `decimal.Decimal`, not floating-point arithmetic, when exact accounting behavior matters.

## Scope

This specification covers:

- The root Python API exposed by `import beancount as bn` and by `beancount.api`.
- The public directive objects, amount/position/inventory objects, account helpers, price and conversion helpers, loader functions, printer functions, and account realization function exported from the root API.
- The Beancount ledger loading contract: parsing input files or strings, resolving includes, booking incomplete postings, running configured transformations, validating entries, and returning entries, errors, and options.
- The installed command-line tools declared by the package: `bean-check`, `bean-doctor`, `bean-example`, `bean-format`, and `treeify`.
- The plugin contract used by ledger `plugin` options.
- User-observable behavior of the public projections over a ledger: textual syntax, directive objects, account sets, inventories, realized trees, price maps, printed output, and CLI diagnostics.

## Installable Surface

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

## Public API

### Numeric Values

`D(strord: Decimal | str | int | float | None = None) -> Decimal` constructs a `Decimal` for Beancount values. `None` and an empty string produce decimal zero. Existing `Decimal` values are returned unchanged. Strings may include commas or spaces used as thousands separators; those separators are removed before conversion. Invalid values raise `ValueError`.

`ZERO` is the Decimal zero constant used by the public API.

`Amount(number: Decimal, currency: str)` is an immutable pair of a number and a currency. The string form is `<number> <currency>` using Beancount display formatting. `Amount.from_string(string)` parses strings such as `"10.50 USD"` and raises `ValueError` for invalid amount text. Amount equality compares both number and currency. Ordering sorts by currency first and number second. Boolean conversion is true when the number is not zero. Negation is supported for decimal numbers. Amount helper functions are available from the `bn.amount` namespace.

`Cost(number: Decimal, currency: str, date: datetime.date, label: str | None)` describes the per-unit cost attached to a booked lot.

`CostSpec(number_per, number_total, currency, date, label, merge)` describes an incomplete cost specification from input syntax before booking has resolved it into a concrete `Cost`. Missing parts are represented by `None` or Beancount's missing-value sentinel, depending on the parse stage.

`Position(units: Amount, cost: Cost | None = None)` is a holding with units and an optional lot cost. `Position.from_string(string)` accepts Beancount-like position text with an optional cost expression and raises `ValueError` for invalid text. Positions render as ledger position syntax, compare by a Beancount-specific currency/cost sort key, support negation, absolute value, and Decimal scalar multiplication, and report their `(unit_currency, cost_currency_or_None)` currency pair.

### Directive Objects

The directive classes are immutable tuple-like objects. All dated directives include:

- `meta`: metadata dictionary.
- `date`: `datetime.date`.

`new_metadata(filename: str, lineno: int, kvlist: dict | None = None) -> dict` returns a metadata dictionary containing `filename` and `lineno`; any supplied key-values are merged into it.

`Account`, `Currency`, and `Flag` are string aliases. `Meta` is a dictionary alias. `Directive` is the public union of directive classes. `Directives` is a list of directives. `Options` is the options-map dictionary returned by loaders.

The public directive classes and fields are:

```python
Open(meta, date, account, currencies, booking)
Close(meta, date, account)
Commodity(meta, date, currency)
Pad(meta, date, account, source_account)
Balance(meta, date, account, amount, tolerance, diff_amount)
Transaction(meta, date, flag, payee, narration, tags, links, postings)
Posting(account, units, cost, price, flag, meta)
TxnPosting(txn, posting)
Note(meta, date, account, comment, tags, links)
Event(meta, date, type, description)
Query(meta, date, name, query_string)
Price(meta, date, currency, amount)
Document(meta, date, account, filename, tags, links)
Custom(meta, date, type, values)
```

`dtypes` is a namespace containing the directive classes `Open`, `Close`, `Commodity`, `Pad`, `Balance`, `Transaction`, `Note`, `Event`, `Query`, `Price`, `Document`, and `Custom`.

`Booking` is an enum of account booking methods. Its public names are `STRICT`, `STRICT_WITH_SIZE`, `NONE`, `AVERAGE`, `FIFO`, `LIFO`, and `HIFO`. The enum controls how ambiguous inventory lot reductions are resolved: strict methods reject ambiguity, `NONE` permits mixed inventories, average merges lots, and FIFO/LIFO/HIFO select a lot according to the named ordering.

The public transaction flags include `FLAG_OKAY`, `FLAG_WARNING`, `FLAG_PADDING`, `FLAG_TRANSFER`, `FLAG_CONVERSIONS`, `FLAG_MERGING`, and `FLAG_SUMMARIZE`. The generated-entry flags identify entries produced by padding, transfers, conversion balancing, merging, or summarization rather than typed directly by the user.

`filter_txns(entries)` yields only `Transaction` directives from an entry list, preserving their existing order.

### Account Helpers

Account names are colon-separated strings such as `Assets:Bank:Checking`. The account namespace provides:

```python
bn.account.is_valid_root(name) -> bool
bn.account.is_valid_leaf(name) -> bool
bn.account.is_valid(name) -> bool
bn.account.join(*components) -> str
bn.account.split(account_name) -> list[str]
bn.account.parent(account_name) -> str | None
bn.account.leaf(account_name) -> str | None
bn.account.sans_root(account_name) -> str | None
bn.account.root(num_components, account_name) -> str
bn.account.has_component(account_name, component) -> bool
bn.account.commonprefix(accounts) -> str
bn.account.parents(account_name) -> iterator[str]
bn.account.parent_matcher(account_name) -> callable
```

`has_component()` matches complete account components only. `parent()` returns `None` for the root/empty case. `parents()` yields the account itself, then its parents upward. `parent_matcher()` returns a predicate that is true for the named account and its children.

`get_account_type(account_name) -> str` returns the root component. `get_account_types(options) -> AccountTypes` extracts the configured root names from an options map. `get_account_sign(account_name, account_types=None) -> int` returns `+1` for assets and expenses, `-1` for liabilities, income, and equity. The classification helpers identify balance-sheet accounts, income-statement accounts, equity accounts, inverted-sign accounts, and accounts belonging to a specific root name. `get_account_sort_key(account_types, account_name)` sorts accounts in the configured root order, then by name.

### Loading Ledgers

`load_file(filename, log_timings=None, log_errors=None, extra_validations=None, encoding=None)` opens a Beancount file, expands user and environment variables in the filename, resolves relative paths against the current working directory, and returns:

```python
(entries, errors, options_map)
```

`entries` is a date-sorted list of directives after parsing, booking, configured transformations, and validation. `errors` is a list of error objects with `source`, `message`, and `entry` attributes. `options_map` is a dictionary of parsed and derived options.

When the input file is encrypted, `load_file()` delegates to encrypted-file loading and does not use the normal pickle load cache. `load_encrypted_file(filename, log_timings=None, log_errors=None, extra_validations=None, dedent=False, encoding=None)` decrypts the file content and loads it as Beancount input.

`load_doc(expect_errors=False)` returns a decorator for tests and examples. The decorated function's docstring is parsed as Beancount input, optionally dedented, and the wrapped function is called with `(entries, errors, options_map)`. `expect_errors=False` fails if errors are produced, `True` fails if none are produced, and `None` performs no error expectation check.

### Options Map

The loader returns only the top-level file's user options as the base options map. Options from included files contribute selected aggregate values:

- `include`: the sorted absolute filenames parsed during the load.
- `operating_currency`: the top-level operating currencies followed by included-file operating currencies, de-duplicated while preserving first occurrence.
- `dcontext`: display precision context updated with numbers seen in included files.
- `pythonpath`: directories from option maps that requested Python-path insertion.

Public user-settable options include the ledger title, root account names, equity leaf names for earnings/balances/conversions, unrealized-gains and rounding accounts, conversion currency, display precision, inferred tolerances and tolerance multiplier, tolerance-from-cost behavior, document directories, operating currencies, comma rendering, plugin processing mode, long-string warning limit, booking method, deprecated pipe separator support, deprecated `None` tags/links support, precise interpolation, and top-level Python-path insertion.

`plugin_processing_mode` accepts `"default"` or `"raw"`. In default mode, Beancount runs standard pre/post transformations around user plugins. In raw mode, only explicitly configured user plugins are run.

### Plugins

A ledger enables plugins with `plugin` options. A plugin is a Python module that defines `__plugins__`, listing transformation functions by name or function object. Each transformer receives `(entries, options_map)` and, when configured, an extra plugin-configuration string. It returns `(new_entries, errors)`.

Plugin import failures and plugin application exceptions are converted into load errors and appended to the returned error list. A plugin may intentionally raise `SystemExit`; that exit is not converted into a normal load error. After each plugin module runs, entries are sorted again by Beancount's directive sort key.

### Inventories

`Inventory(positions=None)` is a mutable collection of positions keyed by `(unit_currency, cost)`. Iterating over an inventory yields its `Position` values; no iteration order is guaranteed. `Inventory.from_string(string)` parses comma-separated position text.

Important inventory operations:

```python
inv.is_empty() -> bool
inv.is_small(tolerances) -> bool
inv.is_mixed() -> bool
inv.is_reduced_by(amount) -> bool
inv.currencies() -> set[str]
inv.cost_currencies() -> set[str]
inv.currency_pairs() -> set[tuple[str, str | None]]
inv.get_positions() -> list[Position]
inv.get_only_position() -> Position | None
inv.get_currency_units(currency) -> Amount
inv.split() -> dict[str, Inventory]
inv.reduce(reducer, *args) -> Inventory
inv.average() -> Inventory
inv.add_amount(units, cost=None) -> (prior_position_or_None, match_status)
inv.add_position(position_or_posting) -> (prior_position_or_None, match_status)
inv.add_inventory(other) -> Inventory
```

Adding an amount with an existing identical lot augments or reduces that lot. If the resulting unit number is zero, the lot is removed. Adding a zero amount for a missing lot is ignored. `add_amount()` and `add_position()` report the prior matching position, if any, and a status indicating whether a lot was created, reduced, augmented, or ignored. `bool(inv)` is intentionally unsupported; use `is_empty()`.

`reduce()` maps every position through a conversion function and accumulates the resulting amounts into a new inventory. `average()` groups lots by unit currency and cost currency, computes total units, skips groups that net to zero, and uses the minimum lot date from the group when an averaged cost is present.

### Prices and Conversions

`build_price_map(entries) -> PriceMap` builds a dictionary from `Price` directives. Keys are `(base_currency, quote_currency)` pairs; values are sorted lists of `(date, rate)` pairs. For duplicate prices on the same date and pair, the later directive for that date is kept. Inverse pairs are generated automatically. If both directions are present in the input, the direction with fewer price points is inverted into the direction with more price points. `PriceMap.forward_pairs` lists the original forward keys retained before automatic inverses were added.

`get_latest_price(price_map, base_quote)` returns `(date, rate)` for the latest available price, or `(None, None)` if unavailable. `get_price(price_map, base_quote, date=None)` returns the latest price on or before `date`, or the latest price when `date` is omitted. A pair may be passed as `("HOOL", "USD")` or as `"HOOL/USD"`. A currency priced into itself, or a quote currency of `None`, returns `(None, Decimal("1"))`.

Conversion helpers work on `Position` and `Posting` objects:

```python
get_units(pos) -> Amount
get_cost(pos) -> Amount
get_weight(pos) -> Amount
get_value(pos, price_map, date=None, output_date_prices=None) -> Amount
convert_position(pos, target_currency, price_map, date=None) -> Amount
convert_amount(amount, target_currency, price_map, date=None, via=None) -> Amount
```

`get_cost()` returns total cost when a concrete cost is present and otherwise returns units. `get_weight()` returns the amount used to balance a posting: concrete cost takes precedence, otherwise units are used, except that a posting price without a cost produces a weight in the price currency. `get_value()` infers a value currency from cost or posting price, looks up a price, and returns converted value when available; if no conversion can be made, it returns the original units. `convert_amount()` first tries a direct price; if `via` currencies are provided, it may synthesize a two-step conversion. Failed conversions return the original amount unchanged.

### Realized Accounts

`RealAccount(account_name)` is a dictionary-like account-tree node. It has:

- `account`: full account name for this node.
- `txn_postings`: postings or account-attached directives associated with this exact account.
- `balance`: final `Inventory` for this exact account's postings.

Child keys must be non-empty strings, child values must be `RealAccount` instances, and a child node's full account name must end with its dictionary key.

`realize(entries, min_accounts=None, compute_balance=True) -> RealAccount` converts a flat directive list into a tree rooted at an empty account name. Transactions are represented in account nodes as `TxnPosting(txn, posting)` pairs, one per posting. Account-attached directives such as open, close, balance, note, and document are stored in the corresponding account. Pad directives are stored on both the padded account and the source account. When `compute_balance` is true, each node's `balance` is computed from postings directly attached to that account, not from child nodes. `min_accounts` ensures named accounts exist even if no postings refer to them.

### Account and Entry Getters

`get_accounts(entries) -> set[str]` returns all accounts referenced by the directive list. Transaction postings contribute their posting accounts; pad directives contribute both accounts; directives attached to one account contribute that account.

`get_account_open_close(entries)` returns a dictionary mapping account names to `[open_directive_or_None, close_directive_or_None]`. If duplicate open or close directives are present for an account, the earliest one is kept for that slot.

### Printing

`format_entry(entry, dcontext=None, render_weights=False, prefix=None, write_source=False) -> str` renders a directive back into Beancount syntax. Metadata keys `filename`, `lineno`, and keys beginning with `__` are not emitted as normal metadata. Tags and links render in sorted order. When `write_source` is true, a source-location comment is emitted before the directive.

`print_entry(entry, dcontext=None, render_weights=False, file=None, write_source=False)` writes one formatted directive and a trailing blank line to a file-like object or standard output.

`print_entries(entries, dcontext=None, render_weights=False, file=None, prefix=None, write_source=False)` writes a list of directives. It inserts blank lines between transactions and between blocks of different directive types. The function requires `entries` to be a list.

Formatting is meant to produce valid Beancount syntax for public directive objects. It is not a guarantee that user comments and original file layout survive a parse-and-print round trip.

## Behavioral Sections

### Ledger Loading and Validation

A load produces a single date-sorted directive stream from a top-level file and its includes. Include paths are resolved relative to the file containing the include directive unless they are absolute. Duplicate included filenames are not parsed again and produce a load error. Include globs that match no files produce a load error.

After parsing, the loader books incomplete transactions, applies plugins and standard transformations according to `plugin_processing_mode`, validates the resulting entries, computes an input hash over parsed files, and returns all accumulated errors instead of raising for normal ledger problems.

Balance assertions apply at the beginning of their date. This means a balance directive on a date is ordered before transactions on the same date. Open directives sort before other same-day directives, document directives sort after transactions, and close directives sort last on the same date.

### Ledger Syntax Objects

Open directives define account lifecycle and optional currency/booking restrictions. Close directives end an account lifecycle. Commodity directives are optional declarations used primarily for commodity metadata. Pad directives request automatic padding transactions so that a later balance assertion can succeed. Balance directives record expected units, tolerance, and a difference amount when checking fails. Transactions carry a flag, optional payee, narration, tags, links, and posting legs. Notes and documents attach dated information to accounts. Events record dated values for arbitrary named variables. Price directives add dated exchange or commodity prices. Custom directives carry plugin-facing dated values.

Transaction postings may omit units during parsing so booking can infer them. A posting may carry a concrete lot cost, an incomplete cost spec before booking, a price, an optional posting flag, and posting-level metadata.

### Account Names and Account Types

Account names use colon-separated components. The default account roots are `Assets`, `Liabilities`, `Equity`, `Income`, and `Expenses`; these roots can be renamed by options near the beginning of the file. The configured roots determine parsing, account classification, normal signs, and account sort order.

Assets and liabilities and equity are balance-sheet accounts. Income and expenses are income-statement accounts. Liabilities, income, and equity are inverted for external-report sign purposes. Assets and expenses have normal sign `+1`; the other roots have normal sign `-1`.

### Inventories and Balances

Inventories preserve lot identity by unit currency and cost. Multiple positions with the same key aggregate into a single lot. Lots with a zero resulting unit quantity are removed rather than retained as zero positions. Mixed inventories are inventories containing both positive and negative lots for the same unit currency.

Realized account balances are expressed as inventories. A child account's postings do not automatically appear in the parent's `txn_postings`; callers that want a subtree balance should combine child balances or traverse the tree.

### Prices and Market Value

Price directives create a date-indexed price database. Lookups are as-of lookups: for a requested date, Beancount returns the latest price whose date is not after the request. A missing price is not an exception for `get_price()`, `get_latest_price()`, or conversion helpers; the public behavior is a `(None, None)` lookup result or an unchanged amount/units result.

Posting weights and market values are distinct. Weight is used to decide whether a transaction balances. Market value is a valuation view computed from a price map.

### Plugins and Transformations

Plugins are part of the public extension model. They transform a directive stream and may add errors. Default loader mode runs standard document, padding, and balance processing around user plugins. Raw mode gives callers explicit control over the plugin list and ordering.

When a user enables the `--auto` flag for `bean-check`, Beancount temporarily enables the standard auto plugin set for that command invocation.

### Command-Line Tools

`bean-check FILENAME` parses, books, transforms, and validates a ledger. It exits with status 0 when no errors are returned and status 1 when errors exist. `--json` writes a JSON object with an `errors` list containing message, filename, and line number. `--verbose` enables timing/logging output. `--no-cache` disables the load cache. `--cache-filename` overrides the cache filename pattern. `--auto` implicitly enables auto plugins while checking.

`bean-doctor` is a diagnostic command group. It provides commands to inspect lexing/parsing, round-trip printed output, validate document/account directory hierarchies, list available options, print parsed options, show context at a file location, find linked or tagged transactions, inspect a file region and balances, print missing open directives, and display inferred display precision. In the command group, subcommand lookup accepts hyphen and underscore variants and documented aliases.

`bean-example` writes a realistic generated ledger. It supports begin date, end date, fictional birth date, random seed, disabling reformatting, output file, and verbose logging. By default it writes to standard output and formats the generated ledger.

`bean-format` reformats Beancount input by aligning numbers and currencies. It uses text matching rather than a parse-and-print cycle, so the intended effect is whitespace-only alignment while preserving comments and file structure. It can write to standard output, a specified output file for a single input, or edit one or more files in place. Alignment may be controlled by prefix width, number width, or fixed currency column.

`treeify` is a standalone text tool for replacing a column of hierarchical names with an ASCII tree. It can read from a file or standard input, write to a file or standard output, choose account-like, loose-account, filename, or custom patterns, and customize delimiters, split regex, and filler text.

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

## Non-Goals

- Beancount does not provide a database server, hosted service, or network-backed accounting system in this surface.
- This specification does not cover web UI behavior, report-rendering projects split out of Beancount v3, ingestion frameworks outside the installed package surface, or deprecated v1/v2 command suites.
- The public contract does not require preserving comments or exact original layout through `load_file()` followed by `print_entries()`; use `bean-format` for whitespace-only source formatting.
- The public contract does not expose private parser extension modules, generated grammar internals, private display-context internals, or test-only comparison helpers.
- Price lookup is date-based, not time-of-day based, and does not synthesize intraday or day-trading semantics.
- Failed market conversion does not invent prices, raise by default, or silently drop the original units; it returns the unchanged amount or units.
- Inventory objects are not immutable. Directive objects are immutable tuple-like records, but inventories intentionally mutate when positions are added.
- Command-line tools are not required to fetch live prices or contact external services for the covered behavior.

## Evaluation Notes

Evaluation focuses on public behavior observable from the documented package surface. Tests may construct public directive objects, load small Beancount ledgers, inspect returned entries/errors/options, realize account trees, build price maps, reduce inventories, format directives, and invoke the installed command-line tools.

The expected implementation should preserve the relationships among views: loader output, account getters, inventories, realized trees, price maps, printed syntax, plugin errors, and CLI status/output should all be derived from the same ledger facts. Scoring rewards correct behavior across those projections rather than matching a particular internal organization.

Tests may cover edge cases such as include resolution, same-day directive ordering, duplicate price dates, missing price conversions, zero inventory lots, configured root account names, plugin failures, JSON check output, and formatter argument combinations. They do not require private module names, private parser internals, hidden fixture layouts, or network access.
