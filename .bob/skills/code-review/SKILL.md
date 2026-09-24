# Code Review Skill

## Purpose

This skill reviews Pull Request changes for correctness, regressions, edge cases, error handling, state consistency, resource management, compatibility, and maintainability issues with concrete engineering impact.

Its goal is to identify meaningful defects introduced or exposed by the Pull Request.

It should not duplicate specialized security, database, API, queue, or architecture reviews unless the issue is directly necessary to explain code correctness.

---

# Core Principle

Review behavior, not aesthetics.

Focus on questions such as:

* Can this code produce an incorrect result?
* Can valid input fail unexpectedly?
* Can invalid input pass unexpectedly?
* Can state become inconsistent?
* Can an exception escape incorrectly?
* Can a previous behavior regress?
* Can resources leak?
* Can duplicate execution produce incorrect behavior?
* Can callers break because of this change?

Avoid comments based only on personal style preference.

---

# When to Use

Use this skill for Pull Requests that modify:

* application logic;
* services;
* domain rules;
* utilities;
* validation;
* state transitions;
* public interfaces;
* shared components;
* error handling;
* algorithms;
* data transformations;
* control flow.

This skill is usually relevant to most non-trivial code changes.

---

# Inputs

Recommended inputs include:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

as well as:

* repository path;
* diff;
* changed files;
* changed symbols;
* related tests;
* related callers and dependencies.

---

# Phase 1 — Understand Intended Behavior

Before producing findings, identify:

* what the changed code is intended to do;
* previous behavior;
* new behavior;
* inputs;
* outputs;
* failure modes;
* state mutations.

Do not report a defect when the expected behavior is unclear without first inspecting context.

---

# Phase 2 — Compare Before and After Behavior

For modified logic, reason about:

```text
BEFORE
  ↓
CHANGE
  ↓
AFTER
```

Identify whether the PR changes:

* return values;
* exceptions;
* validation;
* side effects;
* ordering;
* persistence;
* state;
* public contracts.

Unexpected behavioral differences are review candidates.

---

# Phase 3 — Control Flow Analysis

Inspect:

* branches;
* loops;
* early returns;
* exception paths;
* fall-through behavior;
* unreachable code.

Look for issues such as:

```text
missing branch
incorrect condition
inverted condition
unreachable path
missing return
incorrect fallback
```

Example:

```python
if user.is_admin:
    deny_access()
```

may indicate inverted logic if repository intent shows admins should be allowed.

Do not infer intent from naming alone.

---

# Phase 4 — Null and Missing Value Handling

Inspect behavior for:

```text
None
null
missing key
empty collection
empty string
missing optional field
```

Common defects include:

```text
AttributeError
KeyError
unexpected default behavior
incorrect truthiness handling
```

Example:

```python
email = payload["email"].strip()
```

Potential issue if `email` may be missing or null.

Verify with schema or caller context before reporting.

---

# Phase 5 — Boundary Conditions

Review:

```text
zero
negative values
empty collections
minimum values
maximum values
first element
last element
single element
large values
```

Look for:

* off-by-one errors;
* incorrect pagination;
* wrong slicing;
* invalid limits;
* incorrect range checks.

---

# Phase 6 — State Transitions

For stateful behavior, identify valid transitions.

Example:

```text
PENDING
  ↓
PROCESSING
  ↓
COMPLETED
```

Check whether the PR accidentally allows:

```text
COMPLETED → PROCESSING
```

or skips required intermediate state.

Document expected transition evidence.

---

# Phase 7 — Error Handling

Inspect:

* exceptions raised;
* exceptions caught;
* errors suppressed;
* fallback behavior;
* rollback behavior;
* error translation.

Potential issues:

```text
catch-all exception hides failure
wrong exception type caught
exception swallowed
partial state persists after failure
incorrect HTTP error mapping
```

Avoid recommending generic try/except blocks without a concrete need.

---

# Phase 8 — Partial Failure

Review operations with multiple side effects.

Example:

```text
write database
send notification
enqueue job
```

Ask:

```text
What happens if step 2 fails after step 1 succeeds?
```

Look for inconsistent state or missing rollback/compensation.

---

# Phase 9 — Resource Management

Inspect:

* files;
* sockets;
* database connections;
* cursors;
* locks;
* temporary files;
* external clients.

Look for missing cleanup.

Prefer context managers where applicable.

Example:

```python
file = open(path)
process(file)
```

may leak resources if cleanup is absent.

---

# Phase 10 — Collection Handling

Review:

* list mutation;
* dictionary access;
* set behavior;
* duplicate handling;
* iteration while mutating.

Potential issues:

```text
duplicate entries
lost ordering
missing key
unexpected mutation
shared reference modification
```

---

# Phase 11 — Mutation and Side Effects

Determine whether functions unexpectedly mutate:

* arguments;
* shared state;
* globals;
* cached values;
* ORM entities.

Example:

```python
def normalize(data):
    data["name"] = data["name"].strip()
```

may be surprising if callers expect immutability.

Only report when impact is meaningful.

---

# Phase 12 — Idempotency

For operations that may be retried or repeated, check whether duplicate execution is safe.

Examples:

```text
create payment
send email
create user
enqueue job
apply migration
```

Ask:

```text
If this executes twice, what happens?
```

Coordinate with `queue-review` when asynchronous execution is involved.

---

# Phase 13 — Concurrency and Race Conditions

Look for patterns such as:

```text
check then update
read then write
shared mutable state
non-atomic counters
duplicate creation
```

Example:

```python
if not user_exists(email):
    create_user(email)
```

may race under concurrent requests.

Use database or locking context before classifying severity.

---

# Phase 14 — Ordering Assumptions

Check whether code assumes ordering that is not guaranteed.

Examples:

```text
database result order
dictionary iteration assumptions
set ordering
async completion order
```

Only report when behavior depends on that order.

---

# Phase 15 — Validation Logic

Review:

* required fields;
* type checks;
* range checks;
* enum values;
* normalization;
* contradictory validation.

Look for cases where validation is:

```text
missing
too permissive
too strict
applied after side effects
```

Security-sensitive validation belongs primarily to `security-review`.

---

# Phase 16 — Data Conversion

Inspect conversions such as:

```text
string → integer
string → datetime
JSON → object
float → integer
timezone conversion
encoding conversion
```

Common defects:

```text
silent truncation
timezone mismatch
locale dependence
invalid fallback
precision loss
```

---

# Phase 17 — Date and Time Handling

Inspect:

* timezone awareness;
* naive datetimes;
* expiration logic;
* daylight-saving assumptions;
* comparison operators.

Example:

```python
datetime.now()
```

versus timezone-aware application behavior.

Only report when context shows actual inconsistency.

---

# Phase 18 — Backward Compatibility

Identify changes that may break callers.

Examples:

```text
required parameter added
return type changed
exception type changed
field removed
default behavior changed
```

Coordinate with `api-review` for external HTTP contracts.

---

# Phase 19 — Removed Behavior

Removed code deserves explicit inspection.

Look for:

```text
removed validation
removed error handling
removed fallback
removed retry
removed default value
removed branch
```

A deletion may introduce regression even if new code looks clean.

---

# Phase 20 — Dead or Unreachable Logic

Identify newly introduced logic that can never execute.

Example:

```python
if value is None:
    return

if value is None:
    raise ValueError()
```

The second branch is unreachable.

Avoid broad dead-code cleanup unrelated to the PR.

---

# Phase 21 — Incorrect Boolean Logic

Inspect compound conditions:

```python
if user.is_active and user.is_admin or user.is_owner:
```

Verify operator precedence and intended grouping.

Potential defect may require:

```python
if user.is_active and (user.is_admin or user.is_owner):
```

Use actual domain intent as evidence.

---

# Phase 22 — Default Values

Check whether new defaults alter behavior unexpectedly.

Examples:

```text
timeout defaults to None
limit defaults to zero
boolean defaults to True
```

Default changes can have system-wide impact.

---

# Phase 23 — Exception Compatibility

When exception behavior changes, identify affected callers.

Example:

Before:

```text
returns None
```

After:

```text
raises ValueError
```

Callers may not handle the new exception.

Use `change-impact` evidence where available.

---

# Phase 24 — Performance Defects With Correctness Impact

This skill may report performance issues only when they are severe enough to affect functionality.

Examples:

```text
unbounded loop
accidental quadratic behavior
loading entire large dataset
blocking operation inside hot path
```

Pure optimization recommendations belong outside the core review unless material.

---

# Phase 25 — Logging Side Effects

Look for code where logging itself may break execution.

Example:

```python
logger.info("user=%s", user.profile.name)
```

when `profile` may be absent.

Security-sensitive logging belongs to `security-review`.

---

# Phase 26 — Configuration Assumptions

Check code changes that assume:

```text
environment variable exists
configuration value has valid type
service is always enabled
```

Example:

```python
timeout = int(os.environ["TIMEOUT"])
```

may fail at startup if configuration is optional or undocumented.

Use repository configuration evidence.

---

# Phase 27 — Regression Signals

Pay special attention when:

```text
existing tests changed significantly
validation removed
fallback removed
shared helper changed
public function signature changed
```

These may indicate regression risk.

---

# Finding Requirements

Every finding should include:

```text
id
category
severity
confidence
title
description
file
line
evidence
impact
recommendation
verification_status
introduced_by_pr
```

---

# Finding Categories

Suggested categories:

```text
LOGIC_ERROR
REGRESSION
EDGE_CASE
ERROR_HANDLING
STATE_CONSISTENCY
RESOURCE_MANAGEMENT
CONCURRENCY
COMPATIBILITY
VALIDATION
DATA_CONVERSION
NULL_HANDLING
IDEMPOTENCY
CONTROL_FLOW
```

Use the most specific category available.

---

# Severity Guidance

## CRITICAL

Use only when the defect can cause catastrophic or irreversible failure.

Examples may include:

* widespread destructive data corruption;
* complete critical-system outage.

Critical severity should be rare.

---

## HIGH

Examples:

* major functional failure;
* broad regression;
* significant data inconsistency;
* common-path crash;
* broken core workflow.

---

## MEDIUM

Examples:

* edge-case failure with meaningful impact;
* incomplete error handling;
* localized regression;
* incorrect behavior under specific valid conditions.

---

## LOW

Examples:

* minor robustness issue;
* low-impact compatibility problem;
* small correctness issue with limited reach.

---

## INFO

Use for contextual observations that are not defects.

Avoid excessive INFO findings.

---

# Confidence Guidance

## CONFIRMED

Use when:

* behavior is directly observable;
* test reproduces it;
* logic proves the issue;
* repository evidence is conclusive.

## LIKELY

Use when evidence is strong but not fully reproduced.

## POTENTIAL

Use when additional context or execution is required.

## INFORMATIONAL

Use for non-defect context.

---

# Introduced-by-PR Classification

Use:

```text
INTRODUCED_BY_PR
PRE_EXISTING
EXPOSED_BY_PR
UNCERTAIN
```

Prefer findings introduced by or directly relevant to the PR.

Do not fill the review with unrelated pre-existing problems.

---

# Verification Strategy

For important findings, recommend verification.

Examples:

```text
existing unit test
new regression test
integration test
repository inspection
type checker
static analyzer
```

Pass verification candidates to:

```text
finding-verification
```

---

# Example Finding

```json
{
  "id": "CR-001",
  "category": "NULL_HANDLING",
  "severity": "MEDIUM",
  "confidence": "LIKELY",
  "title": "Missing nullable profile handling",
  "description": "The new response builder dereferences user.profile.name, but profile is optional in the User model.",
  "file": "app/api/users.py",
  "line": 84,
  "evidence": [
    "app/models/user.py defines profile as nullable",
    "app/api/users.py accesses user.profile.name without a null check"
  ],
  "impact": "Requests for users without a profile may return a 500 error.",
  "recommendation": "Handle users without a profile or enforce the invariant before this code path.",
  "verification_status": "UNVERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/code-review.json
```

Optionally generate:

```text
reports/findings/<pr-id>/code-review.md
```

The JSON artifact is canonical.

---

# Metrics

Record:

```text
files_reviewed
symbols_reviewed
findings_total

logic_errors
regressions
edge_case_findings
error_handling_findings
state_consistency_findings
compatibility_findings

critical_findings
high_findings
medium_findings
low_findings

confirmed_findings
likely_findings
potential_findings

verification_candidates
```

Save to:

```text
reports/metrics/<pr-id>-code-review.json
```

---

# Avoid Duplicate Specialized Findings

If a finding is primarily:

```text
SQL injection
authorization bypass
secret exposure
```

prefer `security-review`.

If primarily:

```text
missing index
unsafe migration
N+1 query
```

prefer `database-review`.

If primarily:

```text
OpenAPI mismatch
HTTP contract break
```

prefer `api-review`.

If primarily:

```text
missing retry
queue timeout
duplicate job execution
```

prefer `queue-review`.

If primarily architectural:

```text
layer violation
circular dependency
responsibility collapse
```

prefer `architecture-review`.

The general code reviewer may reference these concerns but should avoid duplicating specialist findings.

---

# Review Noise Rules

Do not create findings for:

* formatting;
* import ordering;
* naming preference;
* comment style;
* minor refactoring preference;
* theoretical patterns without impact;
* issues already handled by linters unless they have real behavioral consequences.

---

# Completion Criteria

The skill is complete when:

* changed behavioral code is reviewed;
* major control-flow paths are inspected;
* regressions are considered;
* error handling is reviewed;
* important edge cases are considered;
* public behavior changes are evaluated;
* high-value findings are structured;
* verification candidates are identified;
* metrics are saved.

---

# Human Summary Format

Use:

```text
Code Review

Files reviewed:
...

Findings:
Critical:
High:
Medium:
Low:

Confirmed:
Likely:
Potential:

Primary concerns:
...

Verification candidates:
...
```

Keep the summary concise.

Detailed findings belong in JSON.

---

# Engineering Principle

A strong Pull Request review is not a catalog of stylistic preferences.

It is a focused search for changes that can make the system behave incorrectly.

The objective is:

> Find the smallest set of meaningful correctness issues that materially improves confidence in the Pull Request.