# PR Guardian Planning Rules

These rules apply whenever Bob is planning a Pull Request review inside PR Guardian.

The purpose of the planning phase is to determine the minimum set of analysis steps required to produce a reliable, contextual, and evidence-based review.

The plan must reduce unnecessary work, avoid irrelevant reviewers, and define how findings will be verified.

---

## 1. Start From Pull Request Intent

Before creating the review plan, identify:

* Pull Request title;
* Pull Request description;
* commits;
* changed files;
* lines added;
* lines removed;
* declared purpose;
* affected components.

Summarize the Pull Request intent in one concise paragraph.

Do not plan specialized reviews before understanding what the Pull Request is trying to accomplish.

---

## 2. Identify Change Domains

Classify the Pull Request into one or more domains.

Possible domains include:

```text
APPLICATION_LOGIC
SECURITY
AUTHENTICATION
AUTHORIZATION
API
DATABASE
MIGRATION
BACKGROUND_JOB
QUEUE
DEPENDENCY
CONFIGURATION
OBSERVABILITY
TESTING
DOCUMENTATION
INFRASTRUCTURE
CI_CD
PERFORMANCE
```

Use only domains supported by actual changed files or repository context.

---

## 3. Identify Risk Triggers

Inspect the Pull Request for risk triggers.

Examples:

### Security triggers

* authentication changes;
* authorization changes;
* user-controlled input;
* SQL construction;
* command execution;
* file operations;
* token handling;
* cryptography;
* secrets.

### Database triggers

* model changes;
* migrations;
* raw SQL;
* indexes;
* transactions;
* constraints.

### API triggers

* routes;
* schemas;
* serializers;
* OpenAPI files;
* HTTP status behavior.

### Background processing triggers

* RQ;
* Celery;
* Kafka;
* RabbitMQ;
* async workers;
* scheduled jobs.

### Architecture triggers

* new dependencies;
* cross-layer calls;
* large new services;
* responsibility changes;
* module coupling.

---

## 4. Build a Review Scope

The plan must define the review scope.

Example:

```text
Review Scope

Primary files:
- app/auth/service.py
- app/api/users.py

Related files:
- app/models/user.py
- tests/test_auth.py
- openapi.yaml

Excluded:
- unrelated reporting modules
- static assets
```

Avoid repository-wide analysis unless required.

---

## 5. Select Reviewers Adaptively

Choose only relevant skills.

Example:

```text
Selected Reviewers

pr-understanding
change-impact
code-review
security-review
test-impact
api-review
finding-verification
review-synthesis
```

Do not select:

```text
database-review
queue-review
```

unless the Pull Request actually affects those domains.

---

## 6. Define Reviewer Purpose

For every selected reviewer, define what it should answer.

Example:

```text
security-review

Questions:
- Does the new endpoint enforce authorization?
- Can user-controlled data reach a sensitive sink?
- Are tokens handled safely?
```

Avoid vague planning instructions such as:

```text
"Review security."
```

---

## 7. Define Repository Context Needed

Determine what context must be inspected beyond the diff.

Possible context includes:

```text
callers
callees
models
services
tests
configuration
schemas
migrations
dependencies
OpenAPI contracts
worker definitions
repository history
```

Do not load unrelated repository context.

---

## 8. Plan Change-Impact Analysis

For relevant changes, determine:

* direct callers;
* direct dependencies;
* affected endpoints;
* affected jobs;
* affected database entities;
* affected tests;
* affected public interfaces.

The plan should explicitly state which impact relationships need investigation.

---

## 9. Plan Test Analysis

For code changes, identify:

* existing related tests;
* behaviors changed;
* likely regression paths;
* missing scenarios;
* opportunities for verification tests.

Example:

```text
Test Impact Plan

Existing tests:
- test_create_api_key
- test_revoke_api_key

Potential gaps:
- cross-tenant access
- expired key
- revoked key reuse
```

---

## 10. Plan Verification Before Review Publication

Important findings should have a verification strategy when practical.

Possible verification methods:

```text
existing pytest test
generated regression test
Ruff
Bandit
Semgrep
pip-audit
mypy
coverage
repository evidence
OpenAPI comparison
migration inspection
```

Example:

```text
Potential finding:
Cross-tenant access may be possible.

Verification:
Generate an isolated test using two synthetic organizations.
```

---

## 11. Prefer Deterministic Verification

When both AI reasoning and deterministic tools can validate a finding, use both.

Example:

```text
Bob identifies possible unsafe SQL
        ↓
Semgrep or repository inspection
        ↓
verification result
```

The plan should prioritize executable evidence for high-impact findings.

---

## 12. Define Parallelizable Work

Identify independent review tasks that can run in parallel.

Good candidates:

```text
security-review
test-impact
architecture-review
database-review
api-review
queue-review
```

Do not parallelize tasks that require outputs from one another.

Example:

```text
pr-understanding
        ↓
change-impact
        ↓
parallel specialized reviews
        ↓
finding-verification
        ↓
review-synthesis
```

---

## 13. Define Dependencies Between Tasks

The plan should make dependencies explicit.

Example:

```text
Task 1: Understand PR
        ↓
Task 2: Build repository context
        ↓
Task 3A: Security review
Task 3B: Test-impact review
Task 3C: API review
        ↓
Task 4: Verify important findings
        ↓
Task 5: Synthesize final review
```

Do not start review synthesis before specialized findings exist.

---

## 14. Estimate Review Complexity

Classify the Pull Request review complexity as:

```text
SMALL
MEDIUM
LARGE
```

Suggested interpretation:

### SMALL

* few changed files;
* localized behavior;
* limited dependencies;
* low-risk domains.

### MEDIUM

* multiple modules;
* moderate cross-component impact;
* security, API, database, or test changes.

### LARGE

* broad architectural impact;
* many changed files;
* multiple high-risk domains;
* migrations plus APIs plus authentication;
* substantial dependency changes.

Complexity is operational, not a quality judgment.

---

## 15. Do Not Use Arbitrary Risk Scores

Avoid numeric values such as:

```text
Risk score: 8.4/10
```

unless based on a documented deterministic formula.

Prefer explicit risk factors.

Example:

```text
High-risk factors:
- authorization logic changed
- public API changed
- database migration added
- no related tests modified
```

---

## 16. Define Expected Outputs

Each plan must identify output artifacts.

Example:

```text
reports/findings/pr-42-findings.json
reports/verification/pr-42-verification.json
reports/reviews/pr-42-review.md
reports/metrics/pr-42-metrics.json
```

Output paths should be deterministic where possible.

---

## 17. Define Metrics Before Execution

The plan should state what can be measured.

Examples:

```text
files_changed
files_analyzed
lines_added
lines_removed
reviewers_selected
findings_total
verified_findings
tests_executed
tests_failed
analysis_duration_seconds
```

Do not invent metrics after the review to make results appear stronger.

---

## 18. Preserve Raw Evidence

If external tools will be executed, define where raw output is stored.

Example:

```text
reports/raw/pr-42/
```

Possible files:

```text
ruff.txt
bandit.json
semgrep.json
pytest.txt
coverage.json
```

---

## 19. Plan for Failure

The plan must consider tool or environment failures.

Examples:

```text
dependency installation fails
test suite cannot start
required service unavailable
repository cannot be cloned
static analyzer unavailable
```

When verification cannot be executed:

* preserve the finding;
* mark it UNVERIFIED;
* record the reason.

Do not silently treat missing verification as success.

---

## 20. Avoid Unnecessary Environment Changes

Do not modify the host environment more than necessary.

Prefer:

* existing virtual environments;
* project dependency files;
* isolated environments;
* containers when already supported.

Do not upgrade unrelated dependencies during review.

---

## 21. Identify Dangerous Operations

Before execution, detect commands that might:

* delete files;
* modify databases;
* contact production services;
* publish real messages;
* enqueue real production jobs;
* run destructive migrations;
* invoke external paid APIs.

Replace them with safe alternatives or do not execute them.

---

## 22. Define Stopping Conditions

A review plan should define when enough evidence has been gathered.

Possible stopping conditions:

```text
all selected reviewers completed
high-impact findings verified where practical
relevant tests executed
duplicate findings removed
final synthesis prepared
metrics persisted
```

Do not continue exploring unrelated repository areas once the required evidence is sufficient.

---

## 23. Prioritize High-Value Review Work

When time or resources are constrained, prioritize:

1. correctness defects;
2. authorization and security;
3. data integrity;
4. breaking changes;
5. regression risk;
6. tests;
7. architecture;
8. maintainability;
9. style.

Style should not consume significant review effort.

---

## 24. Resource-Aware Planning

IBM Bob usage is a constrained resource.

Avoid:

* repeated repository exploration;
* repeatedly loading the same context;
* unnecessary reviewers;
* duplicate analysis;
* rewriting existing reports.

Reuse persistent project artifacts when they are current and relevant.

---

## 25. Reuse Existing Context Carefully

Existing analysis may be reused only if:

* it refers to the same repository state;
* it is still relevant;
* the related files have not materially changed.

Do not rely on stale repository context.

---

## 26. Planning Output Format

Produce the plan in the following structure:

```text
# Pull Request Review Plan

## PR Intent

## Changed Files

## Change Domains

## Risk Triggers

## Review Scope

## Related Repository Context

## Selected Reviewers

## Reviewer Questions

## Parallel Tasks

## Task Dependencies

## Verification Strategy

## Test Strategy

## Metrics

## Output Artifacts

## Safety Constraints

## Stopping Conditions
```

---

## 27. Example Plan

```text
# Pull Request Review Plan

## PR Intent

Add API-key authentication for external integrations.

## Changed Files

- app/auth/api_key.py
- app/api/middleware.py
- app/models/api_key.py
- tests/test_api_key.py

## Change Domains

AUTHENTICATION
AUTHORIZATION
API
DATABASE
TESTING

## Risk Triggers

- authentication boundary changed
- database model added
- credentials handled
- middleware modified

## Selected Reviewers

- pr-understanding
- change-impact
- code-review
- security-review
- test-impact
- database-review
- api-review
- finding-verification
- review-synthesis

## Verification Strategy

- run existing API-key tests
- inspect tenant-scoping logic
- generate cross-tenant regression test if needed
- run Bandit
- compare API implementation with OpenAPI

## Metrics

- findings_total
- findings_verified
- tests_executed
- tests_failed
- reviewers_selected
- analysis_duration_seconds
```

---

## 28. Planning Principle

A good plan should answer:

```text
What changed?

What can break?

What context is required?

Which specialists are relevant?

How can important findings be proven?

What evidence will be preserved?
```

If the plan cannot answer these questions, it is not ready for execution.