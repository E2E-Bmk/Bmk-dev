# Source Repository

## 1. Repository Information

Repository Name: Actual Budget

Repository URL:

```text
https://github.com/actualbudget/actual
```

Project Type:

```text
Open-source personal finance and budgeting application
```

Benchmark Folder Name:

```text
actual-budget-realrepo-001
```

## 2. Project Background

Actual Budget is an open-source personal finance and budgeting application. It is designed as a local-first finance tool, which means users can manage their financial data mainly on their own device. It also supports synchronization when a server is configured, so users can move changes between different devices.

The project is written in NodeJS and provides local-only desktop apps for Windows, Mac, and Linux. It can also be deployed through different hosting methods, such as Docker or managed hosting.

From the user side, Actual Budget is mainly used for:

* managing financial accounts
* recording income and expenses
* organizing transactions by categories
* setting budgets
* viewing reports
* creating schedules for recurring transactions
* using rules to automatically process transactions

## 3. Source Signals

The repository README and the local application interface show that Actual Budget is not just a simple expense recorder. It contains several connected modules.

The main modules observed in the project include:

* Budget
* Reports
* Schedules
* Payees
* Rules
* Tags
* Settings
* Accounts
* Transactions
* Categories and category groups

These modules are connected through financial data. For example, when a user creates an account and adds an expense transaction, the transaction changes the account balance. If the transaction has a category, it also changes the budget page and the report page.

A simplified core workflow can be described as:

```text
Account → Transaction → Category → Budget → Report
```

Two more advanced workflows are:

```text
Rule → Transaction → Category → Budget → Report
```

and:

```text
Schedule → Transaction → Budget → Report
```

## 4. Benchmark Adaptation

This benchmark does not try to rebuild the full Actual Budget product. The original project is much larger and includes many features that are not necessary for a first E2E benchmark case.

Instead, this benchmark extracts a smaller but still realistic personal finance task from the original project.

The selected task focuses on:

1. Account management
2. Transaction management
3. Category and category group management
4. Monthly budget management
5. Report generation
6. Scheduled transactions
7. Rule-based transaction automation
8. Error handling and state consistency

The goal is to test whether a model can build a system where financial data stays consistent across different modules.

## 5. Why This Repository Is Suitable

Actual Budget is suitable for an E2E benchmark because its core functions are strongly connected.

A model may be able to implement each function separately, such as:

* creating an account
* adding a transaction
* creating a category
* setting a budget
* generating a report

However, the harder part is making these functions work together.

For example:

```text
Add transaction
→ update account balance
→ update category spending
→ update budget balance
→ update report data
```

If only the transaction is stored but the budget or report is not updated, then the unit-level function may look correct, but the system-level behavior is wrong.

This makes Actual Budget useful for measuring the gap between unit-level correctness and system-level correctness.

## 6. Selected Benchmark Scope

The benchmark task will use a simplified version of Actual Budget.

The selected scope includes:

| Module          | Included in Benchmark | Reason                                                     |
| --------------- | --------------------- | ---------------------------------------------------------- |
| Account         | Yes                   | It is the base of financial state.                         |
| Transaction     | Yes                   | It is the main data source.                                |
| Category        | Yes                   | It connects transactions with budget and reports.          |
| Budget          | Yes                   | It checks whether spending is calculated correctly.        |
| Report          | Yes                   | It checks whether summary data is consistent.              |
| Schedule        | Yes                   | It creates system-level workflows over time.               |
| Rule            | Yes                   | It tests automatic transaction processing.                 |
| Payee           | Partly                | It is mainly used inside transactions and rules.           |
| Tags            | Partly                | It is a helper feature, not the core of the first version. |
| Settings        | No                    | It is not central to the first benchmark task.             |
| Synchronization | No                    | It is outside the first version scope.                     |
| Full UI         | No                    | The benchmark focuses on data behavior, not UI details.    |

## 7. Expected Evaluation Value

This repository can help evaluate whether a model only finishes isolated features or can also maintain correct system behavior.

Possible system-level failures include:

* account balance updates but report data does not update
* transaction category changes but budget data stays old
* rule applies to a transaction but category spending is not recalculated
* schedule creates a transaction but the account balance is not updated
* failed transaction creation leaves partial data
* reports show values inconsistent with accounts or budgets

These failures are exactly the type of problems that an E2E benchmark should expose.
