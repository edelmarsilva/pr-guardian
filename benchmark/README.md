# PR Guardian Benchmarks

## Purpose

The benchmark suite evaluates whether PR Guardian improves Pull Request review quality compared with a simpler baseline workflow.

The benchmark must use controlled, synthetic, or explicitly permitted sample repositories.

Do not use confidential company repositories, client data, personal information, or private production source code.

---

# Benchmark Goals

Measure whether PR Guardian can:

1. detect known defects;
2. reduce false-positive review noise;
3. select only relevant reviewers;
4. verify findings using deterministic evidence;
5. produce concise final reviews;
6. reduce manual review effort.

---

# Benchmark Structure

```text
benchmarks/
├── datasets/
│   ├── pr-001/
│   ├── pr-002/
│   └── ...
├── expected-findings/
├── baseline/
└── bob-assisted/
```

---

# Dataset Philosophy

Each benchmark Pull Request should contain a controlled change with one or more known behaviors.

Examples:

```text
authorization bypass
SQL injection
breaking API response
unsafe migration
duplicate queue execution
missing retry safety
N+1 query
missing regression test
```

The expected defect must be documented before running PR Guardian.

This prevents changing the expected answer after seeing the tool output.

---

# Dataset Requirements

Each dataset should contain:

```text
metadata.json
README.md
base/
head/
```

or a small Git repository with deterministic base/head commits.

Recommended:

```text
benchmarks/datasets/pr-001/
├── README.md
├── metadata.json
└── repository/
```

The repository should contain at least two commits:

```text
BASE
  ↓
HEAD
```

representing the synthetic Pull Request.

---

# Metadata Format

Example:

```json
{
  "id": "pr-001",
  "title": "Cross-tenant report lookup",
  "domains": [
    "SECURITY",
    "API",
    "DATABASE"
  ],
  "expected_reviewers": [
    "code-review",
    "security-review",
    "test-impact",
    "database-review",
    "api-review"
  ],
  "known_findings": [
    "SEC-TENANT-001"
  ]
}
```

---

# Expected Findings

Store canonical expected findings under:

```text
benchmarks/expected-findings/
```

Example:

```text
pr-001.json
```

---

# Expected Finding Format

```json
{
  "pr_id": "pr-001",
  "findings": [
    {
      "id": "SEC-TENANT-001",
      "category": "TENANT_ISOLATION",
      "severity": "HIGH",
      "title": "Report lookup is not scoped by organization",
      "expected_files": [
        "app/repositories/reports.py"
      ],
      "expected_behavior": "A user from organization A must not access organization B resources.",
      "verification_possible": true
    }
  ]
}
```

---

# Benchmark Scenarios

## PR-001 — Tenant Isolation

Introduce:

```text
resource lookup by ID
without organization scope
```

Expected:

```text
security-review selected
database-review selected
test-impact selected
```

Verification should attempt a cross-tenant regression test.

---

## PR-002 — SQL Injection

Introduce:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

Expected:

```text
security-review
database-review
```

Semgrep or Bandit may provide supporting evidence.

---

## PR-003 — Breaking API Contract

Change:

```text
email
```

to:

```text
email_address
```

in a response without API version change.

Expected:

```text
api-review
test-impact
```

OpenAPI mismatch may independently verify the finding.

---

## PR-004 — Unsafe Migration

Introduce:

```text
NOT NULL column
```

without default or backfill on a populated table.

Expected:

```text
database-review
test-impact
```

An isolated migration test should reproduce failure.

---

## PR-005 — Queue Idempotency

Introduce a retryable job that performs a side effect before storing completion state.

Expected:

```text
queue-review
test-impact
```

A retry regression test may reproduce duplicate execution.

---

## PR-006 — N+1 Query

Introduce database access inside a collection loop.

Expected:

```text
database-review
code-review
```

---

## PR-007 — No Defect

Create a legitimate small change with sufficient tests.

Expected:

```text
few or zero publishable findings
```

This dataset is important for measuring false-positive behavior.

---

# Baseline

Store baseline results under:

```text
benchmarks/baseline/
```

A baseline should be simpler than PR Guardian.

Examples:

```text
single general-purpose review prompt
diff-only review
static analyzers alone
```

Do not intentionally weaken the baseline.

The goal is a fair comparison.

---

# Bob-Assisted Results

Store PR Guardian outputs under:

```text
benchmarks/bob-assisted/
```

Example:

```text
benchmarks/bob-assisted/pr-001/
├── findings.json
├── verification.json
├── review.json
└── metrics.json
```

---

# Evaluation Dimensions

## Detection

For each known defect:

```text
detected
not detected
```

---

# True Positive

A benchmark expected finding is considered detected when the final review identifies the same underlying defect.

Exact wording does not need to match.

---

# False Positive

A final published finding that does not correspond to a known benchmark defect or legitimate additional defect may be classified as a false positive after manual inspection.

Do not automatically treat unexpected findings as false positives.

They must be reviewed.

---

# Precision

When ground truth is available:

```text
precision =
true positives
---------------
all published findings
```

---

# Recall

```text
recall =
known findings detected
-----------------------
known findings
```

---

# Verification Yield

Measure:

```text
verified findings
-----------------
findings selected for verification
```

---

# Refutation Rate

Measure:

```text
refuted findings
----------------
conclusive verification results
```

This demonstrates how often verification prevents unsupported findings from reaching the final review.

---

# Adaptive Routing

Measure:

```text
reviewers skipped
-----------------
available reviewers
```

Example:

```text
available: 7
selected: 3
skipped: 4

routing reduction:
57.14%
```

---

# Finding Reduction

Measure:

```text
initial findings
        ↓
refutation
        ↓
deduplication
        ↓
suppression
        ↓
final findings
```

Example:

```text
Initial:    14
Refuted:     3
Duplicates:  2
Suppressed:  1
Final:       8
```

---

# Review Time

When feasible, compare:

```text
manual baseline review time
```

against:

```text
PR Guardian assisted review time
```

The measurement procedure must be documented.

Do not fabricate time savings.

---

# Reviewer Selection Accuracy

For synthetic datasets with known domains, compare:

```text
expected reviewers
vs
selected reviewers
```

Useful measures:

```text
unnecessary reviewers selected
required reviewers missed
```

---

# Test Generation Metrics

Measure:

```text
verification tests generated
verification tests executed
findings reproduced
findings refuted
```

---

# Evidence Quality

Classify final findings by verification status:

```text
VERIFIED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
```

A stronger result has more high-impact findings supported by reproducible evidence.

---

# Benchmark Integrity

Expected findings must be created before running the evaluated system.

Do not modify expected results merely to improve scores.

If the benchmark contains an accidental additional defect, document it and update the dataset transparently.

---

# Reproducibility

Each benchmark should record:

```text
dataset ID
base commit
head commit
PR Guardian version
Bob session/task
tools available
commands executed
date
```

---

# Hackathon Presentation Metrics

Strong metrics to show include:

```text
known defects detected
false positives removed by verification
adaptive reviewers skipped
verification tests generated
verified final findings
review time comparison
```

Avoid opaque scores such as:

```text
PR quality: 94/100
```

Prefer measurable engineering evidence.

---

# Example Presentation

```text
Benchmark PRs:              8
Known injected defects:    12

Baseline detected:          7
PR Guardian detected:      11

Initial PR Guardian findings: 18
Refuted by verification:       4
Duplicates consolidated:       3
Final published findings:     11

Reviewers available per PR:    7
Average reviewers selected:    3.1
```

All numbers must come from actual benchmark runs.

---

# Engineering Principle

A successful benchmark should answer:

> Does PR Guardian find meaningful defects while producing less unsupported review noise?

The benchmark exists to measure that question, not to manufacture a favorable score.