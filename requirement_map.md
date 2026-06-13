# Actual Budget Mini Finance Task Requirement Map

Date: 2026-06-11

Task folder: `actual-budget-realrepo-001`

PRD: `prd.md`

Rubric: `rubric.json`

## 1. Public Requirements

| ID                      | Capability                             | PRD Section                            | Observable Behavior                                                                                         |
| ----------------------- | -------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `REQ-feature-set`       | Bounded personal finance feature set   | Feature Set                            | Product includes accounts, transactions, categories, budgets, reports, schedules, rules, and error handling |
| `REQ-account`           | Account management                     | Account Management                     | User can create accounts, view account information, and check account balance                               |
| `REQ-transaction`       | Transaction management                 | Transaction Management                 | User can add, edit, delete, and view income or expense transactions                                         |
| `REQ-category`          | Category and category group management | Category and Category Group Management | User can create category groups and categories, and assign transactions to categories                       |
| `REQ-budget`            | Monthly budget management              | Monthly Budget Management              | User can set monthly category budgets and view budgeted, spent, and balance values                          |
| `REQ-report`            | Report management                      | Report Management                      | Reports show income, expenses, net worth, cash flow, and budget summary based on current data               |
| `REQ-schedule`          | Scheduled transaction management       | Scheduled Transaction Management       | User can create repeated transaction schedules and use them to generate real transactions                   |
| `REQ-rule`              | Rule-based transaction automation      | Rule-Based Transaction Automation      | User can create rules that update matching transactions automatically                                       |
| `REQ-payee-tag`         | Payee and tag management               | Payee and Tag Management               | User can reuse payees, assign tags, and use payees in rules                                                 |
| `REQ-atomic`            | Error handling and state consistency   | Error Handling and State Consistency   | Invalid operations fail without creating partial data or changing existing financial state                  |
| `REQ-global-invariants` | Cross-module financial consistency     | Global Invariants                      | Account balance, category spending, budget balance, and report values remain consistent                     |
| `REQ-unit-eval`         | Unit testing definition                | Evaluation Style                       | Unit tests check one feature module at a time                                                               |
| `REQ-system-eval`       | System testing definition              | Evaluation Style                       | System tests check workflows across multiple modules and use system dimension labels                        |

## 2. Unit Coverage

| Test     | Feature        | Requirement refs                                | Public basis                                                     |
| -------- | -------------- | ----------------------------------------------- | ---------------------------------------------------------------- |
| `SQU001` | account        | `REQ-account`                                   | Create a new account with zero initial balance                   |
| `SQU002` | account        | `REQ-account`                                   | Rename an existing account and keep its balance unchanged        |
| `SQU003` | transaction    | `REQ-transaction`, `REQ-account`                | Add an expense transaction under an account                      |
| `SQU004` | transaction    | `REQ-transaction`, `REQ-account`                | Add an income transaction under an account                       |
| `SQU005` | transaction    | `REQ-transaction`                               | Edit an existing transaction amount                              |
| `SQU006` | transaction    | `REQ-transaction`                               | Delete an existing transaction                                   |
| `SQU007` | category       | `REQ-category`                                  | Create a category group and a category under it                  |
| `SQU008` | category       | `REQ-category`, `REQ-transaction`               | Assign a transaction to a category                               |
| `SQU009` | budget         | `REQ-budget`, `REQ-category`                    | Set a monthly budget amount for a category                       |
| `SQU010` | budget         | `REQ-budget`, `REQ-transaction`, `REQ-category` | Calculate spent and balance values for a category                |
| `SQU011` | report         | `REQ-report`, `REQ-account`, `REQ-transaction`  | Generate a simple report with total income and total expenses    |
| `SQU012` | report         | `REQ-report`                                    | Calculate net worth from account balances                        |
| `SQU013` | schedule       | `REQ-schedule`                                  | Create a scheduled transaction with repeat information           |
| `SQU014` | rule           | `REQ-rule`, `REQ-payee-tag`                     | Create a rule that sets category based on payee                  |
| `SQU015` | payee/tag      | `REQ-payee-tag`, `REQ-transaction`              | Reuse a payee and assign a tag to a transaction                  |
| `SQU016` | error handling | `REQ-atomic`, `REQ-transaction`                 | Reject a transaction without an account and keep state unchanged |

Unit requirement coverage:

* `REQ-account`: covered by `SQU001`, `SQU002`, `SQU003`, `SQU004`
* `REQ-transaction`: covered by `SQU003`, `SQU004`, `SQU005`, `SQU006`, `SQU008`, `SQU015`, `SQU016`
* `REQ-category`: covered by `SQU007`, `SQU008`, `SQU010`
* `REQ-budget`: covered by `SQU009`, `SQU010`
* `REQ-report`: covered by `SQU011`, `SQU012`
* `REQ-schedule`: covered by `SQU013`
* `REQ-rule`: covered by `SQU014`
* `REQ-payee-tag`: covered by `SQU014`, `SQU015`
* `REQ-atomic`: covered by `SQU016`

## 3. System Coverage

| Test     | System Dimension              | Crossed Modules                                                   | Requirement refs                                                                                      | Public basis                                                                                            |
| -------- | ----------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `SQS001` | `cross_feature_dataflow`      | account → transaction → balance                                   | `REQ-account`, `REQ-transaction`, `REQ-global-invariants`                                             | Adding a transaction under an account should update the account balance                                 |
| `SQS002` | `cross_feature_dataflow`      | transaction → category → budget                                   | `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-global-invariants`                              | A categorized expense should update category spent and budget balance                                   |
| `SQS003` | `cross_feature_dataflow`      | transaction → report                                              | `REQ-transaction`, `REQ-report`, `REQ-global-invariants`                                              | A transaction should be reflected in total income, total expenses, and net worth                        |
| `SQS004` | `state_accumulation`          | account → multiple transactions → budget → report                 | `REQ-account`, `REQ-transaction`, `REQ-budget`, `REQ-report`                                          | Multiple expenses should accumulate correctly in account, budget, and report values                     |
| `SQS005` | `state_accumulation`          | budget → repeated expenses → remaining balance                    | `REQ-budget`, `REQ-transaction`, `REQ-category`                                                       | Several expenses under the same category should reduce the remaining budget correctly                   |
| `SQS006` | `global_invariant`            | account → transaction → category → budget → report                | `REQ-account`, `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-report`, `REQ-global-invariants` | Account balance, category spending, budget balance, and report totals should agree                      |
| `SQS007` | `global_invariant`            | transaction edit → balance/budget/report refresh                  | `REQ-transaction`, `REQ-account`, `REQ-budget`, `REQ-report`, `REQ-global-invariants`                 | Editing a transaction amount should update all dependent values                                         |
| `SQS008` | `error_atomicity`             | invalid transaction → unchanged account/budget/report             | `REQ-transaction`, `REQ-account`, `REQ-budget`, `REQ-report`, `REQ-atomic`                            | A transaction without an account should fail and should not change any financial data                   |
| `SQS009` | `error_atomicity`             | invalid category assignment → unchanged transaction/budget/report | `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-report`, `REQ-atomic`                           | Assigning a missing category should fail without changing existing state                                |
| `SQS010` | `operation_order_sensitivity` | rule → new transaction → category → budget → report               | `REQ-rule`, `REQ-payee-tag`, `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-report`            | A rule created before a transaction should automatically categorize the matching transaction            |
| `SQS011` | `operation_order_sensitivity` | transaction → rule → existing transaction update → budget/report  | `REQ-rule`, `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-report`                             | A rule created after a transaction should be able to update existing matching transactions              |
| `SQS012` | `boundary_crossing`           | schedule → transaction → account → budget → report                | `REQ-schedule`, `REQ-transaction`, `REQ-account`, `REQ-budget`, `REQ-report`                          | A scheduled transaction should behave like a normal transaction after it is generated                   |
| `SQS013` | `boundary_crossing`           | schedule → rule → transaction → category → budget → report        | `REQ-schedule`, `REQ-rule`, `REQ-transaction`, `REQ-category`, `REQ-budget`, `REQ-report`             | A generated scheduled transaction should also be processed by rules and reflected in budget and reports |
| `SQS014` | `global_invariant`            | transaction delete → account/budget/report refresh                | `REQ-transaction`, `REQ-account`, `REQ-budget`, `REQ-report`, `REQ-global-invariants`                 | Deleting a transaction should remove its effect from balance, budget, and reports                       |

System requirement coverage:

* `REQ-account`: covered by `SQS001`, `SQS004`, `SQS006`, `SQS007`, `SQS008`, `SQS012`, `SQS014`
* `REQ-transaction`: covered by all system tests from `SQS001` to `SQS014`
* `REQ-category`: covered by `SQS002`, `SQS006`, `SQS009`, `SQS010`, `SQS011`, `SQS013`
* `REQ-budget`: covered by `SQS002`, `SQS004`, `SQS005`, `SQS006`, `SQS007`, `SQS008`, `SQS009`, `SQS010`, `SQS011`, `SQS012`, `SQS013`, `SQS014`
* `REQ-report`: covered by `SQS003`, `SQS004`, `SQS006`, `SQS007`, `SQS008`, `SQS009`, `SQS010`, `SQS011`, `SQS012`, `SQS013`, `SQS014`
* `REQ-schedule`: covered by `SQS012`, `SQS013`
* `REQ-rule`: covered by `SQS010`, `SQS011`, `SQS013`
* `REQ-payee-tag`: covered by `SQS010`, `SQS011`, `SQS013`
* `REQ-atomic`: covered by `SQS008`, `SQS009`
* `REQ-global-invariants`: covered by `SQS001`, `SQS002`, `SQS003`, `SQS006`, `SQS007`, `SQS014`

## 4. System Dimension Coverage

| System Dimension              | Test Cases                   | Meaning in this task                                                                   |
| ----------------------------- | ---------------------------- | -------------------------------------------------------------------------------------- |
| `cross_feature_dataflow`      | `SQS001`, `SQS002`, `SQS003` | Checks whether data from one module correctly flows into another module                |
| `state_accumulation`          | `SQS004`, `SQS005`           | Checks whether repeated transactions accumulate correctly over time                    |
| `global_invariant`            | `SQS006`, `SQS007`, `SQS014` | Checks whether account, budget, category, and report values stay consistent            |
| `error_atomicity`             | `SQS008`, `SQS009`           | Checks whether failed operations leave no partial changes                              |
| `operation_order_sensitivity` | `SQS010`, `SQS011`           | Checks whether rule behavior works correctly under different operation orders          |
| `boundary_crossing`           | `SQS012`, `SQS013`           | Checks workflows that cross schedule, rule, transaction, budget, and report boundaries |

## 5. Notes on Unit and System Difference

The unit tests mainly check whether each single module works.

For example:

```text
create account
add transaction
create category
set budget
generate report
create rule
create schedule
```

These functions may be implemented correctly one by one.

The system tests check whether these modules still work correctly after they are connected.

For example:

```text
create account
→ add transaction
→ assign category
→ update budget
→ update report
```

This is harder because the same transaction affects several different parts of the system.

This task is expected to show a gap between unit-level correctness and system-level correctness. A model may pass many unit tests, but still fail when financial data must stay consistent across accounts, categories, budgets, reports, schedules, and rules.

## 6. Reference and Model Verification Plan

The final benchmark should include at least three score reports:

| Solution                  | Expected Role                                    | Report File                                  |
| ------------------------- | ------------------------------------------------ | -------------------------------------------- |
| Reference implementation  | Correct implementation used to verify the rubric | `score_report_reference_unit_system_v1.json` |
| Model or agent solution 1 | First tested model or agent                      | `score_report_model_001_unit_system_v1.json` |
| Model or agent solution 2 | Second tested model or agent                     | `score_report_model_002_unit_system_v1.json` |

The reference implementation should ideally pass all unit and system tests.

Model or agent implementations are expected to show a possible unit-system gap.
