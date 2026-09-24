# Test Impact Analysis Skill

## Purpose

This skill analyzes whether a Pull Request is adequately covered by tests.

Its goal is to identify:

* which behaviors changed;
* which existing tests are relevant;
* which scenarios are missing;
* which regression risks remain untested;
* which findings can be verified through executable tests.

This skill should not generate large numbers of tests automatically.

It should first understand behavior and risk.

---

# Core Question

For every meaningful change, determine:

```text
What behavior changed?
        ↓
Which tests cover it?
        ↓
Which scenarios are missing?
        ↓
What should be verified?
```

---

# When to Use

Use this skill whenever a Pull Request changes:

* application behavior;
* business logic;
* authentication;
* authorization;
* APIs;
* database behavior;
* state transitions;
* background jobs;
* error handling;
* public interfaces;
* bug fixes;
* validation.

It is especially important for medium- and high-risk changes.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
reports/findings/<pr-id>/code-review.json
reports/findings/<pr-id>/security-review.json
```

plus:

* repository path;
* test directories;
* coverage configuration;
* CI configuration;
* changed production files;
* changed test files.

---

# Phase 1 — Identify Existing Test Stack

Detect the test tooling already used by the repository.

For Python projects, inspect for:

```text
pytest
unittest
pytest-cov
coverage.py
pytest-mock
unittest.mock
hypothesis
testcontainers
requests-mock
responses
```

Do not introduce a new testing framework without a clear reason.

---

# Phase 2 — Identify Test Locations

Locate test directories and conventions.

Examples:

```text
tests/
test/
spec/
integration/
e2e/
```

Identify:

* unit tests;
* integration tests;
* API tests;
* end-to-end tests;
* fixtures;
* test utilities.

---

# Phase 3 — Map Changed Code to Existing Tests

For every meaningful changed symbol, identify related tests.

Example:

```text
Changed:
AuthService.validate_api_key()

Related tests:
- test_valid_api_key
- test_invalid_api_key
- test_expired_api_key
```

Use:

* symbol references;
* module imports;
* naming conventions;
* test fixtures;
* direct service usage.

---

# Phase 4 — Compare Production Changes With Test Changes

Identify whether related tests were:

```text
ADDED
MODIFIED
UNCHANGED
REMOVED
```

Example:

```text
Production:
AuthService.validate_token changed

Related tests:
12

Modified tests:
0
```

This is a test-impact signal, not automatically a defect.

---

# Phase 5 — Identify Changed Behaviors

Extract behavior changes from PR context.

Examples:

```text
new success path
new error path
new authorization rule
new required field
new state transition
new retry behavior
new validation rule
new API response
```

Testing should align with behavior, not merely changed lines.

---

# Phase 6 — Build a Behavior-to-Test Matrix

Produce a matrix.

Example:

```text
Behavior                         Covered?
------------------------------------------------
valid API key                    YES
invalid API key                  YES
expired API key                  NO
revoked API key                  NO
cross-tenant API key             NO
missing API key                  YES
```

This is one of the most important outputs of the skill.

---

# Phase 7 — Test Happy Paths

Check whether the intended successful behavior is covered.

Examples:

```text
valid creation
valid update
valid authentication
successful queue processing
valid database write
```

Do not assume a successful integration test covers all relevant behavior.

---

# Phase 8 — Test Failure Paths

Identify expected failure modes.

Examples:

```text
invalid input
dependency unavailable
permission denied
database failure
timeout
missing resource
conflict
```

Failure paths are often under-tested.

---

# Phase 9 — Test Edge Cases

Consider:

```text
empty values
null values
boundary values
large values
duplicates
special characters
Unicode
unexpected ordering
```

Prioritize edge cases with real behavioral relevance.

---

# Phase 10 — Authentication Testing

When authentication changes, check for:

```text
valid credentials
invalid credentials
expired credentials
revoked credentials
missing credentials
malformed credentials
```

---

# Phase 11 — Authorization Testing

When authorization changes, check for:

```text
allowed role
denied role
resource ownership
cross-tenant access
privilege escalation
unauthorized modification
```

Example:

```text
Organization A user
        ↓
attempts to access
        ↓
Organization B resource
```

This is a high-value regression scenario.

---

# Phase 12 — API Testing

When API behavior changes, check coverage for:

```text
success status
validation errors
authentication errors
authorization errors
not found
conflict
malformed body
unexpected failure
```

Also inspect:

```text
response schema
headers
content type
```

---

# Phase 13 — Database Testing

When persistence changes, evaluate tests for:

```text
insert
update
delete
constraints
transactions
rollback
foreign keys
uniqueness
nullability
```

SQLite-based tests may not be sufficient for PostgreSQL-specific behavior.

Record the limitation if relevant.

---

# Phase 14 — Migration Testing

When migrations are changed, consider:

```text
migration applies successfully
existing data remains valid
constraints can be applied
rollback behavior
default values
nullability
```

Do not run destructive migration tests against production databases.

---

# Phase 15 — Queue and Background Job Testing

For queue-related changes, inspect coverage for:

```text
enqueue behavior
correct queue
successful execution
retry
timeout
failure handling
duplicate execution
idempotency
```

Coordinate with `queue-review`.

---

# Phase 16 — Retry Testing

When retry behavior changes, test sequences such as:

```text
attempt 1 → transient failure
attempt 2 → transient failure
attempt 3 → success
```

Verify:

```text
retry count
retry interval
exception classification
final failure
```

---

# Phase 17 — Regression Testing

Every bug fix should ideally have a regression test.

Expected workflow:

```text
bug
 ↓
failing regression test
 ↓
fix
 ↓
passing regression test
```

If a bug fix has no regression test, report it as a test-impact finding.

---

# Phase 18 — Removed Tests

Pay attention when the Pull Request removes tests.

Determine whether:

```text
behavior was removed
test became obsolete
coverage was lost
```

A deleted test is not automatically a problem.

---

# Phase 19 — Weak Tests

Inspect whether tests meaningfully assert behavior.

Weak patterns include:

```python
assert response is not None
```

when the important behavior is status, payload, or persistence.

Also watch for:

```text
tests with no meaningful assertions
tests that only verify mocks
tests that cannot fail for the intended bug
```

---

# Phase 20 — Mocking Quality

Mocks should isolate external boundaries.

Good mock targets:

```text
HTTP services
email services
cloud APIs
external queues
filesystem
clock
```

Avoid mocking the exact internal behavior being tested.

---

# Phase 21 — Test Isolation

Look for tests depending on:

```text
execution order
global state
shared database state
shared Redis state
current time
network
```

These can create flaky behavior.

---

# Phase 22 — Flaky Test Signals

Inspect for:

```text
time.sleep()
random values without fixed seeds
shared resources
race conditions
retrying failed tests
```

Do not classify a test as flaky without evidence.

---

# Phase 23 — Coverage Analysis

If supported, run coverage.

For Python:

```bash
pytest --cov=app --cov-branch --cov-report=term-missing
```

or adapt to repository configuration.

Coverage is a signal, not proof of test quality.

---

# Phase 24 — Diff Coverage

When practical, evaluate coverage specifically for changed lines.

This is often more meaningful than repository-wide coverage.

Desired concept:

```text
changed lines
      ↓
covered?
```

If tooling supports diff coverage, preserve results.

---

# Phase 25 — Identify Untested Critical Paths

Prioritize missing tests for:

```text
security boundaries
data integrity
authorization
state transitions
public APIs
queue retries
error handling
```

Not all uncovered code deserves equal attention.

---

# Phase 26 — Generate Verification Candidates

Turn important findings into executable verification ideas.

Example:

```text
Finding:
Possible cross-tenant access.

Verification test:
Create organizations A and B.
Authenticate as A.
Request B resource.
Expect 403 or 404.
```

Pass these to:

```text
finding-verification
```

---

# Phase 27 — Test Generation Policy

Generate tests only when:

* behavior is clear;
* the test can be deterministic;
* the test adds meaningful confidence;
* verification value is high.

Avoid generating tests solely to increase test count.

---

# Phase 28 — Temporary Verification Tests

When creating temporary verification tests:

* store them separately when practical;
* clearly label them;
* use synthetic data;
* avoid modifying production behavior.

Suggested location:

```text
reports/verification/<pr-id>/tests/
```

or a temporary workspace.

---

# Phase 29 — Test Execution

When safe, execute relevant tests.

Start with focused tests.

Example:

```bash
pytest tests/test_auth.py -q
```

Then broader affected tests.

Finally, run the relevant suite if practical.

---

# Phase 30 — Failure Classification

Classify test failures as:

```text
PRODUCT_DEFECT
TEST_DEFECT
ENVIRONMENT_FAILURE
DEPENDENCY_FAILURE
CONFIGURATION_FAILURE
UNKNOWN
```

Do not automatically assume every failure proves a PR defect.

---

# Phase 31 — CI Awareness

Inspect CI when available.

Determine whether the repository already runs:

```text
unit tests
integration tests
coverage
lint
type checks
security checks
```

A missing local test may still be covered by CI-specific suites.

---

# Finding Categories

Use categories such as:

```text
MISSING_TEST
MISSING_REGRESSION_TEST
MISSING_FAILURE_PATH
MISSING_AUTHORIZATION_TEST
MISSING_SECURITY_TEST
MISSING_EDGE_CASE
WEAK_ASSERTION
TEST_ISOLATION
FLAKY_TEST_RISK
COVERAGE_GAP
```

---

# Severity Guidance

## HIGH

Examples:

```text
critical authorization change has no negative test
data integrity behavior has no regression coverage
```

## MEDIUM

Examples:

```text
important failure path untested
significant edge case untested
```

## LOW

Examples:

```text
minor behavior lacks explicit test
small coverage gap
```

Avoid CRITICAL except in exceptional circumstances.

---

# Confidence

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

Example:

```text
Missing cross-tenant test

CONFIRMED
```

if related tests were inspected and none cover it.

---

# Example Finding

```json
{
  "id": "TEST-001",
  "category": "MISSING_AUTHORIZATION_TEST",
  "severity": "HIGH",
  "confidence": "CONFIRMED",
  "title": "Cross-tenant access is not covered by tests",
  "description": "The Pull Request adds organization-scoped API key access but no test verifies that a key from one organization cannot access resources from another.",
  "file": "tests/test_api_keys.py",
  "line": null,
  "evidence": [
    "authorization logic changed in app/auth/api_key.py",
    "existing API-key tests cover valid and invalid keys",
    "no test uses two different organizations"
  ],
  "impact": "A tenant-isolation regression could reach production without automated detection.",
  "recommendation": "Add a regression test using two synthetic organizations and assert cross-tenant access is rejected.",
  "verification_status": "NOT_APPLICABLE",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/test-impact.json
```

Optionally:

```text
reports/findings/<pr-id>/test-impact.md
```

---

# Behavior Matrix Artifact

Also generate:

```text
reports/raw/<pr-id>/test-impact-matrix.json
```

Recommended structure:

```json
{
  "behaviors": [
    {
      "behavior": "valid API key authentication",
      "covered": true,
      "tests": [
        "test_valid_api_key"
      ]
    },
    {
      "behavior": "cross-tenant API key rejection",
      "covered": false,
      "tests": []
    }
  ]
}
```

---

# Metrics

Record:

```text
changed_behaviors
behaviors_with_tests
behaviors_without_tests

related_tests
tests_added
tests_modified
tests_removed

tests_executed
tests_passed
tests_failed

missing_regression_tests
missing_failure_tests
missing_authorization_tests
missing_edge_case_tests

coverage_before
coverage_after
branch_coverage

verification_candidates
```

Only include coverage metrics when actually measured.

Save:

```text
reports/metrics/<pr-id>-test-impact.json
```

---

# Coverage Gap Priority

Classify gaps:

```text
CRITICAL_PATH
HIGH_VALUE
MEDIUM_VALUE
LOW_VALUE
```

Example:

```text
Cross-tenant authorization
CRITICAL_PATH
```

versus:

```text
formatting helper branch
LOW_VALUE
```

---

# Verification Handoff

For findings that can be proven with tests, produce a verification request.

Example:

```json
{
  "finding_id": "SEC-001",
  "verification_type": "REGRESSION_TEST",
  "scenario": "Cross-tenant API key access",
  "expected_result": "403 or 404"
}
```

These requests should be consumable by:

```text
finding-verification
```

---

# What This Skill Must Not Do

Do not:

* rewrite the entire test suite;
* generate tests for every uncovered line;
* modify production code;
* treat coverage percentage as quality proof;
* force arbitrary coverage thresholds;
* run destructive integration tests;
* use production data.

---

# Completion Criteria

The skill is complete when:

* changed behaviors are mapped;
* related tests are identified;
* a behavior-to-test matrix is produced;
* important missing scenarios are identified;
* existing tests are executed when practical;
* coverage is measured when available;
* verification candidates are produced;
* findings and metrics are persisted.

---

# Human Summary Format

Use:

```text
Test Impact

Changed behaviors:
...

Covered behaviors:
...

Missing behaviors:
...

Tests executed:
Passed:
Failed:

Coverage:
...

High-value gaps:
...

Verification candidates:
...
```

---

# Engineering Principle

The goal is not:

> Maximize test count.

The goal is:

> Determine whether the Pull Request has enough executable evidence to detect meaningful regressions.