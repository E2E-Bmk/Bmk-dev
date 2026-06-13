# Actual Budget Mini Finance Task PRD

## 1. Background

This task is based on Actual Budget, an open-source personal finance and budgeting application. Actual Budget is designed as a local-first finance tool. It can be used on a local device, and it can also support synchronization between devices when a server is configured.

The original Actual Budget project is a complete product. This benchmark does not try to rebuild every function of the original project. Instead, it selects several core functions that are common in personal finance management and suitable for testing.

The main workflow of this simplified task is:

```text
Account → Transaction → Category → Budget → Report
```

Besides this basic workflow, this task also includes two more advanced workflows:

```text
Rule → Transaction → Category → Budget → Report
```

and:

```text
Schedule → Transaction → Budget → Report
```

These workflows are useful because one financial operation usually affects several parts of the system. For example, after a user adds an expense transaction, the account balance, category spending, budget balance, and report data should all be updated.

## 2. Product Goal

The goal of this task is to build a simplified personal finance system.

The system should allow users to manage accounts, record income and expenses, organize transactions by categories, set monthly budgets, view reports, create scheduled transactions, and use rules to automatically process transactions.

The most important requirement is state consistency. The system should not only make each function work separately, but also keep the whole financial state correct after several operations.

## 3. Feature Set

This task contains the following modules:

1. Account Management
2. Transaction Management
3. Category and Category Group Management
4. Monthly Budget Management
5. Report Management
6. Scheduled Transaction Management
7. Rule-Based Transaction Automation
8. Payee and Tag Management
9. Error Handling and State Consistency

## 4. Requirements

### 4.1 Account Management

The system should support basic account management.

Each account should include:

* account id
* account name
* account type
* current balance
* budget status, such as on-budget or off-budget

The user should be able to:

* create an account
* rename an account
* view account information
* view account balance
* view transactions under an account

The account balance should be calculated from the transactions linked to this account.

For example, if an account has one expense of `60.00` and no income, its balance should be `-60.00`.

When an account is renamed, existing transactions linked to this account should still be linked to the renamed account. The account balance should also remain correct after the rename operation.

### 4.2 Transaction Management

The system should support adding, editing, deleting, and viewing transactions.

Each transaction should include:

* transaction id
* date
* account
* payee
* notes
* category
* payment amount
* deposit amount
* tags

A transaction can be an expense or an income.

* `Payment` means money goes out.
* `Deposit` means money comes in.

A transaction should not have both payment and deposit greater than `0`. If both fields are greater than `0`, the operation should be rejected.

The user should be able to:

* add an expense transaction
* add an income transaction
* edit a transaction
* delete a transaction
* search or filter transactions
* link a transaction to an account
* link a transaction to a category
* link a transaction to a payee
* assign tags to a transaction

When a transaction changes, related account balances, budget values, and reports should also change.

### 4.3 Category and Category Group Management

The system should support category groups and categories.

A category group contains several categories. For example:

```text
Usual Expenses
  - Food
  - Transport
  - General
  - Bills

Investments and Savings
  - Savings

Income
  - Income
  - Starting Balances
```

The user should be able to:

* create a category group
* rename a category group
* create a category under a group
* rename a category
* assign a transaction to a category
* view spending by category

If a transaction is assigned to a category, the spending of that category should be updated in budgets and reports.

For example, if a user adds a `Food` expense of `60.00`, the `Food` category should show that `60.00` has been spent in that month.

When a category is renamed, related transactions and budgets should still point to the renamed category. Category spending, budget balance, and report data should remain consistent after the rename operation.

### 4.4 Monthly Budget Management

The system should support monthly budgeting.

The budget data should be grouped by month. It should include:

* budgeted amount
* spent amount
* balance
* category-level budget data

The main budget table should include:

```text
Category | Budgeted | Spent | Balance
```

The user should be able to:

* view the budget of a given month
* set a budget amount for a category
* view how much has been spent in each category
* view the remaining balance of each category
* see whether a category is overspent

The basic calculation is:

```text
Balance = Budgeted Amount - Spent Amount
```

If the user sets `0.00` as the budget for Food and spends `60.00`, then the Food balance should become `-60.00`.

The budget data should update when a related transaction is added, edited, deleted, or moved to another category.

Income transactions should be counted as income in reports. They should not be counted as category spending unless they are explicitly assigned to an income category.

### 4.5 Report Management

The system should support reports based on account and transaction data.

The report module should be able to show:

* total income
* total expenses
* average per month
* average per transaction
* net worth
* cash flow
* budget overview

Report values should be calculated from current system data.

For example, if the system has only one expense transaction of `60.00`, then the report should show total expenses as `60.00`. The account balance and net worth should also reflect this expense.

Reports should stay consistent with accounts, transactions, categories, and budgets.

The report command should calculate values from the current stored data. It should not rely on stale report values saved from earlier commands.

Reports may appear in the state output, but these report values should be recalculated from the current data when `report` or `state` is called. If a transaction, category, budget, rule, or schedule changes, the report output should reflect the latest state.

### 4.6 Scheduled Transaction Management

The system should support scheduled transactions.

A scheduled transaction is used for financial activities that happen repeatedly, such as salary, rent, phone bills, or subscriptions.

Each schedule should include:

* schedule id
* schedule name
* payee
* account
* category
* amount
* direction, such as payment or deposit
* repeat setting
* day of month
* whether it can generate a real transaction

The user should be able to:

* create a schedule
* choose whether it repeats
* set a repeat date, such as every month on a certain day
* generate a transaction from a schedule
* link the generated transaction to the schedule

When a schedule creates a real transaction, that transaction should affect account balance, budget, and reports in the same way as a normal transaction.

### 4.7 Rule-Based Transaction Automation

The system should support rules for automatically processing transactions.

A rule contains conditions and actions.

For example:

```text
Condition:
payee is Starbucks

Action:
set category to Food
```

The user should be able to:

* create a rule
* define one or more conditions
* define one or more actions
* apply the rule to matching transactions
* apply rules to existing transactions
* apply rules to new transactions

Rules may update fields such as:

* category
* payee
* notes
* tags
* account

For the first version, rules must at least support setting a transaction category by matching its payee. Other rule actions are optional.

Rules are important because they connect several modules together. If a rule changes the category of a transaction, the category spending, budget balance, and reports should also be updated.

For example:

```text
Rule: payee is Starbucks → category is Food
Transaction: Starbucks expense 30.00
Expected result:
- the transaction category becomes Food
- Food spending increases by 30.00
- the budget balance changes
- the report data changes
```

### 4.8 Payee and Tag Management

The system should support payees and tags as helper information for transactions.

A payee means the person, store, or source related to a transaction.

Examples:

```text
Family
Canteen
Starbucks
China Mobile
Landlord
```

The user should be able to:

* create or reuse a payee
* search transactions by payee
* use payee information in rules

Tags are optional labels for transactions. They can be used for extra organization.

Examples:

```text
travel
reimbursement
school project
temporary expense
```

Tags are not the main part of budget calculation, but adding tags should not affect the correctness of transactions, budgets, or reports.

### 4.9 Error Handling and State Consistency

The system should reject invalid operations and keep existing data safe.

Invalid operations may include:

* adding a transaction without an account
* adding a transaction with an invalid amount
* adding a transaction with both payment and deposit greater than `0`
* assigning a transaction to a missing category
* creating a budget for a missing category
* creating a schedule without required fields
* creating a rule with an invalid action
* importing invalid transaction data

When an operation fails, the system should:

* show a clear error message
* not create partial data
* not change account balance
* not change category spending
* not change budget balance
* not change report values

For example, if the user tries to add a transaction without choosing an account, the system should reject it. No transaction should be created, and the account balance should stay the same.

## 5. Global Invariants

The following rules should always hold.

### GI-001 Account Balance

For each account:

```text
Account Balance = Total Deposits - Total Payments
```

Only transactions linked to this account should affect its balance.

### GI-002 Category Spending

For each category and month:

```text
Category Spending = Sum of all payment transactions in this category during this month
```

If a transaction is moved to another category, the old category and the new category should both update correctly.

Deposit transactions should be counted as income in reports. They should not be counted as category spending unless they are explicitly assigned to an income category.

### GI-003 Budget Balance

For each category and month:

```text
Budget Balance = Budgeted Amount - Spent Amount
```

If spending is larger than the budgeted amount, the balance should be negative.

### GI-004 Report Consistency

Reports should use the same data as accounts, transactions, categories, and budgets.

For example, if there is only one expense of `60.00`, then these values should match:

```text
Account balance = -60.00
Category spending = 60.00
Total expenses = 60.00
Net worth = -60.00
```

### GI-005 Rule Propagation

If a rule changes a transaction, all related modules should update.

For example:

```text
Rule changes category
→ transaction category changes
→ category spending changes
→ budget changes
→ reports change
```

### GI-006 Schedule Propagation

If a schedule creates a transaction, the generated transaction should work like a normal transaction.

It should affect:

* account balance
* category spending
* budget balance
* reports

### GI-007 Failed Operation Safety

A failed operation should not leave partial changes.

For example:

```text
failed transaction creation
→ no new transaction
→ no balance change
→ no budget change
→ no report change
```

## 6. Implementation Interface

The implementation should be a Python command-line program named:

```text
budgetmini.py
```

The program should store all data in a JSON file. The first command-line argument should be the data file path.

The general command format should be:

```bash
python budgetmini.py <data_file> <command> [options]
```

For example:

```bash
python budgetmini.py data.json create-account --name Cash --type checking --on-budget
```

Each command should:

1. read the JSON data file;
2. perform the requested operation;
3. update related financial state if needed;
4. save the JSON data file;
5. print a simple result to standard output.

If the data file does not exist, the program should create a new empty financial state.

### 6.1 Data Storage

The JSON data file should store at least the following information:

```text
accounts
transactions
category_groups
categories
budgets
rules
schedules
payees
tags
```

The exact internal JSON structure can be chosen by the implementer, but the program must provide stable command behavior and stable output for evaluation.

The system should be able to recalculate account balances, budget values, and report values from transaction data.

### 6.2 Required Commands

The program should support the following commands.

#### Account Commands

```bash
create-account
rename-account
list-accounts
```

Example:

```bash
python budgetmini.py data.json create-account --name Cash --type checking --on-budget
python budgetmini.py data.json rename-account --old Cash --new "Wechat Pay"
python budgetmini.py data.json list-accounts
```

When `rename-account` is used, transactions that were linked to the old account name should still be linked to the renamed account.

#### Category Commands

```bash
create-category-group
rename-category-group
create-category
rename-category
```

Example:

```bash
python budgetmini.py data.json create-category-group --name "Usual Expenses"
python budgetmini.py data.json create-category --group "Usual Expenses" --name Food
python budgetmini.py data.json rename-category --old Food --new Meals
```

When `rename-category` is used, related transactions and budgets should still be linked to the renamed category.

#### Budget Commands

```bash
set-budget
show-budget
```

Example:

```bash
python budgetmini.py data.json set-budget --month 2026-06 --category Food --amount 100
python budgetmini.py data.json show-budget --month 2026-06
```

#### Transaction Commands

```bash
add-transaction
edit-transaction
delete-transaction
assign-category
list-transactions
```

Example:

```bash
python budgetmini.py data.json add-transaction --id tx1 --date 2026-06-10 --account Cash --payee Canteen --category Food --payment 60 --deposit 0
python budgetmini.py data.json edit-transaction --id tx1 --payment 80
python budgetmini.py data.json delete-transaction --id tx1
python budgetmini.py data.json assign-category --transaction tx1 --category Food
python budgetmini.py data.json list-transactions
```

The `list-transactions` command should support optional filters such as:

```bash
--account
--category
--payee
--month
```

Example:

```bash
python budgetmini.py data.json list-transactions --category Food --month 2026-06
```

A transaction should not have both `--payment` and `--deposit` greater than `0`. If this happens, the command should fail and the state should stay unchanged.

#### Report Commands

```bash
report
state
```

The `report` command should output report data for a given month.

Example:

```bash
python budgetmini.py data.json report --month 2026-06
```

The `report` command should calculate values from the latest stored data every time it is called.

The `state` command should output the full current system state as JSON. This command is mainly used to inspect the system and check whether the state is correct.

The `state` command should include at least:

```text
accounts
transactions
category_groups
categories
budgets
rules
schedules
reports
payees
tags
```

Example:

```bash
python budgetmini.py data.json state
```

The `reports` field in the state output may be included for convenience, but it should reflect the latest calculated report values.

#### Rule Commands

```bash
create-rule
apply-rules
```

For the first version, rule commands must at least support this pattern:

```text
if payee equals <value>, then set category to <category>
```

Example:

```bash
python budgetmini.py data.json create-rule --name "Starbucks to Food" --field payee --equals Starbucks --set-category Food
python budgetmini.py data.json apply-rules
```

If a matching transaction exists, applying rules should update the transaction category and recalculate related budget and report values.

#### Schedule Commands

```bash
create-schedule
generate-scheduled-transaction
```

Example:

```bash
python budgetmini.py data.json create-schedule --name "Phone Bill" --payee "China Mobile" --account "Bank Card" --category Bills --amount 30 --direction payment --repeat monthly --day 15
python budgetmini.py data.json generate-scheduled-transaction --schedule "Phone Bill" --date 2026-06-15 --id tx1
```

The generated transaction should use the account, payee, category, amount, and direction stored in the schedule.

#### Tag Commands

```bash
assign-tag
```

Example:

```bash
python budgetmini.py data.json assign-tag --transaction tx1 --tag school
```

### 6.3 Output Format

Most successful commands may print a short success message, such as:

```text
ok
```

Commands that return data should output JSON.

The following commands should output JSON:

```text
list-accounts
list-transactions
show-budget
report
state
```

The output JSON should be valid and parseable.

For example, the `report` command may output:

```json
{
  "month": "2026-06",
  "total_income": 0,
  "total_expenses": 60,
  "net_worth": -60,
  "cash_flow": -60
}
```

The `state` command may output:

```json
{
  "accounts": {
    "Cash": {
      "name": "Cash",
      "type": "checking",
      "on_budget": true,
      "balance": -60
    }
  },
  "transactions": {
    "tx1": {
      "id": "tx1",
      "date": "2026-06-10",
      "account": "Cash",
      "payee": "Canteen",
      "category": "Food",
      "payment": 60,
      "deposit": 0,
      "tags": []
    }
  },
  "category_groups": {
    "Usual Expenses": {
      "name": "Usual Expenses",
      "categories": ["Food"]
    }
  },
  "categories": {
    "Food": {
      "name": "Food",
      "group": "Usual Expenses"
    }
  },
  "budgets": {
    "2026-06": {
      "Food": {
        "budgeted": 100,
        "spent": 60,
        "balance": 40
      }
    }
  },
  "rules": {},
  "schedules": {},
  "reports": {
    "2026-06": {
      "total_income": 0,
      "total_expenses": 60,
      "net_worth": -60,
      "cash_flow": -60
    }
  },
  "payees": {
    "Canteen": {
      "name": "Canteen"
    }
  },
  "tags": {}
}
```

### 6.4 Error Behavior

If a command fails, the program should:

* return a non-zero exit code;
* print an error message to standard error;
* keep the previous JSON data unchanged.

For example, adding a transaction without an account should fail:

```bash
python budgetmini.py data.json add-transaction --id tx1 --date 2026-06-10 --payee Canteen --payment 60
```

Expected behavior:

```text
error: account is required
```

No transaction should be created, and no balance, budget, or report value should change.

Another invalid example is adding a transaction with both payment and deposit:

```bash
python budgetmini.py data.json add-transaction --id tx2 --date 2026-06-10 --account Cash --payee Test --payment 60 --deposit 20
```

Expected behavior:

```text
error: transaction cannot have both payment and deposit
```

The transaction should not be created, and the previous state should stay unchanged.

## 7. Non-Goals

This benchmark does not need to rebuild the full Actual Budget product.

The following parts are outside the first version:

* real bank synchronization
* multi-device sync server
* user login system
* cloud deployment
* full desktop UI
* mobile app
* advanced investment tracking
* complete report dashboard customization
* internationalization
* real collaboration between users

The first version focuses on personal finance data and cross-module consistency.
