# PR Guardian

PR Guardian is an evidence-based, multi-agent Pull Request review harness designed to improve software review workflows.

IBM Bob is the primary AI engineering environment used to orchestrate repository understanding, change-impact analysis, code review, security review, test-impact analysis, architecture review, finding verification, and review synthesis.

The project goal is not simply to generate comments for a Pull Request.

The goal is to produce contextual, measurable, and verifiable engineering reviews.

---

## Core Principles

PR Guardian follows four principles:

### Contextual

Do not analyze only the diff.

Whenever possible, understand:

* surrounding code;
* dependencies;
* related modules;
* tests;
* architecture;
* API contracts;
* database models;
* queue or asynchronous behavior;
* repository conventions.

---

### Adaptive

Do not execute every reviewer for every Pull Request.

Select only the review skills relevant to the change.

Examples:

A documentation-only Pull Request should not trigger database or security analysis unless required.

An authentication-related Pull Request should trigger security and test-impact analysis.

---

### Multi-Agent

Use specialized review skills for different engineering concerns.

Core review domains include:

* Pull Request understanding;
* change impact;
* code correctness;
* security;
* testing;
* architecture;
* database changes;
* APIs;
* queues and asynchronous processing.

---

### Evidence-Based

Do not treat every AI-generated observation as a confirmed defect.

Whenever practical, verify important findings using:

* tests;
* static analyzers;
* security analyzers;
* repository evidence;
* dependency analysis;
* reproducible execution.

Prefer:

```text
finding
    ↓
evidence
    ↓
verification
    ↓
review
```

over:

```text
finding
    ↓
comment
```

---

## Main Workflow

The expected review workflow is:

```text
Pull Request
    ↓
PR Understanding
    ↓
Repository Context
    ↓
Change Impact
    ↓
Adaptive Reviewer Selection
    ↓
Parallel Specialized Reviews
    ↓
Finding Normalization
    ↓
Finding Verification
    ↓
Deduplication
    ↓
Review Synthesis
    ↓
Metrics
    ↓
Final Review
```

Do not skip directly from diff extraction to final review.

---

## Repository Structure

The main project structure is:

```text
.bob/
app/
guardian/
github/
repository/
analyzers/
models/
reports/
workspace/
benchmarks/
docs/
tests/
bob_sessions/
```

---

## Target Repositories

Repositories under analysis must be stored temporarily under:

```text
workspace/repositories/
```

These repositories are runtime workspaces and must not be committed.

Do not treat target repositories as part of PR Guardian source code.

---

## Bob Skills

Project-specific Bob skills are located under:

```text
.bob/skills/
```

Core skills include:

```text
pr-understanding
change-impact
code-review
security-review
test-impact
architecture-review
database-review
api-review
queue-review
finding-verification
review-synthesis
```

Use specialized skills instead of placing detailed engineering knowledge in this file.

---

## Skill Responsibilities

### pr-understanding

Determine the purpose, scope, changed files, commits, affected domains, and technical intent of the Pull Request.

---

### change-impact

Identify direct and indirect consequences of modified code.

Consider:

* callers;
* dependencies;
* public interfaces;
* tests;
* APIs;
* persistence;
* background jobs.

---

### code-review

Analyze correctness, maintainability, error handling, edge cases, regressions, and implementation defects.

---

### security-review

Identify security-sensitive changes and risks involving:

* authentication;
* authorization;
* injection;
* secrets;
* input validation;
* file handling;
* cryptography;
* API keys;
* unsafe execution.

---

### test-impact

Determine whether the Pull Request is adequately tested.

Identify:

* affected tests;
* missing tests;
* regression risks;
* uncovered behavior;
* opportunities for executable verification.

---

### architecture-review

Analyze architectural boundaries, coupling, responsibilities, layering, SOLID principles, and maintainability.

---

### database-review

Analyze database-related changes including:

* schema;
* ORM models;
* migrations;
* queries;
* indexes;
* transactions;
* constraints;
* N+1 risks.

---

### api-review

Review API changes and verify consistency with:

* routes;
* HTTP behavior;
* request schemas;
* response schemas;
* OpenAPI definitions;
* compatibility expectations.

---

### queue-review

Analyze background processing and asynchronous code.

Consider:

* retries;
* timeouts;
* idempotency;
* failure handling;
* queue selection;
* observability;
* duplicate execution.

---

### finding-verification

Validate significant findings using deterministic evidence whenever practical.

Examples:

* pytest;
* coverage;
* Bandit;
* Semgrep;
* Ruff;
* pip-audit;
* repository inspection.

---

### review-synthesis

Consolidate findings into a concise, actionable Pull Request review.

Remove duplicates and low-value noise.

---

## Findings

All findings should follow a common structure.

Each finding should contain, whenever applicable:

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
```

---

## Severity

Use the following severity levels:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Severity must reflect actual technical impact.

Do not inflate severity to make reports appear more important.

---

## Confidence

Use the following confidence classifications:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

Definitions:

### CONFIRMED

The issue has direct evidence or has been reproduced.

### LIKELY

Strong evidence exists, but full reproduction has not been performed.

### POTENTIAL

The issue is plausible but requires additional validation.

### INFORMATIONAL

The finding is primarily contextual or advisory.

---

## Verification Status

Use:

```text
VERIFIED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
```

A finding may be high severity but still unverified.

Keep severity and confidence independent.

---

## Review Noise

Avoid unnecessary comments.

Do not report:

* formatting preferences already handled by linters;
* purely subjective style preferences;
* speculative architectural opinions without evidence;
* duplicate findings;
* trivial observations with no engineering impact.

Prioritize high-value findings.

---

## Inline Comments

Inline Pull Request comments should be used only when the finding is tied to a specific changed line or file.

Prefer inline publication for:

```text
CONFIRMED
LIKELY
```

Use summary reports for:

```text
POTENTIAL
INFORMATIONAL
```

unless the finding is important enough to require attention.

---

## Production Code Changes

PR Guardian is primarily a review system.

Do not modify the target Pull Request automatically unless the current task explicitly requires implementation or remediation.

Analysis tasks should remain read-only.

---

## Tests

When a finding can be verified through a regression test, prefer:

```text
identify potential issue
    ↓
create isolated test
    ↓
execute test
    ↓
classify finding
```

Generated tests must use safe and isolated test data.

Do not modify production behavior merely to force a test result.

---

## Static Analysis

Use deterministic tools when appropriate.

Possible tools include:

```text
pytest
coverage
ruff
bandit
semgrep
pip-audit
mypy
```

Tool output must be interpreted.

Do not automatically treat every tool warning as a confirmed defect.

---

## Metrics

Every review should produce measurable results when possible.

Useful metrics include:

```text
files_changed
lines_added
lines_removed
files_analyzed

reviewers_executed

findings_total
findings_critical
findings_high
findings_medium
findings_low

findings_confirmed
findings_likely
findings_potential

tests_executed
tests_passed
tests_failed

generated_tests
verified_findings

analysis_duration_seconds
```

Avoid arbitrary scores when objective values are available.

---

## Reports

Human-readable reports belong under:

```text
reports/
```

Suggested structure:

```text
reports/raw/
reports/findings/
reports/verification/
reports/reviews/
reports/metrics/
```

Use Markdown for human-readable output.

Use JSON for machine-readable output.

---

## Benchmarks

Controlled Pull Request datasets belong under:

```text
benchmarks/
```

Use benchmark cases with known defects when measuring reviewer quality.

Possible cases include:

```text
SQL injection
authorization bypass
N+1 query
breaking API change
missing retry
insufficient test coverage
unsafe migration
command injection
```

Benchmark findings must be documented separately from generated results.

---

## Baseline Comparison

When evaluating PR Guardian, preserve both:

```text
baseline/
```

and:

```text
bob-assisted/
```

results.

Do not overwrite baseline evidence.

Metrics should support comparisons such as:

```text
manual review time
vs
Bob-assisted review time
```

and:

```text
known issues
vs
detected issues
```

---

## GitHub Integration

GitHub integration should remain isolated from review logic.

The `github/` package handles:

* Pull Request retrieval;
* changed files;
* commits;
* review publication;
* webhooks.

The review engine should not depend directly on HTTP request details.

---

## Repository Analysis

Repository inspection belongs under:

```text
repository/
```

Responsibilities include:

* cloning;
* diff extraction;
* file analysis;
* dependency analysis;
* repository history;
* call relationships.

---

## Review Orchestration

Review workflow code belongs under:

```text
guardian/
```

The orchestrator coordinates the complete review.

The router decides which reviewers are relevant.

Example:

```text
PR modifies README only
    ↓
documentation-related analysis

PR modifies authentication
    ↓
code-review
security-review
test-impact

PR modifies SQL and migrations
    ↓
code-review
database-review
test-impact
```

Do not invoke unnecessary reviewers.

---

## Security

Never expose or commit:

```text
GitHub tokens
API keys
passwords
private keys
database credentials
webhook secrets
```

Use environment variables.

Provide safe examples through:

```text
.env.example
```

---

## Data Policy

Use only safe demonstration data.

Do not include:

* confidential company repositories;
* private customer data;
* personal information;
* secrets;
* production credentials.

Benchmark repositories should contain synthetic or appropriately licensed data.

Document public datasets and repositories used for evaluation under:

```text
docs/data-sources.md
```

---

## Bob Session Evidence

Bob IDE task screenshots belong under:

```text
bob_sessions/
```

Use descriptive filenames.

Examples:

```text
task01_pr_understanding.png
task02_security_review.png
task03_test_impact.png
task04_finding_verification.png
task05_review_synthesis.png
```

Do not delete valid hackathon evidence.

---

## Engineering Goal

PR Guardian should optimize for:

```text
review quality
developer time saved
low review noise
high-value findings
reproducibility
verification
measurable impact
```

The goal is not to generate the maximum number of comments.

The goal is to help developers identify meaningful Pull Request risks faster and with stronger engineering evidence.